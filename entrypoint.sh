#!/bin/bash

# Exit on any error
set -e

echo "Starting FRITZ!Box Log Saver Container..."
echo "URL: $FRITZBOX_URL"
echo "Username: $FRITZBOX_USERNAME"
echo "Interval: $INTERVAL_MINUTES minutes"
echo "Log Path: $LOG_PATH"
echo "Timezone: $TIMEZONE"

# Validate required environment variables
if [ -z "$FRITZBOX_USERNAME" ]; then
    echo "ERROR: FRITZBOX_USERNAME environment variable is required"
    exit 1
fi

if [ -z "$FRITZBOX_PASSWORD" ]; then
    echo "ERROR: FRITZBOX_PASSWORD environment variable is required"
    exit 1
fi

# Validate interval
if ! [[ "$INTERVAL_MINUTES" =~ ^[0-9]+$ ]] || [ "$INTERVAL_MINUTES" -lt 1 ]; then
    echo "ERROR: INTERVAL_MINUTES must be a positive integer"
    exit 1
fi

# Create dynamic settings.yaml
cat > /app/src/settings.yaml <<EOF
url: "$FRITZBOX_URL"
username: "$FRITZBOX_USERNAME"
password: "$FRITZBOX_PASSWORD"
logpath: "$LOG_PATH"
exclude: []
EOF

# Add exclude patterns if provided
if [ -n "$EXCLUDE_PATTERNS" ]; then
    echo "Adding exclude patterns: $EXCLUDE_PATTERNS"
    # Convert comma-separated patterns to YAML array
    IFS=',' read -ra PATTERNS <<< "$EXCLUDE_PATTERNS"
    echo "exclude:" > /tmp/exclude.yaml
    for pattern in "${PATTERNS[@]}"; do
        echo "  - \"$(echo "$pattern" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')\"" >> /tmp/exclude.yaml
    done
    # Replace the exclude line in settings.yaml
    sed -i '/exclude: \[\]/d' /app/src/settings.yaml
    cat /tmp/exclude.yaml >> /app/src/settings.yaml
fi

echo "Generated settings.yaml:"
cat /app/src/settings.yaml
echo ""

# Function to run the log collector
run_collector() {
    echo "$(date): Running FRITZ!Box log collection..."
    cd /app
    python src/main.py
    if [ $? -eq 0 ]; then
        echo "$(date): Log collection completed successfully"
    else
        echo "$(date): Error during log collection (exit code: $?)"
    fi
}

# Run once at startup
run_collector

# Convert minutes to seconds
INTERVAL_SECONDS=$((INTERVAL_MINUTES * 60))

echo "Starting periodic execution every $INTERVAL_MINUTES minutes..."

# Main loop
while true; do
    echo "$(date): Waiting $INTERVAL_MINUTES minutes until next execution..."
    sleep $INTERVAL_SECONDS
    run_collector
done
