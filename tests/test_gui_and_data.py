"""
Unit and integration tests for NetSentry Fing 4.0.6 UI and data layers.
"""

import unittest
import os
import sys
from PyQt6.QtWidgets import QApplication

# Ensure QApplication exists for widget tests
app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)

from data.device_store import DeviceRecord, DeviceStore
from gui.styles.theme import (
    COLORS, get_stylesheet, get_fing_device_type_info,
    DEVICE_ICONS, STATUS_COLORS
)
from gui.device_detail import DeviceDetailView
from gui.device_list import DeviceListView


class TestDataAndTheme(unittest.TestCase):
    """Test data model and theme tokens."""

    def test_device_record_serialization(self):
        rec = DeviceRecord(
            mac="04:EC:D8:02:C4:6B",
            ip="192.168.68.68",
            hostname="KnifemasterYT",
            vendor="HP",
            model="HP OMEN 40L Gaming GT21-0xxx",
            os="Windows",
            device_type="desktop",
            is_online=True,
            is_blocked=False,
        )
        d = rec.to_dict()
        self.assertEqual(d["mac"], "04:EC:D8:02:C4:6B")
        self.assertEqual(d["model"], "HP OMEN 40L Gaming GT21-0xxx")
        self.assertEqual(d["os"], "Windows")

        rec2 = DeviceRecord.from_dict(d)
        self.assertEqual(rec2.mac, "04:EC:D8:02:C4:6B")
        self.assertEqual(rec2.model, "HP OMEN 40L Gaming GT21-0xxx")
        self.assertEqual(rec2.os, "Windows")

    def test_fing_device_type_info(self):
        icon, name = get_fing_device_type_info("laptop")
        self.assertEqual(name, "Laptop")
        self.assertIn("💻", icon)

        icon, name = get_fing_device_type_info("television")
        self.assertEqual(name, "Television")

        icon, name = get_fing_device_type_info("unknown_xyz")
        self.assertEqual(name, "Generic")

    def test_oui_lookup_expanded(self):
        from data.oui_database import OUIDatabase
        db = OUIDatabase()
        self.assertEqual(db.lookup("04:EC:D8:02:C4:6B"), "HP")
        self.assertEqual(db.lookup("54:EE:75:11:22:33"), "Lenovo")
        self.assertEqual(db.lookup("E8:50:8B:AA:BB:CC"), "Samsung")
        self.assertEqual(db.lookup("FC:65:DE:77:88:99"), "Amazon")

    def test_device_identifier_heuristics(self):
        from core.device_identifier import identify_device
        res = identify_device("192.168.68.68", "04:EC:D8:02:C4:6B", vendor="HP")
        self.assertEqual(res["vendor"], "HP")
        self.assertEqual(res["device_type"], "desktop")

    def test_stylesheet_generation(self):
        qss = get_stylesheet()
        self.assertIn("QMainWindow", qss)
        self.assertIn("blockBtnRed", qss)
        self.assertIn("blockBtnGrey", qss)
        self.assertIn("badgeOnline", qss)
        self.assertIn("fingTable", qss)


class TestFingGUIWidgets(unittest.TestCase):
    """Test widget behavior and Block button state."""

    def setUp(self):
        self.detail_view = DeviceDetailView()
        self.list_view = DeviceListView()

    def test_block_button_state_unblocked(self):
        """When device is unblocked, button must be Red with Block text."""
        device_data = {
            "mac": "04:EC:D8:02:C4:6B",
            "ip": "192.168.68.68",
            "hostname": "KnifemasterYT",
            "model": "HP OMEN 40L Gaming GT21-0xxx",
            "vendor": "HP",
            "device_type": "desktop",
            "is_blocked": False,
            "is_online": True,
        }
        self.detail_view.set_device(device_data)
        self.assertEqual(self.detail_view._block_btn.objectName(), "blockBtnRed")
        self.assertIn("Block network access", self.detail_view._block_btn.text())

    def test_block_button_state_blocked(self):
        """When device is blocked, button must be Greyed out with Blocked text."""
        device_data = {
            "mac": "04:EC:D8:02:C4:6B",
            "ip": "192.168.68.68",
            "hostname": "KnifemasterYT",
            "model": "HP OMEN 40L Gaming GT21-0xxx",
            "vendor": "HP",
            "device_type": "desktop",
            "is_blocked": True,
            "is_online": True,
        }
        self.detail_view.set_device(device_data)
        self.assertEqual(self.detail_view._block_btn.objectName(), "blockBtnGrey")
        self.assertIn("Blocked", self.detail_view._block_btn.text())

    def test_block_button_toggle_flow(self):
        """Clicking block button toggles from red to greyed out and emits signal."""
        device_data = {
            "mac": "04:EC:D8:02:C4:6B",
            "ip": "192.168.68.68",
            "hostname": "KnifemasterYT",
            "is_blocked": False,
        }
        self.detail_view.set_device(device_data)

        # Capture signal
        emitted_blocks = []
        emitted_unblocks = []
        self.detail_view.block_requested.connect(lambda mac: emitted_blocks.append(mac))
        self.detail_view.unblock_requested.connect(lambda mac: emitted_unblocks.append(mac))

        # First click: block
        self.detail_view._on_block_clicked()
        self.assertEqual(len(emitted_blocks), 1)
        self.assertEqual(emitted_blocks[0], "04:EC:D8:02:C4:6B")
        self.assertEqual(self.detail_view._block_btn.objectName(), "blockBtnGrey")
        self.assertIn("Blocked", self.detail_view._block_btn.text())

        # Second click: unblock
        self.detail_view._on_block_clicked()
        self.assertEqual(len(emitted_unblocks), 1)
        self.assertEqual(emitted_unblocks[0], "04:EC:D8:02:C4:6B")
        self.assertEqual(self.detail_view._block_btn.objectName(), "blockBtnRed")
        self.assertIn("Block network access", self.detail_view._block_btn.text())

    def test_device_list_rendering(self):
        """Test device list table population."""
        devices = [
            {
                "mac": "04:EC:D8:02:C4:6B",
                "ip": "192.168.68.68",
                "hostname": "KnifemasterYT",
                "model": "HP OMEN 40L",
                "vendor": "HP",
                "device_type": "desktop",
                "is_online": True,
                "is_blocked": False,
            },
            {
                "mac": "34:E6:D7:11:22:33",
                "ip": "192.168.68.21",
                "hostname": "ThinkPad",
                "model": "X1 Carbon",
                "vendor": "Lenovo",
                "device_type": "laptop",
                "is_online": True,
                "is_blocked": True,
            }
        ]
        self.list_view.update_devices(devices)
        self.assertEqual(self.list_view._table.rowCount(), 2)

        # Row selection signal
        selected_macs = []
        self.list_view.device_selected.connect(lambda mac: selected_macs.append(mac))
        self.list_view._on_cell_clicked(0, 1)
        self.assertEqual(len(selected_macs), 1)
        self.assertEqual(selected_macs[0], "04:ec:d8:02:c4:6b")


if __name__ == "__main__":
    unittest.main()
