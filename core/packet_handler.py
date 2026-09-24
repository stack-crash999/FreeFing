"""
NetSentry - Packet Handler
Controls Windows IP forwarding to drop or forward traffic from blocked devices.
"""

import logging
import subprocess
import winreg

logger = logging.getLogger("netsentry.packet_handler")

# Registry key for IP forwarding
IP_FORWARD_KEY = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters"
IP_FORWARD_VALUE = "IPEnableRouter"


class PacketHandler:
    """
    Controls Windows IP forwarding behavior.

    When a device is ARP-spoofed, its traffic routes through the host PC.
    - IP forwarding DISABLED (default) → traffic is dropped → device has no internet
    - IP forwarding ENABLED → traffic is forwarded → MITM position (not used for blocking)

    For internet blocking, we keep IP forwarding DISABLED so the host PC
    simply drops the spoofed traffic at the kernel level.
    """

    def __init__(self):
        self._original_forwarding_state = None
        self._save_original_state()

    def _save_original_state(self):
        """Save the original IP forwarding state to restore later."""
        try:
            self._original_forwarding_state = self._get_ip_forwarding()
            logger.info(
                f"Original IP forwarding state: "
                f"{'enabled' if self._original_forwarding_state else 'disabled'}"
            )
        except Exception as e:
            logger.error(f"Could not read IP forwarding state: {e}")
            self._original_forwarding_state = False

    def _get_ip_forwarding(self) -> bool:
        """Check if Windows IP forwarding is currently enabled."""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                IP_FORWARD_KEY,
                0,
                winreg.KEY_READ
            )
            value, _ = winreg.QueryValueEx(key, IP_FORWARD_VALUE)
            winreg.CloseKey(key)
            return value == 1
        except FileNotFoundError:
            return False
        except Exception as e:
            logger.error(f"Error reading IP forwarding state: {e}")
            return False

    def _set_ip_forwarding(self, enabled: bool) -> bool:
        """Enable or disable Windows IP forwarding via registry."""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                IP_FORWARD_KEY,
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(
                key, IP_FORWARD_VALUE, 0,
                winreg.REG_DWORD, 1 if enabled else 0
            )
            winreg.CloseKey(key)

            # Also use netsh to apply immediately
            state = "enabled" if enabled else "disabled"
            subprocess.run(
                ["netsh", "interface", "ipv4", "set", "interface",
                 "interface=all", f"forwarding={state}"],
                capture_output=True, timeout=10
            )

            logger.info(f"IP forwarding {'enabled' if enabled else 'disabled'}")
            return True

        except PermissionError:
            logger.error(
                "Permission denied setting IP forwarding. "
                "Run as Administrator."
            )
            return False
        except Exception as e:
            logger.error(f"Failed to set IP forwarding: {e}")
            return False

    def enable_blocking_mode(self):
        """
        Configure the system for blocking mode.
        Ensures IP forwarding is DISABLED so spoofed traffic gets dropped.
        """
        self._set_ip_forwarding(False)
        logger.info("Blocking mode enabled: IP forwarding disabled, traffic will be dropped.")

    def enable_forwarding_mode(self):
        """
        Enable IP forwarding for MITM analysis (not used for blocking).
        Only use this if you want to inspect traffic rather than block it.
        """
        self._set_ip_forwarding(True)
        logger.info("Forwarding mode enabled: traffic will pass through.")

    def restore_original_state(self):
        """Restore the IP forwarding state to what it was before NetSentry started."""
        if self._original_forwarding_state is not None:
            self._set_ip_forwarding(self._original_forwarding_state)
            logger.info(
                f"Restored IP forwarding to original state: "
                f"{'enabled' if self._original_forwarding_state else 'disabled'}"
            )

    def add_firewall_block(self, ip: str, rule_name: str = None):
        """
        Add a Windows Firewall rule to block traffic to/from a specific IP.
        This is an additional layer on top of ARP spoofing.
        """
        if not rule_name:
            rule_name = f"NetSentry_Block_{ip.replace('.', '_')}"

        try:
            # Block outbound to target
            subprocess.run([
                "netsh", "advfirewall", "firewall", "add", "rule",
                f"name={rule_name}_out",
                "dir=out", "action=block",
                f"remoteip={ip}",
                "enable=yes"
            ], capture_output=True, timeout=10)

            # Block inbound from target
            subprocess.run([
                "netsh", "advfirewall", "firewall", "add", "rule",
                f"name={rule_name}_in",
                "dir=in", "action=block",
                f"remoteip={ip}",
                "enable=yes"
            ], capture_output=True, timeout=10)

            logger.info(f"Firewall block rules added for {ip}")
            return True

        except Exception as e:
            logger.error(f"Failed to add firewall rules: {e}")
            return False

    def remove_firewall_block(self, ip: str, rule_name: str = None):
        """Remove previously added firewall block rules."""
        if not rule_name:
            rule_name = f"NetSentry_Block_{ip.replace('.', '_')}"

        try:
            subprocess.run([
                "netsh", "advfirewall", "firewall", "delete", "rule",
                f"name={rule_name}_out"
            ], capture_output=True, timeout=10)

            subprocess.run([
                "netsh", "advfirewall", "firewall", "delete", "rule",
                f"name={rule_name}_in"
            ], capture_output=True, timeout=10)

            logger.info(f"Firewall block rules removed for {ip}")
            return True

        except Exception as e:
            logger.error(f"Failed to remove firewall rules: {e}")
            return False
