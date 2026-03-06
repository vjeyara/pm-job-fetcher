#!/bin/bash
# Installs the plist and starts the background service

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_SRC="$SCRIPT_DIR/com.pmjobfetcher.monitor.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/com.pmjobfetcher.monitor.plist"
OUTPUT_DIR="$SCRIPT_DIR/output"

# Create output dir so logs can be written
mkdir -p "$OUTPUT_DIR"

# Unload any existing instance first (ignore errors)
launchctl unload "$PLIST_DEST" 2>/dev/null

# Copy plist to LaunchAgents
cp "$PLIST_SRC" "$PLIST_DEST"

# Load and start the service
launchctl load "$PLIST_DEST"

echo "Monitor started. Jobs will be checked every 30 minutes."
echo "  To stop:  bash stop_monitor.sh"
echo "  Logs:     $OUTPUT_DIR/monitor.log"
echo "  Errors:   $OUTPUT_DIR/monitor_error.log"
echo ""
echo "  Status check: launchctl list | grep pmjobfetcher"
