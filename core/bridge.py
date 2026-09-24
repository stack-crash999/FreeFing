"""
NetSentry - JSON IPC Bridge
Headless backend bridge for C# / .NET frontend.
Communicates via JSON-lines over stdin / stdout.
"""

import sys
import os
import re
import json
import time
import socket
import logging
import threading
import subprocess
from datetime import datetime
from typing import Dict, List

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from data.device_store import DeviceStore, DeviceRecord
from data.oui_database import OUIDatabase
from core.network_utils import get_network_info, get_local_mac
from core.scanner import NetworkScanner
from core.device_identifier import fast_identify_device, enrich_device_identity, discover_upnp_devices
from core.fingerprinter import DeviceFingerprinter
from core.arp_spoofer import ARPSpoofer
from core.packet_handler import PacketHandler

logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("netsentry.bridge")


import ipaddress

def is_ip_in_subnet(ip: str, subnet_cidr: str) -> bool:
    """Check if an IPv4 address belongs to the given subnet CIDR."""
    if not ip or not subnet_cidr:
        return False
    try:
        net = ipaddress.ip_network(subnet_cidr, strict=False)
        return ipaddress.ip_address(ip) in net
    except Exception:
        return False


def discover_arp_table() -> List[tuple]:
    """Parse local system ARP table for all active dynamic hosts."""
    devices = []
    try:
        res = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=5)
        pattern = re.compile(
            r"(\d+\.\d+\.\d+\.\d+)\s+([\da-fA-F]{2}[-:][\da-fA-F]{2}[-:][\da-fA-F]{2}[-:][\da-fA-F]{2}[-:][\da-fA-F]{2}[-:][\da-fA-F]{2})\s+(\w+)"
        )
        for m in pattern.finditer(res.stdout):
            ip = m.group(1)
            mac = m.group(2).replace("-", ":").lower()
            atype = m.group(3).lower()
            if atype == "dynamic" and mac != "ff:ff:ff:ff:ff:ff":
                devices.append((ip, mac))
    except Exception as e:
        logger.debug(f"ARP table parse error: {e}")
    return devices


