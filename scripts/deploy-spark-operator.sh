#!/bin/bash
set -e

echo "⚡ Deploying Spark Operator..."

# Create service accounts and RBAC
echo "🔐 Setting up service accounts and RBAC..."
kubectl apply -f k8s/spark-operator/service-account.yaml

# Add Spark Operator Helm repository
echo "📦 Adding Spark Operator Helm repository..."
helm repo add spark-operator https://googlecloudplatform.github.io/spark-on-k8s-operator
helm repo update

# Install Spark Operator with custom values
echo "🚀 Installing Spark Operator..."
helm install spark-operator spark-operator/spark-operator \
    --namespace spark-operator \
    --create-namespace \
    --values k8s/spark-operator/spark-operator-values.yaml \
    --set webhook.enable=true \
    --set webhook.port=8080 \
    --set serviceAccounts.spark.name=spark \
    --set serviceAccounts.sparkoperator.name=spark-operator \
    --wait

# Wait for operator to be ready
echo "⏳ Waiting for Spark Operator to be ready..."
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=spark-operator -n spark-operator --timeout=300s

# Verify installation
echo "✅ Spark Operator deployment complete!"
kubectl get pods -n spark-operator
kubectl get crd | grep spark

# Check operator logs
echo "📋 Spark Operator logs:"
kubectl logs -n spark-operator -l app.kubernetes.io/name=spark-operator --tail=20