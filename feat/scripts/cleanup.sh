#!/bin/bash

# cleanup.sh
# Script to clean up all deployed resources

set -e

echo "🧹 Cleaning up Kubernetes resources..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Kill port forwarding processes
print_status "Stopping port forwarding..."
pkill -f "kubectl port-forward" || true

# Delete Spark application
print_status "Deleting Spark application..."
kubectl delete sparkapplication kafka-spark-streaming --ignore-not-found=true

# Delete Spark Operator
print_status "Uninstalling Spark Operator..."
helm uninstall spark-operator -n spark-operator || true
kubectl delete namespace spark-operator --ignore-not-found=true

# Delete Kafka
print_status "Deleting Kafka resources..."
kubectl delete -f k8s/kafka-setup.yaml --ignore-not-found=true

# Delete RBAC resources
print_status "Deleting RBAC resources..."
kubectl delete -f k8s/spark-operator-rbac.yaml --ignore-not-found=true

# Delete Docker images
print_status "Cleaning up Docker images..."
eval $(minikube docker-env)
docker rmi kafka-spark-streaming:latest || true

print_status "✅ Cleanup completed!"
print_status "To stop minikube completely, run: minikube stop"