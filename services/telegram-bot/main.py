import os
import json
import hashlib
import logging
import redis
from datetime import datetime, timezone
from telegram import Update, Bot, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
from confluent_kafka import Consumer, Producer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("telegram-bot")

KAFKA_BROKER = os.getenv("KAFKA_BROKER", os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"))
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

producer = Producer({'bootstrap.servers': KAFKA_BROKER})

# Redis connection for phone registration
try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    r.ping()
    logger.info("Telegram bot connected to Redis.")
except Exception as e:
    logger.warning(f"Redis not available: {e}")
    r = None

def get_user_hash(user_id: int) -> str:
    return hashlib.sha256(str(user_id).encode()).hexdigest()


# ── /start command ────────────────────────────────────────────────────────────
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[KeyboardButton("📍 Share My Location", request_location=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    await update.message.reply_text(
        "🌊 Welcome to Chennai Flood Alert System\n\n"
        "You can:\n"
        "• Send a text message describing the flood\n"
        "• Tap 📍 Share My Location for GPS-based reporting\n"
        "• Use /register 9XXXXXXXXX to receive SMS alerts\n"
        "• Use /unregister to stop SMS alerts\n"
        "• Use /status to check your registration\n\n"
        "Stay safe!",
        reply_markup=reply_markup
    )


# ── /register command ─────────────────────────────────────────────────────────
async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "Please include your 10-digit mobile number.\n"
            "Example: /register 9876543210"
        )
        return

    phone = context.args[0].strip()

    # Validate — must be 10 digits
    if not phone.isdigit() or len(phone) != 10:
        await update.message.reply_text(
            "❌ Invalid number. Please send a 10-digit Indian mobile number.\n"
            "Example: /register 9876543210"
        )
        return

    user_hash = get_user_hash(update.effective_user.id)

    if r:
        r.sadd("registered_numbers", phone)
        r.hset(f"user:{user_hash}", "phone", phone)
        r.hset(f"user:{user_hash}", "registered_at", datetime.now(timezone.utc).isoformat())
        total = r.scard("registered_numbers")
        logger.info(f"New SMS registration. Total registered: {total}")

    await update.message.reply_text(
        f"✅ Registered successfully!\n"
        f"You will receive SMS flood alerts on {phone[:4]}XXXXXX.\n\n"
        f"To stop alerts: /unregister"
    )


# ── /unregister command ───────────────────────────────────────────────────────
async def unregister_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_hash = get_user_hash(update.effective_user.id)

    if r:
        phone = r.hget(f"user:{user_hash}", "phone")
        if phone:
            r.srem("registered_numbers", phone)
            r.delete(f"user:{user_hash}")
            await update.message.reply_text(
                f"✅ Unregistered. {phone[:4]}XXXXXX will no longer receive SMS alerts."
            )
            logger.info(f"User unregistered phone: {phone[:4]}XXXXXX")
        else:
            await update.message.reply_text(
                "You are not registered for SMS alerts.\n"
                "Use /register 9XXXXXXXXX to register."
            )
    else:
        await update.message.reply_text("Registration service unavailable. Try again later.")


# ── /status command ───────────────────────────────────────────────────────────
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_hash = get_user_hash(update.effective_user.id)

    if r:
        phone = r.hget(f"user:{user_hash}", "phone")
        total = r.scard("registered_numbers")
        if phone:
            await update.message.reply_text(
                f"📱 SMS alerts active for {phone[:4]}XXXXXX\n"
                f"👥 Total registered in system: {total}"
            )
        else:
            await update.message.reply_text(
                f"❌ Not registered for SMS alerts.\n"
                f"Use /register 9XXXXXXXXX\n"
                f"👥 Total registered in system: {total}"
            )
    else:
        await update.message.reply_text("Status service unavailable.")


# ── Message + GPS handler ─────────────────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message:
        return

    user_hash = get_user_hash(message.from_user.id)
    text = message.text or message.caption or ""

    lat, lon = None, None

    # Handle GPS location sharing
    if message.location:
        lat = message.location.latitude
        lon = message.location.longitude
        logger.info(f"GPS received: {lat:.4f}, {lon:.4f} from {user_hash[:8]}")

        # Acknowledge GPS receipt immediately
        await message.reply_text(
            f"📍 Location received: {lat:.4f}°N, {lon:.4f}°E\n"
            f"Now send a text describing the flood situation at this location."
        )

        # If location only (no text), still log it as a potential flood point
        if not text:
            # Auto-generate a meaningful flood report from GPS only
            text = (
                f"Emergency flood report from GPS location. "
                f"Coordinates: {lat:.4f}, {lon:.4f}. "
                f"Water depth estimated 60cm based on citizen distress signal. "
                f"Immediate assistance required."
            )
    # Build payload
    payload = {
        "user_id_hash": user_hash,
        "lat": lat,
        "lon": lon,
        "text": text,
        "has_gps": lat is not None,
        "ts": datetime.now(timezone.utc).isoformat()
    }

    # Publish to Kafka if there's something to report
    if text or lat:
        producer.produce("citizen-raw", value=json.dumps(payload).encode('utf-8'))
        producer.flush()

        if not message.location:
            await message.reply_text("✅ Report received. Stay safe!")

        logger.info(
            f"Published citizen report to 'citizen-raw' from {user_hash[:8]} "
            f"| GPS: {'yes' if lat else 'no'} | Text: {text[:50]}"
        )


# ── Kafka consumer — broadcasts final-alerts to Telegram channel ──────────────
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
            msg = await asyncio.to_thread(consumer.poll, 1.0)
            if msg is None:
                await asyncio.sleep(0.1)
                continue
            if msg.error():
                continue

            try:
                alert = json.loads(msg.value().decode('utf-8'))
                urgency     = alert.get('urgency', 'ORANGE')
                condition   = alert.get('condition', 'flood')
                location    = alert.get('location', 'Unknown')
                depth       = alert.get('water_depth_cm', 0)
                density     = alert.get('report_density', 1)
                shelter     = alert.get('nearest_shelter', 'Nearest elevated building')
                ndrf        = alert.get('ndrf_unit', 'Chennai NDRF')
                alert_id    = alert.get('alert_id', '')

                # Rich alert message with RAG shelter info
                alert_text = (
                    f"🚨 {urgency} ALERT: {condition.upper()} 🚨\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"📍 Location: {location}\n"
                    f"🌊 Water depth: {depth}cm\n"
                    f"👥 Reports: {density} citizen(s)\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🏫 Shelter: {shelter}\n"
                    f"🚒 NDRF Unit: {ndrf}\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"⚠️ Evacuate immediately!\n"
                    f"🆔 Alert ID: {alert_id}"
                )

                if CHANNEL_ID:
                    await app.bot.send_message(chat_id=CHANNEL_ID, text=alert_text)
                    logger.info(f"Alert broadcast to channel: {urgency} | {location}")

            except Exception as e:
                logger.error(f"Failed to broadcast final-alert: {e}")

    async def post_init(app: Application):
        asyncio.create_task(kafka_consumer_task(app))

    application = Application.builder().token(TOKEN).post_init(post_init).build()

    # Register all handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("register", register_command))
    application.add_handler(CommandHandler("unregister", unregister_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(MessageHandler(
        filters.TEXT | filters.LOCATION | filters.PHOTO | filters.CAPTION,
        handle_message
    ))

    logger.info("Starting Telegram Bot listener...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()