#!/bin/bash
set -e

echo "🏗️ Building and deploying Spark application..."

# Build Docker image
echo "🐳 Building Docker image..."
docker build -t spark-streaming:latest -f docker/Dockerfile .

# Load image into Minikube
echo "📦 Loading image into Minikube..."
minikube image load spark-streaming:latest

# Create ConfigMap in DEFAULT namespace
echo "⚙️ Creating ConfigMap..."
kubectl apply -f k8s/spark-app/configmap.yaml -n default

# Deploy SparkApplication to DEFAULT namespace (and remove jars.packages)
echo "🚀 Deploying SparkApplication..."
sed 's/namespace: spark/namespace: default/g' k8s/spark-app/spark-application.yaml | \
  sed '/spark.jars.packages/d' | \
  kubectl apply -f -

# Wait for application to start
echo "⏳ Waiting for SparkApplication to start..."
sleep 10

# Check application status in DEFAULT namespace
echo "📊 Checking application status..."
kubectl get sparkapplication -n default
kubectl describe sparkapplication spark-streaming-processor -n default

# Get driver pod logs from DEFAULT namespace
echo "📋 Driver pod logs:"
DRIVER_POD=$(kubectl get pods -n default -l spark-role=driver -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [ -n "$DRIVER_POD" ]; then
    kubectl logs -n default $DRIVER_POD --tail=50
else
    echo "Driver pod not yet available. Check back in a moment."
fi

echo "✅ Application deployment complete!"
echo "🔍 Monitor the application with:"
echo "kubectl logs -n default -l spark-role=driver -f"