from kafka import KafkaProducer
import json
import time
from datetime import datetime, timezone

def create_sample_message():
    return {
        "Restaurantid": 234,
        "Event": "map_click",
        "Properties": {
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "is_relevant": True,
            "data_array": [1.0, 2.3, 2.4, 12.0]
        }
    }

def main():
    producer = KafkaProducer(
        bootstrap_servers=['localhost:9093'],  # Changed from 9092 to 9093
        value_serializer=lambda x: json.dumps(x).encode('utf-8'),
        acks=1,
        request_timeout_ms=30000,
        metadata_max_age_ms=30000,
        retry_backoff_ms=1000,
        max_block_ms=30000
    )
    
    print("Starting to send messages...")
    for i in range(5):
        message = create_sample_message()
        try:
            future = producer.send('input-topic', message)
            record_metadata = future.get(timeout=30)
            print(f"Sent message {i+1}: {message}")
            print(f"  -> Offset: {record_metadata.offset}")
        except Exception as e:
            print(f"Failed to send message {i+1}: {e}")
        time.sleep(2)
    
    producer.flush()
    producer.close()
    print("Finished!")

if __name__ == "__main__":
    main()