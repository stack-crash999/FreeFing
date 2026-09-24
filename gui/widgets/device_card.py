"""
NetSentry - Device Card Widget
Individual device card for the device list view.
"""

from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QWidget
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from gui.styles.theme import DEVICE_ICONS, STATUS_COLORS, COLORS


class StatusDot(QWidget):
    """Colored dot indicator for device status."""

    def __init__(self, status: str = "offline", parent=None):
        super().__init__(parent)
        self.setFixedSize(10, 10)
        self._status = status
        self._update_style()

    def set_status(self, status: str):
        self._status = status
        self._update_style()

    def _update_style(self):
        color = STATUS_COLORS.get(self._status, STATUS_COLORS["offline"])
        self.setStyleSheet(f"""
            background-color: {color};
            border-radius: 5px;
            border: none;
        """)


class DeviceCard(QFrame):
    """
    A card widget displaying device information.
    Shows: icon, name, IP, MAC, vendor, status, and block button.

    Signals:
        clicked: Emitted when the card is clicked (mac_address)
        block_requested: Emitted when block button is clicked (mac_address)
        unblock_requested: Emitted when unblock button is clicked (mac_address)
    """

    clicked = pyqtSignal(str)
    block_requested = pyqtSignal(str)
    unblock_requested = pyqtSignal(str)

    def __init__(self, device_data: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("deviceCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._data = device_data
        self._mac = device_data.get("mac", "")
        self._is_blocked = device_data.get("is_blocked", False)

        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)

        # Device icon
        device_type = self._data.get("device_type", "unknown")
        icon_text = DEVICE_ICONS.get(device_type, "❓")
        icon_label = QLabel(icon_text)
        icon_label.setFixedSize(40, 40)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(f"""
            font-size: 22px;
            background-color: {COLORS['bg_tertiary']};
            border-radius: 10px;
        """)
        layout.addWidget(icon_label)

        # Device info column
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setContentsMargins(0, 0, 0, 0)

        # Device name
        name = self._data.get("display_name", "") or self._data.get("device_name", "") or self._data.get("hostname", "") or self._data.get("vendor", "Unknown Device")
        name_label = QLabel(name)
        name_label.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        name_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        info_layout.addWidget(name_label)

        # IP + MAC
        ip = self._data.get("ip", "")
        mac = self._data.get("mac", "")
        detail_text = f"{ip}  •  {mac}"
        detail_label = QLabel(detail_text)
        detail_label.setFont(QFont("Segoe UI", 11))
        detail_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        info_layout.addWidget(detail_label)

        # Vendor
        vendor = self._data.get("vendor", "Unknown")
        if vendor and vendor != "Unknown":
            vendor_label = QLabel(vendor)
            vendor_label.setFont(QFont("Segoe UI", 10))
            vendor_label.setStyleSheet(f"color: {COLORS['text_muted']};")
            info_layout.addWidget(vendor_label)

        layout.addLayout(info_layout, 1)

        # Status indicator
        status = "blocked" if self._is_blocked else ("online" if self._data.get("is_online", True) else "offline")
        self._status_dot = StatusDot(status)
        status_text = QLabel(status.capitalize())
        status_text.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        status_text.setStyleSheet(f"color: {STATUS_COLORS.get(status, COLORS['text_muted'])};")

        status_layout = QVBoxLayout()
        status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self._status_dot, 0, Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(status_text, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(status_layout)

        # Block/Unblock button
        if self._is_blocked:
            btn = QPushButton("Blocked")
            btn.setObjectName("unblockButton")
            btn.setToolTip("Click to unblock")
            btn.clicked.connect(lambda: self.unblock_requested.emit(self._mac))
        else:
            btn = QPushButton("Block")
            btn.setObjectName("blockButton")
            btn.setToolTip("Click to block internet access")
            btn.clicked.connect(lambda: self.block_requested.emit(self._mac))

        btn.setFixedWidth(70)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(btn)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._mac)
        super().mousePressEvent(event)

    def update_data(self, device_data: dict):
        """Update the card with new device data."""
        self._data = device_data
        self._mac = device_data.get("mac", "")
        self._is_blocked = device_data.get("is_blocked", False)
        # Rebuild UI
        for i in reversed(range(self.layout().count())):
            item = self.layout().itemAt(i)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
        self._setup_ui()
