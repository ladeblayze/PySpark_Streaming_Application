Kafka + Spark Streaming on Kubernetes
A production-ready streaming data pipeline that reads messages from Kafka, applies transformations using PySpark, and outputs results to another Kafka topic - all running on Kubernetes.
Architecture Overview

Kubernetes Cluster: Minikube for local development
Message Broker: Apache Kafka (managed by Strimzi operator)
Stream Processing: Apache Spark 3.5.0 with structured streaming
Data Transformation: Multiply array values by 2, filter by timestamp
Containerization: Docker with custom PySpark image

Requirements Met

[*] Kubernetes cluster capable of handling Spark jobs (batch and streaming)
[*] Dockerized PySpark streaming application
[*] Kafka integration with input/output topics
[*] Data transformation (multiply data_array by 2)
[*] Timestamp filtering (events from last hour)
[*]JSON message processing
[*] Real-time streaming with micro-batch processing

File Structure
spark-kafka-k8s/
├── README.md
├── Dockerfile
├── src/
│   ├── spark_streaming_app.py
│   ├── requirements.txt
│   
├── 
├── kubernetes/
│   ├── kafka-cluster.yaml
│   ├── kafka-topics.yaml
│   └── spark-job.yaml
├── 
├── scripts/
│   ├── setup.sh
│   ├── deploy.sh
│   ├── verify.sh
│   └── cleanup.sh
├── 
└── testing/
    ├── data_producer.py
    
Prerequisites

Docker Desktop
kubectl
minikube
Helm 3.x
Python 3.8+

Quick Start
1. Start Minikube
bash
minikube start --cpus=4 --memory=8192 --driver=docker
2. Install Infrastructure
bash
chmod +x ./scripts/setup.sh && ./scripts/setup.sh
3. Deploy Application
bash
chmod +x ./scripts/deploy.sh && ./scripts/deploy.sh
4. Verify Deployment
bash
kubectl get pods -A
kubectl logs -f spark-streaming-job -n spark

Detailed Setup Instructions
Step 1: Infrastructure Setup
Install Kafka and Spark operators:
bash
# Add Helm repositories
helm repo add strimzi https://strimzi.io/charts/
helm repo add spark-operator https://kubeflow.github.io/spark-operator
helm repo update

# Create namespaces
kubectl create namespace kafka
kubectl create namespace spark

# Install Strimzi Kafka operator
helm install kafka-operator strimzi/strimzi-kafka-operator -n kafka

# Create Spark service account and permissions
kubectl create serviceaccount spark -n spark
kubectl create clusterrolebinding spark-role --clusterrole=edit --serviceaccount=spark:spark

Step 2: Deploy Kafka Cluster
bash
# Deploy Kafka cluster with KRaft mode (ZooKeeper-free)
kubectl apply -f kafka-cluster.yaml
kubectl wait kafka/kafka-cluster --for=condition=Ready --timeout=600s -n kafka

# Create input and output topics
kubectl apply -f kafka-topics.yaml
kubectl wait --for=condition=Ready kafkatopic/input-topic -n kafka --timeout=120s
kubectl wait --for=condition=Ready kafkatopic/output-topic -n kafka --timeout=120s

Step 3: Build and Deploy Spark Application
bash
# Build Docker image
docker build -t spark-kafka-streaming:latest .
minikube image load spark-kafka-streaming:latest

# Deploy Spark streaming job
kubectl apply -f spark-job.yaml
Configuration Details
Kafka Cluster Configuration
The Kafka cluster uses:

KRaft mode: No ZooKeeper dependency (Strimzi 0.47+)
2 broker replicas: For fault tolerance
Replication factor 2: High availability
Ephemeral storage: Suitable for development/testing

Spark Application Configuration

Spark version: 3.5.0
Memory: 2GB driver, 1GB executor
Streaming trigger: 10-second micro-batches
Checkpoint location: Local /tmp/checkpoint
Kafka integration: Native Kafka 0.10+ connector

Data Processing Logic
The streaming application:

Reads JSON messages from input-topic
Parses JSON using defined schema
Multiplies each element in data_array by 2
Filters events with timestamps >= current time - 1 hour
Outputs transformed JSON to output-topic

Input Message Format:
json{
  "Restaurantid": 234,
  "Event": "map_click", 
  "Properties": {
    "timestamp": "2025-09-02T23:00:00Z",
    "is_relevant": true,
    "data_array": [1.0, 2.3, 2.4, 12.0]
  }
}
Output Message Format:
json{
  "Restaurantid": 234,
  "Event": "map_click",
  "Properties": {
    "timestamp": "2025-09-02T23:00:00Z", 
    "is_relevant": true,
    "data_array": [2.0, 4.6, 4.8, 24.0]
  }
}
Testing the Pipeline
Method 1: Internal Testing (Recommended)
bash
# Send test message from inside Kafka cluster
kubectl exec -it kafka-cluster-dual-role-0 -n kafka -- /bin/bash

# Send formatted JSON message
echo "{\"Restaurantid\": 234, \"Event\": \"map_click\", \"Properties\": {\"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\", \"is_relevant\": true, \"data_array\": [1.0, 2.3, 2.4, 12.0]}}" | \
/opt/kafka/bin/kafka-console-producer.sh --topic input-topic --bootstrap-server localhost:9092

# Verify output
/opt/kafka/bin/kafka-console-consumer.sh --topic output-topic --from-beginning --bootstrap-server localhost:9092

exit
Method 2: External Producer
bash
# Port-forward Kafka service
kubectl port-forward svc/kafka-cluster-kafka-bootstrap 9093:9092 -n kafka

# Run Python producer (in separate terminal)
python ./testing/data_producer.py
Verification Steps
Check All Components
bash# Verify Kafka cluster
kubectl get kafka -n kafka
kubectl get kafkatopic -n kafka

# Verify Spark job
kubectl get pods -n spark
kubectl logs spark-streaming-job -n spark

# Check resource status
kubectl get all -n kafka
kubectl get all -n spark
Expected Output
Successful Spark logs show:
Spark streaming job started successfully!
"numInputRows" : 1,
"numOutputRows" : 1
Successful data transformation:

Input: [1.0, 2.3, 2.4, 12.0]
Output: [2.0, 4.6, 4.8, 24.0] (each value × 2)

Troubleshooting
Common Issues
Kafka Topics Not Ready
bashkubectl describe kafkatopic input-topic -n kafka
kubectl logs deployment/strimzi-cluster-operator -n kafka
Spark Job Failed
bashkubectl logs spark-streaming-job -n spark
kubectl describe pod spark-streaming-job -n spark
Connectivity Issues
bash# Verify internal Kafka connectivity
kubectl exec -it kafka-cluster-dual-role-0 -n kafka -- \
/opt/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092
Resource Constraints
Minimum requirements:

CPU: 4 cores
Memory: 8GB
Disk: 20GB

For lower resource environments, reduce Kafka/Spark memory allocations in the configuration files.
Technology Versions

Kubernetes: 1.28+
Apache Kafka: 3.9.0
Apache Spark: 3.5.0
Strimzi Operator: 0.47.0
Python: 3.8+
Docker: Latest


Clean Up
bash
# Delete applications
kubectl delete pod spark-streaming-job -n spark
kubectl delete kafkatopic input-topic output-topic -n kafka
kubectl delete kafka kafka-cluster -n kafka

# Uninstall operators
helm uninstall kafka-operator -n kafka
helm uninstall spark-operator -n spark

# Stop minikube
minikube stop
minikube delete
Documentation References

Strimzi Kafka Operator
Apache Spark on Kubernetes
Kafka Structured Streaming
Minikube Documentation