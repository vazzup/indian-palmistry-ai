#!/bin/bash

# Setup cleanup cron job for inactive analyses
# This script should be run once during server setup

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CLEANUP_SCRIPT="$PROJECT_DIR/app/scripts/cleanup_inactive_analyses.py"
PYTHON_PATH="$(which python3)"
LOG_FILE="$PROJECT_DIR/logs/cleanup.log"

# Ensure logs directory exists
mkdir -p "$PROJECT_DIR/logs"

# Create the cron job entry
CRON_JOB="0 2 * * * cd $PROJECT_DIR && $PYTHON_PATH -m app.scripts.cleanup_inactive_analyses --days=7 >> $LOG_FILE 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "cleanup_inactive_analyses"; then
    echo "Cleanup cron job already exists"
else
    # Add the cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "Added cleanup cron job: runs daily at 2:00 AM"
    echo "Logs will be written to: $LOG_FILE"
fi

# Test the cleanup script (dry run)
echo "Testing cleanup script (dry run)..."
cd "$PROJECT_DIR"
$PYTHON_PATH -m app.scripts.cleanup_inactive_analyses --dry-run

echo "Cleanup cron job setup completed!"
echo ""
echo "To manually run cleanup:"
echo "  cd $PROJECT_DIR"
echo "  python3 -m app.scripts.cleanup_inactive_analyses --dry-run  # (test run)"
echo "  python3 -m app.scripts.cleanup_inactive_analyses           # (actual cleanup)"