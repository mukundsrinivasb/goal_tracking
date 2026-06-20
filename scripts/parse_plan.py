"""
parse_plan.py — Syncs the ## Plan section from the latest log to Turso.

Usage:
  export TURSO_URL="libsql://task-tracking-mukundsrinivasb.aws-ap-south-1.turso.io"
  export TURSO_TOKEN="your_token"

  python scripts/parse_plan.py               # latest log
  python scripts/parse_plan.py logs/20_06_2026.md  # specific file
"""

import asyncio
import os
import sys
from pathlib import Path
import libsql_client
import re

from log_utils import get_latest_log_file, filename_to_date, parse_plan

TURSO_URL   = os.getenv('TURSO_URL', 'libsql://task-tracking-mukundsrinivasb.aws-ap-south-1.turso.io')
TURSO_TOKEN = os.getenv('TURSO_TOKEN', '')


async def insert_plan(log_date: str, rows: list[dict], client: libsql_client.Client):
    inserted = skipped = 0
    for r in rows:
        result = await client.execute(
            """
            INSERT INTO daily_plans (log_date, start_time, task, remarks)
            SELECT ?, ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM daily_plans WHERE log_date = ? AND task = ?
            )
            """,
            [log_date, r['start_time'], r['task'], r['remarks'], log_date, r['task']]
        )
        if result.rows_affected:
            inserted += 1
        else:
            skipped += 1

    print(f"✅ {log_date} — {inserted} inserted, {skipped} skipped.")

    summary_file = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary_file:
        with open(summary_file, 'a') as f:
            f.write("### 📋 Plan Tasks Synced to Turso\n")
            f.write(f"- **Date:** {log_date}\n")
            f.write(f"- **Inserted:** {inserted}\n")
            f.write(f"- **Skipped (duplicates):** {skipped}\n")


async def main(target: str | None):
    if not TURSO_TOKEN:
        print("❌ TURSO_TOKEN not set. Run: export TURSO_TOKEN=your_token")
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

    async with libsql_client.create_client(TURSO_URL, auth_token=TURSO_TOKEN) as client:
        await insert_plan(log_date, rows, client)


if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(main(target))
