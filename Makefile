.PHONY: help build run stop logs clean setup full-stack

# Default target
help:
	@echo "FRITZ!Box Log Saver - Docker Commands"
	@echo "======================================"
	@echo ""
	@echo "Setup Commands:"
	@echo "  setup          - Setup .env file from template"
	@echo "  build          - Build the Docker image"
	@echo ""
	@echo "Basic Usage:"
	@echo "  run            - Start log saver container"
	@echo "  stop           - Stop log saver container"
	@echo "  logs           - Show container logs"
	@echo "  status         - Show container status"
	@echo ""
	@echo "Full Stack (with Grafana/Loki):"
	@echo "  full-stack     - Start complete monitoring stack"
	@echo "  stop-stack     - Stop complete monitoring stack"
	@echo "  grafana        - Open Grafana in browser"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean          - Clean up containers and images"
	@echo "  restart        - Restart log saver"
	@echo ""
	@echo "Environment Variables (set in .env file):"
	@echo "  FRITZBOX_USERNAME   - Your FRITZ!Box username"
	@echo "  FRITZBOX_PASSWORD   - Your FRITZ!Box password"
	@echo "  FRITZBOX_URL        - FRITZ!Box URL (default: http://fritz.box)"
	@echo "  INTERVAL_MINUTES    - Collection interval (default: 15)"

# Setup .env file
setup:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env file from template."; \
		echo "Please edit .env file with your FRITZ!Box credentials."; \
	else \
		echo ".env file already exists."; \
	fi

# Build Docker image
build:
	docker-compose build

# Start log saver only
run: setup
	@if [ ! -f .env ]; then echo "Please run 'make setup' first and configure .env"; exit 1; fi
	docker-compose up -d fritzbox-log-saver
	@echo "FRITZ!Box Log Saver started. Use 'make logs' to see output."

# Start full monitoring stack
full-stack: setup
	@if [ ! -f .env ]; then echo "Please run 'make setup' first and configure .env"; exit 1; fi
	docker-compose -f docker-compose.full.yml up -d
	@echo "Full monitoring stack started:"
	@echo "- Grafana: http://localhost:3000 (admin/admin)"
	@echo "- Loki: http://localhost:3100"
	@echo "Use 'make logs' to see log saver output."

# Stop containers
stop:
	docker-compose down

stop-stack:
	docker-compose -f docker-compose.full.yml down

# Show logs
logs:
	docker-compose logs -f fritzbox-log-saver

# Show container status
status:
	docker-compose ps

# Restart log saver
restart:
	docker-compose restart fritzbox-log-saver

# Open Grafana in browser
grafana:
	@echo "Opening Grafana at http://localhost:3000"
	@echo "Default credentials: admin/admin"
	@if command -v open >/dev/null 2>&1; then \
		open http://localhost:3000; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open http://localhost:3000; \
	else \
		echo "Please open http://localhost:3000 in your browser"; \
	fi

# Clean up
clean:
	docker-compose down -v
	docker-compose -f docker-compose.full.yml down -v
	docker system prune -f
	@echo "Cleaned up containers, networks, and unused images"

# Show log file contents
show-logs:
	@if [ -f logs/fritzLog.jsonl ]; then \
		echo "Last 10 log entries:"; \
		tail -n 10 logs/fritzLog.jsonl | jq .; \
	else \
		echo "No log file found. Container may not have run yet."; \
	fi

# Test configuration
test:
	@echo "Testing Docker configuration..."
	docker-compose config
	@echo "Configuration is valid!"
