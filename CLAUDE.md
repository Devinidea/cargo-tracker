# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Cargo Tracker (海运清单管理工具) — a Flask + SQLite + vanilla-JS app for tracking shipping cargo. Users create shipments, pack items into boxes, and OCR Chinese e-commerce order screenshots (Taobao/Pinduoduo) via MiniMax Vision API to populate item lists. Designed to run on a Synology NAS in Docker. UI and code comments are in Chinese.

## Commands

```bash
# Local dev (auto-runs init_db on startup, serves on :5180 with debug=True)
pip install -r requirements.txt
export MINIMAX_API_KEY=...   # required for /api/ocr only
python app.py

# Init DB only
python db_schema.py

# Production (what the Docker image runs)
gunicorn --bind 0.0.0.0:5180 --workers 2 --timeout 120 app:app

# Docker
docker-compose up -d         # uses .env (copy from .env.example)
docker logs -f cargo-tracker
```

There are no tests, linter, or build step. Health check: `GET /api/health`.

## Architecture

**Three-tier data model** (`db_schema.py`): `shipments` → `boxes` (FK shipment_id, CASCADE) → `items` (FK box_id, CASCADE). All timestamps are stored as text with `datetime('now', '+8 hours')` to hardcode China timezone (`Asia/Shanghai`); the frontend parses them by appending `+08:00`.

**Flat module layout** (no blueprints/packages):
- `app.py` — all Flask routes. URL conventions: `/api/shipments`, `/api/shipments/<id>/boxes` (nested for create only), `/api/boxes/<id>`, `/api/items/<id>`. Mutations return `{success, data?, error?}`.
- `db_schema.py` — `init_db()` + thin per-table CRUD helpers. Each helper opens and closes its own connection (no pooling, no ORM). Connections use `row_factory = sqlite3.Row` and helpers convert to plain dicts before returning.
- `static/index.html` — entire frontend in one file: inline CSS, inline vanilla JS, no build, no dependencies. Flask serves it via `static_url_path=''` so `/` returns it directly.

**OCR flow** (`/api/ocr` → `_call_minimax_vision`): accepts base64 or URL, writes a temp image, posts to `https://api.minimax.chat/v1/coding_plan/vlm` with a prompt that asks for a JSON array of `{name, quantity, price}`. The response `content` is regex-scanned for `\[.*\]` and JSON-parsed; on parse failure the raw text is returned with `note: "未能解析出商品列表，请手动录入"` so the client can fall back to manual entry. Note: the `MINIMAX_API_URL` constant at the top of `app.py` points at a different endpoint and is unused — the live URL is the one inside `_call_minimax_vision`.

## Things that will trip you up

- **Hardcoded Linux paths.** `DB_PATH = "/data/cargo_tracker.db"` and OCR temp files written to `/tmp/...`. On Windows these resolve to `C:\data\...` and `C:\tmp\...`; on macOS the `/data` write fails without `sudo`. These paths assume the Docker environment. For native non-Linux dev, override `DB_PATH` (or run in Docker).
- **`frontend/dist/index.html` is a duplicate of `static/index.html`.** Flask only serves from `static/`. Edits to `frontend/dist/` have no effect — always edit `static/index.html`.
- **`update_*` helpers issue one UPDATE per non-None field** and return `cursor.rowcount` from the *last* statement only. A multi-field update where the last field happens to be unchanged can report `False` even though earlier fields were written. Prefer passing only the fields you actually want to change.
- **`init_db()` runs at import time** in `app.py` (module-level call). Importing `app` for any reason will try to create `/data` and open the SQLite file.
- **CORS is wide open** (`CORS(app)` with defaults) and `debug=True` is on in `app.py`'s `__main__`. Gunicorn in Docker bypasses the debug flag, but don't expose `python app.py` directly.
