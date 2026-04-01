#!/usr/bin/env python3
"""
ban-app generator
Reads SQLite data, resolves GeoIP, renders the static HTML dashboard.
"""

import sqlite3
import json
import sys
import os
import re
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

# --- Paths ---
DB_PATH      = os.path.join(config.APP_BASE, config.DATA_DIR, config.DB_FILE)
OUTPUT_PATH  = os.path.join(config.APP_BASE, config.HTML_DIR, config.OUTPUT_HTML)
TEMPLATE_PATH = os.path.join(config.APP_BASE, config.SOURCES_DIR, config.TEMPLATE_FILE)

try:
    import geoip2.database
    GEOIP_AVAILABLE = True
except ImportError:
    GEOIP_AVAILABLE = False
    print("[WARN] geoip2 not installed. GeoIP features disabled.")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def resolve_geoip(ip_list):
    """Returns dict: {country_iso2: count}"""
    if not GEOIP_AVAILABLE or not os.path.exists(config.GEOIP_DB):
        return {}
    counts = defaultdict(int)
    try:
        with geoip2.database.Reader(config.GEOIP_DB) as reader:
            for ip in ip_list:
                try:
                    resp = reader.country(ip)
                    iso = resp.country.iso_code
                    name = resp.country.name
                    if iso:
                        counts[iso] = counts.get(iso, 0) + 1
                except Exception:
                    pass
    except Exception as e:
        print(f"[WARN] GeoIP error: {e}")
    return dict(counts)


