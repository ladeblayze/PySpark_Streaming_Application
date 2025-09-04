FROM apache/spark:3.5.0-scala2.12-java11-python3-ubuntu

USER root

# Install kafka-python
RUN pip install --no-cache-dir kafka-python

# Download Kafka connector JAR directly
RUN wget -P /opt/spark/jars/ https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.5.0/spark-sql-kafka-0-10_2.12-3.5.0.jar

# Download required dependencies for Kafka connector
RUN wget -P /opt/spark/jars/ https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.4.0/kafka-clients-3.4.0.jar
RUN wget -P /opt/spark/jars/ https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.5.0/spark-token-provider-kafka-0-10_2.12-3.5.0.jar
RUN wget -P /opt/spark/jars/ https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar

# Copy application files
COPY src/spark_streaming_app.py /opt/spark/work-dir/
COPY src/requirements.txt /opt/spark/work-dir/

# Create ivy cache directory with proper permissions
RUN mkdir -p /home/spark/.ivy2/cache && chown -R 185:185 /home/spark/.ivy2

WORKDIR /opt/spark/work-dir

# Switch back to spark user
USER 185