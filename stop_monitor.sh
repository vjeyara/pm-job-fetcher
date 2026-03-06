#!/bin/bash
# Stops and unloads the background job monitoring service

PLIST="$HOME/Library/LaunchAgents/com.pmjobfetcher.monitor.plist"

launchctl unload "$PLIST" 2>/dev/null

if [ $? -eq 0 ] || [ ! -f "$PLIST" ]; then
    echo "Monitor stopped."
else
    echo "Monitor was not running (or already stopped)."
fi
