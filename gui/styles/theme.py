"""
NetSentry - Fing Desktop 4.0.6 Inspired Theme
Comprehensive QSS and design tokens matching Fing Desktop 4.0.6 dark aesthetics.
"""

# ── Color Palette ──
COLORS = {
    # Core Backgrounds
    "bg_window": "#0b101d",       # Deepest midnight navy
    "bg_sidebar": "#090d18",      # Sidebar background
    "bg_card": "#121829",         # Panel / Card / Table container
    "bg_card_inner": "#161e33",   # Inner nested containers
    "bg_surface": "#1b243b",      # Raised buttons, badges, inputs
    "bg_surface_hover": "#243050",# Button hover
    "bg_input": "#131b2e",        # Search / input boxes

    # Accents & Primaries
    "accent_blue": "#2d68ff",     # Fing primary action blue
    "accent_blue_hover": "#3b82f6",
    "accent_blue_pressed": "#1d4ed8",
    "accent_glow": "rgba(45, 104, 255, 0.18)",

    # Badges & Statuses
    "status_online_bg": "#0f2b23",
    "status_online_text": "#34d399",
    "status_online_border": "#174738",

    "status_offline_bg": "#1c2438",
    "status_offline_text": "#94a3b8",
    "status_offline_border": "#28344f",

    "status_blocked_bg": "#33161c",
    "status_blocked_text": "#f87171",
    "status_blocked_border": "#542129",

    # Block Button Specific Colors
    "block_btn_red_bg": "#ef4444",
    "block_btn_red_hover": "#dc2626",
    "block_btn_red_text": "#ffffff",

    "block_btn_grey_bg": "#232c40",
    "block_btn_grey_hover": "#2a364e",
    "block_btn_grey_text": "#78879e",
    "block_btn_grey_border": "#374563",

    # Pills & Header Badges
    "pill_purple_bg": "#1f253e",
    "pill_purple_text": "#a5b4fc",
    "pill_purple_border": "#2c3659",

    "pill_green_bg": "#102e26",
    "pill_green_text": "#34d399",
    "pill_green_border": "#1b4d3f",

    # Text
    "text_primary": "#f8fafc",    # Bright headings
    "text_secondary": "#cbd5e1",  # Body text
    "text_muted": "#64748b",      # Dim metadata / placeholders
    "text_accent": "#93c5fd",

    # Borders & Dividers
    "border_subtle": "#1e2942",
    "border_medium": "#2a395c",
    # Profile Avatar
    "avatar_bg": "#d97706",
    "avatar_text": "#ffffff",

    # Legacy / Compatibility Aliases
    "bg_primary": "#0b101d",
    "bg_secondary": "#121829",
    "bg_tertiary": "#1b243b",
    "accent": "#2d68ff",
    "accent_hover": "#3b82f6",
    "accent_dark": "#1d4ed8",
    "success": "#22c55e",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "danger_hover": "#dc2626",
    "border": "#1e2942",
    "border_active": "#2d68ff",
    "divider": "#1e2942",
    "scrollbar_bg": "#090d18",
    "scrollbar_handle": "#232d44",
    "scrollbar_hover": "#334160",
    "shadow": "rgba(0, 0, 0, 0.4)",
}

# Status colors for device indicators
STATUS_COLORS = {
    "online": COLORS["status_online_text"],
    "offline": COLORS["text_muted"],
    "blocked": COLORS["status_blocked_text"],
    "scanning": COLORS["warning"],
}

# Device type icons mapping
DEVICE_ICONS = {
    "smartphone": "📱",
    "tablet": "📱",
    "laptop": "💻",
    "router": "🌐",
    "printer": "🖨️",
    "smart_tv": "📺",
    "television": "📺",
    "iot_device": "💡",
    "smart_device": "💡",
    "voice_control": "🎙️",
    "server": "🖥️",
    "desktop": "🖥️",
    "game_console": "🎮",
    "generic": "⚙️",
    "unknown": "⚙️",
}

FONT_FAMILY = "'Segoe UI', -apple-system, BlinkMacSystemFont, 'Inter', Roboto, sans-serif"


