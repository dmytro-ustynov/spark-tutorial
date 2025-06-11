"""
Simple Console-Only Security Analytics
This version outputs results to console instead of PostgreSQL for immediate feedback
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleSecurityAnalytics:
    def __init__(self):
        # Set up packages
        os.environ["PYSPARK_SUBMIT_ARGS"] = "--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 pyspark-shell"
        
        # Initialize Spark Session
        self.spark = SparkSession.builder \
            .appName("SimpleSecurityAnalytics") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.streaming.checkpointLocation", "/tmp/simple-checkpoints") \
            .getOrCreate()
        
        self.spark.sparkContext.setLogLevel("WARN")
        logger.info("✅ Simple Spark Session initialized")

    def create_kafka_stream(self):
        """Create Kafka stream reader for security events"""
        
        # Define the schema for incoming events
        event_schema = StructType([
            StructField("timestamp", TimestampType(), True),
            StructField("event_id", StringType(), True),
            StructField("event_type", StringType(), True),
            StructField("source_ip", StringType(), True),
            StructField("destination_ip", StringType(), True),
            StructField("username", StringType(), True),
            StructField("result", StringType(), True),
            StructField("severity", StringType(), True)
        ])
        
        # Read from Kafka
        kafka_df = self.spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", "localhost:9092") \
            .option("subscribe", "security-events") \
            .option("startingOffsets", "latest") \
            .option("failOnDataLoss", "false") \
            .load()
        
        # Parse JSON messages
        events_df = kafka_df.select(
            from_json(col("value").cast("string"), event_schema).alias("data")
        ).select("data.*")
        
        logger.info("📡 Kafka stream reader created")
        return events_df

    def detect_brute_force_attacks(self, events_df):
        """Simple brute force detection with console output"""
        
        brute_force_alerts = events_df \
            .filter(col("event_type") == "auth_attempt") \
            .filter(col("result") == "failed") \
            .withWatermark("timestamp", "10 minutes") \
            .groupBy(
                window(col("timestamp"), "5 minutes").alias("window"),
                col("source_ip")
            ) \
            .count() \
            .filter(col("count") > 10) \
            .select(
                col("window.start").alias("window_start"),
                col("window.end").alias("window_end"),
                col("source_ip"),
                col("count").alias("failed_attempts"),
                lit("BRUTE_FORCE_DETECTED").alias("alert_type")
            )
        
        return brute_force_alerts

    def detect_ddos_attacks(self, events_df):
        """Simple DDoS detection with console output"""
        
        ddos_alerts = events_df \
            .filter(col("event_type") == "network_connection") \
            .withWatermark("timestamp", "5 minutes") \
            .groupBy(
                window(col("timestamp"), "1 minute").alias("window"),
                col("destination_ip")
            ) \
            .count() \
            .filter(col("count") > 1000) \
            .select(
                col("window.start").alias("window_start"),
                col("window.end").alias("window_end"),
                col("destination_ip").alias("target_ip"),
                col("count").alias("request_count"),
                lit("DDOS_DETECTED").alias("alert_type")
            )
        
        return ddos_alerts

    def start_simple_analytics(self):
        """Start analytics with console output only"""
        logger.info("🚀 Starting simple security analytics (console output)...")
        
        # Create input stream
        events_df = self.create_kafka_stream()
        
        # Show raw events for verification
        raw_events_query = events_df \
            .select("timestamp", "event_type", "source_ip", "destination_ip", "severity") \
            .writeStream \
            .format("console") \
            .option("truncate", False) \
            .option("numRows", 5) \
            .trigger(processingTime="10 seconds") \
            .queryName("raw_events") \
            .start()
        
        # Brute force detection
        brute_force_alerts = self.detect_brute_force_attacks(events_df)
        brute_force_query = brute_force_alerts \
            .writeStream \
            .format("console") \
            .option("truncate", False) \
            .trigger(processingTime="30 seconds") \
            .queryName("brute_force_alerts") \
            .start()
        
        # DDoS detection
        ddos_alerts = self.detect_ddos_attacks(events_df)
        ddos_query = ddos_alerts \
            .writeStream \
            .format("console") \
            .option("truncate", False) \
            .trigger(processingTime="30 seconds") \
            .queryName("ddos_alerts") \
            .start()
        
        # Event statistics
        event_stats = events_df \
            .groupBy("event_type", "severity") \
            .count() \
            .orderBy(desc("count"))
        
        stats_query = event_stats \
            .writeStream \
            .format("console") \
            .option("truncate", False) \
            .outputMode("complete") \
            .trigger(processingTime="20 seconds") \
            .queryName("event_statistics") \
            .start()
        
        logger.info("✅ All console queries started")
        logger.info("👀 Watch the console output for:")
        logger.info("   • Raw security events (every 10s)")
        logger.info("   • Brute force alerts (every 30s)")
        logger.info("   • DDoS alerts (every 30s)")
        logger.info("   • Event statistics (every 20s)")
        logger.info("🔥 Trigger attacks with: ./lab-control.sh attack-bf or ./lab-control.sh attack-ddos")
        
        # Wait for termination
        try:
            raw_events_query.awaitTermination()
        except KeyboardInterrupt:
            logger.info("🛑 Stopping analytics pipeline...")
        finally:
            self.spark.stop()

if __name__ == "__main__":
    # Create and start analytics
    analytics = SimpleSecurityAnalytics()
    analytics.start_simple_analytics()
