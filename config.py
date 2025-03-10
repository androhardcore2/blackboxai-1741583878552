import pytz
from pathlib import Path

# Application Settings
APP_NAME = "Article Rewriter Pro"
APP_VERSION = "1.0.0"
APP_WINDOW_SIZE = "1280x800"

# File Paths
SETTINGS_FILE = "settings.json"
CREDENTIALS_FILE = "client_secrets.json"
LOG_FILE = "app.log"

# UI Settings
UI_THEME = "default"  # Can be "default", "clam", "alt", "classic"
UI_FONT = "Segoe UI"
UI_FONT_SIZE = 10
UI_COLORS = {
    "primary": "#2980b9",     # Blue
    "secondary": "#27ae60",   # Green
    "warning": "#f39c12",     # Orange
    "error": "#c0392b",       # Red
    "success": "#27ae60",     # Green
    "info": "#3498db",        # Light Blue
    "background": "#f0f0f0",  # Light Gray
    "text": "#2c3e50",        # Dark Blue Gray
}

# Logging Settings
LOG_LEVELS = ["ALL", "INFO", "WARNING", "ERROR", "SUCCESS", "DEBUG"]
MAX_LOG_HISTORY = 500

# API Settings
API_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

# Article Processing
MAX_ARTICLE_LENGTH = 50000  # characters
MIN_ARTICLE_LENGTH = 100    # characters
MAX_TITLE_LENGTH = 100     # characters

# Scheduling
TIMEZONE = pytz.timezone('Asia/Jakarta')
DEFAULT_SCHEDULE_INTERVAL = 5  # minutes
MIN_SCHEDULE_INTERVAL = 1      # minutes
MAX_SCHEDULE_INTERVAL = 1440   # minutes (24 hours)

# Progress Bar Settings
PROGRESS_UPDATE_INTERVAL = 100  # milliseconds

# Tree View Settings
TREE_ROW_HEIGHT = 25
TREE_COLUMN_WIDTHS = {
    "#0": 50,      # ID column
    "Title": 300,  # Title column
    "Schedule": 150  # Schedule column
}

# Preview Settings
PREVIEW_FONT = "Segoe UI"
PREVIEW_FONT_SIZE = 10
PREVIEW_WRAP_LENGTH = 80  # characters

# HTML Settings
ALLOWED_HTML_TAGS = [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'p', 'br', 'hr',
    'ul', 'ol', 'li',
    'strong', 'em', 'u', 'strike',
    'blockquote', 'pre', 'code',
    'table', 'thead', 'tbody', 'tr', 'th', 'td'
]

# Button Styles
BUTTON_STYLES = {
    "primary": {
        "background": UI_COLORS["primary"],
        "foreground": "white",
        "activebackground": "#3498db",
        "activeforeground": "white",
        "font": (UI_FONT, UI_FONT_SIZE)
    },
    "secondary": {
        "background": UI_COLORS["secondary"],
        "foreground": "white",
        "activebackground": "#2ecc71",
        "activeforeground": "white",
        "font": (UI_FONT, UI_FONT_SIZE)
    },
    "warning": {
        "background": UI_COLORS["warning"],
        "foreground": "white",
        "activebackground": "#f1c40f",
        "activeforeground": "white",
        "font": (UI_FONT, UI_FONT_SIZE)
    }
}

# Tab Settings
TAB_STYLES = {
    "width": 150,
    "padding": 10,
    "background": UI_COLORS["background"],
    "selected_background": UI_COLORS["primary"],
    "foreground": UI_COLORS["text"],
    "selected_foreground": "white"
}

# Frame Styles
FRAME_STYLES = {
    "padding": 10,
    "relief": "flat",
    "borderwidth": 1,
    "background": "white"
}

# Entry Styles
ENTRY_STYLES = {
    "font": (UI_FONT, UI_FONT_SIZE),
    "relief": "solid",
    "borderwidth": 1
}

# Label Styles
LABEL_STYLES = {
    "font": (UI_FONT, UI_FONT_SIZE),
    "foreground": UI_COLORS["text"],
    "background": "white"
}

# Treeview Styles
TREEVIEW_STYLES = {
    "background": "white",
    "foreground": UI_COLORS["text"],
    "selected_background": UI_COLORS["primary"],
    "selected_foreground": "white",
    "alternate_background": "#f8f9fa"
}

# Dialog Settings
DIALOG_STYLES = {
    "width": 400,
    "height": 300,
    "background": "white",
    "title_font": (UI_FONT, UI_FONT_SIZE + 2, "bold"),
    "button_width": 10
}

# Progress Bar Styles
PROGRESS_STYLES = {
    "height": 20,
    "background": UI_COLORS["background"],
    "foreground": UI_COLORS["primary"]
}
