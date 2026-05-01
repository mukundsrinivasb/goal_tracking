import sys
from log_utils import get_latest_log_file

def main():
    latest_log = get_latest_log_file()
    
    if not latest_log:
        print("No logs found. Cannot update README.")
        sys.exit(0)
        
    print(f"Updating README with contents from: {latest_log}")
    
    # Read the contents of the most recent log
    with open(latest_log, 'r') as log_file:
        log_content = log_file.read()
        
    # Overwrite the README completely
    with open('README.md', 'w') as readme_file:
        readme_file.write("# Latest G.S.P. Log\n\n")
        readme_file.write(log_content)
        
    print("✅ README.md successfully overwritten.")

if __name__ == "__main__":
    main()
