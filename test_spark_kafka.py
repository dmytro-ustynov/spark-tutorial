#!/usr/bin/env python3
"""
Quick Spark Kafka Test Script
Run this to verify your Spark-Kafka setup is working
"""

import os
import sys

# Set up environment for PySpark with Kafka
def setup_pyspark_environment():
    """Configure environment for PySpark with Kafka integration"""
    
    # Spark packages for Kafka integration - updated for compatibility
    packages = [
        "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0",
        "org.postgresql:postgresql:42.7.1"
    ]
    
    # Set environment variables for PySpark
    os.environ["PYSPARK_SUBMIT_ARGS"] = f"--packages {','.join(packages)} pyspark-shell"
    
    print("🔧 PySpark environment configured with packages:")
    for pkg in packages:
        print(f"  📦 {pkg}")

def test_kafka_connection():
    """Test Spark-Kafka integration"""
    
    try:
        from pyspark.sql import SparkSession
        from pyspark.sql.functions import col
        
        print("\n🚀 Creating Spark session with Kafka support...")
        
        spark = SparkSession.builder \
            .appName("KafkaConnectionTest") \
            .config("spark.sql.adaptive.enabled", "true") \
            .getOrCreate()
        
        spark.sparkContext.setLogLevel("WARN")
        
        print("✅ Spark session created successfully")
        
        # Test Kafka stream creation
        print("📡 Testing Kafka stream creation...")
        
        kafka_df = spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", "localhost:9092") \
            .option("subscribe", "security-events") \
            .option("startingOffsets", "latest") \
            .load()
        
        print("✅ Kafka stream created successfully!")
        print("📋 Kafka stream schema:")
        kafka_df.printSchema()
        
        # Test if we can access the data
        print("\n🔍 Testing data access...")
        parsed_df = kafka_df.select(
            col("key").cast("string"),
            col("value").cast("string"),
            col("timestamp")
        )
        
        print("✅ Data parsing successful!")
        print("📋 Parsed schema:")
        parsed_df.printSchema()
        
        spark.stop()
        
        print("\n🎉 All tests passed! Your Spark-Kafka integration is working correctly.")
        print("\n📚 You can now run the analytics examples:")
        print("   python examples/security_analytics_template.py")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Install with: pip install pyspark")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Make sure Kafka is running: ./lab-control.sh status")
        print("2. Check if events are being generated: ./lab-control.sh logs-recent")
        print("3. Verify port 9092 is accessible: telnet localhost 9092")
        return False

if __name__ == "__main__":
    print("🔧 Spark Kafka Integration Test")
    print("=" * 40)
    
    # Setup environment
    setup_pyspark_environment()
    
    # Run test
    success = test_kafka_connection()
    
    sys.exit(0 if success else 1)
