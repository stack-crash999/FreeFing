"""
NetSentry - Device Store
SQLite-backed persistent storage for discovered devices and their history.
"""

import os
import json
import sqlite3
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger("netsentry.device_store")

DB_DIR = os.path.join(os.environ.get("APPDATA", "."), "NetSentry")
DB_PATH = os.path.join(DB_DIR, "devices.db")


class DeviceRecord:
    """Represents a discovered network device."""

    def __init__(self, mac: str, ip: str = "", hostname: str = "",
                 vendor: str = "Unknown", device_type: str = "unknown",
                 device_name: str = "", model: str = "", os: str = "",
                 open_ports: list = None, first_seen: str = "", last_seen: str = "",
                 times_seen: int = 0, is_blocked: bool = False,
                 is_online: bool = False, is_gateway: bool = False,
                 custom_name: str = "", notes: str = ""):
        self.mac = mac.upper()
        self.ip = ip
        self.hostname = hostname
        self.vendor = vendor
        self.device_type = device_type
        self.model = model or device_name or (f"{vendor} Device" if vendor != "Unknown" else "")
        self.os = os or "Windows"
        self.device_name = device_name or self.model or hostname or vendor
        self.open_ports = open_ports or []
        self.first_seen = first_seen or datetime.now().isoformat()
        self.last_seen = last_seen or datetime.now().isoformat()
        self.times_seen = times_seen
        self.is_blocked = is_blocked
        self.is_online = is_online
        self.is_gateway = is_gateway
        self.custom_name = custom_name
        self.notes = notes

    @property
    def display_name(self) -> str:
        """Get the best display name for this device."""
        if self.custom_name:
            return self.custom_name
        if self.hostname and self.hostname != self.ip:
            return self.hostname
        if self.model:
            return self.model
        if self.vendor and self.vendor != "Unknown":
            return f"{self.vendor} Device"
        return self.ip or self.mac

    def to_dict(self) -> dict:
        return {
            "mac": self.mac,
            "ip": self.ip,
            "hostname": self.hostname,
            "vendor": self.vendor,
            "model": self.model,
            "os": self.os,
            "device_type": self.device_type,
            "device_name": self.device_name,
            "open_ports": self.open_ports,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "times_seen": self.times_seen,
            "is_blocked": self.is_blocked,
            "is_online": self.is_online,
            "is_gateway": self.is_gateway,
            "custom_name": self.custom_name,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DeviceRecord":
        ports = data.get("open_ports", [])
        if isinstance(ports, str):
            try:
                ports = json.loads(ports)
            except (json.JSONDecodeError, TypeError):
                ports = []
        return cls(
            mac=data.get("mac", ""),
            ip=data.get("ip", ""),
            hostname=data.get("hostname", ""),
            vendor=data.get("vendor", "Unknown"),
            model=data.get("model", ""),
            os=data.get("os", "Windows"),
            device_type=data.get("device_type", "unknown"),
            device_name=data.get("device_name", ""),
            open_ports=ports,
            first_seen=data.get("first_seen", ""),
            last_seen=data.get("last_seen", ""),
            times_seen=data.get("times_seen", 0),
            is_blocked=bool(data.get("is_blocked", False)),
            is_online=bool(data.get("is_online", False)),
            is_gateway=bool(data.get("is_gateway", False)),
            custom_name=data.get("custom_name", ""),
            notes=data.get("notes", ""),
        )


class DeviceStore:
    """SQLite-backed device history database."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Create the database schema if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    mac TEXT PRIMARY KEY,
                    ip TEXT,
                    hostname TEXT,
                    vendor TEXT DEFAULT 'Unknown',
                    device_type TEXT DEFAULT 'unknown',
                    device_name TEXT,
                    open_ports TEXT DEFAULT '[]',
                    first_seen TEXT,
                    last_seen TEXT,
                    times_seen INTEGER DEFAULT 0,
                    is_blocked INTEGER DEFAULT 0,
                    is_gateway INTEGER DEFAULT 0,
                    custom_name TEXT DEFAULT '',
                    notes TEXT DEFAULT ''
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS scan_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    device_count INTEGER,
                    new_devices INTEGER,
                    scan_duration_ms INTEGER
                )
            """)
            conn.commit()
        logger.info(f"Device database initialized at: {self.db_path}")

    def upsert_device(self, device: DeviceRecord):
        """Insert or update a device record."""
        with sqlite3.connect(self.db_path) as conn:
            existing = conn.execute(
                "SELECT times_seen, first_seen FROM devices WHERE mac = ?",
                (device.mac,)
            ).fetchone()

            if existing:
                times_seen = existing[0] + 1
                first_seen = existing[1]
                conn.execute("""
                    UPDATE devices SET
                        ip = ?, hostname = ?, vendor = ?, device_type = ?,
                        device_name = ?, open_ports = ?, last_seen = ?,
                        times_seen = ?, is_gateway = ?
                    WHERE mac = ?
                """, (
                    device.ip, device.hostname, device.vendor, device.device_type,
                    device.device_name, json.dumps(device.open_ports),
                    datetime.now().isoformat(), times_seen, int(device.is_gateway),
                    device.mac
                ))
            else:
                conn.execute("""
                    INSERT INTO devices
                        (mac, ip, hostname, vendor, device_type, device_name,
                         open_ports, first_seen, last_seen, times_seen, is_blocked,
                         is_gateway, custom_name, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    device.mac, device.ip, device.hostname, device.vendor,
                    device.device_type, device.device_name,
                    json.dumps(device.open_ports), device.first_seen,
                    device.last_seen, 1, int(device.is_blocked),
                    int(device.is_gateway), device.custom_name, device.notes
                ))
            conn.commit()

    def get_device(self, mac: str) -> Optional[DeviceRecord]:
        """Get a device by MAC address."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM devices WHERE mac = ?", (mac.upper(),)
            ).fetchone()
            if row:
                return DeviceRecord.from_dict(dict(row))
        return None

    def get_all_devices(self) -> list:
        """Get all stored devices."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM devices ORDER BY last_seen DESC").fetchall()
            return [DeviceRecord.from_dict(dict(row)) for row in rows]

    def set_blocked(self, mac: str, blocked: bool):
        """Set the blocked status of a device."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE devices SET is_blocked = ? WHERE mac = ?",
                (int(blocked), mac.upper())
            )
            conn.commit()

    def set_custom_name(self, mac: str, name: str):
        """Set a custom display name for a device."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE devices SET custom_name = ? WHERE mac = ?",
                (name, mac.upper())
            )
            conn.commit()

    def log_scan(self, device_count: int, new_devices: int, duration_ms: int):
        """Log a completed scan to history."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO scan_history (timestamp, device_count, new_devices, scan_duration_ms) VALUES (?, ?, ?, ?)",
                (datetime.now().isoformat(), device_count, new_devices, duration_ms)
            )
            conn.commit()

    def get_blocked_devices(self) -> list:
        """Get all currently blocked devices."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM devices WHERE is_blocked = 1"
            ).fetchall()
            return [DeviceRecord.from_dict(dict(row)) for row in rows]

    def get_device_count(self) -> int:
        """Get total number of known devices."""
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute("SELECT COUNT(*) FROM devices").fetchone()
            return result[0] if result else 0
