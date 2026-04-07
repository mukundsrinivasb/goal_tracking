#!/bin/bash

LOG_DIR="../../logs"

echo "Starting remark cleanup"

# Find the newest md file
LATEST_LOG=$(ls "$LOG_DIR"/*.md 2>/dev/null | sort -r | head -1)

# Check if the file is actually found
if [[ -n "$LATEST_LOG" && -f "$LATEST_LOG" ]]; then
  echo "found latest log: $LATEST_LOG"

  #use the stream editor
  sed -i 's/_add_remarks_/incomplete/g' "$LATEST_LOG"

fi