def get_stylesheet() -> str:
    """Generate the complete application stylesheet styled like Fing Desktop 4.0.6."""
    c = COLORS
    return f"""
    /* ══════════════════════════════════════════════
       GLOBAL RESET
       ══════════════════════════════════════════════ */
    QMainWindow, QWidget#centralWidget {{
        background-color: {c['bg_window']};
        color: {c['text_primary']};
        font-family: {FONT_FAMILY};
    }}

    QWidget {{
        color: {c['text_primary']};
        font-family: {FONT_FAMILY};
        font-size: 13px;
    }}

    /* ══════════════════════════════════════════════
       SIDEBAR & NAVIGATION
       ══════════════════════════════════════════════ */
    QFrame#sidebar {{
        background-color: {c['bg_sidebar']};
        border-right: 1px solid {c['border_subtle']};
    }}

    QPushButton#sidebarBtn {{
        background-color: transparent;
        color: {c['text_secondary']};
        border: none;
        border-left: 3px solid transparent;
        border-radius: 0px;
        padding: 8px 16px;
        text-align: left;
        font-size: 13px;
        font-weight: 500;
        min-height: 22px;
    }}

    QPushButton#sidebarBtn:hover {{
        background-color: #11182c;
        color: {c['text_primary']};
    }}

    QPushButton#sidebarBtn:checked {{
        background-color: #121d38;
        color: #60a5fa;
        border-left: 3px solid {c['accent_blue']};
        font-weight: 600;
    }}

    /* Top navigation bar buttons (< > and Scan) */
    QPushButton#topNavBtn {{
        background-color: {c['bg_surface']};
        border: 1px solid {c['border_medium']};
        border-radius: 6px;
        color: {c['text_primary']};
        padding: 4px 10px;
        font-size: 13px;
        font-weight: 700;
        min-height: 24px;
    }}

    QPushButton#topNavBtn:hover {{
        background-color: {c['bg_surface_hover']};
        border-color: {c['border_medium']};
        color: {c['text_primary']};
    }}

    QPushButton#topNavBtn:disabled {{
        background-color: transparent;
        border-color: #162035;
        color: {c['text_muted']};
    }}

    QPushButton#scanNetworkBtn {{
        background-color: {c['bg_surface']};
        border: 1px solid {c['border_medium']};
        border-radius: 8px;
        color: {c['text_primary']};
        padding: 6px 16px;
        font-size: 13px;
        font-weight: 600;
        min-height: 26px;
    }}

    QPushButton#scanNetworkBtn:hover {{
        background-color: {c['bg_surface_hover']};
        border-color: {c['accent_blue']};
        color: #ffffff;
    }}

    QPushButton#scanNetworkBtn:pressed {{
        background-color: {c['accent_blue_pressed']};
    }}

    /* ══════════════════════════════════════════════
       UPGRADE PROMO CARD (Fing style)
       ══════════════════════════════════════════════ */
    QFrame#upgradeCard {{
        background-color: #10172a;
        border: 1px solid #1e2e50;
        border-radius: 10px;
        padding: 12px;
    }}

    QPushButton#upgradeBtn {{
        background-color: {c['accent_blue']};
        color: #ffffff;
        border: none;
        border-radius: 6px;
        padding: 8px 14px;
        font-size: 12px;
        font-weight: 600;
    }}

    QPushButton#upgradeBtn:hover {{
        background-color: {c['accent_blue_hover']};
    }}

    QPushButton#upgradeBtn:pressed {{
        background-color: {c['accent_blue_pressed']};
    }}

    /* ══════════════════════════════════════════════
       USER PROFILE CARD (Bottom of Sidebar)
       ══════════════════════════════════════════════ */
    QFrame#userProfileCard {{
        background-color: transparent;
        border: none;
        padding: 6px 4px;
    }}

    QLabel#userAvatar {{
        background-color: {c['avatar_bg']};
        color: {c['avatar_text']};
        border-radius: 16px;
        font-size: 13px;
        font-weight: 700;
        min-width: 32px;
        max-width: 32px;
        min-height: 32px;
        max-height: 32px;
        qproperty-alignment: 'AlignCenter';
    }}

    /* ══════════════════════════════════════════════
       SEARCH BAR & FILTER DROPDOWNS
       ══════════════════════════════════════════════ */
    QLineEdit#fingSearch {{
        background-color: {c['bg_input']};
        border: 1px solid {c['border_subtle']};
        border-radius: 8px;
        color: {c['text_primary']};
        padding: 7px 12px 7px 32px;
        font-size: 13px;
    }}

    QLineEdit#fingSearch:focus {{
        border-color: {c['accent_blue']};
        background-color: #162038;
    }}

    QLineEdit#fingSearch::placeholder {{
        color: {c['text_muted']};
    }}

    QComboBox#filterCombo {{
        background-color: {c['bg_surface']};
        border: 1px solid {c['border_subtle']};
        border-radius: 6px;
        color: {c['text_secondary']};
        padding: 5px 12px;
        font-size: 12px;
        font-weight: 500;
        min-height: 22px;
    }}

    QComboBox#filterCombo:hover {{
        background-color: {c['bg_surface_hover']};
        border-color: {c['border_medium']};
        color: {c['text_primary']};
    }}

    QComboBox#filterCombo::drop-down {{
        border: none;
        width: 18px;
    }}

    QComboBox#filterCombo QAbstractItemView {{
        background-color: {c['bg_card']};
        border: 1px solid {c['border_medium']};
        border-radius: 6px;
        color: {c['text_primary']};
        selection-background-color: #1a2744;
        selection-color: #60a5fa;
        padding: 4px;
    }}

    /* ══════════════════════════════════════════════
       TABLE WIDGET (Fing Desktop 4.0.6 Table)
       ══════════════════════════════════════════════ */
    QFrame#tableContainer {{
        background-color: {c['bg_card']};
        border: 1px solid {c['border_subtle']};
        border-radius: 12px;
        padding: 0px;
    }}

    QTableWidget#fingTable {{
        background-color: transparent;
        alternate-background-color: transparent;
        color: {c['text_primary']};
        border: none;
        gridline-color: transparent;
        selection-background-color: #1a2542;
        selection-color: {c['text_primary']};
        font-size: 13px;
    }}

    QTableWidget#fingTable::item {{
        padding: 10px 8px;
        border-bottom: 1px solid #162035;
    }}

    QTableWidget#fingTable::item:hover {{
        background-color: #18223b;
    }}

    QTableWidget#fingTable::item:selected {{
        background-color: #1a2744;
    }}

    QHeaderView::section {{
        background-color: transparent;
        color: {c['text_muted']};
        border: none;
        border-bottom: 1px solid #1e2b48;
        padding: 10px 8px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }}

    /* ══════════════════════════════════════════════
       CHECKBOX & BADGES
       ══════════════════════════════════════════════ */
    QCheckBox::indicator {{
        width: 15px;
        height: 15px;
        border-radius: 4px;
        border: 1px solid #334155;
        background-color: #12192b;
    }}

    QCheckBox::indicator:hover {{
        border-color: #64748b;
    }}

    QCheckBox::indicator:checked {{
        background-color: #2563eb;
        border-color: #3b82f6;
    }}

    QLabel#badgeOnline {{
        background-color: {c['status_online_bg']};
        color: {c['status_online_text']};
        border: 1px solid {c['status_online_border']};
        border-radius: 11px;
        font-size: 11px;
        font-weight: 600;
        qproperty-alignment: 'AlignCenter';
    }}

    QLabel#badgeBlocked {{
        background-color: {c['status_blocked_bg']};
        color: {c['status_blocked_text']};
        border: 1px solid {c['status_blocked_border']};
        border-radius: 11px;
        font-size: 11px;
        font-weight: 600;
        qproperty-alignment: 'AlignCenter';
    }}

    QLabel#badgeOffline {{
        background-color: {c['status_offline_bg']};
        color: {c['status_offline_text']};
        border: 1px solid {c['status_offline_border']};
        border-radius: 11px;
        font-size: 11px;
        font-weight: 600;
        qproperty-alignment: 'AlignCenter';
    }}

    QLabel#pillPurple {{
        background-color: {c['pill_purple_bg']};
        color: {c['pill_purple_text']};
        border: 1px solid {c['pill_purple_border']};
        border-radius: 12px;
        padding: 3px 12px;
        font-size: 12px;
        font-weight: 500;
    }}

    QLabel#pillGreen {{
        background-color: {c['pill_green_bg']};
        color: {c['pill_green_text']};
        border: 1px solid {c['pill_green_border']};
        border-radius: 12px;
        padding: 3px 12px;
        font-size: 12px;
        font-weight: 500;
    }}

    /* ══════════════════════════════════════════════
       DEVICE DETAIL MULTI-CARD PANELS
       ══════════════════════════════════════════════ */
    QFrame#fingCard {{
        background-color: {c['bg_card']};
        border: 1px solid {c['border_subtle']};
        border-radius: 10px;
        padding: 16px;
    }}

    QLabel#fingCardTitle {{
        font-size: 15px;
        font-weight: 700;
        color: {c['text_primary']};
    }}

    QLabel#fingCardSubText {{
        font-size: 12px;
        color: {c['text_muted']};
    }}

    /* Right sidebar action buttons in Detail view */
    QPushButton#actionToolBtn {{
        background-color: {c['bg_surface']};
        border: 1px solid {c['border_subtle']};
        border-radius: 6px;
        color: {c['text_secondary']};
        padding: 8px 14px;
        font-size: 12px;
        font-weight: 500;
        text-align: left;
        min-height: 24px;
    }}

    QPushButton#actionToolBtn:hover {{
        background-color: {c['bg_surface_hover']};
        border-color: {c['border_medium']};
        color: {c['text_primary']};
    }}

    /* ══════════════════════════════════════════════
       BLOCK / UNBLOCK BUTTON REQUIREMENT:
       - Unblocked: Red, says "Block network access"
       - Blocked: Greyed out, says "Blocked"
       ══════════════════════════════════════════════ */
    QPushButton#blockBtnRed {{
        background-color: {c['block_btn_red_bg']};
        border: 1px solid #b91c1c;
        border-radius: 6px;
        color: {c['block_btn_red_text']};
        padding: 8px 14px;
        font-size: 12px;
        font-weight: 600;
        text-align: left;
        min-height: 24px;
    }}

    QPushButton#blockBtnRed:hover {{
        background-color: {c['block_btn_red_hover']};
        border-color: #991b1b;
    }}

    QPushButton#blockBtnGrey {{
        background-color: {c['block_btn_grey_bg']};
        border: 1px solid {c['block_btn_grey_border']};
        border-radius: 6px;
        color: {c['block_btn_grey_text']};
        padding: 8px 14px;
        font-size: 12px;
        font-weight: 600;
        text-align: left;
        min-height: 24px;
    }}

    QPushButton#blockBtnGrey:hover {{
        background-color: {c['block_btn_grey_hover']};
        color: {c['text_secondary']};
    }}

    /* ══════════════════════════════════════════════
       SCROLLBARS
       ══════════════════════════════════════════════ */
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 0px;
    }}

    QScrollBar::handle:vertical {{
        background: #232d44;
        min-height: 30px;
        border-radius: 4px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: #334160;
    }}

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QScrollBar:horizontal {{
        background: transparent;
        height: 8px;
        margin: 0px;
    }}

    QScrollBar::handle:horizontal {{
        background: #232d44;
        min-width: 30px;
        border-radius: 4px;
    }}
    """


# Mapping for device type icons and display names matching Fing
FING_DEVICE_TYPES = {
    "laptop": ("💻", "Laptop"),
    "desktop": ("🖥️", "Desktop"),
    "television": ("📺", "Television"),
    "printer": ("🖨️", "Printer"),
    "voice_control": ("🎙️", "Voice Control"),
    "smart_device": ("💡", "Smart Device"),
    "phone": ("📱", "Mobile"),
    "smartphone": ("📱", "Mobile"),
    "tablet": ("📱", "Tablet"),
    "router": ("🌐", "Router"),
    "server": ("🖥️", "Server"),
    "game_console": ("🎮", "Console"),
    "generic": ("⚙️", "Generic"),
    "unknown": ("⚙️", "Generic"),
}


def get_fing_device_type_info(device_type: str) -> tuple[str, str]:
    """Return (icon, display_name) for a device type."""
    key = (device_type or "generic").lower().replace(" ", "_")
    return FING_DEVICE_TYPES.get(key, ("⚙️", "Generic"))
