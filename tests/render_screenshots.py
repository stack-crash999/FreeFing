"""
Render screenshots of MainWindow in Device List view and Device Detail view.
"""

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))
from PyQt6.QtWidgets import QApplication

app = QApplication(sys.argv)

from gui.styles.theme import get_stylesheet
app.setStyleSheet(get_stylesheet())

from gui.main_window import MainWindow

window = MainWindow()
window.resize(1280, 800)
window.show()

# Directly run initialization so sample devices and network info are populated
window._initialize()
app.processEvents()

output_dir = r"C:\Users\oroog\.gemini\antigravity-ide\brain\1e8fac5a-128d-4c2b-92e0-1d10e941e6d8"

# 1. Capture Device List View
window._navigate_to("devices")
app.processEvents()
pix_list = window.grab()
list_path = os.path.join(output_dir, "fing_gui_device_list.png")
pix_list.save(list_path)
print(f"Device List screenshot saved to {list_path}")

# 2. Capture Device Detail View (KnifemasterYT)
window._show_device_detail("04:ec:d8:02:c4:6b")
app.processEvents()
pix_detail = window.grab()
detail_path = os.path.join(output_dir, "fing_gui_device_detail.png")
pix_detail.save(detail_path)
print(f"Device Detail screenshot saved to {detail_path}")

# 3. Capture Blocked State in Detail View
window._device_detail._update_block_button_state(True)
app.processEvents()
pix_blocked = window.grab()
blocked_path = os.path.join(output_dir, "fing_gui_device_detail_blocked.png")
pix_blocked.save(blocked_path)
print(f"Device Detail Blocked screenshot saved to {blocked_path}")

window.close()
app.quit()
