# 🌊 Chennai Flood Alert System

> Zero-cost real-time urban flood detection and citizen alert system for Chennai, India.
> Built with Kafka, Ollama (Llama 3.2), RAG, Redis, and Telegram.

[![Docker](https://img.shields.io/badge/Docker-10%20containers-blue)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Cost](https://img.shields.io/badge/Infrastructure%20Cost-₹0-brightgreen)](README.md)

---

## What It Does

Citizens report floods via Telegram in English or Tanglish. The system automatically:

1. Extracts flood location, severity, and water depth using local Llama 3.2
2. Triggers alerts when depth exceeds 50cm or 3+ reports arrive in 10 minutes
3. Enriches alerts with nearest shelter and NDRF unit using RAG
4. Broadcasts to Telegram channel and sends SMS to registered citizens

---

## Architecture

```
Citizen (Telegram) → Kafka → NLP Service (Llama 3.2) → Decision Engine (Redis)
                                                              ↓
                                                         RAG Service
                                                              ↓
                                               Telegram Channel + SMS Alert
```

**Services (10 Docker containers):**

| Service | Role |
|---|---|
| kafka | Message broker (KRaft mode, no Zookeeper) |
| redis | Sliding window state + citizen registrations |
| ollama | Runs Llama 3.2 locally for NLP |
| nlp-service | Consumes citizen-raw, extracts flood data |
| decision-engine | Triggers alerts based on rules |
| ragservice | Returns shelter + NDRF info per zone |
| telegram-bot | Receives reports, broadcasts alerts |
| weather-ingestor | Polls OpenWeatherMap every 5 min |
| reservoir-scraper | Scrapes Chennai reservoir levels |
| dashboard | Live ops dashboard at port 8081 |

---

## Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Python 3.11+ (for simulation script)
- A Telegram bot token (from [@BotFather](https://t.me/BotFather))
- OpenWeatherMap free API key

---

## Setup

**1. Clone the repository:**

```bash
git clone https://github.com/YOUR_USERNAME/chennai-flood-alert.git
cd chennai-flood-alert
```

**2. Create your `.env` file:**

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHANNEL_ID=your_channel_id
OPENWEATHERMAP_API_KEY=your_key
FAST2SMS_API_KEY=your_key
ALERT_PHONE_NUMBERS=9XXXXXXXXX
KAFKA_BROKER=kafka:9092
REDIS_HOST=redis
OLLAMA_MODEL=llama3.2:3b
TARGET_CITY=Chennai
```

**3. Start all containers:**

```bash
docker compose up -d
```

**4. Wait 30 seconds, then create Kafka topics:**

```bash
docker exec -it kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic citizen-raw --partitions 1 --replication-factor 1
docker exec -it kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic nlp-results --partitions 1 --replication-factor 1
docker exec -it kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic risk-scores --partitions 1 --replication-factor 1
docker exec -it kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic final-alerts --partitions 1 --replication-factor 1
docker exec -it kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic weather-raw --partitions 1 --replication-factor 1
docker exec -it kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic reservoir-raw --partitions 1 --replication-factor 1
docker exec -it kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic weather-aggregates --partitions 1 --replication-factor 1
```

**5. Pull the Ollama model:**

```bash
docker exec -it ollama ollama pull llama3.2:3b
```

**6. Restart services:**

```bash
docker compose restart decision-engine nlp-service telegram-bot
```

**7. Open the dashboard:**

```
http://localhost:8081
```

---

## Running a Simulation

```bash
pip install requests
```

```powershell
# Windows PowerShell
$env:TELEGRAM_BOT_TOKEN="your_token"
$env:SIMULATE_CHAT_ID="your_telegram_user_id"
python simulate.py
```

```bash
# Linux / Mac
TELEGRAM_BOT_TOKEN=your_token SIMULATE_CHAT_ID=your_id python simulate.py
```

The simulation sends 4 scenarios automatically:
- English flood report with depth
- Tanglish flood report
- Density trigger (3 Adyar reports)
- Saidapet emergency

---

## Citizen Bot Commands

| Command | Action |
|---|---|
| `/start` | Welcome message + GPS location button |
| `/register 9XXXXXXXXX` | Register for SMS alerts |
| `/unregister` | Remove from SMS list |
| `/status` | Check registration + total count |
| Share Location | GPS-based flood report |

---

## Alert Trigger Rules

- **Rule 1:** Water depth > 50cm → immediate RED alert
- **Rule 2:** 3+ critical/high reports from same zone within 10 minutes → ORANGE/RED alert

---

## Dashboard Pages

| Page | URL path | Description |
|---|---|---|
| Live Feed | `/#live` | Real-time alert feed + pipeline status |
| Risk Map | `/#map` | Chennai zone map with severity markers |
| Analytics | `/#analytics` | Data table, zone distribution, R charts |
| Relief Hubs | `/#shelters` | All 11 shelter zones with NDRF units |
| Register | `/#register` | Bot commands + quick report form |

---

## Deploy to Vercel / Netlify

The dashboard (`services/dashboard/dashboard.html`) is a single HTML file with no build step.

**Vercel:**

```bash
npm i -g vercel
vercel --prod
```

Point it to `services/dashboard/` as the root. Set environment variable `VITE_API_URL` to your deployed backend URL.

**Netlify:**

Drag and drop the `services/dashboard/` folder to [app.netlify.com](https://app.netlify.com).

> Note: For a live dashboard connected to real data, deploy the full Docker stack on a VPS (DigitalOcean, Railway, or Render) and update `API_BASE` in the dashboard HTML to point to your deployed API URL.

---

## RAG Knowledge Base

The system covers 11 Chennai flood zones:

Velachery · Tambaram · Adyar · Saidapet · Mudichur · Porur · Perambur · T Nagar · Anna Nagar · Chrompet · Neelankari

Each zone has a designated shelter, NDRF unit, historical flood depth, and evacuation route.

---

## Adding Maps

The current dashboard uses a static satellite image. To add interactive maps:

**Option A — Leaflet.js (free):**

```html
<link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
<div id="map" style="height:400px;"></div>
<script>
  const map = L.map('map').setView([13.0827, 80.2707], 12);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
  // Add alert markers from your API
  fetch('/api/alerts').then(r=>r.json()).then(data=>{
    data.alerts.forEach(a=>{
      const coords = ZONE_COORDS[a.zone.toLowerCase()];
      if(coords) L.circleMarker(coords, {
        color: a.severity==='critical' ? '#ff716c' : '#ff8439',
        radius: 12
      }).addTo(map).bindPopup(`${a.zone}: ${a.depth_cm}cm`);
    });
  });
</script>
```

**Option B — Google Maps (requires API key):**

Get a free Google Maps API key at [console.cloud.google.com](https://console.cloud.google.com). Add it to `.env` as `GOOGLE_MAPS_API_KEY`.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Message Broker | Apache Kafka 3.7 (KRaft) |
| State Management | Redis 7 |
| LLM | Ollama + Llama 3.2 3B (local) |
| NLP Pipeline | Python + FastAPI |
| RAG | Dictionary lookup (11 zones) |
| Alert Channel | Telegram Bot API |
| SMS Fallback | Fast2SMS Quick Route |
| Analytics | R (ggplot2, dplyr, lubridate) |
| Dashboard | Vanilla HTML/CSS/JS |
| Containerization | Docker Compose |

---

## Project Structure

```
chennai-flood-alert/
├── services/
│   ├── telegram-bot/        # Receives reports, broadcasts alerts
│   ├── nlp-service/         # Llama 3.2 NLP extraction
│   ├── decision-engine/     # Alert trigger rules + Redis
│   ├── rag-service/         # Shelter + NDRF knowledge base
│   ├── weather-ingestor/    # OpenWeatherMap polling
│   ├── reservoir-scraper/   # Reservoir level scraping
│   └── dashboard/           # Live ops dashboard
├── r-analysis/              # R analytics + chart generation
├── data/                    # CSV logs + generated reports
├── docker-compose.yml
├── simulate.py              # Demo simulation script
├── DEMO_GUIDE.md            # Faculty demo instructions
└── README.md
```

---

## Environment Variables

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | From @BotFather |
| `TELEGRAM_CHANNEL_ID` | Your alert channel ID |
| `OPENWEATHERMAP_API_KEY` | Free tier works |
| `FAST2SMS_API_KEY` | Requires ₹100 recharge for API |
| `ALERT_PHONE_NUMBERS` | Comma-separated 10-digit numbers |
| `OLLAMA_MODEL` | Default: llama3.2:3b |
| `DENSITY_THRESHOLD` | Reports to trigger density alert (default: 3) |
| `DEPTH_THRESHOLD_CM` | Depth to trigger immediate alert (default: 50) |
| `WINDOW_MINUTES` | Sliding window duration (default: 10) |

---

## Built By

**Akilan S P** (22MIA1191)
B.Tech CSE with Business Analytics Specialization
VIT Chennai

---

## License

VIT-chennai