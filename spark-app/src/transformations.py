"""Transformation functions for the streaming application."""
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, current_timestamp, udf, array
from pyspark.sql.types import ArrayType, DoubleType
from typing import List, Optional


def multiply_list(arr: Optional[List[float]]) -> Optional[List[float]]:
    """UDF to multiply each element in an array by 2.
    
    Args:
        arr: Input array of floats
        
    Returns:
        Array with each element multiplied by 2
    """
    if arr is None:
        return None
    return [x * 2 for x in arr]


# Register UDF
multiply_udf = udf(multiply_list, ArrayType(DoubleType()))


def multiply_array_by_two(df: DataFrame) -> DataFrame:
    """Multiply data_array values by 2.
    
    Args:
        df: Input DataFrame with data_array column
        
    Returns:
        DataFrame with transformed_array column
    """
    return df.withColumn(
        "transformed_array",
        multiply_udf(col("data_array"))
    )


def filter_current_events(df: DataFrame) -> DataFrame:
    """Filter events with timestamp >= now().
    
    Args:
        df: Input DataFrame with event_timestamp_parsed column
        
    Returns:
        DataFrame filtered for current/future events
    """
    return df.filter(
        col("event_timestamp_parsed") >= current_timestamp()
    )