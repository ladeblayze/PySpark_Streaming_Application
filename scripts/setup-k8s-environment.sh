#!/bin/bash

# setup-k8s-environment.sh
# Script to set up the complete Kubernetes environment

set -e

echo "🚀 Setting up Kubernetes environment for Spark Streaming with Kafka"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if minikube is running
check_minikube() {
    print_status "Checking minikube status..."
    if ! minikube status &>/dev/null; then
        print_warning "Minikube not running. Starting minikube..."
        minikube start --driver=docker --memory=6000 --cpus=4
        
        # Enable addons
        minikube addons enable ingress
        minikube addons enable dashboard
    else
        print_status "Minikube is already running"
    fi
}

# Function to build Docker image
build_docker_image() {
    print_status "Building Docker image..."
    
    # Set docker environment to use minikube's docker daemon
    eval $(minikube docker-env)
    
    # Build the image
    docker build -t kafka-spark-streaming:latest .
    
    print_status "Docker image built successfully"
}

# Function to deploy Kafka
deploy_kafka() {
    print_status "Deploying Kafka cluster..."
    
    kubectl apply -f k8s/kafka-setup.yaml
    
    print_status "Waiting for Kafka to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/zookeeper -n kafka
    kubectl wait --for=condition=available --timeout=300s deployment/kafka-broker -n kafka
    
    print_status "Kafka cluster deployed successfully"
}

# Function to install Spark Operator
install_spark_operator() {
    print_status "Installing Spark Operator..."
    
    # Apply RBAC
    kubectl apply -f k8s/spark-operator-rbac.yaml
    
    # Install spark operator using helm
    if ! helm repo list | grep -q spark-operator; then
        helm repo add spark-operator https://googlecloudplatform.github.io/spark-on-k8s-operator
    fi
    
    helm repo update
    
    # Install or upgrade spark operator
    helm upgrade --install spark-operator spark-operator/spark-operator \
        --namespace spark-operator \
        --create-namespace \
        --set sparkJobNamespace=default \
        --set enableWebhook=true \
        --set enableBatchScheduler=true
    
    print_status "Waiting for Spark Operator to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/spark-operator -n spark-operator
    
    print_status "Spark Operator installed successfully"
}

# Function to create topics
create_kafka_topics() {
    print_status "Creating Kafka topics..."
    
    # Wait for Kafka to be fully ready
    sleep 30
    
    # Create topics using kubectl exec
    kubectl exec -n kafka deployment/kafka-broker -- kafka-topics --create \
        --bootstrap-server localhost:9092 \
        --topic restaurant-events \
        --partitions 3 \
        --replication-factor 1 \
        --if-not-exists
    
    kubectl exec -n kafka deployment/kafka-broker -- kafka-topics --create \
        --bootstrap-server localhost:9092 \
        --topic processed-events \
        --partitions 3 \
        --replication-factor 1 \
        --if-not-exists
    
    print_status "Kafka topics created successfully"
}

# Function to deploy Spark application
deploy_spark_app() {
    print_status "Deploying Spark application..."
    
    kubectl apply -f k8s/spark-application.yaml
    
    print_status "Spark application deployed successfully"
}

# Function to setup port forwarding
setup_port_forwarding() {
    print_status "Setting up port forwarding..."
    
    # Kill any existing port forwards
    pkill -f "kubectl port-forward" || true
    
    # Port forward Kafka (run in background)
    kubectl port-forward -n kafka service/kafka-service 30092:9093 &
    
    print_status "Port forwarding setup complete"
    print_status "Kafka accessible at localhost:30092"
}

# Main execution
main() {
    print_status "Starting deployment process..."
    
    # Check prerequisites
    if ! command -v minikube &> /dev/null; then
        print_error "minikube not found. Please install minikube first."
        exit 1
    fi
    
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl not found. Please install kubectl first."
        exit 1
    fi
    
    if ! command -v helm &> /dev/null; then
        print_error "helm not found. Please install helm first."
        exit 1
    fi
    
    # Execute deployment steps
    check_minikube
    build_docker_image
    deploy_kafka
    install_spark_operator
    create_kafka_topics
    deploy_spark_app
    setup_port_forwarding
    
    print_status "✅ Deployment completed successfully!"
    print_status ""
    print_status "📋 Next steps:"
    print_status "1. Check Kafka topics: kubectl exec -n kafka deployment/kafka-broker -- kafka-topics --list --bootstrap-server localhost:9092"
    print_status "2. Check Spark application: kubectl get sparkapplication"
    print_status "3. Send test data: python3 data_producer.py --kafka-servers localhost:30092 --mode batch --count 5"
    print_status "4. Check processed messages: kubectl exec -n kafka deployment/kafka-broker -- kafka-console-consumer --bootstrap-server localhost:9092 --topic processed-events --from-beginning"
    print_status ""
    print_status "🔍 Monitoring commands:"
    print_status "- Spark application logs: kubectl logs -f sparkapplication-kafka-spark-streaming-driver"
    print_status "- Kafka logs: kubectl logs -f -n kafka deployment/kafka-broker"
    print_status "- All pods status: kubectl get pods -A"
}

# Run main function
main