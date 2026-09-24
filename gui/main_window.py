"""
NetSentry - Main Window (Fing Desktop 4.0.6 Design)
Primary application window with top navigation bar, Fing sidebar, and stacked views.
Coordinates network scanner, fingerprinter, and ARP spoofer.
"""

import sys
import logging
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QFrame, QStackedWidget, QLabel, QMessageBox,
    QStatusBar, QApplication
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

from gui.styles.theme import COLORS, get_stylesheet
from gui.dashboard import DashboardView
from gui.device_list import DeviceListView
from gui.device_detail import DeviceDetailView
from gui.settings_panel import SettingsPanel

from core.scanner import NetworkScanner
from core.fingerprinter import DeviceFingerprinter
from core.arp_spoofer import ARPSpoofer
from core.packet_handler import PacketHandler
from core.network_utils import get_network_info, get_local_mac

from data.device_store import DeviceStore, DeviceRecord
from data.oui_database import OUIDatabase

logger = logging.getLogger("netsentry.main_window")


class MainWindow(QMainWindow):
    """
    Main application window replicating Fing Desktop 4.0.6:
    - Top bar with < > history buttons, network title, and top-right "Scan network" button
    - Fing left sidebar:
        - Network header (Name, "Personal workspace")
        - Main navigation: Overview, Devices, People, Timeline, Internet, Setup, Security, Insights
        - Tools, Notifications
        - Premium upgrade card ("Get 3 Premium months free", "Switch now")
        - User profile ("Or Oog", oroog1442@gmail.com)
    - Stacked views: Dashboard, DeviceList, DeviceDetail, Blocked, Settings
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fing Desktop 4.0.6 — NetSentry")
        self.setMinimumSize(1150, 750)
        self.resize(1280, 820)

        # Core engines
        self._device_store = DeviceStore()
        self._oui_db = OUIDatabase()
        self._scanner = None
        self._fingerprinter = None
        self._arp_spoofer = None
        self._packet_handler = PacketHandler()
        self._network_info = {}
        self._devices = {}  # mac -> device data dict
        self._local_mac = None

        # Navigation history
        self._history = []
        self._history_idx = -1
        self._current_view = "devices"

        # Setup
        self._setup_ui()
        self._setup_connections()

        # Load network info and existing devices
        QTimer.singleShot(500, self._initialize)

    def _setup_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        central.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        central.setStyleSheet(f"background-color: {COLORS['bg_window']};")
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Top Bar (Fing Header: < > arrows + Scan network) ──
        top_bar = QFrame()
        top_bar.setFixedHeight(50)
        top_bar.setStyleSheet(f"""
            background-color: {COLORS['bg_window']};
            border-bottom: 1px solid {COLORS['border_subtle']};
            padding: 0px 16px;
        """)
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(12, 0, 16, 0)
        top_bar_layout.setSpacing(10)

        # History nav buttons: < and >
        self._back_btn = QPushButton("❮")
        self._back_btn.setObjectName("topNavBtn")
        self._back_btn.setFixedWidth(32)
        self._back_btn.setEnabled(False)
        self._back_btn.clicked.connect(self._go_back)
        top_bar_layout.addWidget(self._back_btn)

        self._fwd_btn = QPushButton("❯")
        self._fwd_btn.setObjectName("topNavBtn")
        self._fwd_btn.setFixedWidth(32)
        self._fwd_btn.setEnabled(False)
        self._fwd_btn.clicked.connect(self._go_forward)
        top_bar_layout.addWidget(self._fwd_btn)

        # Window branding indicator
        app_brand = QLabel("Fing Desktop 4.0.6")
        app_brand.setStyleSheet("color: #64748b; font-size: 11px; margin-left: 6px;")
        top_bar_layout.addWidget(app_brand)

        top_bar_layout.addStretch()

        # Scan network button
        self._scan_btn = QPushButton("↻  Scan network")
        self._scan_btn.setObjectName("scanNetworkBtn")
        self._scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._scan_btn.clicked.connect(self._toggle_scan)
        top_bar_layout.addWidget(self._scan_btn)

        root_layout.addWidget(top_bar)

        # ── Main Body: Sidebar + Stacked Content ──
        body_widget = QWidget()
        body_layout = QHBoxLayout(body_widget)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # ── Sidebar (Replicating Fing Desktop 4.0.6 Sidebar) ──
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 16, 12, 16)
        sidebar_layout.setSpacing(4)

        # Network Header Section
        net_section_label = QLabel("Network")
        net_section_label.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 600; padding-left: 8px;")
        sidebar_layout.addWidget(net_section_label)

        self._sidebar_net_name = QLabel("RedtailAlfa")
        self._sidebar_net_name.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self._sidebar_net_name.setStyleSheet("color: #f8fafc; padding-left: 8px; margin-top: 2px;")
        sidebar_layout.addWidget(self._sidebar_net_name)

        self._sidebar_workspace = QLabel("Personal workspace")
        self._sidebar_workspace.setStyleSheet("color: #64748b; font-size: 11px; padding-left: 8px; margin-bottom: 12px;")
        sidebar_layout.addWidget(self._sidebar_workspace)

        # Primary Navigation items
        self._nav_buttons = {}
        primary_nav = [
            ("dashboard", "📡  Overview"),
            ("devices", "💻  Devices"),
            ("people", "👥  People"),
            ("timeline", "⏱️  Timeline"),
            ("internet", "🌐  Internet"),
            ("settings", "⚙️  Setup"),
            ("blocked", "🛡️  Security"),
            ("insights", "📊  Insights"),
        ]

        for key, text in primary_nav:
            btn = QPushButton(text)
            btn.setObjectName("sidebarBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self._navigate_to(k, push_history=True))
            sidebar_layout.addWidget(btn)
            self._nav_buttons[key] = btn

        # Divider / Secondary section
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background-color: {COLORS['border_subtle']}; margin: 8px 4px;")
        sidebar_layout.addWidget(div)

        secondary_nav = [
            ("tools", "✔️  Tools"),
            ("notifications", "🔔  Notifications"),
        ]
        for key, text in secondary_nav:
            btn = QPushButton(text)
            btn.setObjectName("sidebarBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self._navigate_to(k, push_history=True))
            sidebar_layout.addWidget(btn)
            self._nav_buttons[key] = btn

        sidebar_layout.addStretch()

        # Premium Upgrade Promo Card
        upgrade_card = QFrame()
        upgrade_card.setObjectName("upgradeCard")
        up_layout = QVBoxLayout(upgrade_card)
        up_layout.setSpacing(6)
        up_layout.setContentsMargins(10, 10, 10, 10)

        up_title = QLabel("Get 3 Premium months\nfree")
        up_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        up_title.setStyleSheet("color: #f8fafc;")
        up_layout.addWidget(up_title)

        up_sub = QLabel("Same features, just yearly\nbilling.")
        up_sub.setStyleSheet("color: #64748b; font-size: 10px;")
        up_layout.addWidget(up_sub)

        switch_btn = QPushButton("Switch now")
        switch_btn.setObjectName("upgradeBtn")
        switch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        up_layout.addWidget(switch_btn)

        sidebar_layout.addWidget(upgrade_card)

        # User Profile Widget (Or Oog, oroog1442@gmail.com)
        profile_card = QFrame()
        profile_card.setObjectName("userProfileCard")
        prof_layout = QHBoxLayout(profile_card)
        prof_layout.setContentsMargins(4, 8, 4, 4)
        prof_layout.setSpacing(10)

        avatar = QLabel("Or")
        avatar.setObjectName("userAvatar")
        prof_layout.addWidget(avatar)

        prof_vbox = QVBoxLayout()
        prof_vbox.setSpacing(1)
        user_name = QLabel("Or Oog")
        user_name.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        user_name.setStyleSheet("color: #f8fafc;")

        user_email = QLabel("oroog1442@gmail.com")
        user_email.setStyleSheet("color: #64748b; font-size: 10px;")

        prof_vbox.addWidget(user_name)
        prof_vbox.addWidget(user_email)
        prof_layout.addLayout(prof_vbox)

        sidebar_layout.addWidget(profile_card)
        body_layout.addWidget(sidebar)

        # ── Stacked Content Area ──
        self._stack = QStackedWidget()

        self._dashboard = DashboardView()
        self._device_list = DeviceListView()
        self._device_detail = DeviceDetailView()
        self._blocked_list = DeviceListView()
        self._settings = SettingsPanel()

        self._stack.addWidget(self._dashboard)      # 0
        self._stack.addWidget(self._device_list)     # 1
        self._stack.addWidget(self._device_detail)   # 2
        self._stack.addWidget(self._blocked_list)    # 3
        self._stack.addWidget(self._settings)        # 4

        body_layout.addWidget(self._stack, 1)
        root_layout.addWidget(body_widget, 1)

        # Status Bar
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        self._status_label = QLabel("Ready")
        status_bar.addWidget(self._status_label, 1)

        # Start on Devices view (as shown in user's screenshot 2)
        self._navigate_to("devices", push_history=True)

    def _setup_connections(self):
        """Wire up all signals between views and engines."""
        # Dashboard
        self._dashboard.scan_requested.connect(self._start_scan)
        self._dashboard.stop_scan_requested.connect(self._stop_scan)

        # Device list
        self._device_list.device_selected.connect(self._show_device_detail)
        self._device_list.block_device.connect(self._block_device)
        self._device_list.unblock_device.connect(self._unblock_device)
        self._device_list.scan_requested.connect(self._start_scan)

        # Blocked list
        self._blocked_list.device_selected.connect(self._show_device_detail)
        self._blocked_list.unblock_device.connect(self._unblock_device)

        # Device detail
        self._device_detail.block_requested.connect(self._block_device)
        self._device_detail.unblock_requested.connect(self._unblock_device)
        self._device_detail.name_changed.connect(self._rename_device)
        self._device_detail.back_requested.connect(self._go_back)

        # Settings
        self._settings.settings_changed.connect(self._on_settings_changed)

    def _navigate_to(self, view_key: str, push_history: bool = True):
        """Navigate to a view by key and update history stack."""
        index_map = {
            "dashboard": 0, "devices": 1,
            "detail": 2, "blocked": 3, "settings": 4,
            "people": 1, "timeline": 0, "internet": 0,
            "insights": 0, "tools": 4, "notifications": 0,
        }
        index = index_map.get(view_key, 1)
        self._stack.setCurrentIndex(index)
        self._current_view = view_key

        # History tracking
        if push_history:
            if self._history_idx < len(self._history) - 1:
                self._history = self._history[:self._history_idx + 1]
            self._history.append(view_key)
            self._history_idx = len(self._history) - 1

        self._update_history_buttons()

        # Update sidebar button states
        for key, btn in self._nav_buttons.items():
            btn.setChecked(key == view_key)

        # Refresh blocked list when navigating there
        if view_key == "blocked":
            blocked = [d for d in self._devices.values() if d.get("is_blocked")]
            self._blocked_list.update_devices(blocked)

    def _update_history_buttons(self):
        """Update < and > button enabled states."""
        self._back_btn.setEnabled(self._history_idx > 0)
        self._fwd_btn.setEnabled(self._history_idx < len(self._history) - 1)

    def _go_back(self):
        """Navigate backward in history."""
        if self._history_idx > 0:
            self._history_idx -= 1
            prev_view = self._history[self._history_idx]
            self._navigate_to(prev_view, push_history=False)

    def _go_forward(self):
        """Navigate forward in history."""
        if self._history_idx < len(self._history) - 1:
            self._history_idx += 1
            next_view = self._history[self._history_idx]
            self._navigate_to(next_view, push_history=False)

    def _toggle_scan(self):
        """Toggle network scan from top bar."""
        if self._scanner and self._scanner.isRunning():
            self._stop_scan()
        else:
            self._start_scan()

    # ═══════════════════════════════════════════
    # Initialization
    # ═══════════════════════════════════════════

    def _initialize(self):
        """Run initial setup tasks."""
        self._dashboard.add_log_entry("NetSentry starting...")

        # Detect network info
        self._network_info = get_network_info()
        self._dashboard.update_network_info(self._network_info)

        ssid = self._network_info.get("ssid") or "RedtailAlfa"
        subnet = self._network_info.get("subnet") or "192.168.1.0/24"
        self._sidebar_net_name.setText(ssid)
        self._sidebar_workspace.setText(f"Subnet: {subnet}")
        self._device_list.set_network_name(ssid)
        self._blocked_list.set_network_name("Blocked Devices")

        # Get local MAC
        self._local_mac = get_local_mac()

        # Load existing devices from database
        existing = self._device_store.get_all_devices()
        if not existing:
            # Seed default devices matching Fing Desktop 4.0.6
            sample_devices = [
                {
                    "mac": "04:EC:D8:02:C4:6B",
                    "ip": "192.168.68.68",
                    "hostname": "KnifemasterYT",
                    "model": "HP OMEN 40L Gaming GT21-0xxx",
                    "vendor": "HP",
                    "device_type": "desktop",
                    "os": "Windows",
                    "is_online": True,
                    "is_blocked": False,
                    "times_seen": 42,
                    "last_seen": datetime.now().isoformat(),
                },
                {
                    "mac": "34:E6:D7:11:22:33",
                    "ip": "192.168.68.21",
                    "hostname": "EPIKA-PF4NAHKT",
                    "model": "Lenovo ThinkPad X1 Carbon 11th Gen",
                    "vendor": "Lenovo",
                    "device_type": "laptop",
                    "os": "Windows",
                    "is_online": True,
                    "is_blocked": False,
                    "times_seen": 20,
                    "last_seen": datetime.now().isoformat(),
                },
                {
                    "mac": "F4:0F:24:AA:BB:CC",
                    "ip": "192.168.68.105",
                    "hostname": "",
                    "model": "Samsung QN75LS03DDFXZA",
                    "vendor": "Samsung",
                    "device_type": "television",
                    "os": "Tizen",
                    "is_online": True,
                    "is_blocked": False,
                    "times_seen": 15,
                    "last_seen": datetime.now().isoformat(),
                },
                {
                    "mac": "70:82:0E:44:55:66",
                    "ip": "192.168.68.110",
                    "hostname": "MF650C Series",
                    "model": "Canon MF650C Series",
                    "vendor": "Canon",
                    "device_type": "printer",
                    "os": "Embedded",
                    "is_online": True,
                    "is_blocked": False,
                    "times_seen": 10,
                    "last_seen": datetime.now().isoformat(),
                },
                {
                    "mac": "FC:65:DE:77:88:99",
                    "ip": "192.168.68.115",
                    "hostname": "Jennifer's Echo Show",
                    "model": "Amazon Echo Show 15",
                    "vendor": "Amazon",
                    "device_type": "voice_control",
                    "os": "Fire OS",
                    "is_online": True,
                    "is_blocked": False,
                    "times_seen": 35,
                    "last_seen": datetime.now().isoformat(),
                },
                {
                    "mac": "B8:D6:1A:12:34:56",
                    "ip": "192.168.68.120",
                    "hostname": "",
                    "model": "Pura",
                    "vendor": "Pura",
                    "device_type": "smart_device",
                    "os": "Embedded",
                    "is_online": True,
                    "is_blocked": False,
                    "times_seen": 18,
                    "last_seen": datetime.now().isoformat(),
                },
                {
                    "mac": "48:27:EA:33:44:55",
                    "ip": "192.168.68.125",
                    "hostname": "",
                    "model": "Hunan Fn-Link Technology",
                    "vendor": "Fn-Link",
                    "device_type": "generic",
                    "os": "Embedded",
                    "is_online": True,
                    "is_blocked": False,
                    "times_seen": 8,
                    "last_seen": datetime.now().isoformat(),
                },
                {
                    "mac": "9C:50:EE:98:76:54",
                    "ip": "192.168.68.130",
                    "hostname": "DESKTOP-71XK93L",
                    "model": "HP OMEN 25L Gaming GT15-1xxx",
                    "vendor": "HP",
                    "device_type": "desktop",
                    "os": "Windows",
                    "is_online": True,
                    "is_blocked": False,
                    "times_seen": 30,
                    "last_seen": datetime.now().isoformat(),
                },
                {
                    "mac": "E8:50:8B:11:00:22",
                    "ip": "192.168.68.135",
                    "hostname": "",
                    "model": "Samsung Smart TV",
                    "vendor": "Samsung",
                    "device_type": "television",
                    "os": "Tizen",
                    "is_online": True,
                    "is_blocked": False,
                    "times_seen": 12,
                    "last_seen": datetime.now().isoformat(),
                },
            ]
            for s in sample_devices:
                rec = DeviceRecord.from_dict(s)
                self._device_store.upsert_device(rec)
            existing = self._device_store.get_all_devices()

        for device in existing:
            self._devices[device.mac.lower()] = device.to_dict()

        self._update_all_views()

        # Initialize ARP spoofer
        self._arp_spoofer = ARPSpoofer(
            gateway_ip=self._network_info.get("gateway_ip"),
            gateway_mac=self._network_info.get("gateway_mac")
        )
        self._arp_spoofer.spoof_error.connect(self._on_spoof_error)
        self._arp_spoofer.start()

        # Restore blocked devices
        blocked = self._device_store.get_blocked_devices()
        for device in blocked:
            self._arp_spoofer.add_target(device.ip, device.mac)

        self._status_label.setText(
            f"Connected: {ssid} | IP: {self._network_info.get('local_ip', 'N/A')} | {len(self._devices)} devices known"
        )

    # ═══════════════════════════════════════════
    # Scanning
    # ═══════════════════════════════════════════

    def _start_scan(self):
        """Start a network scan."""
        if self._scanner and self._scanner.isRunning():
            return

        self._dashboard.set_scanning(True)
        self._scan_btn.setText("⏹  Stop scan")
        self._status_label.setText("Scanning network...")

        self._scanner = NetworkScanner(
            subnet=self._network_info.get("subnet"),
            gateway_ip=self._network_info.get("gateway_ip"),
            timeout=self._settings.get_settings().get("scan_timeout", 3)
        )
        self._scanner.device_found.connect(self._on_device_found)
        self._scanner.scan_progress.connect(self._dashboard.set_progress)
        self._scanner.scan_complete.connect(self._on_scan_complete)
        self._scanner.scan_error.connect(self._on_scan_error)
        self._scanner.start()

    def _stop_scan(self):
        """Stop the current scan."""
        if self._scanner:
            self._scanner.stop()
            self._dashboard.set_scanning(False)
            self._scan_btn.setText("↻  Scan network")
            self._status_label.setText("Scan stopped.")

    def _on_device_found(self, device_info: dict):
        """Called when the scanner finds a device."""
        mac = device_info.get("mac", "").lower()
        if not mac or mac == "ff:ff:ff:ff:ff:ff":
            return

        if self._local_mac and mac == self._local_mac:
            return

        ip = device_info.get("ip", "")
        hostname = device_info.get("hostname", "")

        if mac in self._devices:
            self._devices[mac]["ip"] = ip
            self._devices[mac]["is_online"] = True
            if hostname:
                self._devices[mac]["hostname"] = hostname
        else:
            vendor = self._oui_db.lookup(mac)
            is_gateway = (ip == self._network_info.get("gateway_ip"))

            self._devices[mac] = {
                "mac": mac,
                "ip": ip,
                "hostname": hostname,
                "vendor": vendor,
                "device_type": "router" if is_gateway else "unknown",
                "device_name": hostname or (f"{vendor} Device" if vendor != "Unknown" else ""),
                "open_ports": [],
                "is_online": True,
                "is_blocked": False,
                "is_gateway": is_gateway,
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
                "times_seen": 1,
                "custom_name": "",
            }

        self._update_all_views()

    def _on_scan_complete(self, results: list):
        """Called when scan completes."""
        self._dashboard.set_scanning(False)
        self._scan_btn.setText("↻  Scan network")
        self._status_label.setText(f"Scan complete: {len(results)} devices found.")

        scanned_macs = {r.get("mac", "").lower() for r in results}
        for mac, data in self._devices.items():
            if mac not in scanned_macs:
                data["is_online"] = False

        # Run fingerprinting
        settings = self._settings.get_settings()
        if settings.get("deep_scan", True):
            devices_to_fingerprint = [
                {"ip": d["ip"], "mac": d["mac"], "hostname": d.get("hostname", "")}
                for d in self._devices.values()
                if d.get("is_online") and d.get("device_type") == "unknown" and not d.get("is_gateway")
            ]

            if devices_to_fingerprint:
                self._fingerprinter = DeviceFingerprinter(devices=devices_to_fingerprint)
                self._fingerprinter.fingerprint_complete.connect(self._on_fingerprint_complete)
                self._fingerprinter.finished.connect(self._on_fingerprinting_done)
                self._fingerprinter.start()

        # Save to database
        for mac, data in self._devices.items():
            record = DeviceRecord.from_dict(data)
            self._device_store.upsert_device(record)

        self._update_all_views()

    def _on_scan_error(self, error: str):
        self._dashboard.set_scanning(False)
        self._scan_btn.setText("↻  Scan network")
        self._status_label.setText(f"Scan error: {error}")
        logger.error(f"Scan error: {error}")

    def _on_fingerprint_complete(self, fp_data: dict):
        mac = fp_data.get("mac", "").lower()
        if mac in self._devices:
            self._devices[mac]["vendor"] = fp_data.get("vendor", "Unknown")
            self._devices[mac]["device_type"] = fp_data.get("device_type", "unknown")
            self._devices[mac]["device_name"] = fp_data.get("device_name", "")
            self._devices[mac]["open_ports"] = fp_data.get("open_ports", [])
            record = DeviceRecord.from_dict(self._devices[mac])
            self._device_store.upsert_device(record)

    def _on_fingerprinting_done(self):
        self._update_all_views()

    # ═══════════════════════════════════════════
    # Blocking & Unblocking
    # ═══════════════════════════════════════════

    def _block_device(self, mac: str):
        """Block internet access for target MAC."""
        mac = mac.lower()
        device = self._devices.get(mac)
        if not device:
            return

        if device.get("is_gateway"):
            QMessageBox.warning(
                self, "Cannot Block Gateway",
                "Blocking the gateway would disconnect ALL devices on the network."
            )
            return

        name = device.get("custom_name") or device.get("hostname") or device.get("ip")
        result = QMessageBox.question(
            self, "Block Network Access",
            f"Are you sure you want to block internet access for:\n\n"
            f"  {name}\n"
            f"  IP: {device.get('ip')}\n"
            f"  MAC: {mac.upper()}\n\n"
            f"All outbound internet traffic from this device will be blocked.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if result != QMessageBox.StandardButton.Yes:
            return

        self._arp_spoofer.add_target(device["ip"], mac)
        device["is_blocked"] = True
        self._device_store.set_blocked(mac, True)

        self._dashboard.add_log_entry(f"🚫 Blocked: {name} ({device.get('ip')})")
        self._update_all_views()

    def _unblock_device(self, mac: str):
        """Unblock internet access for target MAC."""
        mac = mac.lower()
        device = self._devices.get(mac)
        if not device:
            return

        self._arp_spoofer.remove_target(mac)
        device["is_blocked"] = False
        self._device_store.set_blocked(mac, False)

        name = device.get("custom_name") or device.get("hostname") or device.get("ip")
        self._dashboard.add_log_entry(f"✅ Unblocked: {name} ({device.get('ip')})")
        self._update_all_views()

    def _on_spoof_error(self, error: str):
        logger.error(f"ARP spoof error: {error}")

    # ═══════════════════════════════════════════
    # Device Management
    # ═══════════════════════════════════════════

    def _rename_device(self, mac: str, name: str):
        mac = mac.lower()
        if mac in self._devices:
            self._devices[mac]["custom_name"] = name
            self._device_store.set_custom_name(mac, name)
            self._update_all_views()

    def _show_device_detail(self, mac: str):
        mac = mac.lower()
        device = self._devices.get(mac)
        if device:
            self._device_detail.set_device(device)
            self._navigate_to("detail", push_history=True)

    # ═══════════════════════════════════════════
    # View Updates
    # ═══════════════════════════════════════════

    def _update_all_views(self):
        devices_list = list(self._devices.values())
        total = len(devices_list)
        online = sum(1 for d in devices_list if d.get("is_online"))
        blocked = sum(1 for d in devices_list if d.get("is_blocked"))

        self._dashboard.update_stats(total=total, online=online, blocked=blocked)
        self._device_list.update_devices(devices_list)

        # If on device detail view, update it as well
        cur_detail_mac = self._device_detail._device_data.get("mac")
        if cur_detail_mac and cur_detail_mac.lower() in self._devices:
            self._device_detail.set_device(self._devices[cur_detail_mac.lower()])

        self._status_label.setText(
            f"Connected: {self._sidebar_net_name.text()} | {total} devices ({online} online, {blocked} blocked)"
        )

    def _on_settings_changed(self, settings: dict):
        if self._arp_spoofer:
            self._arp_spoofer.interval = settings.get("arp_interval", 1)

    def closeEvent(self, event):
        if self._scanner and self._scanner.isRunning():
            self._scanner.stop()
            self._scanner.wait(2000)

        if self._fingerprinter and self._fingerprinter.isRunning():
            self._fingerprinter.stop()
            self._fingerprinter.wait(2000)

        if self._arp_spoofer and self._arp_spoofer.isRunning():
            self._arp_spoofer.stop()
            self._arp_spoofer.wait(3000)

        self._packet_handler.restore_original_state()
        event.accept()
