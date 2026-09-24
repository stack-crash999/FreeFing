"""
NetSentry - Application Entry Point
Handles UAC elevation, Npcap checks, and launches the GUI.
"""

import sys
import os
import logging

# Add the project root to path so all imports work
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def main():
    """Application entry point."""

    # ── Step 1: Setup Logging ──
    from utils.logger import setup_logging
    logger = setup_logging(level=logging.INFO)
    logger.info("=" * 60)
    logger.info("NetSentry v1.0.0 starting...")
    logger.info("=" * 60)

    # ── Step 2: Check Admin Privileges ──
    from utils.admin import is_admin, request_elevation

    if not is_admin():
        logger.warning("Not running as Administrator.")
        print("\n⚠  NetSentry requires Administrator privileges for network scanning.")
        print("   Requesting elevation...\n")
        request_elevation()
        # If we get here, elevation was denied
        print("❌ Administrator privileges are required. Please run as Administrator.")
        sys.exit(1)

    logger.info("Running with Administrator privileges ✓")

    # ── Step 3: Check Npcap ──
    from utils.npcap_check import check_npcap_or_warn

    npcap_status = check_npcap_or_warn()
    if not npcap_status["installed"]:
        logger.warning("Npcap not found.")
        print("\n⚠  " + npcap_status["message"])
        # Continue anyway — fallback scanning will work without Npcap

    # ── Step 4: Launch GUI ──
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont

    app = QApplication(sys.argv)
    app.setApplicationName("NetSentry")
    app.setOrganizationName("NetSentry")
    app.setApplicationVersion("1.0.0")

    # Apply dark theme
    from gui.styles.theme import get_stylesheet
    app.setStyleSheet(get_stylesheet())

    # Set default font
    font = QFont("Segoe UI", 11)
    app.setFont(font)

    # Show Npcap warning dialog if not installed
    if not npcap_status["installed"]:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Npcap Not Found")
        msg.setText("Npcap is not installed on this system.")
        msg.setInformativeText(
            "NetSentry requires Npcap for full network scanning capabilities.\n\n"
            "Without Npcap, the app will use a fallback scanning method "
            "that may be slower and less accurate.\n\n"
            "Download Npcap from: https://npcap.com"
        )
        msg.setStandardButtons(
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Close
        )
        msg.setDefaultButton(QMessageBox.StandardButton.Ok)
        result = msg.exec()

        if result == QMessageBox.StandardButton.Close:
            sys.exit(0)

    # Create and show main window
    from gui.main_window import MainWindow
    window = MainWindow()
    window.show()

    logger.info("GUI launched successfully.")

    # Run event loop
    exit_code = app.exec()

    logger.info(f"Application exited with code {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
