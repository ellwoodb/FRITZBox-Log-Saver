# 🐳 Docker Quick Start Guide

## Schnellste Methode (Empfohlen)

1. **Repository klonen:**

   ```bash
   git clone https://github.com/PascalHaury/FRITZBox_Log_Saver.git
   cd FRITZBox_Log_Saver
   ```

2. **Interaktiver Start:**
   ```bash
   ./start.sh
   ```
   Das Skript führt Sie durch die komplette Einrichtung!

## Manuelle Einrichtung

1. **Umgebungsdatei erstellen:**

   ```bash
   cp .env.example .env
   ```

2. **Konfiguration bearbeiten:**

   ```bash
   nano .env  # oder mit Ihrem bevorzugten Editor
   ```

3. **Container starten:**

   ```bash
   # Nur Log Saver
   docker-compose up -d

   # Oder vollständiger Stack mit Grafana
   docker-compose -f docker-compose.full.yml up -d
   ```

## Wichtige Befehle

```bash
# Status prüfen
docker-compose ps

# Logs verfolgen
docker-compose logs -f fritzbox-log-saver

# Container stoppen
docker-compose down

# Alles mit Make (wenn verfügbar)
make help
make run
make logs
make stop
```

## Umgebungsvariablen

**Erforderlich:**

- `FRITZBOX_USERNAME` - Ihr FRITZ!Box Benutzername
- `FRITZBOX_PASSWORD` - Ihr FRITZ!Box Passwort

**Optional:**

- `FRITZBOX_URL` - FRITZ!Box URL (Standard: http://fritz.box)
- `INTERVAL_MINUTES` - Sammelintervall (Standard: 15 Minuten)
- `EXCLUDE_PATTERNS` - Auszuschließende Muster (kommagetrennt)

## Ausgabe

Logs werden in `./logs/fritzLog.jsonl` gespeichert und sind bereit für:

- ✅ Promtail/Loki Integration
- ✅ Grafana Visualisierung
- ✅ Weitere Log-Analyse-Tools

## Support

Bei Problemen:

1. `make logs` - Container-Logs prüfen
2. `docker-compose ps` - Container-Status prüfen
3. `.env` Datei auf korrekte Konfiguration prüfen
