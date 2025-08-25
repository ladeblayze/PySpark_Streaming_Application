# Kafka Spark Streaming on Kubernetes

A complete solution for real-time data processing using Apache Spark Structured Streaming with Apache Kafka on Kubernetes, built with the Spark Operator.

## Overview

This project implements a streaming application that:
- Reads messages from a Kafka topic (`restaurant-events`)
- Applies transformations (multiplies data arrays by 2 and filters by timestamp)
- Outputs processed data to another Kafka topic (`processed-events`)
- Runs on Kubernetes using the Spark Operator

## Architecture

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────┐
│   Kafka     │───▶│  Spark Streaming │───▶│   Kafka     │
│  (Input)    │    │   Application    │    │  (Output)   │
│restaurant-  │    │                  │    │processed-   │
│events       │    │                  │    │events       │
└─────────────┘    └──────────────────┘    └─────────────┘
        ▲                     │                     ▼
        │                     │              ┌─────────────┐
┌─────────────┐              │              │  Consumer   │
│ Data        │              │              │ Application │
│ Producer    │              ▼              └─────────────┘
└─────────────┘    ┌──────────────────┐
                   │   Kubernetes     │
                   │   - Minikube     │
                   │   - Spark Operator│
                   └──────────────────┘
```

## Prerequisites

Before starting, ensure you have the following installed:

### Required Software
- **Docker**: For containerization
- **Minikube**: For local Kubernetes cluster
- **kubectl**: Kubernetes command-line tool
- **Helm**: Package manager for Kubernetes
- **Python 3.8+**: For the data producer and tests

### Installation Commands

**On macOS:**
```bash
# Install Docker Desktop from https://docker.com/products/docker-desktop

# Install minikube
brew install minikube

# Install kubectl
brew install kubernetes-cli

# Install helm
brew install helm

# Install Python dependencies
pip install -r requirements.txt
```

**On Ubuntu/Debian:**
```bash
# Docker
sudo apt-get update
sudo apt-get install docker.io
sudo usermod -aG docker $USER

# Minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Python dependencies
pip install -r requirements.txt
```

## Project Structure

```
├── spark_streaming_app.py          # Main Spark streaming application
├── test_streaming_app.py           # Unit tests
├── data_producer.py                # Kafka data producer for testing
├── Dockerfile                      # Docker image for Spark app
├── requirements.txt                # Python dependencies
├── k8s/
│   ├── kafka-setup.yaml           # Kafka and Zookeeper deployment
│   ├── spark-operator-rbac.yaml   # RBAC configurations
│   └── spark-application.yaml     # SparkApplication definition
├── scripts/
│   ├── setup-k8s-environment.sh   # Complete setup script
│   └── cleanup.sh                 # Cleanup script
└── README.md                      # This file
```

## Quick Start (Automated Setup)

For a quick deployment, use the automated setup script:

```bash
# Make scripts executable
chmod +x scripts/setup-k8s-environment.sh
chmod +x scripts/cleanup.sh

# Run the complete setup
./scripts/setup-k8s-environment.sh
```

The script will:
1. Start minikube if not running
2. Build the Docker image
3. Deploy Kafka cluster
4. Install Spark Operator
5. Create Kafka topics
6. Deploy the Spark application
7. Set up port forwarding

## Step-by-Step Manual Setup

### Step 1: Start Minikube

```bash
# Start minikube with sufficient resources
minikube start --driver=docker --memory=8192 --cpus=4

# Enable required addons
minikube addons enable ingress
minikube addons enable dashboard

# Verify minikube is running
minikube status
```

### Step 2: Build Docker Image

```bash
# Configure Docker to use minikube's registry
eval $(minikube docker-env)

# Build the Spark application image
docker build -t kafka-spark-streaming:latest .

# Verify the image was built
docker images | grep kafka-spark-streaming
```

### Step 3: Deploy Kafka Cluster

```bash
# Create Kafka namespace and deploy Kafka components
kubectl apply -f k8s/kafka-setup.yaml

# Wait for deployments to be ready
kubectl wait --for=condition=available --timeout=300s deployment/zookeeper -n kafka
kubectl wait --for=condition=available --timeout=300s deployment/kafka-broker -n kafka

# Verify Kafka is running
kubectl get pods -n kafka
```

### Step 4: Install Spark Operator

```bash
# Apply RBAC configurations
kubectl apply -f k8s/spark-operator-rbac.yaml

# Add Spark Operator Helm repository
helm repo add spark-operator https://googlecloudplatform.github.io/spark-on-k8s-operator
helm repo update

# Install Spark Operator
helm install spark-operator spark-operator/spark-operator \
    --namespace spark-operator \
    --create-namespace \
    --set sparkJobNamespace=default \
    --set enableWebhook=true

# Verify Spark Operator is running
kubectl get pods -n spark-operator
```

### Step 5: Create Kafka Topics

```bash
# Create input topic
kubectl exec -n kafka deployment/kafka-broker -- kafka-topics --create \
    --bootstrap-server localhost:9092 \
    --topic restaurant-events \
    --partitions 3 \
    --replication-factor 1

# Create output topic
kubectl exec -n kafka deployment/kafka-broker -- kafka-topics --create \
    --bootstrap-server localhost:9092 \
    --topic processed-events \
    --partitions 3 \
    --replication-factor 1

# Verify topics were created
kubectl exec -n kafka deployment/kafka-broker -- kafka-topics --list \
    --bootstrap-server localhost:9092
```

### Step 6: Deploy Spark Application

```bash
# Deploy the Spark streaming application
kubectl apply -f k8s/spark-application.yaml

