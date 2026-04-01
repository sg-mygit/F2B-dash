# =============================================================================
# ban-app configuration file
# =============================================================================

# --- Paths ---
APP_BASE        = "/root/ban-app"
SOURCES_DIR     = "sources"
DATA_DIR        = "data"
HTML_DIR        = "html"

DB_FILE         = "banapp.db"          # relative to DATA_DIR
GEOIP_DB        = APP_BASE + "/" + DATA_DIR + "/GeoLite2-Country.mmdb"
OUTPUT_HTML     = "index.html"         # relative to HTML_DIR
TEMPLATE_FILE   = "template.html"      # relative to SOURCES_DIR

FAIL2BAN_CLIENT = "/usr/bin/fail2ban-client"

# --- Data options ---
MAX_HISTORY_POINTS  = 5000      # max timestamps to keep / display (~48h at 30min)
MAX_COUNTRY_DISPLAY = 30      # max countries in the country list

# Field to drive both the stacked area chart AND the world map / country list.
# Options:
#   "curr_fail"   - current fails at time of collection
#   "curr_ban"    - current bans at time of collection
#   "total_fail"  - cumulative fails (all time, per jail)
#   "total_ban"   - cumulative bans (all time, per jail)
CHART_FIELD   = "curr_ban"
GEOMAP_FIELD  = "total_ban"     # same options — drives country list + world map

# --- Color scheme (dark, claude.ai-inspired, brighter accent) ---
COLOR_BG            = "#0d0f12"       # page background
COLOR_PANEL         = "#13161c"       # zone panel background
COLOR_PANEL_BORDER  = "#1e2330"       # panel border
COLOR_TEXT          = "#e2e8f0"       # primary text
COLOR_TEXT_MUTED    = "#7a8499"       # secondary / muted text
COLOR_ACCENT        = "#3b82f6"       # bright blue accent (primary)
COLOR_ACCENT2       = "#06b6d4"       # cyan accent (secondary)
COLOR_ACCENT3       = "#f59e0b"       # amber (warnings / highlights)
COLOR_SUCCESS       = "#22c55e"       # green
COLOR_DANGER        = "#ef4444"       # red

# Jail colors for stacked area chart (cycles if more jails than colors)
JAIL_COLORS = [
    "#3b82f6",  # blue
    "#06b6d4",  # cyan
    "#f59e0b",  # amber
    "#22c55e",  # green
    "#a855f7",  # purple
    "#ef4444",  # red
    "#ec4899",  # pink
    "#14b8a6",  # teal
]

# World map color gradient (low → high hit count)
MAP_COLOR_LOW   = "#1e3a5f"   # dark blue (few hits)
MAP_COLOR_HIGH  = "#ef4444"   # red (many hits)
MAP_COLOR_ZERO  = "#1a1d25"   # near-background (no hits)
MAP_COLOR_OCEAN = "#0d1520"   # ocean / background

# --- Graph options ---
CHART_SMOOTHING     = True    # smooth area curves (monotone interpolation)
CHART_SHOW_TOTAL    = True    # show sum-of-all-jails line on top of stacked area
CHART_FILL_OPACITY  = 0.7     # stacked area fill opacity

# --- Footer ---
FOOTER_HTML = 'Ban-App V1.0 &mdash; <b>Snapi.fr</b> &mdash; All rights reserved 2025'