def load_data():
    conn = get_db()

    # All distinct timestamps (limited to MAX_HISTORY_POINTS, most recent first)
    ts_rows = conn.execute(
        "SELECT DISTINCT ts FROM snapshots ORDER BY ts DESC LIMIT ?",
        (config.MAX_HISTORY_POINTS,)
    ).fetchall()
    timestamps = [r[0] for r in reversed(ts_rows)]   # chronological order

    if not timestamps:
        conn.close()
        return None

    last_ts = timestamps[-1]

    # All jails seen in the last snapshot
    last_jails_rows = conn.execute(
        "SELECT DISTINCT jail FROM snapshots WHERE ts = ? ORDER BY jail",
        (last_ts,)
    ).fetchall()
    jails = [r[0] for r in last_jails_rows]

    # --- Summary table: last snapshot values + all-time sums ---
    summary = []
    total_curr_fail = total_curr_ban = total_all_fail = total_all_ban = 0
    for jail in jails:
        last = conn.execute(
            "SELECT curr_fail, curr_ban, total_fail, total_ban FROM snapshots WHERE ts=? AND jail=?",
            (last_ts, jail)
        ).fetchone()
        if not last:
            continue
        # all-time max (total_fail/total_ban are cumulative from fail2ban itself)
        max_row = conn.execute(
            "SELECT MAX(total_fail), MAX(total_ban) FROM snapshots WHERE jail=?",
            (jail,)
        ).fetchone()
        all_fail = max_row[0] or 0
        all_ban  = max_row[1] or 0

        summary.append({
            "jail":       jail,
            "curr_fail":  last["curr_fail"],
            "curr_ban":   last["curr_ban"],
            "all_fail":   all_fail,
            "all_ban":    all_ban,
        })
        total_curr_fail += last["curr_fail"]
        total_curr_ban  += last["curr_ban"]
        total_all_fail  += all_fail
        total_all_ban   += all_ban

    summary_total = {
        "curr_fail": total_curr_fail,
        "curr_ban":  total_curr_ban,
        "all_fail":  total_all_fail,
        "all_ban":   total_all_ban,
    }

    # --- Time series for chart ---
    field = config.CHART_FIELD   # curr_fail | curr_ban | total_fail | total_ban
    valid_fields = {"curr_fail", "curr_ban", "total_fail", "total_ban"}
    if field not in valid_fields:
        field = "curr_ban"

    # Build series: {jail: [value_per_ts]}
    series = {jail: [] for jail in jails}
    totals_per_ts = []
    for ts in timestamps:
        ts_total = 0
        for jail in jails:
            row = conn.execute(
                f"SELECT {field} FROM snapshots WHERE ts=? AND jail=?",
                (ts, jail)
            ).fetchone()
            val = row[0] if row else 0
            series[jail].append(val)
            ts_total += val
        totals_per_ts.append(ts_total)

    chart_data = {
        "labels":  timestamps,
        "jails":   jails,
        "series":  series,
        "totals":  totals_per_ts,
        "field":   field,
    }

    # --- GeoIP: collect all IPs from the GEOMAP_FIELD scope ---
    geo_field = config.GEOMAP_FIELD
    # Collect IPs from last snapshot (curr_*) or all snapshots (total_*)
    if geo_field.startswith("curr_"):
        # Only IPs from the last timestamp
        ip_rows = conn.execute(
            "SELECT banned_ips FROM snapshots WHERE ts=?", (last_ts,)
        ).fetchall()
    else:
        # All IPs ever recorded
        ip_rows = conn.execute(
            "SELECT banned_ips FROM snapshots"
        ).fetchall()

    all_ips = []
    seen = set()
    for row in ip_rows:
        try:
            ips = json.loads(row[0])
            for ip in ips:
                if ip not in seen:
                    seen.add(ip)
                    all_ips.append(ip)
        except Exception:
            pass

    country_counts = resolve_geoip(all_ips)

    conn.close()

    return {
        "summary":       summary,
        "summary_total": summary_total,
        "chart_data":    chart_data,
        "country_counts": country_counts,
        "last_ts":       last_ts,
        "generated_at":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def render_html(data):
    with open(TEMPLATE_PATH, "r") as f:
        template = f.read()

    # Inject JSON data blobs and config values
    replacements = {
        "%%SUMMARY_JSON%%":        json.dumps(data["summary"]),
        "%%SUMMARY_TOTAL_JSON%%":  json.dumps(data["summary_total"]),
        "%%CHART_DATA_JSON%%":     json.dumps(data["chart_data"]),
        "%%COUNTRY_JSON%%":        json.dumps(data["country_counts"]),
        "%%LAST_TS%%":             data["last_ts"],
        "%%GENERATED_AT%%":        data["generated_at"],
        "%%FOOTER_HTML%%":         config.FOOTER_HTML,
        # Colors
        "%%COLOR_BG%%":            config.COLOR_BG,
        "%%COLOR_PANEL%%":         config.COLOR_PANEL,
        "%%COLOR_PANEL_BORDER%%":  config.COLOR_PANEL_BORDER,
        "%%COLOR_TEXT%%":          config.COLOR_TEXT,
        "%%COLOR_TEXT_MUTED%%":    config.COLOR_TEXT_MUTED,
        "%%COLOR_ACCENT%%":        config.COLOR_ACCENT,
        "%%COLOR_ACCENT2%%":       config.COLOR_ACCENT2,
        "%%COLOR_ACCENT3%%":       config.COLOR_ACCENT3,
        "%%COLOR_SUCCESS%%":       config.COLOR_SUCCESS,
        "%%COLOR_DANGER%%":        config.COLOR_DANGER,
        "%%JAIL_COLORS_JSON%%":    json.dumps(config.JAIL_COLORS),
        "%%MAP_COLOR_LOW%%":       config.MAP_COLOR_LOW,
        "%%MAP_COLOR_HIGH%%":      config.MAP_COLOR_HIGH,
        "%%MAP_COLOR_ZERO%%":      config.MAP_COLOR_ZERO,
        "%%MAP_COLOR_OCEAN%%":     config.MAP_COLOR_OCEAN,
        # Options
        "%%CHART_SMOOTHING%%":     "true" if config.CHART_SMOOTHING else "false",
        "%%CHART_SHOW_TOTAL%%":    "true" if config.CHART_SHOW_TOTAL else "false",
        "%%CHART_FILL_OPACITY%%":  str(config.CHART_FILL_OPACITY),
        "%%MAX_COUNTRY_DISPLAY%%": str(config.MAX_COUNTRY_DISPLAY),
    }

    for placeholder, value in replacements.items():
        template = template.replace(placeholder, value)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        f.write(template)

    print(f"[OK] HTML written to {OUTPUT_PATH}")


def generate():
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found: {DB_PATH}")
        print("        Run collector.py first.")
        sys.exit(1)

    print("Loading data...")
    data = load_data()
    if not data:
        print("[ERROR] No data in database. Run collector.py first.")
        sys.exit(1)

    print(f"  Last snapshot : {data['last_ts']}")
    print(f"  Jails         : {[j['jail'] for j in data['summary']]}")
    print(f"  Countries     : {len(data['country_counts'])}")
    print("Rendering HTML...")
    render_html(data)


if __name__ == "__main__":
    generate()
