#!/bin/bash
set -e

echo "=== Installing Prerequisites ==="
# Add Helm repos
helm repo add strimzi https://strimzi.io/charts/
# helm repo add spark-operator https://kubeflow.github.io/spark-operator
helm repo update

# Create namespaces
kubectl create namespace kafka --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace spark --dry-run=client -o yaml | kubectl apply -f -

echo "=== Installing Kafka Operator ==="
helm install kafka-operator strimzi/strimzi-kafka-operator -n kafka

echo "=== Installing Spark Operator ==="
kubectl create serviceaccount spark -n spark --dry-run=client -o yaml | kubectl apply -f -
kubectl create clusterrolebinding spark-role --clusterrole=edit --serviceaccount=spark:spark --dry-run=client -o yaml | kubectl apply -f -

# helm install spark-operator spark-operator/spark-operator -n spark \
  # --set image.tag=v1beta2-1.4.0-hadoop3 \
  # --set sparkJobNamespace=spark

echo "=== Waiting for operators to be ready ==="
kubectl wait --for=condition=Ready pod -l name=strimzi-cluster-operator -n kafka --timeout=300s

echo "Setup complete! Run ./scripts/deploy.sh to deploy the application."