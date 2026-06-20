"""
parse_plan.py — Syncs the ## Plan section from the latest log to Turso.

Usage:
  export TURSO_URL="libsql://task-tracking-mukundsrinivasb.aws-ap-south-1.turso.io"
  export TURSO_TOKEN="your_token"

  python scripts/parse_plan.py                      # latest log
  python scripts/parse_plan.py logs/20_06_2026.md   # specific file
"""

import os
import sys
import json
from pathlib import Path
import urllib.request
import urllib.error

from log_utils import get_latest_log_file, filename_to_date, parse_plan

TURSO_URL   = os.getenv('TURSO_URL', '')
TURSO_TOKEN = os.getenv('TURSO_TOKEN', '')


def turso_http_url(libsql_url: str) -> str:
    """Convert libsql:// URL to https:// for the HTTP API."""
    return libsql_url.replace('libsql://', 'https://')


def execute_sql(statements: list[dict]) -> list:
    """
    Execute one or more SQL statements via Turso HTTP pipeline API.
    Each statement: {"sql": "...", "args": [...]}
    Returns list of results.
    """
    url = f"{turso_http_url(TURSO_URL)}/v2/pipeline"
    requests = [{"type": "execute", "stmt": s} for s in statements]
    requests.append({"type": "close"})

    payload = json.dumps({"requests": requests}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {TURSO_TOKEN}",
            "Content-Type": "application/json",
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())["results"]
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP {e.code}: {e.read().decode()}")
        sys.exit(1)


def insert_plan(log_date: str, rows: list[dict]):
    inserted = skipped = 0

    # Check which tasks already exist for this date
    check = execute_sql([{
        "sql": "SELECT task FROM daily_plans WHERE log_date = ?",
        "args": [{"type": "text", "value": log_date}]
    }])

    existing = set()
    try:
        for row in check[0]["response"]["result"]["rows"]:
            existing.add(row[0]["value"])
    except (KeyError, IndexError):
        pass

    # Build inserts for new tasks only
    stmts = []
    for r in rows:
        if r['task'] in existing:
            skipped += 1
            continue
        stmts.append({
            "sql": "INSERT INTO daily_plans (log_date, start_time, task, remarks) VALUES (?, ?, ?, ?)",
            "args": [
                {"type": "text",  "value": log_date},
                {"type": "text",  "value": r['start_time']} if r['start_time'] else {"type": "null"},
                {"type": "text",  "value": r['task']},
                {"type": "text",  "value": r['remarks']} if r['remarks'] else {"type": "null"},
            ]
        })
        inserted += 1

    if stmts:
        execute_sql(stmts)

    print(f"✅ {log_date} — {inserted} inserted, {skipped} skipped.")

    summary_file = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary_file:
        with open(summary_file, 'a') as f:
            f.write("### 📋 Plan Tasks Synced to Turso\n")
            f.write(f"- **Date:** {log_date}\n")
            f.write(f"- **Inserted:** {inserted}\n")
            f.write(f"- **Skipped (duplicates):** {skipped}\n")


def main(target: str | None):
    if not TURSO_URL:
        print("❌ TURSO_URL not set. Add it to GitHub Secrets or your .env")
        sys.exit(1)
    if not TURSO_TOKEN:
        print("❌ TURSO_TOKEN not set. Add it to GitHub Secrets or your .env")
        sys.exit(1)

    filepath = target or get_latest_log_file()
    if not filepath:
        print("❌ No log files found in logs/")
        sys.exit(1)

    print(f"📅 Processing: {filepath}")

    log_date = filename_to_date(filepath)
    if not log_date:
        print(f"❌ Could not parse date from filename: {filepath}")
        sys.exit(1)

    text = Path(filepath).read_text(encoding='utf-8')
    rows = parse_plan(text)

    if not rows:
        print(f"⚠️  No plan tasks found in {filepath}")
        sys.exit(0)

    print(f"📄 Parsed {len(rows)} tasks")
    insert_plan(log_date, rows)


if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else None
    main(target)
