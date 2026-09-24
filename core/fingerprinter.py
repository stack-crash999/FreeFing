"""
NetSentry - Device Fingerprinter
Identifies device types using OUI lookup, port scanning, banner grabbing,
and heuristic classification.
"""

import json
import os
import socket
import logging
import threading
from typing import Optional, List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger("netsentry.fingerprinter")

# Load port signatures
_SIGNATURES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "port_signatures.json")

try:
    with open(_SIGNATURES_PATH, "r") as f:
        PORT_SIGNATURES = json.load(f)
except Exception:
    PORT_SIGNATURES = {"tcp_ports": {}, "device_categories": {}, "vendor_to_category": {}}


# Top ports to scan for fingerprinting (ordered by likelihood of being useful)
TOP_PORTS = [
    80, 443, 22, 23, 53, 139, 445, 548, 554, 631,
    5353, 5555, 7000, 8008, 8009, 8060, 8080, 8443,
    9100, 62078, 3389, 5900, 9200, 49152, 49153,
    1900, 3000, 5000, 5001, 6466, 6467, 7100, 8888,
    9000, 9080, 10001, 21, 25
]


class PortScanResult:
    """Result of a port scan on a single port."""
    def __init__(self, port: int, is_open: bool, service: str = "",
                 banner: str = "", category: str = ""):
        self.port = port
        self.is_open = is_open
        self.service = service
        self.banner = banner
        self.category = category


class DeviceFingerprint:
    """Complete fingerprint result for a device."""
    def __init__(self, ip: str, mac: str):
        self.ip = ip
        self.mac = mac
        self.vendor = "Unknown"
        self.hostname = ""
        self.model = ""
        self.os = "Windows"
        self.device_type = "unknown"
        self.device_name = ""
        self.open_ports: List[PortScanResult] = []
        self.categories_detected: List[str] = []
        self.confidence = 0.0

    def to_dict(self) -> dict:
        return {
            "ip": self.ip,
            "mac": self.mac,
            "vendor": self.vendor,
            "hostname": self.hostname,
            "model": self.model,
            "os": self.os,
            "device_type": self.device_type,
            "device_name": self.device_name,
            "open_ports": [
                {"port": p.port, "service": p.service, "banner": p.banner}
                for p in self.open_ports if p.is_open
            ],
            "confidence": self.confidence,
        }


