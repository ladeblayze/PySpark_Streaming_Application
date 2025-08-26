# Spark Structured Streaming on Kubernetes with Kafka

A production-ready Spark Structured Streaming application that processes restaurant events from Kafka, applies transformations, and outputs to another Kafka topic, all running on Kubernetes with the Spark Operator.

## 📋 Prerequisites

- Docker Desktop with Kubernetes enabled OR Minikube
- kubectl CLI tool
- Helm 3.x
- Python 3.8+ (for local testing)
- At least 8GB RAM allocated to Docker/Minikube
- 4 CPU cores

## 🏗️ Architecture
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Kafka     │────>│ Spark Stream │────>│  Kafka Output   │
│   Input     │     │  Processing  │     │     Topic       │
└─────────────┘     └──────────────┘     └─────────────────┘
│
┌──────┴───────┐
│ Spark        │
│ Operator     │
└──────────────┘

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd spark-streaming-k8s
2. Set Up Kubernetes Cluster
bash# Using Minikube
./scripts/setup-cluster.sh

# OR manually with Minikube
minikube start --cpus=4 --memory=8192 --driver=docker
3. Deploy Kafka
bash./scripts/deploy-kafka.sh

# Verify Kafka is running
kubectl get pods -n kafka
4. Install Spark Operator
bash./scripts/deploy-spark-operator.sh

# Verify operator is running
kubectl get pods -n spark-operator
5. Build and Deploy Spark Application
bash# Build Docker image
docker build -t spark-streaming:latest -f docker/Dockerfile .

# Load into Minikube (if using Minikube)
minikube image load spark-streaming:latest

# Deploy application
./scripts/deploy-app.sh

# Check application status
kubectl get sparkapplication -n spark
6. Generate Test Data
bash# Port forward Kafka
kubectl port-forward -n kafka svc/kafka-service 9092:9092 &

# Install dependencies
pip install kafka-python

# Run producer
python scripts/kafka-producer.py --count 100 --interval 2
7. Verify Deployment
bash./scripts/verify-deployment.sh

# Check driver logs
kubectl logs -n spark -l spark-role=driver -f

# Access Spark UI
kubectl port-forward -n spark $(kubectl get pods -n spark -l spark-role=driver -o jsonpath='{.items[0].metadata.name}') 4040:4040
# Open http://localhost:4040


Transformations Applied

Array Multiplication: Multiplies each element in data_array by 2
Time Filtering: Filters events where timestamp >= now()

Input Message Format
json{
  "Restaurantid": 234,
  "Event": "map_click",
  "Properties": {
    "timestamp": "2025-08-25T14:30:00Z",
    "is_relevant": true,
    "data_array": [1.0, 2.3, 2.4, 12.0]
  }
}
Output Message Format
json{
  "restaurant_id": 234,
  "event": "map_click",
  "event_timestamp": "2025-08-25T14:30:00Z",
  "is_relevant": true,
  "transformed_array": [2.0, 4.6, 4.8, 24.0],
  "processed_at": "2025-08-25T13:45:30Z",
  "processing_version": "1.0.0"
}
🧪 Testing
Unit Tests
bashcd spark-app
pip install -r requirements.txt
python -m pytest tests/ -v --cov=src
Integration Testing
bash# Run producer with test data
python scripts/kafka-producer.py --continuous --interval 1

# Check consumer for processed events
kubectl exec -it -n kafka kafka-0 -- kafka-console-consumer \
  --bootstrap-server kafka-service:9092 \
  --topic processed-events \
  --from-beginning
🔧 Troubleshooting
Common Issues and Solutions
1. Spark Driver Pod Fails to Start
Issue: Driver pod is in Error or CrashLoopBackOff state
Solution:
bash# Check driver logs
kubectl logs -n spark -l spark-role=driver --tail=100

# Common fixes:
# - Ensure service account has proper permissions
kubectl apply -f k8s/spark-operator/service-account.yaml

# - Verify image is loaded in Minikube
minikube image list | grep spark-streaming

# - Check resource limits
kubectl describe sparkapplication -n spark spark-streaming-processor
2. Kafka Connection Issues
Issue: Cannot connect to Kafka from Spark
Solution:
bash# Verify Kafka is running
kubectl get pods -n kafka

# Test Kafka connectivity
kubectl run kafka-test --image=confluentinc/cp-kafka:7.5.0 --rm -it --restart=Never -n kafka -- \
  kafka-topics --list --bootstrap-server kafka-service.kafka.svc.cluster.local:9092

# Check Kafka service
kubectl get svc -n kafka
3. Memory Issues
Issue: Executor OOM errors
Solution:
bash# Increase executor memory in spark-application.yaml
# Edit: spec.executor.memory: "4g"

# Reapply configuration
kubectl apply -f k8s/spark-app/spark-application.yaml
4. Checkpoint Issues
Issue: Checkpoint directory errors
Solution:
bash# Use persistent volume for checkpoints
# Add to spark-application.yaml:
volumes:
- name: checkpoint-volume
  persistentVolumeClaim:
    claimName: spark-checkpoint-pvc
5. Topic Not Found
Issue: Kafka topic not found
Solution:
bash# Recreate topics
kubectl delete job kafka-topic-creator -n kafka
kubectl apply -f k8s/kafka/kafka-topics.yaml
📝 Configuration
Environment Variables
VariableDescriptionDefaultKAFKA_BOOTSTRAP_SERVERSKafka broker addresseskafka-service.kafka.svc.cluster.local:9092INPUT_TOPICInput Kafka topicrestaurant-eventsOUTPUT_TOPICOutput Kafka topicprocessed-eventsCHECKPOINT_LOCATIONCheckpoint directory/tmp/checkpointTRIGGER_INTERVALProcessing trigger interval10 secondsLOG_LEVELSpark log levelINFO
Scaling
bash# Scale executors
kubectl edit sparkapplication -n spark spark-streaming-processor
# Change spec.executor.instances

# Scale Kafka partitions for better parallelism
kubectl exec -it -n kafka kafka-0 -- kafka-topics \
  --alter --topic restaurant-events \
  --partitions 6 \
  --bootstrap-server kafka-service:9092
🧹 Cleanup
bash# Delete Spark application
kubectl delete sparkapplication -n spark spark-streaming-processor

# Delete all resources
kubectl delete namespace spark kafka spark-operator

# Stop Minikube
minikube stop

# Delete Minikube cluster
minikube delete
📚 Documentation Consulted

Apache Spark Documentation
Spark on Kubernetes Operator
Kafka Documentation
Kubernetes Documentation
PySpark Structured Streaming Guide