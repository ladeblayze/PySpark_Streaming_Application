#!/bin/bash
set -e

echo "🎯 Deploying Kafka to Kubernetes..."

# Deploy Zookeeper and Kafka
echo "📦 Deploying Zookeeper and Kafka..."
kubectl apply -f k8s/kafka/kafka-deployment.yaml

# Wait for Kafka to be ready
echo "⏳ Waiting for Kafka to be ready..."
kubectl wait --for=condition=Ready pod -l app=zookeeper -n kafka --timeout=300s
kubectl wait --for=condition=Ready pod -l app=kafka -n kafka --timeout=300s

# Create topics
echo "📝 Creating Kafka topics..."
kubectl apply -f k8s/kafka/kafka-topics.yaml

# Wait for topic creation job to complete
echo "⏳ Waiting for topic creation..."
kubectl wait --for=condition=complete job/kafka-topic-creator -n kafka --timeout=120s

# Verify Kafka deployment
echo "✅ Kafka deployment complete!"
kubectl get pods -n kafka
kubectl logs job/kafka-topic-creator -n kafka

# Port forward for local testing (optional)
echo "🔌 To access Kafka locally, run:"
echo "kubectl port-forward -n kafka svc/kafka-service 9092:9092"