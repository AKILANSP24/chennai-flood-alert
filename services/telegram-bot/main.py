import os
import json
import hashlib
import logging
from datetime import datetime, timezone
from telegram import Update, Bot # type: ignore
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes # type: ignore
import asyncio
from confluent_kafka import Consumer, Producer # type: ignore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("telegram-bot")

KAFKA_BROKER = os.getenv("KAFKA_BROKER", os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"))
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

producer = Producer({'bootstrap.servers': KAFKA_BROKER})

def get_user_hash(user_id: int) -> str:
    return hashlib.sha256(str(user_id).encode()).hexdigest()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Send your location and a text update describing the flood situation.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message:
        return
        
    user_hash = get_user_hash(message.from_user.id)
    text = message.text or message.caption or ""
    
    lat, lon = None, None
    if message.location:
        lat = message.location.latitude
        lon = message.location.longitude
    
    # Fallback to saving location/text to user context if they send them separately
    # For now, we package everything we received into the event
    payload = {
        "user_id_hash": user_hash,
        "lat": lat,
        "lon": lon,
        "text": text,
        "ts": datetime.now(timezone.utc).isoformat()
    }
    
    # Forward to Kafka
    if text or lat:
        producer.produce("citizen-raw", value=json.dumps(payload).encode('utf-8'))
        producer.flush()
        await message.reply_text("Report received. Stay safe!")
        logger.info(f"Published citizen report to 'citizen-raw' from {user_hash}")

def main():
    if not TOKEN or TOKEN == "your_token_here":
        logger.error("TELEGRAM_BOT_TOKEN is missing. Bot cannot start.")
        return

    async def kafka_consumer_task(app: Application):
        consumer = Consumer({
            'bootstrap.servers': KAFKA_BROKER,
            'group.id': 'telegram-broadcaster',
            'auto.offset.reset': 'latest'
        })
        consumer.subscribe(['final-alerts'])
        logger.info("Telegram Bot listening to 'final-alerts'...")
        
        while True:
            msg = await asyncio.to_thread(consumer.poll, 1.0) # type: ignore
            if msg is None:
                await asyncio.sleep(0.1)
                continue
            if msg.error(): # type: ignore
                continue
                
            try:
                alert = json.loads(msg.value().decode('utf-8')) # type: ignore
                urgency = alert.get('urgency', 'ORANGE')
                condition = alert.get('condition', 'Unknown')
                location = alert.get('location', 'Unknown Region')
                depth = alert.get('water_depth_cm', 0)
                
                alert_text = f"🚨 {urgency} ALERT: {condition.upper()} 🚨\n📍 Location: {location}\n🌊 Depth: {depth}cm"
                
                if CHANNEL_ID:
                    await app.bot.send_message(chat_id=CHANNEL_ID, text=alert_text)
                    logger.info(f"Broadcasted to Channel: {alert_text}")
            except Exception as e:
                logger.error(f"Failed to broadcast final-alert: {e}")

    async def post_init(app: Application):
        # Tie the kafka consumer to the bot's overarching execution loop
        asyncio.create_task(kafka_consumer_task(app))

    application = Application.builder().token(TOKEN).post_init(post_init).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT | filters.LOCATION | filters.PHOTO, handle_message))
    
    logger.info("Starting Telegram Bot listener...")
    # NOTE: Polling is used for safe local development.
    # In production, swap to application.run_webhook(...)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
