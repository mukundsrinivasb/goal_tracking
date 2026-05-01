import sys
import os
import glob
from log_utils import get_latest_log_file

def main():
    # 1. Grab the latest log using your abstracted function
    latest_log = get_latest_log_file()
    
    if not latest_log:
        print("No logs found to check.")
        sys.exit(0)
    
    # 2. Extract the base name (e.g., '20_04_2026')
    base_name = os.path.basename(latest_log).replace('.md', '')
    print(f"Checking for image: images/{base_name}.*")
    
    # 3. Check for matching images with any extension
    matching_images = glob.glob(f"images/{base_name}.*")
    
    if matching_images:
        print(f"✅ Success: Image found for log {base_name}! ({matching_images[0]})")
        sys.exit(0)
    else:
        print(f"❌ Error: No matching image found for {base_name}.")
        print("Please ensure the original photo is uploaded to the images/ directory.")
        sys.exit(1) # This intentionally crashes the GitHub Action

if __name__ == "__main__":
    main()
