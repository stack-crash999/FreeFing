"""
NetSentry - Settings Panel
Application settings and configuration UI.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QComboBox, QCheckBox, QSpinBox, QGroupBox, QFormLayout
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from gui.styles.theme import COLORS


class SettingsPanel(QWidget):
    """
    Settings panel for app configuration.

    Signals:
        settings_changed: Emitted when settings are modified (dict of settings)
    """

    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Title
        title = QLabel("Settings")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        subtitle = QLabel("Configure NetSentry preferences")
        subtitle.setObjectName("subtitleLabel")
        layout.addWidget(subtitle)

        # ── Scanning Settings ──
        scan_group = QGroupBox("Network Scanning")
        scan_group.setStyleSheet(f"""
            QGroupBox {{
                color: {COLORS['text_primary']};
                font-size: 14px;
                font-weight: 600;
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                margin-top: 12px;
                padding: 20px 16px 16px 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }}
        """)
        scan_layout = QFormLayout(scan_group)
        scan_layout.setSpacing(12)

        self._scan_timeout = QSpinBox()
        self._scan_timeout.setRange(1, 30)
        self._scan_timeout.setValue(3)
        self._scan_timeout.setSuffix(" seconds")
        scan_layout.addRow("Scan Timeout:", self._scan_timeout)

        self._auto_scan = QCheckBox("Enable automatic periodic scanning")
        self._auto_scan.setChecked(False)
        scan_layout.addRow("", self._auto_scan)

        self._scan_interval = QSpinBox()
        self._scan_interval.setRange(30, 600)
        self._scan_interval.setValue(60)
        self._scan_interval.setSuffix(" seconds")
        scan_layout.addRow("Scan Interval:", self._scan_interval)

        self._deep_scan = QCheckBox("Enable port scanning (fingerprinting)")
        self._deep_scan.setChecked(True)
        scan_layout.addRow("", self._deep_scan)

        layout.addWidget(scan_group)

        # ── Blocking Settings ──
        block_group = QGroupBox("Internet Blocking")
        block_group.setStyleSheet(scan_group.styleSheet())
        block_layout = QFormLayout(block_group)
        block_layout.setSpacing(12)

        self._arp_interval = QSpinBox()
        self._arp_interval.setRange(1, 10)
        self._arp_interval.setValue(1)
        self._arp_interval.setSuffix(" seconds")
        block_layout.addRow("ARP Packet Interval:", self._arp_interval)

        self._auto_restore = QCheckBox("Auto-restore ARP on exit (recommended)")
        self._auto_restore.setChecked(True)
        block_layout.addRow("", self._auto_restore)

        self._firewall_rules = QCheckBox("Also add Windows Firewall rules")
        self._firewall_rules.setChecked(False)
        block_layout.addRow("", self._firewall_rules)

        layout.addWidget(block_group)

        # ── About Section ──
        about_group = QGroupBox("About")
        about_group.setStyleSheet(scan_group.styleSheet())
        about_layout = QVBoxLayout(about_group)

        about_text = QLabel(
            "NetSentry v1.0.0\n\n"
            "A network management tool for discovering devices, \n"
            "identifying them, and controlling internet access on your LAN.\n\n"
            "⚠ Use responsibly on networks you own or administer.\n\n"
            "Inspired by Fing Network Scanner\n"
            "Built with Python, PyQt6, Scapy"
        )
        about_text.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        about_text.setWordWrap(True)
        about_layout.addWidget(about_text)

        layout.addWidget(about_group)

        # ── Save Button ──
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        save_btn = QPushButton("Save Settings")
        save_btn.setObjectName("primaryButton")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._on_save)
        save_layout.addWidget(save_btn)
        layout.addLayout(save_layout)

        layout.addStretch()

    def _on_save(self):
        settings = {
            "scan_timeout": self._scan_timeout.value(),
            "auto_scan": self._auto_scan.isChecked(),
            "scan_interval": self._scan_interval.value(),
            "deep_scan": self._deep_scan.isChecked(),
            "arp_interval": self._arp_interval.value(),
            "auto_restore": self._auto_restore.isChecked(),
            "firewall_rules": self._firewall_rules.isChecked(),
        }
        self.settings_changed.emit(settings)

    def get_settings(self) -> dict:
        return {
            "scan_timeout": self._scan_timeout.value(),
            "auto_scan": self._auto_scan.isChecked(),
            "scan_interval": self._scan_interval.value(),
            "deep_scan": self._deep_scan.isChecked(),
            "arp_interval": self._arp_interval.value(),
            "auto_restore": self._auto_restore.isChecked(),
            "firewall_rules": self._firewall_rules.isChecked(),
        }
