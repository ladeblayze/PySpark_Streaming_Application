"""Unit tests for transformation functions."""
import unittest
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, array, lit, current_timestamp
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from transformations import multiply_array_by_two, filter_current_events, multiply_list


class TestTransformations(unittest.TestCase):
    """Test cases for transformation functions."""
    
    @classmethod
    def setUpClass(cls):
        """Set up Spark session for tests."""
        cls.spark = SparkSession.builder \
            .appName("TestTransformations") \
            .master("local[*]") \
            .getOrCreate()
        cls.spark.sparkContext.setLogLevel("ERROR")
    
    @classmethod
    def tearDownClass(cls):
        """Stop Spark session."""
        cls.spark.stop()
    
    def test_multiply_list(self):
        """Test multiply_list UDF function."""
        # Test normal case
        result = multiply_list([1.0, 2.0, 3.0])
        self.assertEqual(result, [2.0, 4.0, 6.0])
        
        # Test empty array
        result = multiply_list([])
        self.assertEqual(result, [])
        
        # Test None
        result = multiply_list(None)
        self.assertIsNone(result)
        
        # Test negative numbers
        result = multiply_list([-1.0, -2.5, 0.0])
        self.assertEqual(result, [-2.0, -5.0, 0.0])
    
    def test_multiply_array_by_two(self):
        """Test multiply_array_by_two transformation."""
        # Create test DataFrame
        data = [
            (1, [1.0, 2.0, 3.0]),
            (2, [0.0, -1.0, 5.5]),
            (3, None),
            (4, [])
        ]
        df = self.spark.createDataFrame(data, ["id", "data_array"])
        
        # Apply transformation
        result_df = multiply_array_by_two(df)
        
        # Collect results
        results = result_df.collect()
        
        # Verify results
        self.assertEqual(results[0]["transformed_array"], [2.0, 4.0, 6.0])
        self.assertEqual(results[1]["transformed_array"], [0.0, -2.0, 11.0])
        self.assertIsNone(results[2]["transformed_array"])
        self.assertEqual(results[3]["transformed_array"], [])
    
    def test_filter_current_events(self):
        """Test filter_current_events transformation."""
        # Create test DataFrame with various timestamps
        now = datetime.now()
        future = now + timedelta(hours=1)
        past = now - timedelta(hours=1)
        
        data = [
            (1, future),
            (2, past),
            (3, now),
            (4, None)
        ]
        df = self.spark.createDataFrame(data, ["id", "event_timestamp_parsed"])
        
        # Apply transformation
        result_df = filter_current_events(df)
        
        # Count results - should filter out past events and nulls
        count = result_df.count()
        self.assertGreaterEqual(count, 1)  # At least future event
        self.assertLessEqual(count, 2)  # At most future and now
        
        # Verify that past events are filtered out
        past_events = result_df.filter(
            col("event_timestamp_parsed") < current_timestamp()
        ).count()
        self.assertEqual(past_events, 0)


if __name__ == '__main__':
    unittest.main()