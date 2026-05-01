import os
import sys
from datetime import datetime, timedelta
from log_utils import get_latest_log_file

def get_last_day_of_month(date_obj):
    # Move to the 28th, add 4 days to guarantee next month, then subtract the days of that new month
    next_month = date_obj.replace(day=28) + timedelta(days=4)
    return next_month - timedelta(days=next_month.day)

def main():
    latest_log = get_latest_log_file()
    if not latest_log:
        print("No logs found.")
        sys.exit(0)

    # Extract date from filename (e.g., '12_04_2026')
    base_name = os.path.basename(latest_log).replace('.md', '')
    
    try:
        log_date = datetime.strptime(base_name, '%d_%m_%Y')
    except ValueError:
        print(f"Error parsing date from filename: {base_name}")
        sys.exit(1)
        
    last_day = get_last_day_of_month(log_date)
    days_remaining = (last_day - log_date).days

    # Format dates for output
    parsed_date_str = log_date.strftime('%Y-%m-%d')
    last_day_str = last_day.strftime('%Y-%m-%d')

    print(f"Processing file: {latest_log}")
    print(f"Log Date: {parsed_date_str}")
    print(f"End of Month: {last_day_str}")
    print(f"Days Remaining: {days_remaining}")

    # Write to GitHub Action Summary UI
    summary_file = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary_file:
        with open(summary_file, 'a') as f:
            f.write("### ⏳ Time Remaining in Month\n")
            f.write(f"- **Log Date:** {parsed_date_str}\n")
            f.write(f"- **End of Month:** {last_day_str}\n")
            f.write(f"- **Days Remaining:** {days_remaining} days\n")

    # Update README.md safely
    readme_path = 'README.md'
    if os.path.exists(readme_path):
        with open(readme_path, 'r') as f:
            lines = f.readlines()
        
        # Find the reflection section to strip it out
        cutoff_index = len(lines)
        for i, line in enumerate(lines):
            if line.startswith('## Number of days until reflection'):
                cutoff_index = i
                break
        
        new_lines = lines[:cutoff_index]
        
        with open(readme_path, 'w') as f:
            f.writelines(new_lines)
            # Ensure proper spacing
            if new_lines and not new_lines[-1].endswith('\n'):
                f.write('\n')
            f.write("\n## Number of days until reflection\n")
            f.write(f"{days_remaining}\n")

if __name__ == "__main__":
    main()
