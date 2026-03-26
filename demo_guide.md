# Simple Demo Guide

Here is a quick, easy-to-follow guide on how to present your project during the review.

### 1. Start the Project
Before the review begins:
1. Open your terminal in the project folder.
2. Run `docker-compose up -d`
3. Open `flood_demo.html` in your browser.
4. Have your Telegram app open.

---

### Step-by-Step Presentation

**Step 1: Architecture (HTML Dashboard)**
* Open `flood_demo.html`.
* **Say:** *"This dashboard shows how our system works. We collect citizen reports from Telegram, push them to Kafka, extract depths via NLP (Llama 3.2), and trigger alerts using a Redis-backed decision engine."*

**Step 2: Show It's Real (Terminal)**
* Go to the terminal.
* Run: `docker ps --format "{{.Names}}: {{.Status}}"`
* **Say:** *"Here are our 9 backend microservices running live inside Docker."*
* Run: `docker exec -it kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list`
* **Say:** *"And here are all 7 live Kafka topics."*

**Step 3: The Live Test (Telegram)**
* Open Telegram and send your Bot a message: *"Velachery main road la thanni 60cm iruku."*
* Switch to the terminal and run: `docker logs telegram-bot`, then `docker logs nlp-service`.
* **Say:** *"As you can see, the bot received the message instantly and published it to Kafka, and our NLP engine processed it."*

**Step 4: Explain Tanglish NLP (HTML Dashboard)**
* Go back to `flood_demo.html`.
* Click **Scenario 2 — Tanglish report**.
* **Say:** *"Live LLM extraction can be hard to read in the terminal, so here is what the NLP service guarantee looks like. It normalizes Tanglish logic and extracts structured data."*

**Step 5: Analytics Output (R Reports)**
* Open `data/reports/interactive_flood_map.html` and the `alert_timeline.png` in your browser/viewer.
* **Say:** *"Finally, an R-script parses our alerts database to plot this interactive map and generate timeline statistics."*

---

### 🚨 Emergency Backup Plan
If anything fails during the live Telegram test (e.g. slow NLP, Kafka disconnect):
1. **Don't panic!**
2. Just switch to the `flood_demo.html` dashboard.
3. **Say:** *"Live distributed services can have network hiccups, let me show you the expected scenarios visually."*
4. Run the demo animations (Scenario 1, Scenario 3, Scenario 4).
