"""Configuration module for the streaming application."""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Application configuration."""
    
    # Kafka configuration
    kafka_bootstrap_servers: str
    input_topic: str
    output_topic: str
    starting_offsets: str = "latest"
    
    # Spark configuration
    app_name: str = "SparkStreamingProcessor"
    checkpoint_location: str = "/tmp/checkpoint"
    trigger_interval: str = "10 seconds"
    log_level: str = "INFO"
    processing_version: str = "1.0.0"
    
    # Kubernetes configuration
    is_kubernetes: bool = False
    k8s_namespace: str = "spark"
    spark_image: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Create configuration from environment variables.
        
        Returns:
            Config: Configuration instance
        """
        return cls(
            kafka_bootstrap_servers=os.getenv(
                "KAFKA_BOOTSTRAP_SERVERS", 
                "kafka-service.kafka.svc.cluster.local:9092"
            ),
            input_topic=os.getenv("INPUT_TOPIC", "restaurant-events"),
            output_topic=os.getenv("OUTPUT_TOPIC", "processed-events"),
            starting_offsets=os.getenv("STARTING_OFFSETS", "latest"),
            app_name=os.getenv("APP_NAME", "SparkStreamingProcessor"),
            checkpoint_location=os.getenv("CHECKPOINT_LOCATION", "/tmp/checkpoint"),
            trigger_interval=os.getenv("TRIGGER_INTERVAL", "10 seconds"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            processing_version=os.getenv("PROCESSING_VERSION", "1.0.0"),
            is_kubernetes=os.getenv("IS_KUBERNETES", "false").lower() == "true",
            k8s_namespace=os.getenv("K8S_NAMESPACE", "spark"),
            spark_image=os.getenv("SPARK_IMAGE", None)
        )
    
    def validate(self):
        """Validate configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        if not self.kafka_bootstrap_servers:
            raise ValueError("KAFKA_BOOTSTRAP_SERVERS is required")
        if not self.input_topic:
            raise ValueError("INPUT_TOPIC is required")
        if not self.output_topic:
            raise ValueError("OUTPUT_TOPIC is required")
        if self.is_kubernetes and not self.spark_image:
            raise ValueError("SPARK_IMAGE is required when running on Kubernetes")