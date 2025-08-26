# Multi-stage build for optimized image size
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY spark-app/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM openjdk:11-jre-slim

# Install Python
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/bin/python3 /usr/bin/python

# Set working directory
WORKDIR /opt/spark/work-dir

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY spark-app/src /opt/spark/work-dir/src
COPY spark-app/setup.py /opt/spark/work-dir/

# Set Python path
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/opt/spark/work-dir/src:$PYTHONPATH

# Install Spark
ARG SPARK_VERSION=3.5.0
ARG HADOOP_VERSION=3

RUN curl -L https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz | tar -xz -C /opt/ \
    && mv /opt/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION} /opt/spark \
    && rm -rf /opt/spark/examples /opt/spark/data

# Set Spark environment variables
ENV SPARK_HOME=/opt/spark
ENV PATH=$SPARK_HOME/bin:$SPARK_HOME/sbin:$PATH
ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3

# Download Kafka dependencies
RUN cd /opt/spark/jars && \
    curl -O https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/${SPARK_VERSION}/spark-sql-kafka-0-10_2.12-${SPARK_VERSION}.jar && \
    curl -O https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.5.0/kafka-clients-3.5.0.jar && \
    curl -O https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar && \
    curl -O https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/${SPARK_VERSION}/spark-token-provider-kafka-0-10_2.12-${SPARK_VERSION}.jar

# Create non-root user for Spark
RUN useradd -m -u 185 spark && \
    chown -R spark:spark /opt/spark

# Switch to spark user
USER spark

# Set entrypoint
ENTRYPOINT ["/opt/spark/bin/spark-submit"]
CMD ["--help"]