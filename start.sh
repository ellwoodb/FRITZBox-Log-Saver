#!/bin/bash

# FRITZ!Box Log Saver - Startup Script
# This script helps you get started quickly with Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================"
echo -e "FRITZ!Box Log Saver - Docker Setup"
echo -e "======================================${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker ist nicht installiert!${NC}"
    echo "Bitte installieren Sie Docker von: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null 2>&1; then
    echo -e "${RED}❌ Docker Compose ist nicht verfügbar!${NC}"
    echo "Bitte installieren Sie Docker Compose oder verwenden Sie eine neuere Docker-Version."
    exit 1
fi

echo -e "${GREEN}✅ Docker ist installiert${NC}"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}📝 Erstelle .env Datei...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ .env Datei erstellt${NC}"
else
    echo -e "${GREEN}✅ .env Datei existiert bereits${NC}"
fi

# Check if .env is configured
if grep -q "your_username" .env || grep -q "your_password" .env; then
    echo ""
    echo -e "${YELLOW}⚠️  WICHTIG: Konfiguration erforderlich!${NC}"
    echo ""
    echo "Bitte bearbeiten Sie die .env Datei mit Ihren FRITZ!Box-Daten:"
    echo ""
    echo -e "${BLUE}Erforderliche Einstellungen:${NC}"
    echo "  FRITZBOX_USERNAME=IhrBenutzername"
    echo "  FRITZBOX_PASSWORD=IhrPasswort"
    echo ""
    echo -e "${BLUE}Optionale Einstellungen:${NC}"
    echo "  FRITZBOX_URL=http://fritz.box (oder IP-Adresse)"
    echo "  INTERVAL_MINUTES=15 (Sammelintervall in Minuten)"
    echo ""
    
    read -p "Möchten Sie die .env Datei jetzt bearbeiten? (j/N): " edit_env
    if [[ $edit_env =~ ^[jJyY]$ ]]; then
        if command -v nano &> /dev/null; then
            nano .env
        elif command -v vim &> /dev/null; then
            vim .env
        elif command -v code &> /dev/null; then
            code .env
            echo "Drücken Sie Enter, wenn Sie die Datei gespeichert haben..."
            read
        else
            echo "Bitte bearbeiten Sie die .env Datei mit Ihrem bevorzugten Editor."
            echo "Datei: $(pwd)/.env"
            read -p "Drücken Sie Enter, wenn Sie fertig sind..."
        fi
    else
        echo ""
        echo -e "${YELLOW}Sie können die Datei später bearbeiten:${NC}"
        echo "  nano .env"
        echo "oder"
        echo "  code .env"
        echo ""
        read -p "Drücken Sie Enter, um fortzufahren..."
    fi
fi

echo ""
echo -e "${BLUE}Welche Option möchten Sie starten?${NC}"
echo ""
echo "1) Nur FRITZ!Box Log Saver (empfohlen für den Start)"
echo "2) Vollständiger Monitoring-Stack (Log Saver + Grafana + Loki)"
echo "3) Konfiguration testen"
echo "4) Beenden"
echo ""

read -p "Ihre Wahl (1-4): " choice

case $choice in
    1)
        echo ""
        echo -e "${BLUE}🚀 Starte FRITZ!Box Log Saver...${NC}"
        docker-compose up -d fritzbox-log-saver
        echo ""
        echo -e "${GREEN}✅ FRITZ!Box Log Saver gestartet!${NC}"
        echo ""
        echo "Nützliche Befehle:"
        echo "  make logs    - Live-Logs anzeigen"
        echo "  make status  - Container-Status prüfen"
        echo "  make stop    - Container stoppen"
        echo ""
        echo "Log-Datei wird gespeichert in: ./logs/fritzLog.jsonl"
        ;;
    2)
        echo ""
        echo -e "${BLUE}🚀 Starte vollständigen Monitoring-Stack...${NC}"
        docker-compose -f docker-compose.full.yml up -d
        echo ""
        echo -e "${GREEN}✅ Monitoring-Stack gestartet!${NC}"
        echo ""
        echo -e "${BLUE}Verfügbare Services:${NC}"
        echo "  📊 Grafana:  http://localhost:3000 (admin/admin)"
        echo "  📝 Loki:     http://localhost:3100"
        echo ""
        echo "Der Stack benötigt ein paar Minuten zum vollständigen Start."
        ;;
    3)
        echo ""
        echo -e "${BLUE}🔍 Teste Konfiguration...${NC}"
        docker-compose config
        echo ""
        echo -e "${GREEN}✅ Konfiguration ist gültig!${NC}"
        ;;
    4)
        echo ""
        echo -e "${BLUE}Auf Wiedersehen! 👋${NC}"
        exit 0
        ;;
    *)
        echo ""
        echo -e "${RED}❌ Ungültige Auswahl${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}🎉 Setup abgeschlossen!${NC}"
echo ""
echo -e "${BLUE}Weitere Hilfe:${NC}"
echo "  make help    - Alle verfügbaren Befehle anzeigen"
echo "  make logs    - Container-Logs live verfolgen"
echo ""
