"""
NetSentry - Npcap Detection Utility
Checks for Npcap installation and provides guidance for installation.
"""

import os
import sys
import logging
import subprocess
import ctypes

logger = logging.getLogger("netsentry.npcap")

NPCAP_DOWNLOAD_URL = "https://npcap.com/#download"

# Known Npcap DLL locations
NPCAP_PATHS = [
    os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "Npcap", "wpcap.dll"),
    os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "wpcap.dll"),
    os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "SysWOW64", "Npcap", "wpcap.dll"),
    os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "SysWOW64", "wpcap.dll"),
]

NPCAP_SERVICE_NAME = "npcap"


def is_npcap_installed() -> bool:
    """Check if Npcap is installed by looking for its DLL files."""
    for path in NPCAP_PATHS:
        if os.path.exists(path):
            logger.info(f"Found Npcap DLL at: {path}")
            return True

    # Also check via the Npcap service
    try:
        result = subprocess.run(
            ["sc", "query", NPCAP_SERVICE_NAME],
            capture_output=True, text=True, timeout=5
        )
        if "RUNNING" in result.stdout or "STOPPED" in result.stdout:
            logger.info("Found Npcap via service query.")
            return True
    except Exception:
        pass

    # Try loading wpcap.dll directly
    try:
        ctypes.cdll.LoadLibrary("wpcap.dll")
        logger.info("Successfully loaded wpcap.dll.")
        return True
    except OSError:
        pass

    logger.warning("Npcap not found on this system.")
    return False


def get_npcap_version() -> str:
    """Attempt to get the installed Npcap version."""
    try:
        # Check Npcap install directory for version info
        npcap_dir = os.path.join(os.environ.get("ProgramFiles", ""), "Npcap")
        if os.path.exists(npcap_dir):
            # Read version from the install directory
            for item in os.listdir(npcap_dir):
                if "version" in item.lower():
                    version_file = os.path.join(npcap_dir, item)
                    with open(version_file, "r") as f:
                        return f.read().strip()

        # Try sc query for version info
        result = subprocess.run(
            ["sc", "qc", NPCAP_SERVICE_NAME],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return "Installed (version unknown)"

    except Exception as e:
        logger.debug(f"Could not determine Npcap version: {e}")

    return "Unknown"


def check_npcap_or_warn() -> dict:
    """
    Check Npcap installation status.
    Returns a dict with:
      - installed: bool
      - version: str
      - download_url: str
      - message: str
    """
    installed = is_npcap_installed()
    version = get_npcap_version() if installed else "Not installed"

    if installed:
        return {
            "installed": True,
            "version": version,
            "download_url": NPCAP_DOWNLOAD_URL,
            "message": f"Npcap is installed ({version})."
        }
    else:
        return {
            "installed": False,
            "version": version,
            "download_url": NPCAP_DOWNLOAD_URL,
            "message": (
                "Npcap is required for NetSentry to capture network packets.\n\n"
                f"Please download and install Npcap from:\n{NPCAP_DOWNLOAD_URL}\n\n"
                "During installation, check:\n"
                '  ✓ "Install Npcap in WinPcap API-compatible Mode"\n'
                '  ✓ "Support raw 802.11 traffic" (optional, for WiFi)\n\n'
                "After installation, restart NetSentry."
            )
        }


def open_npcap_download():
    """Open the Npcap download page in the default browser."""
    import webbrowser
    webbrowser.open(NPCAP_DOWNLOAD_URL)
