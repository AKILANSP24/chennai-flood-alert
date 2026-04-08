# 🌊 Chennai Flood Alert System

> Zero-cost real-time urban flood detection and citizen alert system for Chennai, India.
> Built with Kafka, Ollama (Llama 3.2), RAG, Redis, and Telegram.

[![Docker](https://img.shields.io/badge/Docker-10%20containers-blue)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Cost](https://img.shields.io/badge/Infrastructure%20Cost-₹0-brightgreen)](README.md)

---

## Project Title

**Real-Time Urban Flood Detection and Citizen Alert System for Chennai**

## Team

| Name | Institution |
|---|---|
| Arone Benedict L | VIT Chennai |
| Anieruth S | VIT Chennai |
| Akilan S P | VIT Chennai |

*Integrated M.Tech — Computer Science Engineering with Business Analytics*
*VIT Chennai*

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
- Python 3.11+
- A Telegram bot token (from [@BotFather](https://t.me/BotFather))
- OpenWeatherMap free API key

---

## Setup

**1. Clone the repository:**

```bash
git clone https://github.com/AKILANSP24/chennai-flood-alert.git
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

The simulation sends 4 flood scenarios automatically — English report, Tanglish report, density trigger, and emergency alert.

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
- **Rule 2:** 3+ reports from same zone within 10 minutes → ORANGE/RED alert

---

## Dashboard Pages

| Page | Description |
|---|---|
| Live Feed | Real-time alert feed + pipeline status |
| Risk Map | Chennai zone map with severity markers |
| Analytics | Data table, zone distribution, R charts, PDF report download |
| Relief Hubs | All 11 shelter zones with NDRF units |
| Register | Bot commands + quick report form |

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
| Containerisation | Docker Compose |

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
├── r-analysis/              # R analytics + PDF report generation
├── data/                    # CSV logs + generated reports
├── docker-compose.yml
├── simulate.py              # Demo simulation script
└── README.md
```

---

## Environment Variables

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | From @BotFather |
| `TELEGRAM_CHANNEL_ID` | Your alert channel ID |
| `OPENWEATHERMAP_API_KEY` | Free tier works |
| `FAST2SMS_API_KEY` | Requires ₹100 recharge for API route |
| `ALERT_PHONE_NUMBERS` | Comma-separated 10-digit numbers |
| `OLLAMA_MODEL` | Default: llama3.2:3b |
| `DEPTH_THRESHOLD_CM` | Depth to trigger immediate alert (default: 50) |
| `WINDOW_MINUTES` | Sliding window duration (default: 10) |

---

## License

MIT
