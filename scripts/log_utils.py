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
    return latest_filesection{Execution Instructions and Environment Setup}
