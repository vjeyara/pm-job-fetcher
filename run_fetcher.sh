#!/bin/bash
# PM Job Fetcher — daily runner
# Scheduled via cron at 9:00 AM CET every day
# Weekly summary auto-generates on Saturdays

cd "/Users/jeyvenkat/Library/Mobile Documents/com~apple~CloudDocs/Downloads/LandPM BootCamp/Job Fetcher"

/usr/bin/python3 fetch_jobs.py >> logs/fetcher.log 2>&1
