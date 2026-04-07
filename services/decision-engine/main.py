import os
import json
import time
import logging
import urllib.request
import urllib.parse
import csv
import datetime
from confluent_kafka import Consumer, Producer  # type: ignore
import redis  # type: ignore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("decision-engine")

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

# ── Redis connection ──────────────────────────────────────────────────────────
try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    r.ping()
    logger.info("Decision Engine successfully connected to Redis cache.")
except Exception as e:
    logger.warning(f"Failed to connect to Redis. State aggregation will be disabled: {e}")
    r = None

producer = Producer({'bootstrap.servers': KAFKA_BROKER})


# ── Get all alert numbers (static .env + dynamic Redis registrations) ─────────
def get_all_alert_numbers() -> str:
    static = os.getenv("ALERT_PHONE_NUMBERS", "")
    dynamic = []
    if r:
        try:
            dynamic = list(r.smembers("registered_numbers"))
        except Exception:
            dynamic = []
    all_numbers = set()
    if static:
        all_numbers.update(n.strip() for n in static.split(",") if n.strip())
    all_numbers.update(n.strip() for n in dynamic if n.strip())
    result = ",".join(all_numbers)
    logger.info(f"Alert numbers — static: {bool(static)} | dynamic registered: {len(dynamic)} | total: {len(all_numbers)}")
    return result


# ── SMS alert via Fast2SMS ────────────────────────────────────────────────────
def send_sms_alert(location: str, urgency: str, depth: int):
    api_key = os.getenv("FAST2SMS_API_KEY", "")
    numbers = get_all_alert_numbers()

    if not api_key:
        logger.warning("SMS skipped — FAST2SMS_API_KEY not set in .env")
        return

    if not numbers:
        logger.warning("SMS skipped — no registered numbers found")
        return

    message = (
        f"FLOOD {urgency} ALERT - {location}. "
        f"Water depth: {depth}cm. "
        f"Evacuate immediately. Chennai Flood Alert System."
    )

    try:
        params = urllib.parse.urlencode({
            "authorization": api_key,
            "message": message,
            "language": "english",
            "route": "q",
            "numbers": numbers
        })
        url = f"https://www.fast2sms.com/dev/bulkV2?{params}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            if result.get("return"):
                logger.info(f"SMS sent — {urgency} alert for {location} to {len(numbers.split(','))} number(s)")
            else:
                logger.error(f"SMS API returned failure: {result}")
    except Exception as e:
        logger.error(f"SMS dispatch error: {e}")


# ── RAG enrichment ────────────────────────────────────────────────────────────
def enrich_with_rag(location: str, depth: int) -> dict:
    try:
        payload = json.dumps({
            "location": location,
            "depth_cm": depth
        }).encode()
        req = urllib.request.Request(
            "http://ragservice:8100/enrich",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read())
            logger.info(
                f"RAG enriched — shelter: {result.get('rag_shelter')} | "
                f"NDRF: {result.get('rag_ndrf_unit')}"
            )
            return result
    except Exception as e:
        logger.warning(f"RAG enrichment failed, continuing without: {e}")
        return {}


# ── Core alert logic ──────────────────────────────────────────────────────────
def process_risk_score(msg_value: str):
    try:
        data = json.loads(msg_value)
        event = data.get("nlp_event")
        severity = data.get("nlp_severity")
        location = data.get("nlp_location_desc") or "unknown"

        if event == "none" or severity == "low":
            return

        loc_key = f"reports:{location.lower().strip()}"
        report_count = 1
        current_time = int(time.time())

        if r:
            r.zremrangebyscore(loc_key, 0, current_time - 600)
            r.zadd(loc_key, {f"{current_time}_{id(data)}": current_time})
            report_count = r.zcard(loc_key)
            r.expire(loc_key, 600)

        logger.info(
            f"Location: {location} | Severity: {severity} | "
            f"Report density: {report_count}"
        )

        depth_val = 0
        raw_depth = data.get("nlp_water_depth_cm")
        if raw_depth is not None:
            try:
                depth_val = int(float(raw_depth))
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not parse water depth '{raw_depth}': {e}")
                depth_val = 0

        is_critical = severity in ["critical", "high", "emergency"]

        if depth_val > 50 or (is_critical and report_count >= 3):
            alert_urgency = (
                "RED" if depth_val > 50 or severity == "critical" else "ORANGE"
            )
            logger.info(f"🚨 TRIGGERING {alert_urgency} ALERT FOR {location} 🚨")

            # Write to CSV for R analytics
            try:
                log_file = "/data/alerts_log.csv"
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
                with open(log_file, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        datetime.datetime.now().isoformat(),
                        location, severity, depth_val, report_count
                    ])
            except Exception as log_e:
                logger.error(f"Failed to write alerts CSV: {log_e}")

            # RAG enrichment
            rag_data = enrich_with_rag(location, depth_val)

            alert_payload = {
                "alert_id": f"ALRT-{current_time}-{location[:3].upper()}",
                "location": location,
                "urgency": alert_urgency,
                "condition": event,
                "water_depth_cm": depth_val,
                "report_density": report_count,
                "nearest_shelter": rag_data.get("rag_shelter", "Nearest elevated building"),
                "ndrf_unit": rag_data.get("rag_ndrf_unit", "Chennai NDRF"),
                "timestamp": current_time,
                "source": "decision-engine"
            }

            producer.produce(
                "final-alerts",
                value=json.dumps(alert_payload).encode('utf-8')
            )
            producer.flush(timeout=5)

            # SMS to all registered numbers
            send_sms_alert(location, alert_urgency, depth_val)

    except Exception as e:
        logger.error(f"Error in rule evaluation: {e}")


# ── Kafka consumer with retry ─────────────────────────────────────────────────
def create_consumer_with_retry(config, retries=10, delay=5):
    for attempt in range(retries):
        try:
            consumer = Consumer(config)
            logger.info("Kafka consumer connected successfully.")
            return consumer
        except Exception as e:
            logger.warning(
                f"Kafka not ready (attempt {attempt+1}/{retries}), "
                f"retrying in {delay}s... {e}"
            )
            time.sleep(delay)
    raise RuntimeError("Could not connect to Kafka after multiple retries.")


def main():
    consumer = create_consumer_with_retry({
        'bootstrap.servers': KAFKA_BROKER,
        'group.id': 'decision-engine-group',
        'auto.offset.reset': 'latest'
    })

    consumer.subscribe(['risk-scores'])
    logger.info("Decision engine live. Listening to 'risk-scores'...")

    try:
        while True:
            msg = consumer.poll(1.0)  # type: ignore
            if msg is None:
                continue
            if msg.error():  # type: ignore
                logger.error(f"Kafka consumer error: {msg.error()}")  # type: ignore
                continue
            process_risk_score(msg.value().decode('utf-8'))  # type: ignore
    except KeyboardInterrupt:
        logger.info("Shutting down Decision Engine...")
    finally:
        consumer.close()
        producer.flush()


if __name__ == "__main__":
    main()