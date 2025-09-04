#!/bin/bash

echo "=== System Status ==="
kubectl get pods -A

echo ""
echo "=== Kafka Resources ==="
kubectl get kafka,kafkatopic -n kafka

echo ""
echo "=== Spark Job Status ==="
kubectl get pods -n spark
kubectl describe pod spark-streaming-job -n spark | grep -A 5 "Conditions:"

echo ""
echo "=== Recent Events ==="
kubectl get events --sort-by=.metadata.creationTimestamp -A | tail -10

echo ""
echo "=== Testing Pipeline ==="
echo "To test the pipeline:"
echo "1. kubectl exec -it kafka-cluster-dual-role-0 -n kafka -- //bin/bash"
echo "2. echo '{\"Restaurantid\": 234, \"Event\": \"map_click\", \"Properties\": {\"timestamp\": \"2025-09-02T23:00:00Z\", \"is_relevant\": true, \"data_array\": [1.0, 2.3, 2.4, 12.0]}}' | /opt/kafka/bin/kafka-console-producer.sh --topic input-topic --bootstrap-server localhost:9092"
echo "3. /opt/kafka/bin/kafka-console-consumer.sh --topic output-topic --from-beginning --bootstrap-server localhost:9092"
