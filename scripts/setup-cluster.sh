#!/bin/bash
set -e

echo "🚀 Setting up Kubernetes cluster with Minikube..."

# Check if minikube is installed
if ! command -v minikube &> /dev/null; then
    echo "❌ Minikube is not installed. Please install it first."
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed. Please install it first."
    exit 1
fi

# Check if helm is installed
if ! command -v helm &> /dev/null; then
    echo "❌ Helm is not installed. Please install it first."
    exit 1
fi

# Start minikube with sufficient resources
echo "📦 Starting Minikube cluster..."
minikube start \
    --cpus=4 \
    --memory=6500 \
    --kubernetes-version=v1.28.0 \
    --driver=docker

# Enable necessary addons
echo "🔧 Enabling Minikube addons..."
minikube addons enable metrics-server
minikube addons enable dashboard

# Wait for cluster to be ready
echo "⏳ Waiting for cluster to be ready..."
kubectl wait --for=condition=Ready nodes --all --timeout=300s

# Create namespaces
echo "📁 Creating namespaces..."
kubectl apply -f k8s/namespace.yaml

# Verify setup
echo "✅ Cluster setup complete!"
kubectl cluster-info
kubectl get nodes
kubectl get ns

echo "📊 You can access the dashboard with: minikube dashboard"