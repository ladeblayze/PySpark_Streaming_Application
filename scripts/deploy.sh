#!/bin/bash
set -e

echo "Starting deployment..."

# Deploy Kafka (if not already running)
kubectl apply -f kubernetes/kafka-cluster.yaml

# Check if Kafka is already ready or wait for it
echo "Checking Kafka status..."
if kubectl get kafka kafka-cluster -n kafka >/dev/null 2>&1; then
    echo "Kafka cluster exists, checking if ready..."
    # Give it a shorter timeout since it might already be ready
    kubectl wait kafka/kafka-cluster --for=condition=Ready --timeout=60s -n kafka || {
        echo "Kafka not ready yet, but continuing..."
    }
else
    echo "Waiting for Kafka to be created and ready..."
    kubectl wait kafka/kafka-cluster --for=condition=Ready --timeout=600s -n kafka
fi

# Create topics
echo "Creating Kafka topics..."
kubectl apply -f kubernetes/kafka-topics.yaml
kubectl wait --for=condition=Ready kafkatopic/input-topic -n kafka --timeout=120s
kubectl wait --for=condition=Ready kafkatopic/output-topic -n kafka --timeout=120s

# Create Spark namespace and permissions
echo "Setting up Spark namespace..."
kubectl create namespace spark --dry-run=client -o yaml | kubectl apply -f -

echo "Creating Spark service account..."
kubectl create serviceaccount spark -n spark --dry-run=client -o yaml | kubectl apply -f -

echo "Creating Spark RBAC permissions..."
kubectl create clusterrolebinding spark-cluster-role --clusterrole=edit --serviceaccount=spark:spark --dry-run=client -o yaml | kubectl apply -f -

# Verify setup
echo "Verifying Spark setup..."
kubectl get serviceaccount -n spark
kubectl get clusterrolebinding spark-cluster-role

# Build and submit Spark job
echo "Building Docker image..."
docker build -t spark-kafka-streaming:latest .
minikube image load spark-kafka-streaming:latest

echo "Submitting Spark job..."
kubectl delete pod spark-streaming-job -n spark --ignore-not-found=true

# Create Spark job
kubectl apply -f kubernetes/spark-job.yaml

echo "Deployment complete!"
echo "Check job status with: kubectl logs -f spark-streaming-job -n spark"
echo "Check all resources with: kubectl get all -n spark"