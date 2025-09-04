from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

def create_spark_session():
    return SparkSession.builder \
        .appName("KafkaSparkStreaming") \
        .config("spark.sql.adaptive.enabled", "false") \
        .getOrCreate()

def main():
    spark = create_spark_session()
    
    # Define schema for incoming JSON
    schema = StructType([
        StructField("Restaurantid", IntegerType(), True),
        StructField("Event", StringType(), True),
        StructField("Properties", StructType([
            StructField("timestamp", StringType(), True),
            StructField("is_relevant", BooleanType(), True),
            StructField("data_array", ArrayType(DoubleType()), True)
        ]), True)
    ])
    
    # Read from Kafka
    df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka-cluster-kafka-bootstrap.kafka.svc.cluster.local:9092") \
        .option("subscribe", "input-topic") \
        .option("startingOffsets", "latest") \
        .load()
    
    # Parse JSON and apply transformations
    parsed_df = df.select(
        from_json(col("value").cast("string"), schema).alias("data"),
        col("timestamp").alias("kafka_timestamp")
    ).select(
        col("data.Restaurantid").alias("Restaurantid"),
        col("data.Event").alias("Event"),
        col("data.Properties.timestamp").alias("event_timestamp"),
        col("data.Properties.is_relevant").alias("is_relevant"),
        # FIXED: Use expr() for array transformation instead of lambda
        expr("transform(data.Properties.data_array, x -> x * 2)").alias("data_array")
    ).filter(
        # FIXED: More reasonable timestamp filter - events from last hour
        to_timestamp(col("event_timestamp"), "yyyy-MM-dd'T'HH:mm:ss'Z'") >= 
        current_timestamp() - expr("INTERVAL 1 HOUR")
    )
    
    # Convert back to JSON for output
    output_df = parsed_df.select(
        to_json(struct(
            col("Restaurantid"),
            col("Event"),
            struct(
                col("event_timestamp").alias("timestamp"),
                col("is_relevant"),
                col("data_array")
            ).alias("Properties")
        )).alias("value")
    )
    
    # Write to output Kafka topic
    query = output_df.writeStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka-cluster-kafka-bootstrap.kafka.svc.cluster.local:9092") \
        .option("topic", "output-topic") \
        .option("checkpointLocation", "/tmp/checkpoint") \
        .outputMode("append") \
        .trigger(processingTime='10 seconds') \
        .start()
    
    print("Spark streaming job started successfully!")
    print("Waiting for data...")
    
    query.awaitTermination()

if __name__ == "__main__":
    main()