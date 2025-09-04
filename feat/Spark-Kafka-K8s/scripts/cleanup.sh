#!/bin/bash

echo "=== Cleaning up applications ==="
kubectl delete pod spark-streaming-job -n spark --ignore-not-found=true
kubectl delete kafkatopic input-topic output-topic -n kafka --ignore-not-found=true
kubectl delete kafka kafka-cluster -n kafka --ignore-not-found=true

echo "=== Uninstalling operators ==="
helm uninstall kafka-operator -n kafka --ignore-not-found=true

echo "=== Removing namespaces ==="
kubectl delete namespace spark --ignore-not-found=true
kubectl delete namespace kafka --ignore-not-found=true

echo "Cleanup complete!"