class BridgeService:
    def __init__(self):
        self.device_store = DeviceStore()
        self.oui_db = OUIDatabase()
        self.packet_handler = PacketHandler()
        self.network_info = get_network_info()
        self.local_mac = get_local_mac()

        self.devices = {}
        self.upnp_cache = {}
        self.scanner = None
        self.fingerprinter = None
        self.arp_spoofer = None

        self._init_spoofer()
        self._load_stored_devices()
        # Launch background initial discovery, UPnP, and network monitor
        threading.Thread(target=self._initial_discovery_worker, daemon=True).start()
        threading.Thread(target=self._network_monitor_loop, daemon=True).start()

    def _network_monitor_loop(self):
        """Periodically checks if network interface, IP, or SSID has changed."""
        last_ssid = self.network_info.get("ssid")
        last_ip = self.network_info.get("local_ip")
        last_subnet = self.network_info.get("subnet")
        while True:
            time.sleep(4)
            try:
                curr_info = get_network_info()
                curr_ssid = curr_info.get("ssid")
                curr_ip = curr_info.get("local_ip")
                curr_subnet = curr_info.get("subnet")
                if curr_ssid != last_ssid or curr_ip != last_ip or curr_subnet != last_subnet:
                    logger.info(f"Network switch detected: {last_ssid} ({last_ip}) -> {curr_ssid} ({curr_ip}) on {curr_subnet}")
                    last_ssid = curr_ssid
                    last_ip = curr_ip
                    last_subnet = curr_subnet
                    self.network_info = curr_info

                    # Flush old network devices from active memory so old network devices disappear
                    self.devices.clear()
                    self.upnp_cache.clear()

                    # Notify UI of network update and device list purge
                    self.send_event("network_updated", curr_info)
                    self.send_event("devices_cleared", {"subnet": curr_subnet, "ssid": curr_ssid})

                    # Re-init spoofer for new gateway
                    if self.arp_spoofer:
                        self.arp_spoofer.stop()
                    self._init_spoofer()

                    # Trigger fresh discovery for new network
                    threading.Thread(target=self._initial_discovery_worker, daemon=True).start()
            except Exception as e:
                logger.debug(f"Network monitor error: {e}")

    def _init_spoofer(self):
        gw_ip = self.network_info.get("gateway_ip")
        gw_mac = self.network_info.get("gateway_mac")
        self.arp_spoofer = ARPSpoofer(gateway_ip=gw_ip, gateway_mac=gw_mac)
        self.arp_spoofer.spoof_error.connect(self._on_spoof_error)
        self.arp_spoofer.start()
        try:
            self.packet_handler.enable_blocking_mode()
        except Exception as e:
            logger.debug(f"Packet handler blocking mode error: {e}")

        # Restore previously blocked devices
        try:
            blocked_devices = self.device_store.get_blocked_devices()
            curr_subnet = self.network_info.get("subnet", "")
            for bdev in blocked_devices:
                if bdev.ip and bdev.mac and (not curr_subnet or is_ip_in_subnet(bdev.ip, curr_subnet)):
                    self.arp_spoofer.add_target(bdev.ip, bdev.mac)
                    logger.info(f"Restored active block: {bdev.ip} ({bdev.mac})")
        except Exception as e:
            logger.debug(f"Error restoring blocked devices: {e}")

    def _on_spoof_error(self, err_msg: str):
        logger.error(f"ARP Spoofer error: {err_msg}")
        self.send_event("scan_log", {"message": f"[ERROR] Spoofer: {err_msg}"})

    def _get_current_subnet_devices(self) -> List[dict]:
        """Return only devices that belong to the active subnet."""
        curr_subnet = self.network_info.get("subnet", "")
        if not curr_subnet:
            return list(self.devices.values())
        return [d for d in self.devices.values() if is_ip_in_subnet(d.get("ip", ""), curr_subnet)]

    def _load_stored_devices(self):
        """Immediately load stored devices into memory so UI is instantly responsive."""
        stored = self.device_store.get_all_devices()
        curr_subnet = self.network_info.get("subnet", "")
        for d in stored:
            m = d.mac.lower()
            if not curr_subnet or is_ip_in_subnet(d.ip, curr_subnet):
                self.devices[m] = d.to_dict()

        # If database is empty or has fewer than 2 devices, do instant fast ARP identification
        if len(self.devices) < 2:
            gw_ip = self.network_info.get("gateway_ip", "")
            gw_mac = (self.network_info.get("gateway_mac") or "").lower()
            local_ip = self.network_info.get("local_ip", "")
            local_mac = (self.local_mac or "").lower()

            arp_entries = discover_arp_table()
            if gw_ip and gw_mac:
                arp_entries.append((gw_ip, gw_mac))
            if local_ip and local_mac:
                arp_entries.append((local_ip, local_mac))

            curr_subnet = self.network_info.get("subnet", "")
            for ip, mac in arp_entries:
                if not mac or mac == "ff:ff:ff:ff:ff:ff":
                    continue
                if curr_subnet and not is_ip_in_subnet(ip, curr_subnet):
                    continue
                m = mac.lower()
                if m in self.devices:
                    continue
                v = self.oui_db.lookup(m)
                base = fast_identify_device(ip, m, v, gw_ip, local_ip, local_mac)
                dev = {
                    "mac": m,
                    "ip": ip,
                    "hostname": base["name"],
                    "vendor": base["vendor"],
                    "model": base["model"],
                    "os": base["os"],
                    "device_type": base["device_type"],
                    "is_online": True,
                    "is_blocked": False,
                    "times_seen": 10,
                    "last_seen": datetime.now().isoformat(),
                    "custom_name": "",
                }
                self.devices[m] = dev
                self.device_store.upsert_device(DeviceRecord.from_dict(dev))

    def _initial_discovery_worker(self):
        """Runs in background to discover live hosts, query UPnP, and enrich devices."""
        try:
            # 1. Background UPnP probe
            upnp_found = discover_upnp_devices(timeout=1.5)
            if upnp_found:
                self.upnp_cache.update(upnp_found)

            gw_ip = self.network_info.get("gateway_ip", "")
            gw_mac = (self.network_info.get("gateway_mac") or "").lower()
            local_ip = self.network_info.get("local_ip", "")
            local_mac = (self.local_mac or "").lower()

            # 2. Collect ARP table entries
            arp_entries = discover_arp_table()
            if gw_ip and gw_mac:
                arp_entries.append((gw_ip, gw_mac))
            if local_ip and local_mac:
                arp_entries.append((local_ip, local_mac))

            # Deduplicate by MAC & filter to active subnet
            curr_subnet = self.network_info.get("subnet", "")
            unique_targets = {}
            for ip, mac in arp_entries:
                if mac and mac != "ff:ff:ff:ff:ff:ff":
                    if not curr_subnet or is_ip_in_subnet(ip, curr_subnet):
                        unique_targets[mac.lower()] = ip

            def _enrich_worker(item):
                m, ip_addr = item
                existing = self.devices.get(m)
                v = self.oui_db.lookup(m)
                base = fast_identify_device(ip_addr, m, v, gw_ip, local_ip, local_mac)
                enriched = enrich_device_identity(ip_addr, m, base, self.upnp_cache)
                return m, ip_addr, enriched

            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                results = list(executor.map(_enrich_worker, unique_targets.items()))

            for m, ip_addr, id_data in results:
                existing = self.devices.get(m)
                final_name = (existing.get("hostname") if existing and existing.get("hostname") else "") or id_data["name"]
                custom_name = existing.get("custom_name", "") if existing else ""

                dev = {
                    "mac": m,
                    "ip": ip_addr,
                    "hostname": final_name,
                    "vendor": id_data["vendor"],
                    "model": id_data["model"],
                    "os": id_data["os"],
                    "device_type": id_data["device_type"],
                    "is_online": True,
                    "is_blocked": existing.get("is_blocked", False) if existing else False,
                    "times_seen": (existing.get("times_seen", 1) + 1) if existing else 10,
                    "last_seen": datetime.now().isoformat(),
                    "custom_name": custom_name,
                }
                self.devices[m] = dev
                self.device_store.upsert_device(DeviceRecord.from_dict(dev))
                self.send_event("device_updated" if existing else "device_found", dev)

        except Exception as e:
            logger.debug(f"Initial discovery worker error: {e}")



    def send_event(self, event_type: str, data: dict):
        msg = json.dumps({"type": "event", "event": event_type, "data": data})
        sys.stdout.write(msg + "\n")
        sys.stdout.flush()

    def send_response(self, req_id: int, success: bool, data=None, error: str = ""):
        msg = json.dumps({
            "type": "response",
            "id": req_id,
            "success": success,
            "data": data,
            "error": error
        })
        sys.stdout.write(msg + "\n")
        sys.stdout.flush()

    def handle_command(self, cmd_obj: dict):
        req_id = cmd_obj.get("id", 0)
        cmd = cmd_obj.get("cmd") or cmd_obj.get("command") or ""

        if cmd == "get_info":
            try:
                self.network_info = get_network_info()
            except Exception as e:
                logger.debug(f"Error refreshing network info in get_info: {e}")
            self.send_response(req_id, True, {
                "network": self.network_info,
                "local_mac": self.local_mac,
                "device_count": len(self.devices)
            })

        elif cmd == "get_devices":
            self.send_response(req_id, True, self._get_current_subnet_devices())

        elif cmd == "start_scan":
            self._start_scan()
            self.send_response(req_id, True, {"status": "scanning"})

        elif cmd == "stop_scan":
            self._stop_scan()
            self.send_response(req_id, True, {"status": "stopped"})

        elif cmd == "block_device":
            raw_mac = cmd_obj.get("mac", "")
            mac = raw_mac.lower().replace("-", ":").strip()
            if mac not in self.devices:
                stored = self.device_store.get_device(mac)
                if stored:
                    self.devices[mac] = stored.to_dict()

            if mac in self.devices:
                dev = self.devices[mac]
                gw_ip = self.network_info.get("gateway_ip", "")
                gw_mac = (self.network_info.get("gateway_mac") or "").lower().replace("-", ":")
                if dev.get("ip") == gw_ip or mac == gw_mac:
                    self.send_response(req_id, False, error="Cannot block default gateway")
                    return

                # If IP is missing, try resolving from ARP table
                if not dev.get("ip"):
                    for tip, tmac in discover_arp_table():
                        if tmac == mac:
                            dev["ip"] = tip
                            break

                target_ip = dev.get("ip")
                if not target_ip:
                    self.send_response(req_id, False, error="Target IP unknown")
                    return

                if self.arp_spoofer:
                    self.arp_spoofer.add_target(target_ip, mac)
                dev["is_blocked"] = True
                self.device_store.set_blocked(mac, True)
                self.send_response(req_id, True, dev)
                self.send_event("device_updated", dev)
                target_name = dev.get("custom_name") or dev.get("hostname") or target_ip
                self.send_event("scan_log", {"message": f"[SECURITY] 🚫 Blocked network access for {target_name} ({mac})"})
            else:
                self.send_response(req_id, False, error=f"Device {raw_mac} not found")

        elif cmd == "unblock_device":
            raw_mac = cmd_obj.get("mac", "")
            mac = raw_mac.lower().replace("-", ":").strip()
            if mac not in self.devices:
                stored = self.device_store.get_device(mac)
                if stored:
                    self.devices[mac] = stored.to_dict()

            if mac in self.devices:
                dev = self.devices[mac]
                if self.arp_spoofer:
                    self.arp_spoofer.remove_target(mac)
                dev["is_blocked"] = False
                self.device_store.set_blocked(mac, False)
                self.send_response(req_id, True, dev)
                self.send_event("device_updated", dev)
                target_name = dev.get("custom_name") or dev.get("hostname") or dev.get("ip")
                self.send_event("scan_log", {"message": f"[SECURITY] 🟢 Restored network access for {target_name} ({mac})"})
            else:
                self.send_response(req_id, False, error=f"Device {raw_mac} not found")

        elif cmd == "rename_device":
            mac = cmd_obj.get("mac", "").lower()
            new_name = cmd_obj.get("name", "")
            if mac in self.devices:
                self.devices[mac]["custom_name"] = new_name
                self.device_store.set_custom_name(mac, new_name)
                self.send_response(req_id, True, self.devices[mac])
                self.send_event("device_updated", self.devices[mac])
            else:
                self.send_response(req_id, False, error="Device not found")
        else:
            self.send_response(req_id, False, error=f"Unknown command: {cmd}")

    def _refresh_upnp(self):
        """Asynchronously refresh UPnP descriptors."""
        try:
            upnp_found = discover_upnp_devices(timeout=1.5)
            if upnp_found:
                self.upnp_cache.update(upnp_found)
        except Exception as e:
            logger.debug(f"UPnP refresh error: {e}")

    def _start_scan(self):
        if self.scanner and self.scanner.isRunning():
            return
        try:
            self.network_info = get_network_info()
            self.send_event("network_updated", self.network_info)
        except Exception:
            pass

        subnet = self.network_info.get("subnet", "192.168.68.0/22")
        gw_ip = self.network_info.get("gateway_ip", "192.168.68.1")
        self.send_event("scan_log", {"message": f"[INIT] Starting comprehensive network discovery on {subnet}"})
        self.send_event("scan_log", {"message": f"[GATEWAY] Target gateway identified at {gw_ip}"})

        # Trigger UPnP discovery in parallel
        threading.Thread(target=self._refresh_upnp, daemon=True).start()

        self.scanner = NetworkScanner(subnet=subnet, gateway_ip=gw_ip, timeout=3.0)
        self.scanner.device_found.connect(self._on_scanner_device_found)
        self.scanner.scan_progress.connect(self._on_scan_progress)
        self.scanner.scan_complete.connect(self._on_scan_complete)
        self.scanner.scan_log.connect(self._on_scan_log_msg)
        self.scanner.start()

    def _on_scan_log_msg(self, msg: str):
        self.send_event("scan_log", {"message": msg})

    def _on_scan_progress(self, p: int):
        self.send_event("scan_progress", {"progress": p})
        if p == 10:
            self.send_event("scan_log", {"message": "[PHASE 1/4] Broadcasting ARP queries across subnet..."})
        elif p == 40:
            self.send_event("scan_log", {"message": "[PHASE 2/4] Executing ICMP echo probe sweep..."})
        elif p == 70:
            self.send_event("scan_log", {"message": "[PHASE 3/4] Resolving hostnames via mDNS, UPnP and NetBIOS..."})
        elif p == 90:
            self.send_event("scan_log", {"message": "[PHASE 4/4] Fingerprinting hardware vendors & matching OUI..."})

    def _stop_scan(self):
        if self.scanner and self.scanner.isRunning():
            self.scanner.stop()
            self.send_event("scan_log", {"message": "[STOP] Network scan halted by user."})

    def _on_scanner_device_found(self, d_info: dict):
        mac = d_info.get("mac", "").lower()
        if not mac:
            return
        ip = d_info.get("ip", "")
        curr_subnet = self.network_info.get("subnet", "")
        if curr_subnet and not is_ip_in_subnet(ip, curr_subnet):
            return
        passed_hostname = d_info.get("hostname", "")

        gw_ip = self.network_info.get("gateway_ip", "")
        local_ip = self.network_info.get("local_ip", "")
        local_mac = (self.local_mac or "").lower()

        vendor = self.oui_db.lookup(mac)
        base = fast_identify_device(ip, mac, vendor, gw_ip, local_ip, local_mac)
        id_data = enrich_device_identity(ip, mac, base, self.upnp_cache)

        final_name = passed_hostname or id_data["name"]

        if mac in self.devices:
            dev = self.devices[mac]
            dev["ip"] = ip
            dev["is_online"] = True
            if final_name and not dev.get("custom_name"):
                dev["hostname"] = final_name
            if id_data["model"]:
                dev["model"] = id_data["model"]
            if id_data["vendor"] and dev.get("vendor") in ["", "Unknown"]:
                dev["vendor"] = id_data["vendor"]
            if id_data["device_type"] != "generic":
                dev["device_type"] = id_data["device_type"]
            dev["os"] = id_data["os"]
            dev["last_seen"] = datetime.now().isoformat()
        else:
            dev = {
                "mac": mac,
                "ip": ip,
                "hostname": final_name,
                "vendor": id_data["vendor"],
                "model": id_data["model"],
                "os": id_data["os"],
                "device_type": id_data["device_type"],
                "is_online": True,
                "is_blocked": False,
                "times_seen": 1,
                "last_seen": datetime.now().isoformat(),
                "custom_name": "",
            }
            self.devices[mac] = dev

        # Save to SQLite store
        self.device_store.upsert_device(DeviceRecord.from_dict(dev))

        self.send_event("scan_log", {
            "message": f"[IDENTIFIED] {ip:<15} | {dev['model']} ({dev['vendor']}) | Type: {dev['device_type']}"
        })
        self.send_event("device_found", dev)

    def _on_scan_complete(self, results: list):
        count = len(results) if results else len(self.devices)
        self.send_event("scan_log", {"message": f"[COMPLETE] Network scan finished. {count} active device(s) verified."})
        self.send_event("scan_complete", {"count": count})

    def cleanup(self):
        if self.arp_spoofer:
            self.arp_spoofer.stop()
        self.packet_handler.restore_original_state()


def main():
    bridge = BridgeService()
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                cmd = json.loads(line)
                bridge.handle_command(cmd)
            except Exception as e:
                logger.error(f"Error handling cmd: {e}")
    finally:
        bridge.cleanup()


if __name__ == "__main__":
    main()
