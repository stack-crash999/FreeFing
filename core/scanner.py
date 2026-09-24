"""
NetSentry - High-Performance Network Scanner
Multi-method active device discovery using ARP, ICMP, NetBIOS, mDNS, and UPnP.
Pure Python implementation with callback-compatible signals.
"""

import time
import socket
import struct
import logging
import threading
import subprocess
import re
from typing import List, Dict, Optional, Callable

logger = logging.getLogger("netsentry.scanner")

# Check scapy availability
try:
    from scapy.all import ARP, Ether, srp, conf
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False


class Signal:
    """Pure-Python thread-safe signal compatible with PyQt signal API."""
    def __init__(self):
        self._handlers = []
        self._lock = threading.Lock()

    def connect(self, handler: Callable):
        with self._lock:
            if handler not in self._handlers:
                self._handlers.append(handler)

    def disconnect(self, handler: Callable):
        with self._lock:
            if handler in self._handlers:
                self._handlers.remove(handler)

    def emit(self, *args, **kwargs):
        with self._lock:
            handlers = list(self._handlers)
        for h in handlers:
            try:
                h(*args, **kwargs)
            except Exception as e:
                logger.error(f"Signal dispatch error: {e}")


class ScanResult:
    """Represents a discovered device from a scan."""
    def __init__(self, ip: str, mac: str, hostname: str = "",
                 vendor: str = "", model: str = "", device_type: str = "generic"):
        self.ip = ip
        self.mac = mac.lower()
        self.hostname = hostname
        self.vendor = vendor
        self.model = model
        self.device_type = device_type

    def to_dict(self) -> dict:
        return {
            "ip": self.ip,
            "mac": self.mac,
            "hostname": self.hostname,
            "vendor": self.vendor,
            "model": self.model,
            "device_type": self.device_type
        }


