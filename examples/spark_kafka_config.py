"""
Spark Session Configuration for Kafka Integration
This module provides the correct Spark configuration for connecting to Kafka
"""

from pyspark.sql import SparkSession
import os

def create_spark_session_with_kafka(app_name="SecurityAnalytics"):
    """
    Create a Spark session with Kafka integration enabled
    
    This function automatically downloads and configures the necessary
    Kafka connector JARs for Spark Structured Streaming.
    """
    
    # Updated package versions for compatibility
    spark_version = "3.5.0"  
    scala_version = "2.12"   
    
    # Use compatible Kafka connector version
    kafka_package = f"org.apache.spark:spark-sql-kafka-0-10_{scala_version}:{spark_version}"
    
    # PostgreSQL JDBC driver
    postgres_package = "org.postgresql:postgresql:42.7.1"
    
    # Create Spark session with packages
    spark = SparkSession.builder \
        .appName(app_name) \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .config("spark.jars.packages", f"{kafka_package},{postgres_package}") \
        .config("spark.sql.streaming.checkpointLocation", "/tmp/spark-checkpoints") \
        .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
        .getOrCreate()
    
    # Set log level to reduce noise
    spark.sparkContext.setLogLevel("WARN")
    
    print(f"✅ Spark session created with Kafka integration")
    print(f"📦 Kafka package: {kafka_package}")
    print(f"🗄️  PostgreSQL package: {postgres_package}")
    
    return spark

def get_postgres_properties():
    """Get PostgreSQL connection properties"""
    return {
        "user": "spark_user",
        "password": "spark_password",
        "driver": "org.postgresql.Driver",
        "url": "jdbc:postgresql://localhost:5432/security_analytics"
    }

def create_kafka_stream(spark, bootstrap_servers="localhost:9092", topic="security-events"):
    """Create Kafka stream with proper configuration"""
    
    kafka_df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", bootstrap_servers) \
        .option("subscribe", topic) \
        .option("startingOffsets", "latest") \
        .option("failOnDataLoss", "false") \
        .option("kafka.session.timeout.ms", "30000") \
        .option("kafka.request.timeout.ms", "40000") \
        .load()
    
    print(f"📡 Kafka stream reader created for topic: {topic}")
    return kafka_df

if __name__ == "__main__":
    # Test the configuration
    spark = create_spark_session_with_kafka("TestKafkaConnection")
    
    try:
        # Try to create a Kafka stream
        kafka_df = create_kafka_stream(spark)
        print("🎉 Kafka integration test successful!")
        
        # Show the schema
        print("📋 Kafka stream schema:")
        kafka_df.printSchema()
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        spark.stop()
