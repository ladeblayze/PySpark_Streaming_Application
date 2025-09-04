#!/bin/bash
set -e

echo "🔍 Verifying deployment..."

# Function to check component status
check_component() {
    local namespace=$1
    local label=$2
    local component=$3
    
    echo "Checking $component..."
    if kubectl get pods -n $namespace -l $label 2>/dev/null | grep -q Running; then
        echo "✅ $component is running"
        return 0
    else
        echo "❌ $component is not running"
        return 1
    fi
}

# Check Kafka
echo "📊 Kafka Status:"
kubectl get pods -n kafka
check_component "kafka" "app=kafka" "Kafka"
check_component "kafka" "app=zookeeper" "Zookeeper"

# Check Spark Operator
echo -e "\n⚡ Spark Operator Status:"
kubectl get pods -n spark-operator
check_component "spark-operator" "app.kubernetes.io/name=spark-operator" "Spark Operator"

# Check Spark Application
echo -e "\n🚀 Spark Application Status:"
kubectl get sparkapplication -n spark
kubectl get pods -n spark

# Test Kafka connectivity
echo -e "\n🔌 Testing Kafka connectivity..."
kubectl run kafka-test --image=confluentinc/cp-kafka:7.5.0 --rm -it --restart=Never -n kafka -- \
    kafka-topics --list --bootstrap-server kafka-service.kafka.svc.cluster.local:9092 || true

# Check driver logs
echo -e "\n📋 Recent driver logs:"
DRIVER_POD=$(kubectl get pods -n spark -l spark-role=driver -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [ -n "$DRIVER_POD" ]; then
    kubectl logs -n spark $DRIVER_POD --tail=20
fi

# Port forwarding information
echo -e "\n🔗 Port forwarding commands for local testing:"
echo "Kafka: kubectl port-forward -n kafka svc/kafka-service 9092:9092"
echo "Spark UI: kubectl port-forward -n spark \$(kubectl get pods -n spark -l spark-role=driver -o jsonpath='{.items[0].metadata.name}') 4040:4040"

echo -e "\n✅ Verification complete!"