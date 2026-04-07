import os
import json
import logging
import asyncio
from fastapi import FastAPI # type: ignore
from contextlib import asynccontextmanager
from confluent_kafka import Consumer, Producer # type: ignore

from classifier import is_flood_related # type: ignore
from ollama_client import extract_structured_data # type: ignore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nlp-service")

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")

# Load compiled Tanglish lexicon
LEXICON_PATH = os.path.join(os.path.dirname(__file__), "tanglish_lexicon.json")
try:
    with open(LEXICON_PATH, 'r') as f:
        lexicon = json.load(f)
except Exception as e:
    logger.error(f"Failed to load lexicon: {e}")
    lexicon = {}

producer = Producer({'bootstrap.servers': KAFKA_BROKER})

def normalize_tanglish(text: str) -> str:
    words = text.split()
    normalized = []
    for w in words:
        # Simplistic dictionary replacement lookup for the base prototype
        lower_w = w.lower().strip()
        normalized.append(lexicon.get(lower_w, w))
    return " ".join(normalized)

def get_nearest_zone(lat: float, lon: float) -> str:
    """Map GPS coordinates to nearest Chennai flood zone."""
    zones = [
        ("Velachery", 12.9815, 80.2180),
        ("Tambaram", 12.9249, 80.1000),
        ("Adyar", 13.0067, 80.2510),
        ("Saidapet", 13.0201, 80.2201),
        ("Mudichur", 12.9100, 80.0700),
        ("Porur", 13.0359, 80.1560),
        ("Perambur", 13.1167, 80.2334),
        ("T Nagar", 13.0418, 80.2341),
        ("Anna Nagar", 13.0850, 80.2101),
        ("Chrompet", 12.9516, 80.1462),
        ("Neelankari", 12.8434, 80.1561),
        ("Tambaram", 12.9249, 80.1000),
    ]
    
    # Find nearest zone using simple distance calculation
    nearest = "Chennai"
    min_dist = float("inf")
    
    for zone_name, zone_lat, zone_lon in zones:
        dist = ((lat - zone_lat) ** 2 + (lon - zone_lon) ** 2) ** 0.5
        if dist < min_dist:
            min_dist = dist
            nearest = zone_name
    
    return f"{nearest} (GPS verified)"

def process_message(msg_value):
    try:
        data = json.loads(msg_value)
        raw_text = data.get("text", "")
        if not raw_text:
            return
            
        logger.info(f"Processing incident report: {raw_text}")
        
        # 1. NLP Pre-process / Normalize
        normalized_text = normalize_tanglish(raw_text)
        
        # 2. Fast Binary Context Filter (Using XLM-RoBERTa wrapper logic)
        if not is_flood_related(normalized_text):
            logger.info("Message classified as non-emergency noise. Dropping segment.")
            return
            
        # 3. Intelligent Execution (Ollama Extraction)
        extracted = extract_structured_data(normalized_text)
        logger.info(f"Ollama extracted payload: {extracted}")
        
        # 4. Synthesize Pipeline Augmentations into primary Event JSON
        data["nlp_event"] = extracted.get("event")
        data["nlp_severity"] = extracted.get("severity")
        data["nlp_water_depth_cm"] = extracted.get("water_depth_cm")
        data["nlp_location_desc"] = extracted.get("location_desc")
        
        # 5. Egress normalized & enriched document payload back to Kafka
        
        # If location is just coordinates, make it readable
        location = data.get("nlp_location_desc") or ""
        if "coordinates" in location.lower() or "gps" in location.lower():
            lat = data.get("lat")
            lon = data.get("lon")
            if lat and lon:
                # Map coordinates to nearest known Chennai zone
                data["nlp_location_desc"] = get_nearest_zone(float(lat), float(lon))

        producer.produce("risk-scores", value=json.dumps(data).encode('utf-8'))
        producer.poll(0)
        
    except Exception as e:
        logger.error(f"Error executing Kafka text processor routing: {e}")

async def kafka_consumer_loop():
    consumer = Consumer({
        'bootstrap.servers': KAFKA_BROKER,
        'group.id': 'nlp-service-group',
        'auto.offset.reset': 'latest'
    })
    # Subscribed to citizen-raw reports relayed implicitly by the PySpark logic upstream
    consumer.subscribe(['citizen-raw'])
    
    logger.info("Started FastAPI backend listener on Kafka 'nlp-results'...")
    try:
        while True:
            msg = await asyncio.to_thread(consumer.poll, 1.0) # Non-blocking poll via threadpool
            if msg is None:
                await asyncio.sleep(0.1)
                continue
            if msg.error(): # type: ignore
                logger.error(f"Kafka consumer transport error: {msg.error()}") # type: ignore
                continue
            
            # Offload synchronous ML blocking execution to avoid blocking FastAPI
            await asyncio.to_thread(process_message, msg.value().decode('utf-8')) # type: ignore
    finally:
        consumer.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup Lifecyle Event binding
    task = asyncio.create_task(kafka_consumer_loop())
    yield
    # Shutdown Lifecyle Event cleanup
    task.cancel()
    producer.flush()

app = FastAPI(lifespan=lifespan)

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "nlp-engine"}
