"""
NetSentry - Device Detail View (Fing Desktop 4.0.6 Layout)
Displays multi-card two-column layout matching Fing Desktop 4.0.6,
including the dynamic Block button (Red when unblocked, Greyed-out 'Blocked' when blocked).
"""

from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QScrollArea, QInputDialog, QMessageBox,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont, QColor

from gui.styles.theme import COLORS, get_fing_device_type_info


class DeviceDetailView(QWidget):
    """
    Device detail panel replicating Fing Desktop 4.0.6:
    - Top header: Name, metadata pills (Type, Model, OS, Online status), Edit/Flag/Mute buttons
    - 2-Column layout:
      - Left column: Network setup, Insights, Device model (with brand avatar & Revert), Product analysis
      - Right column: Improve security (Limit internet time, Block button), Track activity, Tools (Ping, Traceroute, Ports, WoL)
    """

    block_requested = pyqtSignal(str)      # mac
    unblock_requested = pyqtSignal(str)    # mac
    name_changed = pyqtSignal(str, str)    # mac, new_name
    back_requested = pyqtSignal()
    ping_requested = pyqtSignal(str)       # ip
    scan_ports_requested = pyqtSignal(str) # ip

    def __init__(self, parent=None):
        super().__init__(parent)
        self._device_data = {}
        self._is_blocked = False
        self._setup_ui()

    def _setup_ui(self):
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"background-color: {COLORS['bg_window']};")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 20, 28, 20)
        main_layout.setSpacing(16)

        # ── Scroll Area for whole detail page ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 10, 0)
        content_layout.setSpacing(16)

        # ── Header Row: Device Name & Action Icons ──
        header_top_layout = QHBoxLayout()

        self._name_label = QLabel("Device Details")
        self._name_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self._name_label.setStyleSheet("color: #f8fafc;")
        header_top_layout.addWidget(self._name_label)

        header_top_layout.addStretch()

        # Edit button
        self._edit_btn = QPushButton("✏  Edit")
        self._edit_btn.setObjectName("topNavBtn")
        self._edit_btn.clicked.connect(self._on_edit_name)
        header_top_layout.addWidget(self._edit_btn)

        # Flag button
        flag_btn = QPushButton("⚑")
        flag_btn.setObjectName("topNavBtn")
        flag_btn.setFixedWidth(36)
        header_top_layout.addWidget(flag_btn)

        # Mute button
        mute_btn = QPushButton("🔕")
        mute_btn.setObjectName("topNavBtn")
        mute_btn.setFixedWidth(36)
        header_top_layout.addWidget(mute_btn)

        content_layout.addLayout(header_top_layout)

        # ── Header Sub-row: Metadata Badges ──
        self._badges_layout = QHBoxLayout()
        self._badges_layout.setSpacing(8)

        self._type_pill = QLabel("Desktop  ⌄")
        self._type_pill.setObjectName("pillPurple")
        self._badges_layout.addWidget(self._type_pill)

        self._model_pill = QLabel("Model  ⌄")
        self._model_pill.setObjectName("pillPurple")
        self._badges_layout.addWidget(self._model_pill)

        self._os_pill = QLabel("Windows  ⌄")
        self._os_pill.setObjectName("pillPurple")
        self._badges_layout.addWidget(self._os_pill)

        self._status_pill = QLabel("🟢 Online")
        self._status_pill.setObjectName("pillGreen")
        self._badges_layout.addWidget(self._status_pill)

        self._badges_layout.addStretch()
        content_layout.addLayout(self._badges_layout)

        # ── 2-Column Body Layout ──
        body_layout = QHBoxLayout()
        body_layout.setSpacing(20)

        # ── LEFT COLUMN (Wider: Network setup, Insights, Device model, Product analysis) ──
        left_col = QVBoxLayout()
        left_col.setSpacing(16)

        # 1. Network setup card
        net_setup_card = QFrame()
        net_setup_card.setObjectName("fingCard")
        net_setup_layout = QVBoxLayout(net_setup_card)
        net_setup_layout.setSpacing(14)

        net_setup_title = QLabel("Network setup")
        net_setup_title.setObjectName("fingCardTitle")
        net_setup_layout.addWidget(net_setup_title)

        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        grid.setHorizontalSpacing(30)

        grid.addWidget(self._make_label_dim("IP Address"), 0, 0)
        self._ip_val = self._make_label_val("—")
        grid.addWidget(self._ip_val, 0, 1)

        grid.addWidget(self._make_label_dim("MAC Address"), 1, 0)
        self._mac_val = self._make_label_val("—")
        grid.addWidget(self._mac_val, 1, 1)

        grid.addWidget(self._make_label_dim("Serial No."), 2, 0)
        self._serial_val = self._make_label_val("N/A")
        grid.addWidget(self._serial_val, 2, 1)

        grid.setColumnStretch(1, 1)
        net_setup_layout.addLayout(grid)
        left_col.addWidget(net_setup_card)

        # 2. Insights card
        insights_card = QFrame()
        insights_card.setObjectName("fingCard")
        insights_layout = QHBoxLayout(insights_card)

        insights_title = QLabel("Insights")
        insights_title.setObjectName("fingCardTitle")
        insights_layout.addWidget(insights_title)

        personal_badge = QLabel("• Personal")
        personal_badge.setObjectName("pillPurple")
        personal_badge.setFixedHeight(24)
        insights_layout.addWidget(personal_badge)

        insights_layout.addStretch()
        arrow_lbl = QLabel("⌄")
        arrow_lbl.setStyleSheet("color: #94a3b8; font-size: 14px; font-weight: bold;")
        insights_layout.addWidget(arrow_lbl)
        left_col.addWidget(insights_card)

        # 3. Device model card
        model_card = QFrame()
        model_card.setObjectName("fingCard")
        model_layout = QVBoxLayout(model_card)
        model_layout.setSpacing(14)

        model_header = QHBoxLayout()
        model_title = QLabel("Device model")
        model_title.setObjectName("fingCardTitle")
        model_header.addWidget(model_title)

        model_header.addStretch()

        # Circular brand avatar (e.g. HP)
        self._brand_avatar = QLabel("HP")
        self._brand_avatar.setObjectName("userAvatar")
        self._brand_avatar.setFixedSize(36, 36)
        self._brand_avatar.setStyleSheet("""
            background-color: #1e3a8a;
            color: #93c5fd;
            border-radius: 18px;
            font-size: 12px;
            font-weight: 700;
        """)
        model_header.addWidget(self._brand_avatar)
        model_layout.addLayout(model_header)

        model_grid = QGridLayout()
        model_grid.setVerticalSpacing(10)
        model_grid.setHorizontalSpacing(30)

        model_grid.addWidget(self._make_label_dim("Brand"), 0, 0)
        self._brand_val = self._make_label_val("—")
        model_grid.addWidget(self._brand_val, 0, 1)

        model_grid.addWidget(self._make_label_dim("Model"), 1, 0)
        self._model_val = self._make_label_val("—")
        model_grid.addWidget(self._model_val, 1, 1)

        model_grid.setColumnStretch(1, 1)
        model_layout.addLayout(model_grid)

        # "Does it look good?" prompt sub-panel
        feedback_subpanel = QFrame()
        feedback_subpanel.setStyleSheet("""
            background-color: #161e33;
            border-radius: 8px;
            padding: 10px 14px;
        """)
        feedback_layout = QHBoxLayout(feedback_subpanel)

        feedback_text_vbox = QVBoxLayout()
        feedback_text_vbox.setSpacing(2)
        fb_title = QLabel("Does it look good?")
        fb_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        fb_title.setStyleSheet("color: #f8fafc;")
        fb_sub = QLabel("Please update these details if they no longer look right.")
        fb_sub.setObjectName("fingCardSubText")
        feedback_text_vbox.addWidget(fb_title)
        feedback_text_vbox.addWidget(fb_sub)

        feedback_layout.addLayout(feedback_text_vbox, 1)

        revert_btn = QPushButton("↺  Revert")
        revert_btn.setObjectName("topNavBtn")
        revert_btn.clicked.connect(self._on_revert_clicked)
        feedback_layout.addWidget(revert_btn)

        model_layout.addWidget(feedback_subpanel)
        left_col.addWidget(model_card)

        # 4. Product analysis card
        analysis_card = QFrame()
        analysis_card.setObjectName("fingCard")
        analysis_layout = QVBoxLayout(analysis_card)
        analysis_layout.setSpacing(10)

        analysis_title = QLabel("Product analysis")
        analysis_title.setObjectName("fingCardTitle")
        analysis_layout.addWidget(analysis_title)

        analysis_row = QHBoxLayout()
        analysis_row.addWidget(self._make_label_dim("Value"))
        self._value_badge = QLabel("Popular")
        self._value_badge.setObjectName("pillPurple")
        analysis_row.addWidget(self._value_badge)
        analysis_row.addStretch()
        analysis_layout.addLayout(analysis_row)

        left_col.addWidget(analysis_card)

        # 5. Open Ports Table (if scanned)
        self._ports_card = QFrame()
        self._ports_card.setObjectName("fingCard")
        ports_layout = QVBoxLayout(self._ports_card)
        ports_title = QLabel("Discovered Open Ports")
        ports_title.setObjectName("fingCardTitle")
        ports_layout.addWidget(ports_title)

        self._ports_table = QTableWidget()
        self._ports_table.setObjectName("fingTable")
        self._ports_table.setColumnCount(3)
        self._ports_table.setHorizontalHeaderLabels(["Port", "Service", "Banner"])
        self._ports_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._ports_table.verticalHeader().setVisible(False)
        self._ports_table.setMaximumHeight(160)
        ports_layout.addWidget(self._ports_table)
        left_col.addWidget(self._ports_card)

        body_layout.addLayout(left_col, 65)

        # ── RIGHT COLUMN (Narrower: Improve security, Track activity, Tools) ──
        right_col = QVBoxLayout()
        right_col.setSpacing(16)

        # 1. Improve security
        security_card = QFrame()
        security_card.setObjectName("fingCard")
        security_layout = QVBoxLayout(security_card)
        security_layout.setSpacing(12)

        sec_title = QLabel("Improve security")
        sec_title.setObjectName("fingCardTitle")
        security_layout.addWidget(sec_title)

        # Limit internet time button
        limit_time_btn = QPushButton("⏸  Limit internet time")
        limit_time_btn.setObjectName("actionToolBtn")
        security_layout.addWidget(limit_time_btn)

        # BLOCK BUTTON: Red when unblocked, Greyed-out "Blocked" when blocked
        self._block_btn = QPushButton("🚫  Block network access")
        self._block_btn.setObjectName("blockBtnRed")
        self._block_btn.clicked.connect(self._on_block_clicked)
        security_layout.addWidget(self._block_btn)

        right_col.addWidget(security_card)

        # 2. Track activity
        track_card = QFrame()
        track_card.setObjectName("fingCard")
        track_layout = QVBoxLayout(track_card)
        track_layout.setSpacing(10)

        track_title = QLabel("Track activity")
        track_title.setObjectName("fingCardTitle")
        track_layout.addWidget(track_title)

        user_combo = QComboBox()
        user_combo.setObjectName("filterCombo")
        user_combo.addItems(["👤  Or Oog", "👤  Family Member", "👤  Guest"])
        track_layout.addWidget(user_combo)

        timeline_btn = QPushButton("🕒  See full timeline")
        timeline_btn.setObjectName("actionToolBtn")
        track_layout.addWidget(timeline_btn)

        notify_combo = QComboBox()
        notify_combo.setObjectName("filterCombo")
        notify_combo.addItems(["🔕  Do not notify", "🔔  Notify on connect", "🔔  Notify on disconnect"])
        track_layout.addWidget(notify_combo)

        interval_label = QLabel("Offline detection interval")
        interval_label.setObjectName("fingCardSubText")
        track_layout.addWidget(interval_label)

        interval_combo = QComboBox()
        interval_combo.setObjectName("filterCombo")
        interval_combo.addItems(["10 minutes (automatic)", "5 minutes", "15 minutes", "30 minutes"])
        track_layout.addWidget(interval_combo)

        right_col.addWidget(track_card)

        # 3. Tools
        tools_card = QFrame()
        tools_card.setObjectName("fingCard")
        tools_layout = QVBoxLayout(tools_card)
        tools_layout.setSpacing(10)

        tools_title = QLabel("Tools")
        tools_title.setObjectName("fingCardTitle")
        tools_layout.addWidget(tools_title)

        ping_btn = QPushButton("📈  Ping a target")
        ping_btn.setObjectName("actionToolBtn")
        ping_btn.clicked.connect(self._on_ping_clicked)
        tools_layout.addWidget(ping_btn)

        trace_btn = QPushButton("📍  Start traceroute")
        trace_btn.setObjectName("actionToolBtn")
        tools_layout.addWidget(trace_btn)

        scan_ports_btn = QPushButton("🔒  Find open ports")
        scan_ports_btn.setObjectName("actionToolBtn")
        scan_ports_btn.clicked.connect(self._on_scan_ports_clicked)
        tools_layout.addWidget(scan_ports_btn)

        wol_btn = QPushButton("⚡  Wake on Lan")
        wol_btn.setObjectName("actionToolBtn")
        tools_layout.addWidget(wol_btn)

        right_col.addWidget(tools_card)
        right_col.addStretch()

        body_layout.addLayout(right_col, 35)
        content_layout.addLayout(body_layout)

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def _make_label_dim(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 500;")
        return lbl

    def _make_label_val(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #f8fafc; font-size: 13px; font-weight: 600;")
        return lbl

    def set_device(self, device_data: dict):
        """Populate the view with device data and update all cards."""
        self._device_data = device_data
        mac = device_data.get("mac", "")
        ip = device_data.get("ip", "—")
        hostname = device_data.get("custom_name") or device_data.get("hostname") or device_data.get("model") or "Device"
        dev_type = device_data.get("device_type", "generic")
        vendor = device_data.get("vendor", "Unknown")
        model = device_data.get("model") or vendor or "Generic Device"
        os_name = device_data.get("os") or "Windows"
        is_blocked = device_data.get("is_blocked", False)
        is_online = device_data.get("is_online", True)

        self._is_blocked = is_blocked

        # Header Title
        self._name_label.setText(hostname)

        # Header Badges
        icon, display_type = get_fing_device_type_info(dev_type)
        self._type_pill.setText(f"{icon} {display_type}  ⌄")
        self._model_pill.setText(f"{model}  ⌄")
        self._os_pill.setText(f"{os_name}  ⌄")

        if is_blocked:
            self._status_pill.setText("🔴 Blocked")
            self._status_pill.setObjectName("pillPurple")
        elif is_online:
            self._status_pill.setText("🟢 Online")
            self._status_pill.setObjectName("pillGreen")
        else:
            self._status_pill.setText("⚫ Offline")
            self._status_pill.setObjectName("pillPurple")

        self._status_pill.setStyleSheet("")  # re-trigger QSS

        # Network Setup
        self._ip_val.setText(ip)
        self._mac_val.setText(mac.upper())
        self._serial_val.setText("N/A")

        # Device Model
        self._brand_val.setText(vendor)
        self._model_val.setText(model)
        brand_code = vendor[:2].upper() if vendor and vendor != "Unknown" else "DV"
        self._brand_avatar.setText(brand_code)

        # Block Button state:
        # If blocked -> Greyed out button with "🚫 Blocked"
        # If unblocked -> Red button with "🚫 Block network access"
        self._update_block_button_state(is_blocked)

        # Ports Table
        ports = device_data.get("open_ports", [])
        self._update_ports_table(ports)

    def _update_block_button_state(self, is_blocked: bool):
        """Update block button style and label based on blocked state."""
        self._is_blocked = is_blocked
        if is_blocked:
            # Blocked: Greyed out button saying "Blocked"
            self._block_btn.setText("🚫  Blocked")
            self._block_btn.setObjectName("blockBtnGrey")
            self._block_btn.setStyleSheet("""
                QPushButton {
                    background-color: #232c40;
                    border: 1px solid #374563;
                    border-radius: 6px;
                    color: #78879e;
                    padding: 8px 14px;
                    font-size: 12px;
                    font-weight: 600;
                    text-align: left;
                    min-height: 26px;
                }
                QPushButton:hover {
                    background-color: #2a364e;
                    color: #cbd5e1;
                    border-color: #4b5d84;
                }
            """)
        else:
            # Unblocked: Red button saying "Block network access"
            self._block_btn.setText("🚫  Block network access")
            self._block_btn.setObjectName("blockBtnRed")
            self._block_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ef4444;
                    border: 1px solid #dc2626;
                    border-radius: 6px;
                    color: #ffffff;
                    padding: 8px 14px;
                    font-size: 12px;
                    font-weight: 600;
                    text-align: left;
                    min-height: 26px;
                }
                QPushButton:hover {
                    background-color: #dc2626;
                    border-color: #b91c1c;
                }
            """)

    def _on_block_clicked(self):
        """Handle toggling block / unblock."""
        mac = self._device_data.get("mac")
        if not mac:
            return

        if self._is_blocked:
            # Request unblock -> will revert button back to red
            self.unblock_requested.emit(mac)
            self._update_block_button_state(False)
        else:
            # Request block -> will turn button greyed out and say "Blocked"
            self.block_requested.emit(mac)
            self._update_block_button_state(True)

    def _update_ports_table(self, ports: list):
        """Populate open ports table."""
        self._ports_table.setRowCount(len(ports))
        for row, port_info in enumerate(ports):
            if isinstance(port_info, dict):
                port_num = str(port_info.get("port", ""))
                service = port_info.get("service", "")
                banner = port_info.get("banner", "")
            else:
                port_num = str(port_info)
                service = "open"
                banner = ""

            p_item = QTableWidgetItem(port_num)
            p_item.setForeground(QColor(COLORS["text_primary"]))
            s_item = QTableWidgetItem(service)
            s_item.setForeground(QColor(COLORS["text_secondary"]))
            b_item = QTableWidgetItem(banner)
            b_item.setForeground(QColor(COLORS["text_muted"]))

            self._ports_table.setItem(row, 0, p_item)
            self._ports_table.setItem(row, 1, s_item)
            self._ports_table.setItem(row, 2, b_item)

    def _on_edit_name(self):
        """Open dialog to edit custom device name."""
        current_name = self._name_label.text()
        new_name, ok = QInputDialog.getText(
            self, "Edit Device Name", "Enter new name for this device:", text=current_name
        )
        if ok and new_name.strip():
            mac = self._device_data.get("mac")
            if mac:
                self._name_label.setText(new_name.strip())
                self.name_changed.emit(mac, new_name.strip())

    def _on_revert_clicked(self):
        """Revert custom details back to default detected hardware."""
        mac = self._device_data.get("mac")
        hostname = self._device_data.get("hostname") or self._device_data.get("model") or "Device"
        self._name_label.setText(hostname)
        if mac:
            self.name_changed.emit(mac, "")

    def _on_ping_clicked(self):
        ip = self._device_data.get("ip")
        if ip:
            self.ping_requested.emit(ip)

    def _on_scan_ports_clicked(self):
        ip = self._device_data.get("ip")
        if ip:
            self.scan_ports_requested.emit(ip)
