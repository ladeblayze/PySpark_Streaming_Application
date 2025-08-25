FROM apache/spark:3.5.0-python3

USER root

# Install additional dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download Kafka connector JAR
RUN wget -P /opt/spark/jars/ \
    https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.5.0/spark-sql-kafka-0-10_2.12-3.5.0.jar \
    https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.4.0/kafka-clients-3.4.0.jar \
    https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.5.0/spark-token-provider-kafka-0-10_2.12-3.5.0.jar \
    https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar

# Copy application code
COPY spark_streaming_app.py .
COPY test_streaming_app.py .

# Create checkpoint directory
RUN mkdir -p /tmp/checkpoint && chmod 777 /tmp/checkpoint

# Switch back to spark user
USER 185

# Set environment variables
ENV SPARK_APPLICATION_PYTHON_LOCATION=/app/spark_streaming_app.py
ENV PYSPARK_MAJOR_PYTHON_VERSION=3

CMD ["/opt/spark/bin/spark-submit", \
     "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0", \
     "/app/spark_streaming_app.py"]