#!/usr/bin/env python3
"""
Kafka producer script to generate sample events for testing.
"""
import json
import time
import random
from datetime import datetime, timedelta
from kafka import KafkaProducer
import argparse
import sys


def generate_sample_event():
    """Generate a sample restaurant event."""
    now = datetime.utcnow()
    
    # Random timestamp - some in past, some in future
    if random.random() > 0.5:
        # Future event
        event_time = now + timedelta(minutes=random.randint(1, 60))
    else:
        # Past event
        event_time = now - timedelta(minutes=random.randint(1, 60))
    
    event = {
        "Restaurantid": random.randint(100, 999),
        "Event": random.choice(["map_click", "menu_view", "reservation", "review"]),
        "Properties": {
            "timestamp": event_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "is_relevant": random.choice([True, False]),
            "data_array": [
                round(random.uniform(0, 100), 2) 
                for _ in range(random.randint(3, 6))
            ]
        }
    }
    return event


def main():
    parser = argparse.ArgumentParser(description='Kafka event producer')
    parser.add_argument('--bootstrap-servers', default='localhost:9092',
                       help='Kafka bootstrap servers')
    parser.add_argument('--topic', default='restaurant-events',
                       help='Kafka topic to produce to')
    parser.add_argument('--count', type=int, default=100,
                       help='Number of events to generate')
    parser.add_argument('--interval', type=float, default=1.0,
                       help='Interval between events in seconds')
    parser.add_argument('--continuous', action='store_true',
                       help='Run continuously')
    
    args = parser.parse_args()
    
    # Create Kafka producer
    try:
        producer = KafkaProducer(
            bootstrap_servers=args.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda v: str(v).encode('utf-8') if v else None
        )
        print(f"✅ Connected to Kafka at {args.bootstrap_servers}")
    except Exception as e:
        print(f"❌ Failed to connect to Kafka: {e}")
        sys.exit(1)
    
    # Generate and send events
    count = 0
    try:
        while True:
            event = generate_sample_event()
            key = str(event["Restaurantid"])
            
            # Send to Kafka
            future = producer.send(args.topic, key=key, value=event)
            result = future.get(timeout=10)
            
            count += 1
            print(f"📤 Sent event #{count}: Restaurant {event['Restaurantid']}, "
                  f"Event: {event['Event']}, "
                  f"Timestamp: {event['Properties']['timestamp']}")
            
            if not args.continuous and count >= args.count:
                break
            
            time.sleep(args.interval)
    
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        producer.flush()
        producer.close()
        print(f"✅ Sent {count} events total")


if __name__ == "__main__":
    main()