# Ban-App — fail2ban Monitor

A lightweight fail2ban monitoring dashboard that collects jail data and generates a static HTML report with charts, a world map, and per-country breakdowns.

![Dashboard preview](html/index.html)

---

## Features

- **Jail summary table** — current and cumulative fails/bans per jail
- **Stacked area chart** — timeline of activity across all jails
- **World map** — geographic origin of banned IPs (via MaxMind GeoLite2)
- **Country list** — ranked breakdown with hit bars
- Fully static HTML output — no web server required
- Configurable colors, chart fields, history depth, and more

---

## Project Structure

```
ban-app/
├── data/
│   ├── GeoLite2-Country.mmdb   # MaxMind GeoIP database (not included)
│   └── banapp.db               # SQLite database (not tracked in git)
├── html/
│   └── index.html              # Generated dashboard output
└── sources/
    ├── banapp.py               # Main runner (collect + generate)
    ├── collector.py            # Reads fail2ban jails → stores to SQLite
    ├── generator.py            # Reads SQLite → renders HTML dashboard
    ├── config.py               # All configuration lives here
    └── template.html           # HTML/JS dashboard template
```

> `data/banapp.db` is excluded from git (size). It is created automatically on first run.  
> `data/GeoLite2-Country.mmdb` must be obtained separately from [MaxMind](https://dev.maxmind.com/geoip/geolite2-free-geolocation-data).

---

## Usage

### Run both steps (collect + generate)
```bash
python3 sources/banapp.py
```

### Collect only (update DB, no HTML)
```bash
python3 sources/banapp.py --collect-only
```

### Generate only (re-render HTML from existing DB)
```bash
python3 sources/banapp.py --generate-only
```

### Automate with cron (example: every 30 minutes)
```cron
*/30 * * * * /usr/bin/python3 /root/ban-app/sources/banapp.py >> /var/log/ban-app.log 2>&1
```

---

## Configuration

All settings are in `sources/config.py`.

| Setting | Default | Description |
|---|---|---|
| `APP_BASE` | `/root/ban-app` | Absolute path to the app root |
| `FAIL2BAN_CLIENT` | `/usr/bin/fail2ban-client` | Path to fail2ban-client binary |
| `MAX_HISTORY_POINTS` | `5000` | Max timestamps kept in DB (~48h at 30min intervals) |
| `MAX_COUNTRY_DISPLAY` | `30` | Max countries shown in the country list |
| `CHART_FIELD` | `curr_ban` | Field driving the timeline chart (`curr_fail`, `curr_ban`, `total_fail`, `total_ban`) |
| `GEOMAP_FIELD` | `total_ban` | Field driving the world map and country list |
| `CHART_SMOOTHING` | `True` | Smooth area chart curves |
| `CHART_SHOW_TOTAL` | `True` | Show sum-of-all-jails line on the chart |

Colors, jail palette, and map gradient are also fully configurable in `config.py`.

---

## Requirements

- Python 3.x
- `fail2ban` with `fail2ban-client` accessible
- `geoip2` Python package (for GeoIP lookups)
- MaxMind GeoLite2-Country database (`GeoLite2-Country.mmdb`)

---

## License

Ban-App V1.0 — **Snapi.fr** — All rights reserved 2025
