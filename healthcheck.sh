#!/bin/bash

# Health check script for FRITZ!Box Log Saver Docker container

# Exit codes:
# 0 - healthy
# 1 - unhealthy

LOG_FILE="${LOG_PATH:-/app/logs/fritzLog.jsonl}"
MAX_AGE_MINUTES="${HEALTH_CHECK_MAX_AGE:-60}"

# Check if log file exists
if [ ! -f "$LOG_FILE" ]; then
    echo "UNHEALTHY: Log file $LOG_FILE does not exist"
    exit 1
fi

# Check if log file is not empty
if [ ! -s "$LOG_FILE" ]; then
    echo "UNHEALTHY: Log file $LOG_FILE is empty"
    exit 1
fi

# Check if log file has been modified recently
if [ -n "$MAX_AGE_MINUTES" ]; then
    # Get the modification time of the log file in seconds since epoch
    LOG_MOD_TIME=$(stat -c %Y "$LOG_FILE" 2>/dev/null || stat -f %m "$LOG_FILE" 2>/dev/null)
    
    if [ -z "$LOG_MOD_TIME" ]; then
        echo "UNHEALTHY: Cannot determine log file modification time"
        exit 1
    fi
    
    # Get current time in seconds since epoch
    CURRENT_TIME=$(date +%s)
    
    # Calculate age in minutes
    AGE_SECONDS=$((CURRENT_TIME - LOG_MOD_TIME))
    AGE_MINUTES=$((AGE_SECONDS / 60))
    
    if [ "$AGE_MINUTES" -gt "$MAX_AGE_MINUTES" ]; then
        echo "UNHEALTHY: Log file is too old (${AGE_MINUTES} minutes, max: ${MAX_AGE_MINUTES})"
        exit 1
    fi
fi

# Check if log file contains valid JSON entries
LAST_LINE=$(tail -n 1 "$LOG_FILE")
if [ -n "$LAST_LINE" ]; then
    # Try to parse the last line as JSON
    echo "$LAST_LINE" | python -m json.tool > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "UNHEALTHY: Log file contains invalid JSON"
        exit 1
    fi
fi

echo "HEALTHY: All checks passed"
exit 0
