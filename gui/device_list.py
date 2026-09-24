"""
NetSentry - Device List View (Fing Desktop 4.0.6 Table Layout)
Displays discovered devices in a clean, modern table with search and filtering,
closely matching Fing Desktop 4.0.6.
"""

from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QPushButton, QCheckBox, QAbstractItemView
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont, QColor

from gui.styles.theme import COLORS, get_fing_device_type_info


class DeviceListView(QWidget):
    """
    Device table view replicating Fing Desktop 4.0.6:
    - Header with network name and status pills (Monitoring active, Updated time, Home)
    - Search bar + Status / Type / Brand dropdown filters
    - Clean QTableWidget with Checkbox, Type, Model, Name, Status, and Last Update
    - Footer with Actions, Edit columns, Sort by Status, and pagination
    """

    device_selected = pyqtSignal(str)   # MAC address
    block_device = pyqtSignal(str)      # MAC address
    unblock_device = pyqtSignal(str)    # MAC address
    scan_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._devices = {}  # mac -> dict
        self._filtered_macs = []
        self._network_name = "Local Network"
        self._last_update_str = "Just now"

        self._search_query = ""
        self._filter_status = "All Status"
        self._filter_type = "All Types"
        self._filter_brand = "All Brands"

        self._setup_ui()

    def _setup_ui(self):
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"background-color: {COLORS['bg_window']};")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 20, 28, 20)
        main_layout.setSpacing(14)

        # ── Header: Title & Badges ──
        header_vbox = QVBoxLayout()
        header_vbox.setSpacing(8)

        self._title_label = QLabel(f"Devices of {self._network_name}")
        self._title_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self._title_label.setStyleSheet("color: #f8fafc;")
        header_vbox.addWidget(self._title_label)

        # Badges row
        badges_layout = QHBoxLayout()
        badges_layout.setSpacing(8)

        # Green badge: Monitoring active ⌄
        monitoring_badge = QLabel("Monitoring active  ⌄")
        monitoring_badge.setObjectName("pillGreen")
        badges_layout.addWidget(monitoring_badge)

        # Blue/Purple badge: 🕒 Updated {time}
        self._updated_badge = QLabel(f"🕒 Updated {self._last_update_str}")
        self._updated_badge.setObjectName("pillPurple")
        badges_layout.addWidget(self._updated_badge)

        # Home badge: 🏠 Home ⌄
        home_badge = QLabel("🏠 Home  ⌄")
        home_badge.setObjectName("pillPurple")
        badges_layout.addWidget(home_badge)

        badges_layout.addStretch()
        header_vbox.addLayout(badges_layout)
        main_layout.addLayout(header_vbox)

        # ── Search & Filter Controls Row ──
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)

        # Search bar
        self._search_input = QLineEdit()
        self._search_input.setObjectName("fingSearch")
        self._search_input.setPlaceholderText("🔍  Search")
        self._search_input.setFixedWidth(280)
        self._search_input.textChanged.connect(self._on_search_changed)
        controls_layout.addWidget(self._search_input)

        controls_layout.addStretch()

        # Status filter
        self._status_combo = QComboBox()
        self._status_combo.setObjectName("filterCombo")
        self._status_combo.addItems(["All Status", "Online", "Blocked", "Offline"])
        self._status_combo.currentTextChanged.connect(self._on_status_filter_changed)
        controls_layout.addWidget(self._status_combo)

        # Type filter
        self._type_combo = QComboBox()
        self._type_combo.setObjectName("filterCombo")
        self._type_combo.addItems([
            "All Types", "Laptop", "Desktop", "Television", "Printer",
            "Voice Control", "Smart Device", "Mobile", "Generic"
        ])
        self._type_combo.currentTextChanged.connect(self._on_type_filter_changed)
        controls_layout.addWidget(self._type_combo)

        # Brand filter
        self._brand_combo = QComboBox()
        self._brand_combo.setObjectName("filterCombo")
        self._brand_combo.addItem("All Brands")
        self._brand_combo.currentTextChanged.connect(self._on_brand_filter_changed)
        controls_layout.addWidget(self._brand_combo)

        main_layout.addLayout(controls_layout)

        # ── Devices Table ──
        table_container = QFrame()
        table_container.setObjectName("tableContainer")
        container_layout = QVBoxLayout(table_container)
        container_layout.setContentsMargins(1, 1, 1, 1)

        self._table = QTableWidget()
        self._table.setObjectName("fingTable")
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "", "TYPE", "MODEL", "NAME", "STATUS", "LAST UPDATE"
        ])

        # Table configuration
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)

        self._table.setColumnWidth(0, 38)
        self._table.setColumnWidth(1, 140)
        self._table.setColumnWidth(3, 180)
        self._table.setColumnWidth(4, 90)
        self._table.setColumnWidth(5, 110)

        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self._table.cellClicked.connect(self._on_cell_clicked)
        container_layout.addWidget(self._table)
        main_layout.addWidget(table_container, 1)

        # ── Bottom Bar: Actions, Edit Columns, Sorting, Pagination ──
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)

        actions_btn = QPushButton("Actions  ⌄")
        actions_btn.setObjectName("topNavBtn")
        bottom_layout.addWidget(actions_btn)

        edit_cols_btn = QPushButton("⚙  Edit columns")
        edit_cols_btn.setObjectName("topNavBtn")
        bottom_layout.addWidget(edit_cols_btn)

        sort_btn = QPushButton("Sort by Status  ⬍")
        sort_btn.setObjectName("topNavBtn")
        sort_btn.clicked.connect(self._toggle_sort)
        bottom_layout.addWidget(sort_btn)

        bottom_layout.addStretch()

        self._pagination_label = QLabel("Showing 0 of 0")
        self._pagination_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        bottom_layout.addWidget(self._pagination_label)

        prev_btn = QPushButton("❮")
        prev_btn.setObjectName("topNavBtn")
        prev_btn.setFixedWidth(30)
        bottom_layout.addWidget(prev_btn)

        next_btn = QPushButton("❯")
        next_btn.setObjectName("topNavBtn")
        next_btn.setFixedWidth(30)
        bottom_layout.addWidget(next_btn)

        main_layout.addLayout(bottom_layout)

    def set_network_name(self, name: str):
        """Update network display title."""
        self._network_name = name or "Local Network"
        self._title_label.setText(f"Devices of {self._network_name}")

    def update_devices(self, devices: list):
        """Update full list of devices and refresh table view."""
        self._devices.clear()
        brands = set()
        for d in devices:
            mac = d.get("mac", "").lower()
            if mac:
                self._devices[mac] = d
                vendor = d.get("vendor", "")
                if vendor and vendor != "Unknown":
                    brands.add(vendor)

        # Update brand filter dropdown options
        current_brand = self._brand_combo.currentText()
        self._brand_combo.blockSignals(True)
        self._brand_combo.clear()
        self._brand_combo.addItem("All Brands")
        for b in sorted(brands):
            self._brand_combo.addItem(b)
        idx = self._brand_combo.findText(current_brand)
        if idx >= 0:
            self._brand_combo.setCurrentIndex(idx)
        self._brand_combo.blockSignals(False)

        self._last_update_str = datetime.now().strftime("%H:%M")
        self._updated_badge.setText(f"🕒 Updated {self._last_update_str}")
        self._apply_filters_and_render()

    def add_or_update_device(self, device_data: dict):
        """Add or update a single device entry."""
        mac = device_data.get("mac", "").lower()
        if mac:
            self._devices[mac] = device_data
            self._apply_filters_and_render()

    def _apply_filters_and_render(self):
        """Filter devices and populate the table."""
        self._filtered_macs = []

        query = self._search_query.lower()
        status_filter = self._filter_status.lower()
        type_filter = self._filter_type.lower()
        brand_filter = self._filter_brand

        for mac, d in self._devices.items():
            # Search query matching
            name = (d.get("custom_name") or d.get("hostname") or "").lower()
            model = (d.get("model") or d.get("vendor") or "").lower()
            ip = (d.get("ip") or "").lower()
            vendor = (d.get("vendor") or "").lower()

            if query and not (query in name or query in model or query in ip or query in mac or query in vendor):
                continue

            # Status matching
            is_blocked = d.get("is_blocked", False)
            is_online = d.get("is_online", True)
            status_str = "blocked" if is_blocked else ("online" if is_online else "offline")

            if status_filter != "all status" and status_str != status_filter:
                continue

            # Type matching
            dev_type = (d.get("device_type") or "generic").lower()
            if type_filter != "all types" and type_filter not in dev_type:
                continue

            # Brand matching
            if brand_filter != "All Brands" and d.get("vendor") != brand_filter:
                continue

            self._filtered_macs.append(mac)

        self._render_table()

    def _render_table(self):
        """Render rows in the QTableWidget."""
        total = len(self._devices)
        showing = len(self._filtered_macs)
        self._pagination_label.setText(f"Showing 1-{showing} of {total}" if showing > 0 else f"Showing 0 of {total}")

        self._table.setRowCount(showing)

        for row, mac in enumerate(self._filtered_macs):
            d = self._devices[mac]
            self._table.setRowHeight(row, 46)

            # Col 0: Checkbox
            check_widget = QWidget()
            check_layout = QHBoxLayout(check_widget)
            check_layout.setContentsMargins(12, 0, 0, 0)
            check_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cb = QCheckBox()
            check_layout.addWidget(cb)
            self._table.setCellWidget(row, 0, check_widget)

            # Col 1: TYPE (Icon + Name)
            dev_type = d.get("device_type", "generic")
            icon, display_type = get_fing_device_type_info(dev_type)
            type_item = QTableWidgetItem(f"  {icon}  {display_type}")
            type_item.setFont(QFont("Segoe UI", 12))
            type_item.setData(Qt.ItemDataRole.UserRole, mac)
            self._table.setItem(row, 1, type_item)

            # Col 2: MODEL
            model_text = d.get("model") or d.get("vendor") or "Generic Device"
            model_item = QTableWidgetItem(model_text)
            model_item.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
            model_item.setData(Qt.ItemDataRole.UserRole, mac)
            self._table.setItem(row, 2, model_item)

            # Col 3: NAME
            hostname = d.get("custom_name") or d.get("hostname") or "-"
            name_item = QTableWidgetItem(hostname)
            name_item.setFont(QFont("Segoe UI", 12))
            name_item.setForeground(QColor(COLORS["text_secondary"]))
            name_item.setData(Qt.ItemDataRole.UserRole, mac)
            self._table.setItem(row, 3, name_item)

            # Col 4: STATUS BADGE (Fing rounded pill)
            is_blocked = d.get("is_blocked", False)
            is_online = d.get("is_online", True)

            badge_widget = QWidget()
            badge_layout = QHBoxLayout(badge_widget)
            badge_layout.setContentsMargins(0, 0, 0, 0)
            badge_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            status_badge = QLabel()
            status_badge.setFixedSize(68, 22)
            status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if is_blocked:
                status_badge.setText("Blocked")
                status_badge.setObjectName("badgeBlocked")
            elif is_online:
                status_badge.setText("Online")
                status_badge.setObjectName("badgeOnline")
            else:
                status_badge.setText("Offline")
                status_badge.setObjectName("badgeOffline")

            badge_layout.addWidget(status_badge)
            self._table.setCellWidget(row, 4, badge_widget)

            # Col 5: LAST UPDATE
            last_seen = d.get("last_seen", "")
            last_update_text = self._format_relative_time(last_seen)
            time_item = QTableWidgetItem(last_update_text)
            time_item.setFont(QFont("Segoe UI", 12))
            time_item.setForeground(QColor(COLORS["text_muted"]))
            time_item.setData(Qt.ItemDataRole.UserRole, mac)
            self._table.setItem(row, 5, time_item)

    def _format_relative_time(self, last_seen_str: str) -> str:
        """Format last seen timestamp into Fing-style relative time (e.g. '14m ago')."""
        if not last_seen_str:
            return "Just now"
        try:
            dt = datetime.fromisoformat(last_seen_str)
            diff = datetime.now() - dt
            minutes = int(diff.total_seconds() / 60)
            if minutes < 1:
                return "Just now"
            elif minutes < 60:
                return f"{minutes}m ago"
            hours = minutes // 60
            if hours < 24:
                return f"{hours}h ago"
            days = hours // 24
            return f"{days}d ago"
        except Exception:
            return "Recently"

    def _on_cell_clicked(self, row: int, column: int):
        """Handle clicking any cell to view device details."""
        if 0 <= row < len(self._filtered_macs):
            mac = self._filtered_macs[row]
            self.device_selected.emit(mac)

    def _on_search_changed(self, text: str):
        self._search_query = text
        self._apply_filters_and_render()

    def _on_status_filter_changed(self, text: str):
        self._filter_status = text
        self._apply_filters_and_render()

    def _on_type_filter_changed(self, text: str):
        self._filter_type = text
        self._apply_filters_and_render()

    def _on_brand_filter_changed(self, text: str):
        self._filter_brand = text
        self._apply_filters_and_render()

    def _toggle_sort(self):
        """Toggle table sort."""
        self._filtered_macs.reverse()
        self._render_table()
