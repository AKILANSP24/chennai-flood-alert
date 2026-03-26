import os
import time
import json
import logging
import schedule
import requests
from bs4 import BeautifulSoup
from confluent_kafka import Producer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reservoir-scraper")

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
producer = Producer({'bootstrap.servers': KAFKA_BROKER})

def scrape_reservoirs():
    logger.info("Scraping reservoir levels...")
    try:
        # Note: In a production scenario, we'll implement the exact HTML 
        # table parser here using bs4 for tamilnadupwd.org or cmwssb.
        # Below is a structural skeleton producing mock/default data format
        # compatible with our Spark processor thresholds.
        
        # r = requests.get("https://...cmwssb.in/lake-levels")
        # soup = BeautifulSoup(r.text, 'html.parser')
        # Parse table...
        
        payload = {
            "timestamp": int(time.time()),
            "reservoirs": {
                "chembarambakkam": {"level_ft": 20.0, "capacity_mcft": 3000}, # Spark looks for > 22ft
                "puzhal": {"level_ft": 15.0, "capacity_mcft": 2500},
                "poondi": {"level_ft": 18.5, "capacity_mcft": 2800},
                "cholavaram": {"level_ft": 12.0, "capacity_mcft": 800}
            }
        }
        
        producer.produce("reservoir-raw", value=json.dumps(payload).encode('utf-8'))
        producer.flush()
        logger.info("Successfully published reservoir data to Kafka 'reservoir-raw'.")
    except Exception as e:
        logger.error(f"Error scraping reservoirs: {e}")

if __name__ == "__main__":
    logger.info("Starting Reservoir Scraper. Running hourly...")
    schedule.every(1).hours.do(scrape_reservoirs)
    
    # Run once at startup
    scrape_reservoirs()
    
    while True:
        schedule.run_pending()
        time.sleep(1)
