import re
import os
import glob
from datetime import datetime

def get_latest_log_file(log_dir='logs'):
    """Finds the latest markdown log file based on its filename date."""
    log_files = glob.glob(f"{log_dir}/*.md")
    
    if not log_files:
        return None
    
    def extract_date(filepath):
        # Extracts just the filename, e.g., '20_04_2026' from 'logs/20_04_2026.md'
        filename = os.path.basename(filepath).replace('.md', '')
        try:
            # Parses the specific day_month_year format reliably
            return datetime.strptime(filename, '%d_%m_%Y')
        except ValueError:
            # Fallback just in case a file doesn't match the strict format
            return datetime.fromtimestamp(os.path.getmtime(filepath))

    # Sorts all files chronologically based on the parsed dates, grabs the newest
    latest_file = sorted(log_files, key=extract_date, reverse=True)[0]
    return latest_file


def filename_to_date(filepath: str) -> str | None:
    """Convert dd_mm_yyyy.md filename to YYYY-MM-DD for DB storage."""
    name = os.path.basename(filepath).replace('.md', '')
    try:
        dt = datetime.strptime(name, '%d_%m_%Y')
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        return None
 
def extract_time(task_str: str) -> tuple[str | None, str]:
    """
    Pull @ HHMM from end of task string.
    Returns (start_time, cleaned_task).
    e.g. 'Lunch @ 1345' -> ('13:45', 'Lunch')
    """
    match = re.search(r'@\s*(\d{3,4})\s*$', task_str.strip())
    if match:
        raw = match.group(1).zfill(4)
        start_time = f"{raw[:2]}:{raw[2:]}"
        cleaned = task_str[:match.start()].strip().rstrip(',').strip()
        return start_time, cleaned
    return None, task_str.strip()


def parse_plan(md_text: str) -> list[dict]:
    """
    Extract ## Plan table rows from markdown text.
    Returns list of {start_time, task, remarks} dicts.
    """
    plan_match = re.search(r'^## Plan$(.*?)(?=^## |\Z)', md_text, re.MULTILINE | re.DOTALL)
    if not plan_match:
        return []
 
    rows = []
    for line in plan_match.group(1).splitlines():
        line = line.strip()
        if not line.startswith('|'):
            continue
        cols = [c.strip() for c in line.strip('|').split('|')]
        if len(cols) < 2:
            continue
        task_raw, remarks = cols[0], cols[1]
        if task_raw.lower() == 'task' or re.match(r'^[-: ]+$', task_raw):
            continue
 
        start_time, task_clean = extract_time(task_raw)
        remarks_clean = None if remarks.strip() in ('_add_remarks_', '') else remarks.strip()
 
        rows.append({
            'start_time': start_time,
            'task':       task_clean,
            'remarks':    remarks_clean,
        })
    return rows
