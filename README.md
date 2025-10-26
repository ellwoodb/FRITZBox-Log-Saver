# FRITZ!Box Log Saver

![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)

## Description

"FRITZ!Box Log Saver" is a Python application that allows you to log in to a FRITZ!Box device, retrieve the event log data, and save it to a structured log file in JSON Lines format. This tool is designed to work seamlessly with Promtail and Grafana Loki for log aggregation and monitoring.

## Features

- ✅ Retrieves logs from FRITZ!Box devices
- ✅ Structured JSON Lines output for Promtail integration
- ✅ Incremental logging (only new entries are added)
- ✅ Configurable exclusion filters
- ✅ Timestamp-based deduplication
- ✅ Ready for use with Grafana Loki stack

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Promtail Integration](#promtail-integration)
- [Scheduled logging](#scheduled-logging)
- [Contributing](#contributing)
- [Credits](#credits)
- [License](#license)

## Installation

### 🐳 Docker (Recommended)

Docker provides the easiest way to run the FRITZ!Box Log Saver:

#### Quick Start with Docker Compose

1. Clone the repository:

   ```bash
   git clone https://github.com/PascalHaury/FRITZBox_Log_Saver.git
   cd FRITZBox_Log_Saver
   ```

2. Create the configuration:

   ```bash
   make setup
   # or manually:
   cp .env.example .env
   ```

3. Edit the `.env` file with your FRITZ!Box credentials:

   ```env
   FRITZBOX_USERNAME=your_username
   FRITZBOX_PASSWORD=your_password
   FRITZBOX_URL=http://fritz.box
   INTERVAL_MINUTES=15
   ```

4. Start the container:
   ```bash
   make run
   # or:
   docker-compose up -d
   ```

#### Docker Environment Variables

| Variable            | Description                           | Default                    | Required |
| ------------------- | ------------------------------------- | -------------------------- | -------- |
| `FRITZBOX_USERNAME` | FRITZ!Box username                    | -                          | ✅       |
| `FRITZBOX_PASSWORD` | FRITZ!Box password                    | -                          | ✅       |
| `FRITZBOX_URL`      | FRITZ!Box URL                         | `http://fritz.box`         | ❌       |
| `INTERVAL_MINUTES`  | Collection interval in minutes        | `15`                       | ❌       |
| `LOG_PATH`          | Path to log file inside container     | `/app/logs/fritzLog.jsonl` | ❌       |
| `TIMEZONE`          | Timezone                              | `Europe/Berlin`            | ❌       |
| `EXCLUDE_PATTERNS`  | Patterns to exclude (comma-separated) | -                          | ❌       |

#### Complete Monitoring Stack

For a complete solution with Grafana and Loki:

```bash
make full-stack
```

This starts:

- **FRITZ!Box Log Saver**: Collects logs every X minutes
- **Promtail**: Sends logs to Loki
- **Loki**: Stores and indexes logs
- **Grafana**: Visualization at http://localhost:3000

#### Docker Commands

```bash
# Quick start (interactive)
./start.sh

# Check container status
make status

# Show logs
make logs

# Restart container
make restart

# Stop everything
make stop

# Clean up
make clean

# Show help
make help
```

#### Example with Direct Docker Commands

```bash
# With Docker Compose
docker-compose up -d

# Or with individual Docker commands
docker run -d \
  --name fritzbox-log-saver \
  --restart unless-stopped \
  -e FRITZBOX_USERNAME=myuser \
  -e FRITZBOX_PASSWORD=mypassword \
  -e FRITZBOX_URL=http://fritz.box \
  -e INTERVAL_MINUTES=15 \
  -v $(pwd)/logs:/app/logs \
  ghcr.io/pascalhaury/fritzbox-log-saver:latest
```

#### Log Output

Logs are saved as structured JSON lines in `logs/fritzLog.jsonl`:

```bash
# Follow logs in real-time
make logs

# Show last log entries
tail -n 20 logs/fritzLog.jsonl | jq .

# Check log level distribution
grep -o '"level":"[^"]*"' logs/fritzLog.jsonl | sort | uniq -c
```

### 🐍 Manual Python Installation

For advanced customizations or development:

1. Clone the repository:

   ```sh
   git clone https://github.com/PascalHaury/FRITZBox_Log_Saver.git
   ```

2. Change to the project directory:

   ```sh
   cd FRITZBox_Log_Saver
   ```

3. Install the required Python packages:

   ```sh
   pip install -r requirements.txt
   ```

## Usage

1. Make sure you have created a settings.yaml by renaming the example file [ex_settings.yaml](src/ex_settings.yaml) or by creating the settings.yaml

   1.1 Modify the settings with your specific [configuration](#configuration).<br>
   1.2 The settings.yaml must be in the same folder as the main.py

2. Run the application:

   ```sh
   python main.py
   ```

3. The application will log in to your FRITZ!Box, retrieve event log data, and save it to a JSON Lines file.

## Configuration

1. Create a settings.yaml file with the following configuration:

   ```yaml
   url: http://fritz.box # URL of your FRITZ!Box
   username: your_username # Your FRITZ!Box username
   password: your_password # Your FRITZ!Box password
   exclude:
     - ExcludedKeyword1 # List of keywords to exclude from log
     - ExcludedKeyword2
   logpath: fritzLog.jsonl # Path to the JSON Lines log file
   ```

2. Modify the values according to your FRITZ!Box login credentials and preferences.
3. For a more detailed example please look in the Example File [ex_settings.yaml](src/ex_settings.yaml)

## Promtail Integration

The application now generates logs in JSON Lines format that can be directly consumed by Promtail for Grafana Loki integration.

### Sample Log Entries

**Info Level (Successful Operations):**

```json
{
  "timestamp": 1748578993,
  "level": "info",
  "source": "fritzbox",
  "message": "Internetverbindung IPv6 wurde erfolgreich hergestellt. IP-Adresse: 2001:16b8:a02e:a0ba:de39:6fff:fee6:ba09",
  "labels": {
    "date": "30.05.25",
    "time": "06:23:13",
    "code": "25",
    "component": "system",
    "severity": "info"
  }
}
```

**Error Level (Failed Operations):**

```json
{
  "timestamp": 1748665209,
  "level": "error",
  "source": "fritzbox",
  "message": "[fritz.repeater] Repeater-Anmeldung an der Basis gescheitert: Authentifizierungsfehler. MAC-Adresse: DC:39:6F:E6:BA:0E.",
  "labels": {
    "date": "31.05.25",
    "time": "06:20:09",
    "code": "721",
    "component": "system",
    "severity": "error"
  }
}
```

**Warning Level (Issues & Disturbances):**

````json
{
  "timestamp": 1748830536,
  "level": "warning",
  "source": "fritzbox",
  "message": "DNS-Störung erkannt, Namensauflösung erfolgt ab sofort über öffentliche DNS-Server.",
  "labels": {
    "date": "02.06.25",
    "time": "04:15:36",
    "code": "2337",
    "component": "system",
    "severity": "warning"
  }
}
```

### Promtail Configuration

Use the provided `promtail-config.yaml` as a starting point:

1. Update the `__path__` in the configuration to point to your log file
2. Adjust the Loki server URL if needed
3. Start Promtail: `promtail -config.file=promtail-config.yaml`

### Intelligent Log Level Classification

The application automatically classifies log entries into appropriate levels:
- **Error**: Failed operations, authentication errors, connection failures
- **Warning**: Service disruptions, performance issues, temporary problems
- **Info**: Successful operations, normal status changes, informational messages

### Grafana Dashboard

The structured format includes the following fields for querying in Grafana:
- `level`: Automatically detected log level (error/warning/info)
- `source`: Always "fritzbox"
- `date`: Date of the log entry
- `code`: FRITZ!Box error/event code
- `component`: Component type (always "system")
- `severity`: Same as level, available in labels for filtering

Example LogQL queries:

```logql
# All FRITZ!Box logs
{job="fritzbox"}

# Only error level logs
{job="fritzbox"} | json | level="error"

# Authentication related errors
{job="fritzbox"} | json | level="error" |~ "(?i)authentifizierung|authentication"

# Network connection issues
{job="fritzbox"} |~ "(?i)verbindung|connection" | json | level!="info"

# Filter by specific error code
{job="fritzbox"} | json | code="721"

# DSL related messages
{job="fritzbox"} |~ "DSL"

# Count errors per hour
sum by (level) (count_over_time({job="fritzbox"} | json [1h]))
````

## Scheduled logging

You can schedule the "FRITZ!Box Log Saver" to run automatically at specific times using crontab. To run the script daily at 00:00, follow these steps:

1. Open your crontab configuration for editing:

   ```sh
   crontab -e
   ```

2. Add the following line to schedule the script daily at midnight:

   ```sh
   0 0 * * * /usr/bin/python /path/to/FRITZ-Box-Log-Saver/main.py
   ```

   Replace **_'/usr/bin/python'_** with the path to your Python interpreter
   (you can find it by running **'which python'**).

   Replace **_'/path/to/FRITZ-Box-Log-Saver'_** with the actual path to your project directory.

3. Save and exit the crontab editor.

This will run your script every day at midnight.

## Contributing

Contributions are welcome! If you have any suggestions, improvements, or bug fixes, please open an issue or a pull request.

## Credits

This project was originally created by **Pascal Haury**.

- **Original Author**: Pascal Haury
- **Repository**: https://github.com/PascalHaury/FRITZBox_Log_Saver

Thank you for creating this useful tool for FRITZ!Box log management!

## License

This project is licensed under the MIT License - see the LICENSE file for details.
