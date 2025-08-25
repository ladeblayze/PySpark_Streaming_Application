#!/usr/bin/env python3

import json
import time
import random
from datetime import datetime, timezone, timedelta
from kafka import KafkaProducer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KafkaDataProducer:
    def __init__(self, kafka_servers, topic):
        self.topic = topic
        self.producer = KafkaProducer(
            bootstrap_servers=kafka_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None
        )
        logger.info(f"Kafka producer initialized for servers: {kafka_servers}")
    
    def generate_sample_message(self, restaurant_id=None, event_type=None):
        """Generate a sample restaurant event message."""
        if restaurant_id is None:
            restaurant_id = random.randint(100, 999)
        
        if event_type is None:
            event_type = random.choice([
                "map_click", "menu_view", "reservation_attempt", 
                "phone_call", "website_visit", "review_submit"
            ])
        
        # Generate timestamp (mix of past and future for testing)
        if random.random() < 0.7:  # 70% future timestamps (should pass filter)
            timestamp = datetime.now(timezone.utc) + timedelta(
                minutes=random.randint(1, 60)
            )
        else:  # 30% past timestamps (should be filtered out)
            timestamp = datetime.now(timezone.utc) - timedelta(
                minutes=random.randint(1, 60)
            )
        
        message = {
            "Restaurantid": restaurant_id,
            "Event": event_type,
            "Properties": {
                "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "is_relevant": random.choice([True, False]),
                "data_array": [
                    round(random.uniform(0.1, 20.0), 2) 
                    for _ in range(random.randint(2, 6))
                ]
            }
        }
        return message
    
    def send_message(self, message, key=None):
        """Send a message to Kafka topic."""
        try:
            future = self.producer.send(self.topic, value=message, key=key)
            record_metadata = future.get(timeout=10)
            logger.info(f"Message sent to topic {record_metadata.topic}, "
                       f"partition {record_metadata.partition}, "
                       f"offset {record_metadata.offset}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            return False
    
    def send_batch_messages(self, count=10, delay=1):
        """Send multiple messages with delay."""
        logger.info(f"Sending {count} messages with {delay}s delay...")
        for i in range(count):
            message = self.generate_sample_message()
            key = f"restaurant-{message['Restaurantid']}"
            
            if self.send_message(message, key):
                logger.info(f"Sent message {i+1}/{count}: {message}")
            else:
                logger.error(f"Failed to send message {i+1}/{count}")
            
            if delay > 0 and i < count - 1:
                time.sleep(delay)
        
        logger.info("Batch sending completed")
    
    def send_continuous_messages(self, interval=5):
        """Send messages continuously."""
        logger.info(f"Starting continuous message sending every {interval}s...")
        try:
            while True:
                message = self.generate_sample_message()
                key = f"restaurant-{message['Restaurantid']}"
                
                if self.send_message(message, key):
                    logger.info(f"Sent continuous message: {message}")
                
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("Stopping continuous message sending...")
    
    def close(self):
        """Close the producer."""
        self.producer.close()
        logger.info("Kafka producer closed")

def create_sample_data_file():
    """Create sample data file for reference."""
    sample_messages = []
    producer = KafkaDataProducer("dummy:9092", "dummy")
    
    # Generate sample messages
    for i in range(10):
        message = producer.generate_sample_message()
        sample_messages.append(message)
    
    # Save to file
    with open("sample_data.json", "w") as f:
        json.dump(sample_messages, f, indent=2)
    
    logger.info("Sample data file 'sample_data.json' created")
    return sample_messages

def main():
    """Main function to run data ingestion."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Kafka Data Producer for Restaurant Events")
    parser.add_argument("--kafka-servers", default="localhost:30092", 
                       help="Kafka bootstrap servers")
    parser.add_argument("--topic", default="restaurant-events", 
                       help="Kafka topic name")
    parser.add_argument("--mode", choices=["batch", "continuous", "sample-file"], 
                       default="batch", help="Run mode")
    parser.add_argument("--count", type=int, default=10, 
                       help="Number of messages for batch mode")
    parser.add_argument("--delay", type=int, default=1, 
                       help="Delay between messages in seconds")
    parser.add_argument("--interval", type=int, default=5, 
                       help="Interval for continuous mode in seconds")
    
    args = parser.parse_args()
    
    if args.mode == "sample-file":
        create_sample_data_file()
        return
    
    # Initialize producer
    producer = KafkaDataProducer(args.kafka_servers, args.topic)
    
    try:
        if args.mode == "batch":
            producer.send_batch_messages(args.count, args.delay)
        elif args.mode == "continuous":
            producer.send_continuous_messages(args.interval)
    except Exception as e:
        logger.error(f"Error in data production: {str(e)}")
    finally:
        producer.close()

if __name__ == "__main__":
    main()