FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY entrypoint.sh .
COPY healthcheck.sh .

# Make scripts executable
RUN chmod +x entrypoint.sh healthcheck.sh

# Create directory for logs
RUN mkdir -p /app/logs

# Set environment variables with defaults
ENV FRITZBOX_URL="http://fritz.box" \
    FRITZBOX_USERNAME="" \
    FRITZBOX_PASSWORD="" \
    LOG_PATH="/app/logs/fritzLog.jsonl" \
    INTERVAL_MINUTES="15" \
    EXCLUDE_PATTERNS="" \
    TIMEZONE="Europe/Berlin"

# Set timezone
RUN ln -snf /usr/share/zoneinfo/$TIMEZONE /etc/localtime && echo $TIMEZONE > /etc/timezone

# Expose volume for logs
VOLUME ["/app/logs"]

# Use entrypoint script
ENTRYPOINT ["./entrypoint.sh"]
