import os
import json
import time
import logging
from confluent_kafka import Consumer, Producer # type: ignore
import redis # type: ignore
import csv
import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("decision-engine")

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

# Connect to Redis
try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    r.ping()
    logger.info("Decision Engine successfully connected to Redis cache.")
except Exception as e:
    logger.warning(f"Failed to connect to Redis. State aggregation will be disabled: {e}")
    r = None

producer = Producer({'bootstrap.servers': KAFKA_BROKER})

def process_risk_score(msg_value: str):
    """
    Process incoming risk-scores from the NLP pipeline.
    Validates rules and dispatches actionable alerts to final-alerts topic.
    """
    try:
        data = json.loads(msg_value)
        event = data.get("nlp_event")
        severity = data.get("nlp_severity")
        location = data.get("nlp_location_desc") or "unknown"
        
        # Don't alert on non-events
        if event == "none" or severity == "low":
            return
            
        loc_key = f"reports:{location.lower().strip()}"
        report_count = 1
        current_time = int(time.time())
        
        if r:
            # 1. Clear old reports (sliding window of 10 minutes)
            r.zremrangebyscore(loc_key, 0, current_time - 600)
            
            # 2. Register current report
            r.zadd(loc_key, {f"{current_time}_{id(data)}": current_time})
            
            # 3. Retrieve active report concentration density
            report_count = r.zcard(loc_key)
            r.expire(loc_key, 600)
            
        logger.info(f"Location {location} => Severity: {severity}, Recent Report Density: {report_count}")
        
        # Read absolute water depth from extract
        depth_val = 0
        raw_depth = data.get("nlp_water_depth_cm")
        if raw_depth is not None:
            try:
                depth_val = int(float(raw_depth))  # handles "65.0" strings too
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not parse water depth '{raw_depth}': {e}")
                depth_val = 0
                
        # --- BUSINESS LOGIC RULES FOR DISASTER ALERT ---
        is_critical = severity in ["critical", "high"]
        # Rule 1: Depth > 50cm is an immediate red alert regardless of report density
        # Rule 2: Critical/High severity reports are validated if 3+ reports emerge from the same location in 10 mins
        
        if depth_val > 50 or (is_critical and report_count >= 3):
            alert_urgency = "RED" if depth_val > 50 or severity == "critical" else "ORANGE"
            logger.info(f"🚨 TRIGGERING {alert_urgency} ALERT FOR {location} 🚨")
            
            # Log to CSV for R Analytics
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
                logger.error(f"Failed to write to alerts CSV: {log_e}")
            
            alert_payload = {
                "alert_id": f"ALRT-{current_time}-{location[:3].upper()}",
                "location": location,
                "urgency": alert_urgency,
                "condition": event,
                "water_depth_cm": depth_val,
                "report_density": report_count,
                "timestamp": current_time,
                "source": "decision-engine"
            }
            producer.produce("final-alerts", value=json.dumps(alert_payload).encode('utf-8'))
            producer.poll(0)
            producer.flush(timeout=5)  # waits up to 5 seconds for delivery confirmation
            
    except Exception as e:
        logger.error(f"Error executing rule thresholds: {e}")

def create_consumer_with_retry(config, retries=10, delay=5):
    for attempt in range(retries):
        try:
            consumer = Consumer(config)
            logger.info("Kafka consumer connected successfully.")
            return consumer
        except Exception as e:
            logger.warning(f"Kafka not ready (attempt {attempt+1}/{retries}), retrying in {delay}s...")
            time.sleep(delay)
    raise RuntimeError("Could not connect to Kafka after multiple retries.")

def main():
    consumer = create_consumer_with_retry({
        'bootstrap.servers': KAFKA_BROKER,
        'group.id': 'decision-engine-group',
        'auto.offset.reset': 'latest'
    })
    
    # Subscribing to the enriched topic from the NLP Service
    consumer.subscribe(['risk-scores'])
    logger.info("Decision engine live. Listening to 'risk-scores'...")
    
    try:
        while True:
            msg = consumer.poll(1.0) # type: ignore
            if msg is None:
                continue
            if msg.error(): # type: ignore
                logger.error(f"Kafka consumer error: {msg.error()}") # type: ignore
                continue
                
            process_risk_score(msg.value().decode('utf-8')) # type: ignore
    except KeyboardInterrupt:
        logger.info("Shutting down Decision Engine...")
    finally:
        consumer.close()
        producer.flush()

if __name__ == "__main__":
    main()
