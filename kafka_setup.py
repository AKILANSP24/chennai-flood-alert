import os
import time
from confluent_kafka.admin import AdminClient, NewTopic

def wait_for_kafka(broker, retries=10, delay=5):
    from confluent_kafka import Producer
    for i in range(retries):
        try:
            p = Producer({'bootstrap.servers': broker})
            p.list_topics(timeout=5)
            print("Kafka is ready.")
            return
        except Exception:
            print(f"Waiting for Kafka... ({i+1}/{retries})")
            time.sleep(delay)
    raise RuntimeError("Kafka did not become ready in time.")

def create_topics():
    # Use localhost if running from the host machine, otherwise 'kafka:9092'
    broker = os.getenv("KAFKA_BROKER", "localhost:9092")
    wait_for_kafka(broker)
    admin_client = AdminClient({'bootstrap.servers': broker})
    
    topics = [
        "weather-raw", "reservoir-raw", "citizen-raw", 
        "nlp-results", "risk-scores", "alerts", "weather-aggregates"
    ]
    
    new_topics = [NewTopic(topic, num_partitions=1, replication_factor=1) for topic in topics]
    
    fs = admin_client.create_topics(new_topics)
    for topic, f in fs.items():
        try:
            f.result()  # Wait for operation to complete
            print(f"Topic '{topic}' created successfully.")
        except Exception as e:
            # Often hits topic exists exception which is fine
            print(f"Failed to create topic '{topic}': {e}")

if __name__ == "__main__":
    create_topics()
