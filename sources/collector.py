#!/usr/bin/env python3
"""
ban-app collector
Collects fail2ban jail data and stores it in SQLite.
Run via cron or manually.
"""

import subprocess
import sqlite3
import json
import sys
import os
import re
from datetime import datetime

# Allow running from any directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

# --- Paths ---
DB_PATH = os.path.join(config.APP_BASE, config.DATA_DIR, config.DB_FILE)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS snapshots (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ts          TEXT NOT NULL,
            jail        TEXT NOT NULL,
            curr_fail   INTEGER DEFAULT 0,
            curr_ban    INTEGER DEFAULT 0,
            total_fail  INTEGER DEFAULT 0,
            total_ban   INTEGER DEFAULT 0,
            banned_ips  TEXT DEFAULT '[]'
        );
        CREATE INDEX IF NOT EXISTS idx_ts   ON snapshots(ts);
        CREATE INDEX IF NOT EXISTS idx_jail ON snapshots(jail);
    """)
    conn.commit()


def run(cmd):
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"[ERROR] Command {cmd}: {e}")
        return ""


def get_jails():
    out = run([config.FAIL2BAN_CLIENT, "status"])
    match = re.search(r"Jail list:\s*(.+)", out)
    if not match:
        print("[ERROR] Could not parse jail list")
        return []
    return [j.strip() for j in match.group(1).split(",") if j.strip()]


def get_jail_status(jail):
    out = run([config.FAIL2BAN_CLIENT, "status", jail])
    data = {
        "curr_fail":  0,
        "curr_ban":   0,
        "total_fail": 0,
        "total_ban":  0,
        "banned_ips": [],
    }

    for line in out.splitlines():
        line = line.strip()
        if "Currently failed:" in line:
            data["curr_fail"] = int(re.search(r"\d+", line).group())
        elif "Total failed:" in line:
            data["total_fail"] = int(re.search(r"\d+", line).group())
        elif "Currently banned:" in line:
            data["curr_ban"] = int(re.search(r"\d+", line).group())
        elif "Total banned:" in line:
            data["total_ban"] = int(re.search(r"\d+", line).group())
        elif "Banned IP list:" in line:
            ips_str = line.split(":", 1)[1].strip()
            data["banned_ips"] = [ip for ip in ips_str.split() if ip]

    return data


def collect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    init_db(conn)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    jails = get_jails()

    if not jails:
        print("[WARN] No jails found.")
        conn.close()
        return

    print(f"[{ts}] Collecting {len(jails)} jail(s): {', '.join(jails)}")

    for jail in jails:
        status = get_jail_status(jail)
        conn.execute(
            """INSERT INTO snapshots
               (ts, jail, curr_fail, curr_ban, total_fail, total_ban, banned_ips)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                ts,
                jail,
                status["curr_fail"],
                status["curr_ban"],
                status["total_fail"],
                status["total_ban"],
                json.dumps(status["banned_ips"]),
            ),
        )
        print(
            f"  {jail}: curr_fail={status['curr_fail']} curr_ban={status['curr_ban']}"
            f" total_fail={status['total_fail']} total_ban={status['total_ban']}"
            f" IPs={len(status['banned_ips'])}"
        )

    conn.commit()

    # Prune old data beyond MAX_HISTORY_POINTS timestamps
    cursor = conn.execute(
        "SELECT DISTINCT ts FROM snapshots ORDER BY ts DESC"
    )
    all_ts = [row[0] for row in cursor.fetchall()]
    if len(all_ts) > config.MAX_HISTORY_POINTS:
        to_delete = all_ts[config.MAX_HISTORY_POINTS:]
        placeholders = ",".join("?" * len(to_delete))
        conn.execute(
            f"DELETE FROM snapshots WHERE ts IN ({placeholders})", to_delete
        )
        conn.commit()
        print(f"  Pruned {len(to_delete)} old timestamp(s).")

    conn.close()
    print("Done.")


if __name__ == "__main__":
    collect()
