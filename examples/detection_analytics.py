"""
Security Analytics with Better Detection and Debugging
This version has realistic thresholds and shows debugging information
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImprovedSecurityAnalytics:
    def __init__(self):
        # Set up packages
        os.environ["PYSPARK_SUBMIT_ARGS"] = "--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 pyspark-shell"
        
        # Initialize Spark Session
        self.spark = SparkSession.builder \
            .appName("ImprovedSecurityAnalytics") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.streaming.checkpointLocation", "/tmp/improved-checkpoints") \
            .getOrCreate()
        
        self.spark.sparkContext.setLogLevel("WARN")
        logger.info("✅ Improved Spark Session initialized")

    def create_kafka_stream(self):
        """Create Kafka stream reader with full schema"""
        
        # More complete schema to capture all event data
        event_schema = StructType([
            StructField("timestamp", StringType(), True),  # String first, convert later
            StructField("event_id", StringType(), True),
            StructField("event_type", StringType(), True),
            StructField("source_ip", StringType(), True),
            StructField("destination_ip", StringType(), True),
            StructField("username", StringType(), True),
            StructField("result", StringType(), True),
            StructField("protocol", StringType(), True),
            StructField("port", IntegerType(), True),
            StructField("severity", StringType(), True),
            StructField("failure_reason", StringType(), True),
            StructField("attempt_count", IntegerType(), True),
            StructField("geo_location", StructType([
                StructField("country", StringType(), True),
                StructField("city", StringType(), True)
            ]), True),
            StructField("bytes_sent", IntegerType(), True),
            StructField("bytes_received", IntegerType(), True),
            StructField("response_code", IntegerType(), True),
            StructField("requests_per_second", IntegerType(), True)
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
        
        # Parse JSON and convert timestamp
        events_df = kafka_df.select(
            from_json(col("value").cast("string"), event_schema).alias("data"),
            col("timestamp").alias("kafka_timestamp")
        ).select("data.*", "kafka_timestamp") \
         .withColumn("timestamp", to_timestamp(col("timestamp"))) \
         .filter(col("timestamp").isNotNull())  # Filter out invalid timestamps
        
        logger.info("📡 Kafka stream reader created with full schema")
        return events_df

    def detect_brute_force_attacks(self, events_df):
        """Improved brute force detection with realistic thresholds"""
        
        brute_force_alerts = events_df \
            .filter(col("event_type") == "auth_attempt") \
            .filter(col("result") == "failed") \
            .withWatermark("timestamp", "5 minutes") \
            .groupBy(
                window(col("timestamp"), "2 minutes", "30 seconds").alias("window"),
                col("source_ip"),
                col("destination_ip")
            ) \
            .count() \
            .filter(col("count") >= 5) \
            .select(
                col("window.start").alias("window_start"),
                col("window.end").alias("window_end"),
                col("source_ip"),
                col("destination_ip").alias("target_ip"),
                col("count").alias("failed_attempts"),
                lit("🚨 BRUTE_FORCE_DETECTED").alias("alert_type"),
                current_timestamp().alias("detected_at")
            )
        
        return brute_force_alerts

    def detect_ddos_attacks(self, events_df):
        """Improved DDoS detection with streaming-compatible aggregations"""
        
        ddos_alerts = events_df \
            .filter(col("event_type") == "network_connection") \
            .withWatermark("timestamp", "3 minutes") \
            .groupBy(
                window(col("timestamp"), "1 minute", "30 seconds").alias("window"),
                col("destination_ip"),
                col("port")
            ) \
            .agg(
                count("*").alias("request_count"),
                approx_count_distinct("source_ip").alias("unique_sources")
            ) \
            .filter(col("request_count") >= 100) \
            .select(
                col("window.start").alias("window_start"),
                col("window.end").alias("window_end"),
                col("destination_ip").alias("target_ip"),
                col("port").alias("target_port"),
                col("request_count"),
                col("unique_sources"),
                lit("💥 DDOS_DETECTED").alias("alert_type"),
                current_timestamp().alias("detected_at")
            )
        
        return ddos_alerts

    def analyze_failed_logins(self, events_df):
        """Show all failed login attempts for debugging"""
        
        failed_logins = events_df \
            .filter(col("event_type") == "auth_attempt") \
            .filter(col("result") == "failed") \
            .select(
                col("timestamp"),
                col("source_ip"),
                col("destination_ip"),
                col("username"),
                col("failure_reason"),
                col("geo_location.country").alias("country")
            )
        
        return failed_logins

    def analyze_traffic_volume(self, events_df):
        """Show traffic volume for debugging"""
        
        traffic_volume = events_df \
            .filter(col("event_type") == "network_connection") \
            .withWatermark("timestamp", "2 minutes") \
            .groupBy(
                window(col("timestamp"), "1 minute").alias("window"),
                col("destination_ip")
            ) \
            .count() \
            .select(
                col("window.start").alias("window_start"),
                col("destination_ip"),
                col("count").alias("requests"),
                when(col("count") > 100, "🔥 HIGH").otherwise("📊 NORMAL").alias("volume_level")
            )
        
        return traffic_volume

    def start_improved_analytics(self):
        """Start analytics with debugging and improved detection"""
        logger.info("🚀 Starting improved security analytics...")
        
        # Create input stream
        events_df = self.create_kafka_stream()
        
        print("=" * 80)
        print("🎯 SECURITY ANALYTICS DASHBOARD")
        print("=" * 80)
        print("Monitoring for:")
        print("• Brute Force: ≥5 failed logins per IP in 2 minutes")
        print("• DDoS: ≥100 requests per target in 1 minute")
        print("• Real-time event processing and analysis")
        print("=" * 80)
        
        # 1. Show raw events for verification
        print("\n📡 RAW EVENTS MONITOR:")
        raw_events_query = events_df \
            .select("timestamp", "event_type", "source_ip", "destination_ip", "result", "severity") \
            .writeStream \
            .format("console") \
            .option("truncate", False) \
            .option("numRows", 3) \
            .trigger(processingTime="5 seconds") \
            .queryName("raw_events") \
            .start()
        
        # 2. Failed login analysis (for brute force debugging)
        print("\n🔍 FAILED LOGIN MONITOR:")
        failed_logins = self.analyze_failed_logins(events_df)
        failed_login_query = failed_logins \
            .writeStream \
            .format("console") \
            .option("truncate", False) \
            .option("numRows", 5) \
            .trigger(processingTime="10 seconds") \
            .queryName("failed_logins") \
            .start()
        
        # 3. Traffic volume analysis (for DDoS debugging)
        print("\n📊 TRAFFIC VOLUME MONITOR:")
        traffic_volume = self.analyze_traffic_volume(events_df)
        traffic_query = traffic_volume \
            .writeStream \
            .format("console") \
            .option("truncate", False) \
            .outputMode("append") \
            .trigger(processingTime="15 seconds") \
            .queryName("traffic_volume") \
            .start()
        
        # 4. Brute force alerts
        print("\n🚨 BRUTE FORCE ALERTS:")
        brute_force_alerts = self.detect_brute_force_attacks(events_df)
        brute_force_query = brute_force_alerts \
            .writeStream \
            .format("console") \
            .option("truncate", False) \
            .trigger(processingTime="20 seconds") \
            .queryName("brute_force_alerts") \
            .start()
        
        # 5. DDoS alerts
        print("\n💥 DDOS ALERTS:")
        ddos_alerts = self.detect_ddos_attacks(events_df)
        ddos_query = ddos_alerts \
            .writeStream \
            .format("console") \
            .option("truncate", False) \
            .trigger(processingTime="20 seconds") \
            .queryName("ddos_alerts") \
            .start()
        
        # 6. Summary statistics
        print("\n📈 SUMMARY STATISTICS:")
        summary_stats = events_df \
            .groupBy("event_type", "severity") \
            .count() \
            .orderBy(desc("count"))
        
        stats_query = summary_stats \
            .writeStream \
            .format("console") \
            .option("truncate", False) \
            .outputMode("complete") \
            .trigger(processingTime="30 seconds") \
            .queryName("summary_stats") \
            .start()
        
        logger.info("✅ All monitoring queries started")
        print("\n🎮 CONTROLS:")
        print("• Start brute force: ./lab-control.sh attack-bf")
        print("• Start DDoS: ./lab-control.sh attack-ddos")
        print("• Stop attacks: ./lab-control.sh stop-attacks")
        print("• Press Ctrl+C to stop analytics")
        print("=" * 80)
        
        # Wait for termination
        try:
            raw_events_query.awaitTermination()
        except KeyboardInterrupt:
            logger.info("🛑 Stopping analytics pipeline...")
        finally:
            self.spark.stop()

if __name__ == "__main__":
    # Create and start analytics
    analytics = ImprovedSecurityAnalytics()
    analytics.start_improved_analytics()