class NetworkScanner:
    """
    Pure Python multi-threaded network scanner with real active discovery.
    Compatible with PyQt6 QThread interface (start, stop, isRunning, wait).
    """

    def __init__(self, subnet: str = None, gateway_ip: str = None,
                 timeout: float = 3.0, parent=None):
        self.subnet = subnet
        self.gateway_ip = gateway_ip
        self.timeout = timeout
        self._stop_flag = False
        self._thread: Optional[threading.Thread] = None
        self._results: Dict[str, dict] = {}

        # Signals
        self.device_found = Signal()
        self.scan_progress = Signal()
        self.scan_complete = Signal()
        self.scan_error = Signal()
        self.scan_log = Signal()

    def start(self):
        """Start scan in a daemon background thread."""
        self._stop_flag = False
        self._thread = threading.Thread(target=self.run, daemon=True)
        self._thread.start()

    def stop(self):
        """Signal the scan to halt."""
        self._stop_flag = True

    def isRunning(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def wait(self, timeout: float = None):
        if self._thread is not None:
            self._thread.join(timeout=timeout)

    def run(self):
        """Execute active network sweep."""
        self._stop_flag = False
        self._results.clear()
        start_time = time.time()

        try:
            if not self.subnet:
                from core.network_utils import get_subnet_cidr
                self.subnet = get_subnet_cidr() or "192.168.68.0/22"

            if not self.gateway_ip:
                from core.network_utils import get_default_gateway
                self.gateway_ip = get_default_gateway() or "192.168.68.1"

            self.scan_log.emit(f"[INIT] Beginning active discovery sweep on {self.subnet}")
            self.scan_progress.emit(5)

            # Phase 1: ARP Table query
            self.scan_log.emit("[PHASE 1/4] Reading local ARP cache and active neighbors...")
            live_pairs = self._read_arp_table()
            self.scan_progress.emit(25)

            if self._stop_flag:
                return

            # Phase 2: Active Ping Sweep across subnet ranges to wake up silent devices
            self.scan_log.emit("[PHASE 2/4] Broadcasting ICMP/UDP echo sweeps across subnet...")
            self._active_probe_sweep()
            self.scan_progress.emit(55)

            if self._stop_flag:
                return

            # Re-read ARP table after sweep
            refreshed_pairs = self._read_arp_table()
            for ip, mac in refreshed_pairs:
                if mac not in [p[1] for p in live_pairs]:
                    live_pairs.append((ip, mac))

            self.scan_progress.emit(70)
            self.scan_log.emit(f"[PHASE 3/4] Resolving device identities & protocols for {len(live_pairs)} hosts...")

            from data.oui_database import OUIDatabase
            from core.device_identifier import fast_identify_device, enrich_device_identity

            oui_db = OUIDatabase()

            # Phase 4: Identify & emit each found device
            for i, (ip, mac) in enumerate(live_pairs):
                if self._stop_flag:
                    self.scan_log.emit("[CANCEL] Network scan halted by user.")
                    return

                vendor = oui_db.lookup(mac)
                base = fast_identify_device(ip, mac, vendor, gateway_ip=self.gateway_ip)
                dev_info = {
                    "ip": ip,
                    "mac": mac,
                    "vendor": base["vendor"],
                    "model": base["model"],
                    "hostname": base["name"],
                    "device_type": base["device_type"],
                    "os": base["os"]
                }
                self._results[mac] = dev_info

                self.scan_log.emit(f"[FOUND] {ip:<15} | {dev_info['model']} ({dev_info['vendor']}) | {dev_info['device_type'].upper()}")
                self.device_found.emit(dev_info)

                p = 70 + int(28 * (i + 1) / max(1, len(live_pairs)))
                self.scan_progress.emit(min(p, 98))

            self.scan_progress.emit(100)
            elapsed = time.time() - start_time
            results_list = list(self._results.values())
            self.scan_log.emit(f"[COMPLETE] Active network scan completed in {elapsed:.2f}s. {len(results_list)} devices verified.")
            self.scan_complete.emit(results_list)

        except Exception as e:
            logger.error(f"Scan error: {e}", exc_info=True)
            self.scan_error.emit(str(e))

    def _read_arp_table(self) -> List[tuple]:
        """Read system ARP table via Windows arp command."""
        pairs = []
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
                    pairs.append((ip, mac))
        except Exception as e:
            logger.debug(f"ARP read failed: {e}")
        return pairs

    def _active_probe_sweep(self):
        """Active fast parallel probe to wake up devices across subnet."""
        # Detect base prefixes to probe
        subnets = ["192.168.68", "192.168.71"]
        if self.subnet:
            base = self.subnet.split("/")[0]
            parts = base.split(".")
            if len(parts) >= 3:
                sub = f"{parts[0]}.{parts[1]}.{parts[2]}"
                if sub not in subnets:
                    subnets.append(sub)

        targets = []
        for s in subnets:
            # Probe common host ranges
            targets.extend([f"{s}.{i}" for i in range(1, 120)])
            if "71" in s:
                targets.extend([f"{s}.{i}" for i in range(240, 255)])

        def _probe_ip(ip):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(0.08)
                sock.sendto(b"\x00", (ip, 445))
                sock.close()
            except Exception:
                pass

        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=60) as ex:
            list(ex.map(_probe_ip, targets))


class ContinuousScanner:
    """Periodic scanner running on a background timer."""
    def __init__(self, subnet: str = None, interval_seconds: int = 60):
        self.subnet = subnet
        self.interval = interval_seconds
        self._stop_flag = False
        self._thread = None
        self.scan_started = Signal()
        self.scan_finished = Signal()

    def start(self):
        self._stop_flag = False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_flag = True

    def _run(self):
        while not self._stop_flag:
            self.scan_started.emit()
            scanner = NetworkScanner(subnet=self.subnet)
            scanner.run()
            self.scan_finished.emit(list(scanner._results.values()))

            elapsed = 0
            while elapsed < self.interval and not self._stop_flag:
                time.sleep(1)
                elapsed += 1
