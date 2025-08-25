from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from datetime import datetime
import logging
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def create_spark_session(app_name="KafkaSparkStreaming"):
    """Create and configure Spark session for streaming."""
    try:
        spark = SparkSession.builder \
            .appName(app_name) \
            .config("spark.sql.streaming.checkpointLocation", "/tmp/checkpoint") \
            .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
            .getOrCreate()
        
        spark.sparkContext.setLogLevel("WARN")
        logger.info("Spark session created successfully")
        return spark
    except Exception as e:
        logger.error(f"Failed to create Spark session: {str(e)}")
        raise

def define_schema():
    """Define the schema for incoming JSON messages."""
    return StructType([
        StructField("Restaurantid", IntegerType(), True),
        StructField("Event", StringType(), True),
        StructField("Properties", StructType([
            StructField("timestamp", StringType(), True),
            StructField("is_relevant", BooleanType(), True),
            StructField("data_array", ArrayType(DoubleType()), True)
        ]), True)
    ])

def transform_data(df):
    """Apply transformations to the streaming DataFrame."""
    try:
        # Parse the JSON and apply schema
        parsed_df = df.select(
            from_json(col("value").cast("string"), define_schema()).alias("data")
        ).select("data.*")
        
        # Convert timestamp string to timestamp type
        transformed_df = parsed_df.withColumn(
            "parsed_timestamp", 
            to_timestamp(col("Properties.timestamp"), "yyyy-MM-dd'T'HH:mm:ss'Z'")
        )
        
        # Filter for events with timestamp >= now()
        current_time = datetime.now()
        filtered_df = transformed_df.filter(
            col("parsed_timestamp") >= lit(current_time)
        )
        
        # Multiply data_array by 2
        final_df = filtered_df.withColumn(
            "transformed_data_array",
            transform(col("Properties.data_array"), lambda x: x * 2)
        ).select(
            col("Restaurantid"),
            col("Event"),
            struct(
                col("parsed_timestamp").alias("timestamp"),
                col("Properties.is_relevant").alias("is_relevant"),
                col("transformed_data_array").alias("data_array")
            ).alias("Properties")
        )
        
        logger.info("Data transformation applied successfully")
        return final_df
    
    except Exception as e:
        logger.error(f"Error in data transformation: {str(e)}")
        raise

def create_kafka_source(spark, kafka_servers, input_topic):
    """Create Kafka streaming source."""
    try:
        df = spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", kafka_servers) \
            .option("subscribe", input_topic) \
            .option("startingOffsets", "latest") \
            .option("failOnDataLoss", "false") \
            .load()
        
        logger.info(f"Kafka source created for topic: {input_topic}")
        return df
    except Exception as e:
        logger.error(f"Failed to create Kafka source: {str(e)}")
        raise

def create_kafka_sink(transformed_df, kafka_servers, output_topic):
    """Create Kafka streaming sink."""
    try:
        # Convert DataFrame to JSON string for Kafka output
        kafka_df = transformed_df.select(
            to_json(struct("*")).alias("value")
        )
        
        query = kafka_df \
            .writeStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", kafka_servers) \
            .option("topic", output_topic) \
            .option("checkpointLocation", "/tmp/checkpoint") \
            .outputMode("append") \
            .trigger(processingTime="10 seconds") \
            .start()
        
        logger.info(f"Kafka sink created for topic: {output_topic}")
        return query
    except Exception as e:
        logger.error(f"Failed to create Kafka sink: {str(e)}")
        raise

def main():
    """Main streaming application logic."""
    # Configuration from environment variables
    kafka_servers = os.getenv("KAFKA_SERVERS", "kafka-service:9092")
    input_topic = os.getenv("INPUT_TOPIC", "restaurant-events")
    output_topic = os.getenv("OUTPUT_TOPIC", "processed-events")
    
    logger.info(f"Starting streaming application with config:")
    logger.info(f"Kafka servers: {kafka_servers}")
    logger.info(f"Input topic: {input_topic}")
    logger.info(f"Output topic: {output_topic}")
    
    spark = None
    try:
        # Create Spark session
        spark = create_spark_session()
        
        # Create Kafka streaming source
        kafka_df = create_kafka_source(spark, kafka_servers, input_topic)
        
        # Apply transformations
        transformed_df = transform_data(kafka_df)
        
        # Create Kafka sink and start streaming
        query = create_kafka_sink(transformed_df, kafka_servers, output_topic)
        
        logger.info("Streaming query started successfully")
        
        # Wait for the streaming to finish
        query.awaitTermination()
        
    except Exception as e:
        logger.error(f"Application failed: {str(e)}")
        sys.exit(1)
    finally:
        if spark:
            spark.stop()
            logger.info("Spark session stopped")

if __name__ == "__main__":
    main()