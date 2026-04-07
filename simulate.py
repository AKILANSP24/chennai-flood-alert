"""
Chennai Flood Alert System — Demo Simulation Script
Run this from your project root: python simulate.py
It simulates citizens reporting floods across multiple Chennai zones.
"""

import requests
import time
import os
import sys

# ── Config ────────────────────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("SIMULATE_CHAT_ID", "")  # Your personal Telegram user ID

if not BOT_TOKEN or not CHAT_ID:
    print("ERROR: Set TELEGRAM_BOT_TOKEN and SIMULATE_CHAT_ID in .env")
    print("Get your chat ID by sending /start to @userinfobot on Telegram")
    sys.exit(1)

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def send_message(text: str, delay: float = 2.0):
    """Send a message to the bot as if a citizen typed it."""
    resp = requests.post(BASE_URL, json={
        "chat_id": CHAT_ID,
        "text": text
    })
    if resp.status_code == 200:
        print(f"  ✅ Sent: {text[:60]}...")
    else:
        print(f"  ❌ Failed: {resp.text}")
    time.sleep(delay)

# ── Simulation scenarios ──────────────────────────────────────────────────────
scenarios = [
    {
        "name": "Scenario 1 — English deep water report (Velachery)",
        "messages": [
            "Severe flooding in Velachery! Water is 65cm deep and entering houses fast. Emergency!"
        ],
        "delay_after": 5
    },
    {
        "name": "Scenario 2 — Tanglish report (Tambaram)",
        "messages": [
            "Tambaram la thanni vanthuchu, 70cm iruku, road pudhuchu help pannunga"
        ],
        "delay_after": 5
    },
    {
        "name": "Scenario 3 — Density trigger (3 Adyar reports in quick succession)",
        "messages": [
            "Adyar bridge area flooding badly, water rising fast",
            "Adyar main road completely submerged, need help",
            "Adyar residents please evacuate, waist level water everywhere"
        ],
        "delay_after": 8
    },
    {
        "name": "Scenario 4 — Saidapet emergency",
        "messages": [
            "Saidapet flooding critical! 80cm water level entering homes. Children trapped."
        ],
        "delay_after": 5
    }
]

print("\n" + "="*60)
print("  CHENNAI FLOOD ALERT SYSTEM — DEMO SIMULATION")
print("="*60)
print(f"  Bot: {BOT_TOKEN[:20]}...")
print(f"  Chat ID: {CHAT_ID}")
print("="*60 + "\n")

for i, scenario in enumerate(scenarios, 1):
    print(f"\n[{i}/{len(scenarios)}] {scenario['name']}")
    print("-" * 50)
    for msg in scenario["messages"]:
        send_message(msg, delay=3.0)
    print(f"  ⏳ Waiting {scenario['delay_after']}s for pipeline to process...")
    time.sleep(scenario["delay_after"])

print("\n" + "="*60)
print("  SIMULATION COMPLETE")
print("  Check:")
print("  • Telegram channel for alerts")
print("  • Phone for SMS (if Fast2SMS funded)")
print("  • docker compose logs -f decision-engine")
print("="*60 + "\n")