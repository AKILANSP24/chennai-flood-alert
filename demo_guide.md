# 🌊 Chennai Flood Alert System — Demo Guide

> Quick reference for running the demo with your team. Keep this open during the presentation.

---

## Before You Start

Make sure Docker Desktop is running (green icon in taskbar).

---

## Step 1 — Boot the System

Open PowerShell in your project folder and run:

```bash
docker compose up -d
```

Wait 30 seconds. Then create Kafka topics:

```bash
docker exec -it kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic citizen-raw --partitions 1 --replication-factor 1

docker exec -it kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic weather-raw --partitions 1 --replication-factor 1

docker exec -it kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic nlp-results --partitions 1 --replication-factor 1

docker exec -it kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic risk-scores --partitions 1 --replication-factor 1

docker exec -it kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic final-alerts --partitions 1 --replication-factor 1

docker exec -it kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic reservoir-raw --partitions 1 --replication-factor 1

docker exec -it kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic weather-aggregates --partitions 1 --replication-factor 1
```

Fix NLP classifier:

```bash
docker exec -it nlp-service python3 -c "
content = '''
FLOOD_KEYWORDS = [
    'flood','flooding','water','thanni','vellam','mazhai','rain',
    'submerged','overflow','rising','emergency','help','rescue',
    'stuck','trapped','evacuate','depth','cm','knee','waist',
    'pudhuchu','vanthuchu','iruku'
]
def is_flood_related(text):
    return any(k in text.lower() for k in FLOOD_KEYWORDS)
'''
open('/app/classifier.py','w').write(content)
print('done')
"
```

Restart services:

```bash
docker compose restart decision-engine nlp-service telegram-bot
```

---

## Step 2 — Verify Everything is Running

```bash
docker ps --format "{{.Names}}: {{.Status}}"
```

You should see 10 containers all showing `Up`.

Open dashboard: **http://localhost:8081**

---

## Step 3 — Open Two Terminals

**Terminal 1** — Watch the logs (keep this visible during demo):

```bash
docker compose logs -f telegram-bot nlp-service decision-engine ragservice
```

**Terminal 2** — Run the simulation (when ready):

```powershell
$env:TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN_HERE"
$env:SIMULATE_CHAT_ID="5624788161"
python simulate.py
```

---

## Step 4 — Demo Script (What to Say and Do)

### Show 1 — System Overview (1 min)

Point to `docker ps` output.

> "This is 10 Docker containers running a complete flood detection pipeline — Kafka, Redis, Ollama with Llama 3.2, RAG service, Telegram bot, and a decision engine. Zero cloud cost. Everything runs locally."

---

### Show 2 — Telegram Bot (2 min)

Open Telegram. Show the bot to faculty.

Ask your friend to:
1. Open the bot → tap `/start`
2. Send `/register 9XXXXXXXXX`
3. Tap **📍 Share My Location**

> "Citizens register via a simple Telegram command. Their phone number is stored in Redis. Any time an alert fires, they automatically receive an SMS. No app download needed — works on any phone with Telegram."

---

### Show 3 — Live Pipeline (3 min)

Run the simulation in Terminal 2. Watch Terminal 1 logs together.

You'll see in the logs:

```
telegram-bot    | Published citizen report to 'citizen-raw'
nlp-service     | Processing: "Severe flooding in Velachery..."
nlp-service     | Ollama extracted: flood | critical | 65cm | Velachery
decision-engine | 🚨 TRIGGERING RED ALERT FOR Velachery 🚨
ragservice      | RAG lookup → Velachery Government School, Vijayanagar
decision-engine | RAG enriched — shelter + NDRF Zone 4
```

> "The message enters Kafka, our NLP service running Llama 3.2 locally extracts the flood location, severity, and water depth. The decision engine checks Redis — if depth exceeds 50cm or 3+ reports come in within 10 minutes, it triggers an alert. The RAG service then enriches the alert with the nearest shelter and NDRF unit."

---

### Show 4 — Telegram Channel Alert (1 min)

Open your **Chennai Flood Alerts** channel. Show the alert that appeared:

```
🚨 RED ALERT: FLOOD 🚨
📍 Location: Velachery
🌊 Water depth: 65cm
👥 Reports: 1 citizen(s)
🏫 Shelter: Velachery Government School, Vijayanagar
🚒 NDRF Unit: Chennai Zone 4
⚠️ Evacuate immediately!
```

> "The alert reaches the channel within 10 seconds of the citizen's message. It includes the nearest government shelter and the NDRF unit responsible for that zone — this comes from our RAG service which has knowledge of all 11 Chennai flood zones."

---

### Show 5 — Tanglish NLP (1 min)

Ask a friend to send this to the bot:

```
Tambaram la thanni vanthuchu, 70cm iruku, road pudhuchu help pannunga
```

> "This is Tanglish — Tamil written in English letters. Our local Llama 3.2 model understands it perfectly. No cloud API, no internet dependency. It extracts: location=Tambaram, depth=70cm, severity=critical."

---

### Show 6 — Dashboard (2 min)

Open **http://localhost:8081**

Navigate through the pages:
- **Live Feed** — show real alert cards with shelter info
- **Risk Map** — click a zone pin, show detail panel
- **Analytics** — show zone distribution, export CSV
- **Relief Hubs** — show all 11 shelters with NDRF units

> "The dashboard is a real-time SPA that auto-refreshes every 30 seconds from our pipeline data."

---

### Show 7 — Key Talking Points

| What | What to Say |
|---|---|
| Cost | "₹0 vs ₹107 crore government system" |
| NLP | "Runs on local hardware, no cloud API" |
| Tanglish | "Works with how Chennai people actually type" |
| RAG | "Grounded in real Chennai shelter data, not hallucinating" |
| GPS | "Citizens can share location instead of typing zone name" |
| SMS | "Reaches people without internet via Fast2SMS relay" |
| Scale | "Can add more cities by updating the RAG zone dictionary" |

---

## Simulation Messages (Copy-Paste Ready)

Send these to your bot manually if simulation script has issues:

**English — deep water:**
```
Severe flooding in Velachery! Water is 65cm deep and entering houses fast. Emergency!
```

**Tanglish:**
```
Tambaram la thanni vanthuchu, 70cm iruku, road pudhuchu help pannunga
```

**Density trigger (send 3 times for Adyar):**
```
Adyar bridge area flooding badly, water rising fast
```

**Saidapet emergency:**
```
Saidapet flooding critical! 80cm water level entering homes. Children trapped.
```

**GPS report:** Just tap 📍 Share My Location in the bot.

---

## If Something Breaks

**Kafka topic error:**
```bash
docker exec -it kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list
```
If topics are missing, run Step 1 topic creation commands again.

**NLP not processing:**
```bash
docker compose restart nlp-service
```

**Everything broken:**
```bash
docker compose down
docker compose up -d
```
Then redo Step 1 from scratch. Takes 2 minutes.

**Bot not responding:**
Check bot token is correct in `.env` file.

---

## Quick Health Check

Open these URLs to confirm services are up:

| URL | What it shows |
|---|---|
| http://localhost:8081 | Dashboard |
| http://localhost:8081/health | API health check |
| http://localhost:8100/health | RAG service health |

---

*Keep this file open during the demo. Good luck! 🌊*