class DeviceFingerprinter(QThread):
    """
    Fingerprints a discovered device to determine its type and identity.

    Signals:
        fingerprint_complete: Emitted with the fingerprint result dict
        progress: Emitted with (current_device_index, total_devices)
    """

    fingerprint_complete = pyqtSignal(dict)
    progress = pyqtSignal(int, int)

    def __init__(self, devices: list = None, parent=None):
        """
        Args:
            devices: List of dicts with 'ip' and 'mac' keys
        """
        super().__init__(parent)
        self.devices = devices or []
        self._oui_db = None
        self._stop_flag = False

    def stop(self):
        self._stop_flag = True

    def run(self):
        """Fingerprint all provided devices."""
        self._stop_flag = False

        # Lazy-load OUI database
        from data.oui_database import OUIDatabase
        self._oui_db = OUIDatabase()

        for i, device in enumerate(self.devices):
            if self._stop_flag:
                return

            self.progress.emit(i + 1, len(self.devices))

            try:
                fp = self._fingerprint_device(
                    device.get("ip", ""),
                    device.get("mac", ""),
                    device.get("hostname", "")
                )
                self.fingerprint_complete.emit(fp.to_dict())
            except Exception as e:
                logger.error(f"Fingerprint error for {device}: {e}")

    def _fingerprint_device(self, ip: str, mac: str, hostname: str = "") -> DeviceFingerprint:
        """Run the full fingerprinting pipeline on a single device."""
        fp = DeviceFingerprint(ip=ip, mac=mac)

        # Step 1: OUI Vendor Lookup
        if self._oui_db:
            fp.vendor = self._oui_db.lookup(mac)

        # Step 2: Hostname
        fp.hostname = hostname
        if not fp.hostname:
            try:
                fp.hostname, _, _ = socket.gethostbyaddr(ip)
            except Exception:
                fp.hostname = ""

        # Step 3: Fast Port Scan
        fp.open_ports = self._scan_ports(ip)

        # Step 4: Banner Grab on open HTTP ports
        for port_result in fp.open_ports:
            if port_result.is_open and port_result.port in [80, 8080, 8008, 8443, 443]:
                banner = self._grab_http_banner(ip, port_result.port)
                if banner:
                    port_result.banner = banner

        # Step 5: Enhanced Active Identification (NetBIOS, UPnP, mDNS)
        from core.device_identifier import identify_device
        id_info = identify_device(ip, mac, fp.vendor, fp.open_ports)
        if id_info.get("name") and (not fp.hostname or fp.hostname == ip):
            fp.hostname = id_info["name"]
        fp.model = id_info.get("model", "")
        if id_info.get("vendor") and fp.vendor == "Unknown":
            fp.vendor = id_info["vendor"]
        if id_info.get("device_type") and id_info["device_type"] != "generic":
            fp.device_type = id_info["device_type"]
        else:
            fp.device_type = self._categorize_device(fp)

        fp.os = id_info.get("os", "Windows")
        fp.device_name = fp.hostname or fp.model or self._generate_device_name(fp)
        fp.confidence = self._calculate_confidence(fp)

        logger.info(
            f"Fingerprinted {ip} ({mac}): vendor={fp.vendor}, model={fp.model}, "
            f"type={fp.device_type}, name={fp.device_name}"
        )

        return fp

    def _scan_ports(self, ip: str, timeout: float = 0.5) -> List[PortScanResult]:
        """Fast TCP port scan on top ports."""
        results = []

        def _check_port(port: int) -> PortScanResult:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                result = sock.connect_ex((ip, port))
                sock.close()

                is_open = result == 0
                service = ""
                category = ""

                if is_open:
                    port_info = PORT_SIGNATURES.get("tcp_ports", {}).get(str(port), {})
                    service = port_info.get("service", f"port-{port}")
                    category = port_info.get("category", "")

                return PortScanResult(
                    port=port, is_open=is_open,
                    service=service, category=category
                )
            except Exception:
                return PortScanResult(port=port, is_open=False)

        # Use thread pool for concurrent port scanning
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(_check_port, port): port for port in TOP_PORTS}
            for future in as_completed(futures):
                if self._stop_flag:
                    return results
                try:
                    result = future.result(timeout=2)
                    if result.is_open:
                        results.append(result)
                except Exception:
                    pass

        return results

    def _grab_http_banner(self, ip: str, port: int) -> str:
        """Attempt to grab the HTTP Server header."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((ip, port))
            sock.send(b"GET / HTTP/1.0\r\nHost: " + ip.encode() + b"\r\n\r\n")
            response = sock.recv(1024).decode("utf-8", errors="ignore")
            sock.close()

            # Parse Server header
            for line in response.split("\r\n"):
                if line.lower().startswith("server:"):
                    return line.split(":", 1)[1].strip()

            return ""
        except Exception:
            return ""

    def _categorize_device(self, fp: DeviceFingerprint) -> str:
        """
        Determine device type using heuristic rules combining:
        - Vendor name
        - Open ports
        - Hostname patterns
        - Banner info
        """
        scores = {}  # category -> score

        # Score from vendor
        vendor_category = PORT_SIGNATURES.get("vendor_to_category", {}).get(fp.vendor, "")
        if vendor_category:
            scores[vendor_category] = scores.get(vendor_category, 0) + 3

        # Score from open ports
        for port_result in fp.open_ports:
            if port_result.is_open and port_result.category:
                cat = port_result.category
                scores[cat] = scores.get(cat, 0) + 2

        # Score from hostname patterns
        hostname_lower = (fp.hostname or "").lower()
        hostname_hints = {
            "iphone": "smartphone", "ipad": "tablet", "macbook": "laptop",
            "imac": "laptop", "android": "smartphone", "galaxy": "smartphone",
            "pixel": "smartphone", "oneplus": "smartphone",
            "desktop": "laptop", "laptop": "laptop", "pc": "laptop",
            "printer": "printer", "camera": "ip_camera",
            "tv": "smart_tv", "roku": "smart_tv", "chromecast": "smart_tv",
            "xbox": "game_console", "playstation": "game_console",
            "nintendo": "game_console", "switch": "game_console",
            "echo": "smart_device", "alexa": "smart_device",
            "google-home": "smart_device", "nest": "smart_device",
            "sonos": "smart_device", "hue": "smart_device",
            "raspberrypi": "iot_device", "esp": "iot_device",
        }
        for hint, category in hostname_hints.items():
            if hint in hostname_lower:
                scores[category] = scores.get(category, 0) + 4

        # Determine winner
        if not scores:
            return "unknown"

        best_category = max(scores, key=scores.get)

        # Map subcategories to main types
        type_map = {
            "smartphone": "smartphone", "tablet": "tablet",
            "laptop": "laptop", "windows_pc": "laptop", "mac": "laptop",
            "router": "router", "printer": "printer",
            "ip_camera": "iot_device", "smart_tv": "smart_tv",
            "chromecast": "smart_tv", "roku": "smart_tv",
            "smart_device": "iot_device", "iot_device": "iot_device",
            "nas": "server", "server": "server",
            "game_console": "game_console",
            "iphone": "smartphone", "android": "smartphone",
            "apple_device": "smartphone", "ubiquiti": "router",
        }

        return type_map.get(best_category, "unknown")

    def _generate_device_name(self, fp: DeviceFingerprint) -> str:
        """Generate a human-readable device name."""
        if fp.hostname and fp.hostname != fp.ip:
            return fp.hostname

        type_names = {
            "smartphone": "Phone", "tablet": "Tablet",
            "laptop": "Computer", "router": "Router",
            "printer": "Printer", "smart_tv": "Smart TV",
            "iot_device": "Smart Device", "server": "Server",
            "game_console": "Game Console",
        }
        type_name = type_names.get(fp.device_type, "Device")

        if fp.vendor and fp.vendor != "Unknown":
            return f"{fp.vendor} {type_name}"

        return f"{type_name} ({fp.ip})"

    def _calculate_confidence(self, fp: DeviceFingerprint) -> float:
        """Calculate a confidence score (0.0 - 1.0) for the fingerprint."""
        score = 0.0

        if fp.vendor and fp.vendor != "Unknown":
            score += 0.3

        if fp.hostname:
            score += 0.2

        if fp.open_ports:
            score += min(0.3, len(fp.open_ports) * 0.05)

        if fp.device_type != "unknown":
            score += 0.2

        return min(1.0, score)


def fingerprint_single(ip: str, mac: str, hostname: str = "") -> dict:
    """
    Convenience function to fingerprint a single device synchronously.
    Returns a dict with all fingerprint data.
    """
    from data.oui_database import OUIDatabase
    oui_db = OUIDatabase()

    fp_engine = DeviceFingerprinter.__new__(DeviceFingerprinter)
    fp_engine._oui_db = oui_db
    fp_engine._stop_flag = False

    result = fp_engine._fingerprint_device(ip, mac, hostname)
    return result.to_dict()
