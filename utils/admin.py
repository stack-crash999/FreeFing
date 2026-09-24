"""
NetSentry - UAC Elevation Helper
Handles Windows Administrator privilege detection and elevation.
"""

import sys
import os
import ctypes
import logging

logger = logging.getLogger("netsentry.admin")


def is_admin() -> bool:
    """Check if the current process has Administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except AttributeError:
        # Not on Windows
        return os.getuid() == 0
    except Exception:
        return False


def request_elevation():
    """
    Re-launch the current script with Administrator privileges via UAC prompt.
    This will terminate the current (non-elevated) process.
    """
    if is_admin():
        return True

    try:
        script = os.path.abspath(sys.argv[0])
        params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])

        logger.info("Requesting UAC elevation...")

        # ShellExecuteW returns > 32 on success
        ret = ctypes.windll.shell32.ShellExecuteW(
            None,           # hwnd
            "runas",        # operation - triggers UAC
            sys.executable, # executable
            f'"{script}" {params}',  # parameters
            None,           # directory
            1               # SW_SHOWNORMAL
        )

        if ret > 32:
            logger.info("Elevation request sent, terminating current process.")
            sys.exit(0)
        else:
            logger.error(f"Elevation failed with return code: {ret}")
            return False

    except Exception as e:
        logger.error(f"Failed to request elevation: {e}")
        return False


def ensure_admin():
    """
    Ensure the application is running with admin privileges.
    If not, attempt UAC elevation. Returns True if admin, False if elevation failed.
    """
    if is_admin():
        logger.info("Running with Administrator privileges.")
        return True

    logger.warning("Not running as Administrator. Requesting elevation...")
    request_elevation()
    return False
