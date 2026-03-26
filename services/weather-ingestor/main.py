import os
import time
import json
import logging
import schedule
import requests
from confluent_kafka import Producer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("weather-ingestor")

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
LAT = "13.0827"
LON = "80.2707"

producer = Producer({'bootstrap.servers': KAFKA_BROKER})

def fetch_weather():
    if not API_KEY or API_KEY == "your_key_here":
        logger.warning("OPENWEATHERMAP_API_KEY is not valid. Skipping API request.")
        return

    url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Structure payload for Spark integration
        payload = {
            "source": "openweathermap",
            "lat": float(LAT),
            "lon": float(LON),
            "temp_c": data.get("main", {}).get("temp"),
            "humidity": data.get("main", {}).get("humidity"),
            "rain_1h_mm": data.get("rain", {}).get("1h", 0.0),
            "rain_3h_mm": data.get("rain", {}).get("3h", 0.0),
            "timestamp": int(time.time()),
            "raw": data
        }
        
        producer.produce("weather-raw", value=json.dumps(payload).encode('utf-8'))
        producer.flush()
        logger.info("Successfully published OpenWeatherMap data to Kafka 'weather-raw'.")
    except Exception as e:
        logger.error(f"Error fetching weather: {e}")

if __name__ == "__main__":
    logger.info("Starting Weather Ingestor. Polling every 5 minutes...")
    # Poll every 5 minutes
    schedule.every(5).minutes.do(fetch_weather)
    
    # Run once at startup
    fetch_weather()
    
    while True:
        schedule.run_pending()
        time.sleep(1)
