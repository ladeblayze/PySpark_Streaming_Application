**Spark Structured Streaming on Kubernetes with Kafka**



A production-ready Spark Structured Streaming application that processes restaurant events from Kafka, applies transformations, and writes the results to another Kafka topic — all orchestrated on Kubernetes with the Spark Operator.



📋 **Prerequisites**



Docker Desktop (with Kubernetes enabled) or Minikube



kubectl CLI



Helm 3.x



Python 3.8+ (for local testing)



At least 6GB RAM + 4 CPU cores allocated to Docker/Minikube



🏗️ **Architecture**

┌─────────────┐     ┌──────────────┐     ┌─────────────────┐

│   Kafka     │────>│ Spark Stream │────>│  Kafka Output   │

│   Input     │     │  Processing  │     │     Topic       │

└─────────────┘     └──────────────┘     └─────────────────┘

&nbsp;       │

&nbsp;       ▼

┌──────────────┐

│ Spark        │

│ Operator     │

└──────────────┘



🚀 **Quick Start**

1\. Clone the Repository

git clone <repository-url>

cd spark-streaming-k8s



2\. Set Up Kubernetes Cluster

\# With helper script

./scripts/setup-cluster.sh



\# OR manually with Minikube

minikube start --cpus=4 --memory=7000 --driver=docker



3\. Deploy Kafka

./scripts/deploy-kafka.sh

kubectl get pods -n kafka   # verify



4\. Install Spark Operator

./scripts/deploy-spark-operator.sh

kubectl get pods -n spark-operator   # verify



5\. Build \& Deploy Spark Application

\# Build image

docker build -t spark-streaming:latest -f docker/Dockerfile .



\# Load into Minikube

minikube image load spark-streaming:latest



\# Deploy app

./scripts/deploy-app.sh

kubectl get sparkapplication -n spark   # verify



6\. Generate Test Data

kubectl port-forward -n kafka svc/kafka-service 9092:9092 \&



pip install kafka-python

python scripts/kafka-producer.py --count 100 --interval 2



7\. Verify Deployment

./scripts/verify-deployment.sh



\# Tail driver logs

kubectl logs -n spark -l spark-role=driver -f





Access the Spark UI:



kubectl port-forward -n spark \\

&nbsp; $(kubectl get pods -n spark -l spark-role=driver -o jsonpath='{.items\[0].metadata.name}') \\

&nbsp; 4040:4040

\# Open http://localhost:4040



📊 **Application Details**



Transformations Applied



Array Multiplication → multiplies each element in data\_array by 2



Time Filtering → keeps only events with timestamp ≥ now()



Input Format



{

&nbsp; "Restaurantid": 234,

&nbsp; "Event": "map\_click",

&nbsp; "Properties": {

&nbsp;   "timestamp": "2025-08-25T14:30:00Z",

&nbsp;   "is\_relevant": true,

&nbsp;   "data\_array": \[1.0, 2.3, 2.4, 12.0]

&nbsp; }

}





Output Format



{

&nbsp; "restaurant\_id": 234,

&nbsp; "event": "map\_click",

&nbsp; "event\_timestamp": "2025-08-25T14:30:00Z",

&nbsp; "is\_relevant": true,

&nbsp; "transformed\_array": \[2.0, 4.6, 4.8, 24.0],

&nbsp; "processed\_at": "2025-08-25T13:45:30Z",

&nbsp; "processing\_version": "1.0.0"

}



🧪 **Testing**



Unit Tests



cd spark-app

pip install -r requirements.txt

python -m pytest tests/ -v --cov=src





Integration Tests



python scripts/kafka-producer.py --continuous --interval 1



kubectl exec -it -n kafka kafka-0 -- kafka-console-consumer \\

&nbsp; --bootstrap-server kafka-service:9092 \\

&nbsp; --topic processed-events \\

&nbsp; --from-beginning



🔧 Troubleshooting



Driver pod fails →



kubectl logs -n spark -l spark-role=driver --tail=100

kubectl apply -f k8s/spark-operator/service-account.yaml

minikube image list | grep spark-streaming





Kafka connection issues →



kubectl get pods -n kafka

kubectl get svc -n kafka





Executor OOM → increase executor memory in spark-application.yaml



Checkpoint errors → mount a PVC for checkpoints



Topic not found → recreate topics via k8s/kafka/kafka-topics.yaml



📝 Configuration

Variable	Description	Default

KAFKA\_BOOTSTRAP\_SERVERS	Kafka brokers	kafka-service.kafka.svc.cluster.local:9092

INPUT\_TOPIC	Input Kafka topic	restaurant-events

OUTPUT\_TOPIC	Output Kafka topic	processed-events

CHECKPOINT\_LOCATION	Checkpoint directory	/tmp/checkpoint

TRIGGER\_INTERVAL	Trigger interval	10s

LOG\_LEVEL	Spark log level	INFO



Scaling



\# Spark executors

kubectl edit sparkapplication -n spark spark-streaming-processor



\# Kafka partitions

kubectl exec -it -n kafka kafka-0 -- kafka-topics \\

&nbsp; --alter --topic restaurant-events \\

&nbsp; --partitions 6 \\

&nbsp; --bootstrap-server kafka-service:9092



🧹 Cleanup

kubectl delete sparkapplication -n spark spark-streaming-processor

kubectl delete namespace spark kafka spark-operator

minikube stop \&\& minikube delete



📚 **References**



Apache Spark Docs



Spark on Kubernetes Operator



Apache Kafka Docs



Kubernetes Docs



PySpark Structured Streaming Guide



Tested with:



Spark 3.5.0



Kafka 3.5.0



Kubernetes 1.28.0



Python 3.11



📂 Project Structure

spark-streaming-k8s/

├── README.md

├── docker/              # Docker image

├── spark-app/           # Application code \& tests

├── k8s/                 # Kubernetes manifests

├── scripts/             # Helper scripts

└── data/                # Sample data

