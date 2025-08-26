"""Unit tests for configuration module."""
import unittest
import os
from unittest.mock import patch
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from config import Config


class TestConfig(unittest.TestCase):
    """Test cases for Config class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = Config(
            kafka_bootstrap_servers="localhost:9092",
            input_topic="input",
            output_topic="output"
        )
        
        self.assertEqual(config.kafka_bootstrap_servers, "localhost:9092")
        self.assertEqual(config.input_topic, "input")
        self.assertEqual(config.output_topic, "output")
        self.assertEqual(config.starting_offsets, "latest")
        self.assertEqual(config.app_name, "SparkStreamingProcessor")
        self.assertFalse(config.is_kubernetes)
    
    @patch.dict(os.environ, {
        "KAFKA_BOOTSTRAP_SERVERS": "kafka:9092",
        "INPUT_TOPIC": "test-input",
        "OUTPUT_TOPIC": "test-output",
        "IS_KUBERNETES": "true",
        "K8S_NAMESPACE": "test-namespace",
        "SPARK_IMAGE": "spark:latest"
    })
    def test_from_env(self):
        """Test configuration from environment variables."""
        config = Config.from_env()
        
        self.assertEqual(config.kafka_bootstrap_servers, "kafka:9092")
        self.assertEqual(config.input_topic, "test-input")
        self.assertEqual(config.output_topic, "test-output")
        self.assertTrue(config.is_kubernetes)
        self.assertEqual(config.k8s_namespace, "test-namespace")
        self.assertEqual(config.spark_image, "spark:latest")
    
    def test_validate_missing_kafka_servers(self):
        """Test validation with missing Kafka servers."""
        config = Config(
            kafka_bootstrap_servers="",
            input_topic="input",
            output_topic="output"
        )
        
        with self.assertRaises(ValueError) as context:
            config.validate()
        self.assertIn("KAFKA_BOOTSTRAP_SERVERS", str(context.exception))
    
    def test_validate_missing_spark_image_k8s(self):
        """Test validation with missing Spark image in Kubernetes mode."""
        config = Config(
            kafka_bootstrap_servers="kafka:9092",
            input_topic="input",
            output_topic="output",
            is_kubernetes=True,
            spark_image=None
        )
        
        with self.assertRaises(ValueError) as context:
            config.validate()
        self.assertIn("SPARK_IMAGE", str(context.exception))


if __name__ == '__main__':
    unittest.main()