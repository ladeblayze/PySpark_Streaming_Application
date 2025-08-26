## 1. Spark Application Code

### spark-app/src/streaming_app.py
```python
#!/usr/bin/env python3
"""
Spark Structured Streaming Application for processing Kafka events.
"""
import os
import sys
import json
import logging
from typing import Dict, Any
from datetime import datetime
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    from_json, col, current_timestamp, 
    to_timestamp, expr, udf, array, lit
)
from pyspark.sql.types import (
    StructType, StructField, StringType, 
    BooleanType, ArrayType, DoubleType, IntegerType
)
from config import Config
from transformations import multiply_array_by_two, filter_current_events

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StreamingProcessor:
    """Main streaming processor class."""
    
    def __init__(self, config: Config):
        """Initialize the streaming processor.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.spark = None
        self.schema = self._define_schema()
    
    def _define_schema(self) -> StructType:
        """Define the schema for incoming Kafka messages.
        
        Returns:
            StructType: Schema definition
        """
        return StructType([
            StructField("Restaurantid", IntegerType(), True),
            StructField("Event", StringType(), True),
            StructField("Properties", StructType([
                StructField("timestamp", StringType(), True),
                StructField("is_relevant", BooleanType(), True),
                StructField("data_array", ArrayType(DoubleType()), True)
            ]), True)
        ])
    
    def create_spark_session(self) -> SparkSession:
        """Create and configure Spark session.
        
        Returns:
            SparkSession: Configured Spark session
        """
        logger.info("Creating Spark session...")
        
        builder = SparkSession.builder \
            .appName(self.config.app_name)
        
        # Add Kafka packages
        packages = [
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0",
            "org.apache.kafka:kafka-clients:3.5.0"
        ]
        builder = builder.config("spark.jars.packages", ",".join(packages))
        
        # Configure for Kubernetes if running in K8s
        if self.config.is_kubernetes:
            builder = builder \
                .config("spark.master", "k8s://https://kubernetes.default.svc:443") \
                .config("spark.kubernetes.namespace", self.config.k8s_namespace) \
                .config("spark.kubernetes.container.image", self.config.spark_image)
        
        # Additional Spark configurations
        builder = builder \
            .config("spark.sql.streaming.checkpointLocation", self.config.checkpoint_location) \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
        
        self.spark = builder.getOrCreate()
        self.spark.sparkContext.setLogLevel(self.config.log_level)
        
        logger.info(f"Spark session created: {self.spark.version}")
        return self.spark
    
    def read_from_kafka(self) -> DataFrame:
        """Read streaming data from Kafka.
        
        Returns:
            DataFrame: Streaming DataFrame from Kafka
        """
        logger.info(f"Reading from Kafka topic: {self.config.input_topic}")
        
        return self.spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", self.config.kafka_bootstrap_servers) \
            .option("subscribe", self.config.input_topic) \
            .option("startingOffsets", self.config.starting_offsets) \
            .option("failOnDataLoss", "false") \
            .option("kafka.security.protocol", "PLAINTEXT") \
            .load()
    
    def process_stream(self, df: DataFrame) -> DataFrame:
        """Process the streaming data.
        
        Args:
            df: Input streaming DataFrame
            
        Returns:
            DataFrame: Processed streaming DataFrame
        """
        logger.info("Processing stream...")
        
        # Parse JSON from Kafka value
        parsed_df = df.select(
            col("key").cast("string").alias("key"),
            from_json(col("value").cast("string"), self.schema).alias("data"),
            col("timestamp").alias("kafka_timestamp")
        )
        
        # Extract nested fields
        flattened_df = parsed_df.select(
            col("key"),
            col("data.Restaurantid").alias("restaurant_id"),
            col("data.Event").alias("event"),
            col("data.Properties.timestamp").alias("event_timestamp"),
            col("data.Properties.is_relevant").alias("is_relevant"),
            col("data.Properties.data_array").alias("data_array"),
            col("kafka_timestamp")
        )
        
        # Convert timestamp string to timestamp type
        df_with_timestamp = flattened_df.withColumn(
            "event_timestamp_parsed",
            to_timestamp(col("event_timestamp"), "yyyy-MM-dd'T'HH:mm:ss'Z'")
        )
        
        # Apply transformations
        # 1. Multiply data array by 2
        df_transformed = multiply_array_by_two(df_with_timestamp)
        
        # 2. Filter for events with timestamp >= now()
        df_filtered = filter_current_events(df_transformed)
        
        # Add processing metadata
        df_final = df_filtered \
            .withColumn("processed_at", current_timestamp()) \
            .withColumn("processing_version", lit(self.config.processing_version))
        
        return df_final
    
    def write_to_kafka(self, df: DataFrame):
        """Write processed data to Kafka.
        
        Args:
            df: Processed DataFrame to write
            
        Returns:
            StreamingQuery: The streaming query handle
        """
        logger.info(f"Writing to Kafka topic: {self.config.output_topic}")
        
        # Prepare data for Kafka output
        output_df = df.select(
            col("restaurant_id").cast("string").alias("key"),
            expr("""
                to_json(struct(
                    restaurant_id,
                    event,
                    event_timestamp,
                    is_relevant,
                    transformed_array,
                    processed_at,
                    processing_version
                ))
            """).alias("value")
        )
        
        # Write to Kafka
        query = output_df \
            .writeStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", self.config.kafka_bootstrap_servers) \
            .option("topic", self.config.output_topic) \
            .option("checkpointLocation", self.config.checkpoint_location) \
            .outputMode("append") \
            .trigger(processingTime=self.config.trigger_interval) \
            .start()
        
        return query
    
    def run(self):
        """Main execution method."""
        try:
            # Create Spark session
            self.create_spark_session()
            
            # Read from Kafka
            input_df = self.read_from_kafka()
            
            # Process stream
            processed_df = self.process_stream(input_df)
            
            # Write to Kafka
            query = self.write_to_kafka(processed_df)
            
            logger.info("Streaming application started successfully")
            logger.info(f"Query ID: {query.id}")
            logger.info(f"Query Name: {query.name}")
            
            # Wait for termination
            query.awaitTermination()
            
        except Exception as e:
            logger.error(f"Error in streaming application: {e}", exc_info=True)
            if self.spark:
                self.spark.stop()
            sys.exit(1)
        finally:
            if self.spark:
                self.spark.stop()


def main():
    """Main entry point."""
    config = Config.from_env()
    processor = StreamingProcessor(config)
    processor.run()


if __name__ == "__main__":
    main()