# Check the application status
kubectl get sparkapplication

# Check driver pod status
kubectl get pods | grep driver
```

### Step 7: Set up Port Forwarding

```bash
# Port forward Kafka for external access
kubectl port-forward -n kafka service/kafka-service 30092:9093 &

# Verify connection
echo "Kafka is now accessible at localhost:30092"
```

## Testing the Application

### 1. Generate Sample Data

Create sample data file:
```bash
python3 data_producer.py --mode sample-file
```

### 2. Send Test Messages

Send a batch of test messages:
```bash
python3 data_producer.py --kafka-servers localhost:30092 --mode batch --count 10 --delay 2
```

Send continuous messages:
```bash
python3 data_producer.py --kafka-servers localhost:30092 --mode continuous --interval 5
```

### 3. Verify Message Processing

Check input messages:
```bash
kubectl exec -n kafka deployment/kafka-broker -- kafka-console-consumer \
    --bootstrap-server localhost:9092 \
    --topic restaurant-events \
    --from-beginning \
    --max-messages 5
```

Check processed output:
```bash
kubectl exec -n kafka deployment/kafka-broker -- kafka-console-consumer \
    --bootstrap-server localhost:9092 \
    --topic processed-events \
    --from-beginning \
    --max-messages 5
```

## Monitoring and Debugging

### Application Logs

```bash
# Get Spark driver logs
kubectl logs -f $(kubectl get pods | grep driver | awk '{print $1}')

# Get Spark executor logs
kubectl logs -f $(kubectl get pods | grep executor | awk '{print $1}')
```

### System Status

```bash
# Check all pods status
kubectl get pods -A

# Check Spark application details
kubectl describe sparkapplication kafka-spark-streaming

# Check Kafka broker logs
kubectl logs -f -n kafka deployment/kafka-broker

# Check Zookeeper logs  
kubectl logs -f -n kafka deployment/zookeeper
```

### Useful Monitoring Commands

```bash
# Monitor pod resources
kubectl top pods -A

# Check events
kubectl get events --sort-by=.metadata.creationTimestamp

# Spark UI (when available)
kubectl port-forward service/kafka-spark-streaming-ui-svc 4040:4040
```

## Running Tests

```bash
# Run unit tests
python -m pytest test_streaming_app.py -v

# Run tests with coverage
python -m pytest test_streaming_app.py --cov=spark_streaming_app --cov-report=html
```

## Configuration

### Environment Variables

The Spark application accepts these environment variables:

- `KAFKA_SERVERS`: Kafka bootstrap servers (default: `kafka-service:9092`)
- `INPUT_TOPIC`: Input topic name (default: `restaurant-events`)
- `OUTPUT_TOPIC`: Output topic name (default: `processed-events`)

### Spark Application Tuning

Modify `k8s/spark-application.yaml` to adjust:

- **Resources**: Driver/executor memory and CPU
- **Scaling**: Number of executor instances
- **Streaming**: Processing trigger interval
- **Checkpointing**: Checkpoint location and settings

Example modifications:
```yaml
driver:
  cores: 2
  memory: "2g"
executor:
  cores: 2
  instances: 4
  memory: "2g"
```

## Data Format

### Input Message Format
```json
{
  "Restaurantid": 234,
  "Event": "map_click", 
  "Properties": {
    "timestamp": "2025-06-23T00:00:03Z",
    "is_relevant": true,
    "data_array": [1.0, 2.3, 2.4, 12]
  }
}
```

### Output Message Format
```json
{
  "Restaurantid": 234,
  "Event": "map_click",
  "Properties": {
    "timestamp": "2025-06-23T00:00:03Z", 
    "is_relevant": true,
    "data_array": [2.0, 4.6, 4.8, 24.0]
  }
}
```

## Troubleshooting

### Common Issues

**1. Pods stuck in Pending state**
```bash
kubectl describe pod <pod-name>
# Usually indicates resource constraints
```

**2. Spark application fails to start**
```bash
# Check driver logs
kubectl logs <driver-pod-name>

# Check for image pull issues
kubectl describe pod <driver-pod-name>
```

**3. Kafka connection issues**
```bash
# Test Kafka connectivity
kubectl exec -n kafka deployment/kafka-broker -- kafka-broker-api-versions --bootstrap-server localhost:9092
```

**4. Out of memory errors**
```bash
# Increase memory in spark-application.yaml
spec:
  driver:
    memory: "2g"
  executor:
    memory: "2g"
```

### Performance Tuning

1. **Increase parallelism**: Add more executor instances
2. **Optimize batch size**: Adjust trigger interval
3. **Tune Kafka consumer**: Modify consumer configurations
4. **Resource allocation**: Increase CPU/memory based on workload

## Cleanup

Remove all deployed resources:

```bash
# Use cleanup script
./scripts/cleanup.sh

# Or manual cleanup
kubectl delete sparkapplication kafka-spark-streaming
kubectl delete -f k8s/kafka-setup.yaml
helm uninstall spark-operator -n spark-operator
kubectl delete namespace spark-operator kafka

# Stop minikube (optional)
minikube stop
```

## Documentation References

This solution was built using the following documentation:
- [Apache Spark Structured Streaming Guide](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)
- [Spark Operator Documentation](https://github.com/GoogleCloudPlatform/spark-on-k8s-operator)
- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Minikube Documentation](https://minikube.sigs.k8s.io/docs/)
- [Helm Documentation](https://helm.sh/docs/)

## License

This project is for demonstration purposes as part of a coding challenge.