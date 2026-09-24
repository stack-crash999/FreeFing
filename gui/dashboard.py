"""
NetSentry - Dashboard View
Network overview with stats, scan button, and network info card.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QProgressBar, QScrollArea, QGridLayout, QTextEdit
)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont

from gui.styles.theme import COLORS, DEVICE_ICONS


class StatCard(QFrame):
    """A statistics card showing a value and label."""

    def __init__(self, value: str, label: str, color: str = None, parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setMinimumSize(140, 100)

        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._value_label = QLabel(value)
        self._value_label.setObjectName("statValue")
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if color:
            self._value_label.setStyleSheet(f"color: {color}; font-size: 32px; font-weight: 700;")
        layout.addWidget(self._value_label)

        self._text_label = QLabel(label)
        self._text_label.setObjectName("statLabel")
        self._text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._text_label)

    def set_value(self, value: str):
        self._value_label.setText(value)

    def set_color(self, color: str):
        self._value_label.setStyleSheet(f"color: {color}; font-size: 32px; font-weight: 700;")


class DashboardView(QWidget):
    """
    Main dashboard showing network overview, statistics, and scan controls.

    Signals:
        scan_requested: Emitted when the user clicks the scan button
        stop_scan_requested: Emitted when stopping a scan
    """

    scan_requested = pyqtSignal()
    stop_scan_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_scanning = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # ── Title Section ──
        title_layout = QVBoxLayout()
        title = QLabel("Network Dashboard")
        title.setObjectName("titleLabel")
        title_layout.addWidget(title)

        subtitle = QLabel("Monitor and manage devices on your local network")
        subtitle.setObjectName("subtitleLabel")
        title_layout.addWidget(subtitle)
        layout.addLayout(title_layout)

        # ── Network Info Card ──
        self._network_card = QFrame()
        self._network_card.setObjectName("networkInfoCard")
        net_layout = QGridLayout(self._network_card)
        net_layout.setSpacing(16)

        # Network info labels
        self._ssid_label = self._make_info_row("Wi-Fi Network", "Scanning...", net_layout, 0)
        self._gateway_label = self._make_info_row("Gateway", "—", net_layout, 1)
        self._local_ip_label = self._make_info_row("Your IP", "—", net_layout, 2)
        self._subnet_label = self._make_info_row("Subnet", "—", net_layout, 3)

        layout.addWidget(self._network_card)

        # ── Stats Row ──
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        self._total_devices_card = StatCard("0", "DEVICES", COLORS["accent"])
        self._online_card = StatCard("0", "ONLINE", COLORS["success"])
        self._blocked_card = StatCard("0", "BLOCKED", COLORS["danger"])
        self._new_card = StatCard("0", "NEW", COLORS["warning"])

        stats_layout.addWidget(self._total_devices_card)
        stats_layout.addWidget(self._online_card)
        stats_layout.addWidget(self._blocked_card)
        stats_layout.addWidget(self._new_card)

        layout.addLayout(stats_layout)

        # ── Scan Button ──
        scan_container = QHBoxLayout()
        scan_container.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._scan_btn = QPushButton("⚡  Scan Network")
        self._scan_btn.setObjectName("scanButton")
        self._scan_btn.setMinimumWidth(240)
        self._scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._scan_btn.clicked.connect(self._on_scan_clicked)
        scan_container.addWidget(self._scan_btn)

        layout.addLayout(scan_container)

        # ── Progress Bar ──
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setFixedHeight(6)
        self._progress_bar.setVisible(False)
        layout.addWidget(self._progress_bar)

        # ── Activity Log ──
        log_title = QLabel("Activity Log")
        log_title.setObjectName("sectionTitle")
        layout.addWidget(log_title)

        self._activity_log = QTextEdit()
        self._activity_log.setReadOnly(True)
        self._activity_log.setMaximumHeight(200)
        self._activity_log.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 12px;
                font-family: 'Cascadia Code', 'Consolas', monospace;
                font-size: 11px;
            }}
        """)
        layout.addWidget(self._activity_log)

        layout.addStretch()

    def _make_info_row(self, label_text: str, value_text: str, grid: QGridLayout, row: int):
        """Create a label-value pair in the network info card."""
        label = QLabel(label_text)
        label.setFont(QFont("Segoe UI", 11))
        label.setStyleSheet(f"color: {COLORS['text_muted']};")

        value = QLabel(value_text)
        value.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        value.setStyleSheet(f"color: {COLORS['text_primary']};")

        col = 0 if row < 2 else 2
        actual_row = row % 2
        grid.addWidget(label, actual_row, col)
        grid.addWidget(value, actual_row, col + 1)

        return value

    def _on_scan_clicked(self):
        if self._is_scanning:
            self.stop_scan_requested.emit()
        else:
            self.scan_requested.emit()

    # ── Public update methods ──

    def set_scanning(self, scanning: bool):
        """Update UI for scanning state."""
        self._is_scanning = scanning
        if scanning:
            self._scan_btn.setText("⏹  Stop Scan")
            self._scan_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['danger']};
                    color: white;
                    border: none;
                    border-radius: 12px;
                    padding: 14px 36px;
                    font-size: 15px;
                    font-weight: 700;
                    min-height: 28px;
                }}
                QPushButton:hover {{ background: {COLORS['danger_hover']}; }}
            """)
            self._progress_bar.setVisible(True)
            self._progress_bar.setValue(0)
        else:
            self._scan_btn.setText("⚡  Scan Network")
            self._scan_btn.setObjectName("scanButton")
            self._scan_btn.setStyleSheet("")  # Reset to theme default
            self._progress_bar.setVisible(False)

    def set_progress(self, value: int):
        self._progress_bar.setValue(value)

    def update_network_info(self, info: dict):
        """Update the network info card."""
        self._ssid_label.setText(info.get("ssid", "Unknown") or "Wired Connection")
        self._gateway_label.setText(info.get("gateway_ip", "—") or "—")
        self._local_ip_label.setText(info.get("local_ip", "—") or "—")
        self._subnet_label.setText(info.get("subnet", "—") or "—")

    def update_stats(self, total: int = 0, online: int = 0, blocked: int = 0, new: int = 0):
        """Update the statistics cards."""
        self._total_devices_card.set_value(str(total))
        self._online_card.set_value(str(online))
        self._blocked_card.set_value(str(blocked))
        self._new_card.set_value(str(new))

    def add_log_entry(self, message: str):
        """Add a timestamped entry to the activity log."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._activity_log.append(
            f'<span style="color:{COLORS["text_muted"]}">[{timestamp}]</span> '
            f'<span style="color:{COLORS["text_secondary"]}">{message}</span>'
        )
        # Auto-scroll to bottom
        scrollbar = self._activity_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
