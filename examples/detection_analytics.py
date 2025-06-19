#!/usr/bin/env python3
"""
Working Detection Analytics Script with Proper Kafka Configuration

This version uses the correct Kafka connection approach for Spark Structured Streaming.
"""

import os
import logging
import shutil
import uuid
import socket
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SecurityAnalytics:
    def __init__(self):
        """Initialize Spark session with proper Kafka configuration"""

        # Detect environment
        self.environment = self.detect_environment()
        logger.info(f"🔍 Detected environment: {self.environment}")

        # Clean up checkpoints
        self.cleanup_checkpoints()

        # Set Spark packages
        os.environ["PYSPARK_SUBMIT_ARGS"] = "--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 pyspark-shell"

        # Create unique checkpoint directory
        self.checkpoint_dir = f"/tmp/spark-working-{uuid.uuid4().hex[:8]}"

        # Create Spark session
        self.spark = SparkSession.builder \
            .appName("WorkingSecurityAnalytics") \
            .config("spark.sql.adaptive.enabled", "false") \
            .config("spark.sql.streaming.checkpointLocation", self.checkpoint_dir) \
            .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
            .getOrCreate()

        self.spark.sparkContext.setLogLevel("WARN")
        self.kafka_topic = "security-events"

        logger.info("✅ Spark session initialized")

    def detect_environment(self):
        """Detect environment"""
        try:
            socket.gethostbyname('kafka')
            return "container"
        except socket.gaierror:
            return "local"

    def cleanup_checkpoints(self):
        """Clean up checkpoint directories"""
        import glob
        for pattern in ["/tmp/spark-*", "/tmp/temporary-*"]:
            for path in glob.glob(pattern):
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                except:
                    pass

    def get_kafka_server(self):
        """Get the correct Kafka server based on environment"""
        if self.environment == "container":
            return "kafka:29092"  # This is what works based on our debug
        else:
            return "localhost:9092"

    def create_kafka_stream(self):
        """Create Kafka stream - the correct way"""

        kafka_server = self.get_kafka_server()
        logger.info(f"🔗 Connecting to Kafka: {kafka_server}")

        # Define event schema
        event_schema = StructType([
            StructField("timestamp", StringType(), True),
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
            StructField("geo_location", StructType([
                StructField("country", StringType(), True),
                StructField("city", StringType(), True),
                StructField("latitude", DoubleType(), True),
                StructField("longitude", DoubleType(), True)
            ]), True)
        ])

        # Create streaming DataFrame - this is the key!
        kafka_df = self.spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", kafka_server) \
            .option("subscribe", self.kafka_topic) \
            .option("startingOffsets", "latest") \
            .option("failOnDataLoss", "false") \
            .load()

        # Parse events
        events_df = kafka_df.select(
            from_json(col("value").cast("string"), event_schema).alias("data"),
            col("timestamp").alias("kafka_timestamp")
        ).select("data.*", "kafka_timestamp") \
         .withColumn("timestamp", to_timestamp(col("timestamp"))) \
         .filter(col("timestamp").isNotNull())

        logger.info(f"✅ Kafka stream created successfully")
        return events_df

    def detect_brute_force_attacks(self, events_df):
        """Brute force detection"""

        brute_force_alerts = events_df \
            .filter(col("event_type") == "auth_attempt") \
            .filter(col("result") == "failed") \
            .withWatermark("timestamp", "10 minutes") \
            .groupBy(
                window(col("timestamp"), "2 minutes", "30 seconds"),
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

        logger.info("🔍 Brute force detection configured")
        return brute_force_alerts

    def monitor_failed_logins(self, events_df):
        """Monitor failed logins"""

        failed_logins = events_df \
            .filter(col("event_type") == "auth_attempt") \
            .filter(col("result") == "failed") \
            .select(
                "timestamp",
                "source_ip",
                "destination_ip",
                "username",
                "failure_reason",
                col("geo_location.country").alias("country")
            )

        logger.info("👁️ Failed login monitor configured")
        return failed_logins

    def create_event_rate_monitor(self, events_df):
        """Monitor event rates"""

        event_rates = events_df \
            .withWatermark("timestamp", "1 minute") \
            .groupBy(
                window(col("timestamp"), "30 seconds"),
                col("event_type")
            ) \
            .count() \
            .select(
                col("window.start").alias("window_start"),
                col("event_type"),
                col("count").alias("events_per_30sec")
            )

        logger.info("📊 Event rate monitor configured")
        return event_rates

    def start_analytics(self):
        """Start the analytics pipeline"""

        logger.info("🚀 Starting security analytics pipeline...")

        try:
            # Create Kafka stream
            events_df = self.create_kafka_stream()

            # Create monitoring streams
            brute_force_alerts = self.detect_brute_force_attacks(events_df)
            failed_logins = self.monitor_failed_logins(events_df)
            event_rates = self.create_event_rate_monitor(events_df)

            # Display info
            print("\n" + "="*80)
            print("🔍 WORKING CYBERSECURITY ANALYTICS")
            print("="*80)
            print(f"🌍 Environment: {self.environment.upper()}")
            print(f"📡 Kafka Server: {self.get_kafka_server()}")
            print(f"📊 Topic: {self.kafka_topic}")
            print("\n🎯 Active Monitoring:")
            print("   • Event rates (every 20s)")
            print("   • Failed login attempts (every 15s)")
            print("   • Brute force alerts (every 30s)")
            print("\n💡 To trigger attacks:")
            print("   • Brute Force: ./lab-control.sh attack-bf")
            print("   • Stop: ./lab-control.sh stop-attacks")
            print("\n⏱️  Expected Detection Time: 2-3 minutes after attack starts")
            print("="*80)

            # Start queries
            logger.info("🚀 Starting monitoring queries...")

            # 1. Event rates
            rates_query = event_rates \
                .writeStream \
                .format("console") \
                .option("truncate", False) \
                .option("numRows", 8) \
                .trigger(processingTime="20 seconds") \
                .queryName("EventRates") \
                .start()

            # 2. Failed logins
            failed_query = failed_logins \
                .writeStream \
                .format("console") \
                .option("truncate", False) \
                .option("numRows", 6) \
                .trigger(processingTime="15 seconds") \
                .queryName("FailedLogins") \
                .start()

            # 3. Brute force alerts
            alerts_query = brute_force_alerts \
                .writeStream \
                .format("console") \
                .option("truncate", False) \
                .option("numRows", 5) \
                .trigger(processingTime="30 seconds") \
                .queryName("BruteForceAlerts") \
                .start()

            logger.info("✅ All monitoring queries started successfully!")
            logger.info("👀 Watch for:")
            logger.info("   • Event rates showing normal ~50 events/30sec")
            logger.info("   • Failed logins during attacks")
            logger.info("   • Brute force alerts when threshold exceeded")
            logger.info("🔥 Start attack: ./lab-control.sh attack-bf")

            # Wait for termination
            try:
                rates_query.awaitTermination()
            except KeyboardInterrupt:
                logger.info("🛑 Stopping analytics...")
            finally:
                for query in [rates_query, failed_query, alerts_query]:
                    if query.isActive:
                        query.stop()

                self.cleanup_checkpoints()
                self.spark.stop()
                logger.info("✅ Analytics stopped and cleaned up")

        except Exception as e:
            logger.error(f"❌ Error: {e}")
            self.cleanup_checkpoints()
            if hasattr(self, 'spark'):
                self.spark.stop()
            raise

def main():
    """Main entry point"""

    print("🔍 WORKING CYBERSECURITY ANALYTICS")
    print("=" * 50)
    print("\n🚀 Starting...")

    try:
        analytics = SecurityAnalytics()
        analytics.start_analytics()
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        print("   • Check: docker-compose logs kafka")
        print("   • Restart: docker-compose restart")

if __name__ == "__main__":
    main()
