#!/usr/bin/env python3
"""
Quick Event Verification Script
Tests that events are flowing from Kafka and can be parsed correctly
"""

import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

def verify_event_flow():
    """Quick verification that events are flowing and parseable"""
    
    print("🔍 Event Flow Verification")
    print("=" * 40)
    
    # Set up packages
    os.environ["PYSPARK_SUBMIT_ARGS"] = "--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 pyspark-shell"
    
    try:
        # Create Spark session
        spark = SparkSession.builder \
            .appName("EventVerification") \
            .config("spark.sql.adaptive.enabled", "true") \
            .getOrCreate()
        
        spark.sparkContext.setLogLevel("WARN")
        
        print("✅ Spark session created")
        
        # Define event schema
        event_schema = StructType([
            StructField("timestamp", StringType(), True),
            StructField("event_type", StringType(), True),
            StructField("source_ip", StringType(), True),
            StructField("result", StringType(), True),
            StructField("severity", StringType(), True)
        ])
        
        # Read from Kafka
        kafka_df = spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", "localhost:9092") \
            .option("subscribe", "security-events") \
            .option("startingOffsets", "latest") \
            .load()
        
        # Parse events
        events_df = kafka_df.select(
            from_json(col("value").cast("string"), event_schema).alias("data")
        ).select("data.*") \
         .withColumn("timestamp", to_timestamp(col("timestamp")))
        
        print("✅ Kafka stream and parsing configured")
        
        # Show events for 30 seconds
        print("\n📡 Monitoring events for 30 seconds...")
        print("If you see events below, your setup is working!")
        print("-" * 60)
        
        query = events_df \
            .select("timestamp", "event_type", "source_ip", "result", "severity") \
            .writeStream \
            .format("console") \
            .option("truncate", False) \
            .option("numRows", 10) \
            .trigger(processingTime="3 seconds") \
            .start()
        
        # Wait for 30 seconds
        query.awaitTermination(30)
        query.stop()
        
        print("-" * 60)
        print("✅ Event verification complete!")
        print("\n📊 What you should have seen:")
        print("• Regular events every 3 seconds")
        print("• Different event types: auth_attempt, network_connection, etc.")
        print("• Various source IPs and severities")
        print("\n🎯 If no events appeared:")
        print("1. Check log generator: ./lab-control.sh logs-recent")
        print("2. Verify Kafka: docker-compose ps")
        print("3. Check topic: ./lab-control.sh kafka-ui")
        
        spark.stop()
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    verify_event_flow()
