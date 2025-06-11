"""
Security Analytics with Apache Spark Streaming
Student Template for Cybersecurity Event Detection

This template provides the basic structure for implementing
real-time security analytics using Spark Structured Streaming.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import logging

# Import our Kafka configuration helper
from spark_kafka_config import create_spark_session_with_kafka, get_postgres_properties, create_kafka_stream

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityAnalytics:
    def __init__(self):
        # Initialize Spark Session with Kafka integration
        self.spark = create_spark_session_with_kafka("SecurityAnalytics")
        
        # Database connection properties
        self.db_properties = get_postgres_properties()
        
        logger.info("✅ Spark Session initialized with Kafka support")

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
            StructField("protocol", StringType(), True),
            StructField("port", IntegerType(), True),
            StructField("severity", StringType(), True),
            StructField("geo_location", StructType([
                StructField("country", StringType(), True),
                StructField("city", StringType(), True)
            ]), True),
            StructField("failure_reason", StringType(), True),
            StructField("attempt_count", IntegerType(), True),
            StructField("bytes_sent", IntegerType(), True),
            StructField("bytes_received", IntegerType(), True),
            StructField("response_code", IntegerType(), True),
            StructField("requests_per_second", IntegerType(), True)
        ])
        
        # Use the helper function to create Kafka stream
        kafka_df = create_kafka_stream(self.spark)
        
        # Parse JSON messages
        events_df = kafka_df.select(
            from_json(col("value").cast("string"), event_schema).alias("data"),
            col("timestamp").alias("kafka_timestamp")
        ).select("data.*", "kafka_timestamp")
        
        logger.info("📡 Kafka stream reader created")
        return events_df

    def detect_brute_force_attacks(self, events_df):
        """
        Task 1: Detect brute force attacks
        
        TODO for students:
        1. Filter for failed authentication attempts
        2. Group by time windows and source IP
        3. Count attempts and flag suspicious IPs
        4. Return DataFrame with alerts
        """
        
        # STUDENT IMPLEMENTATION STARTS HERE
        brute_force_alerts = events_df \
            .filter(col("event_type") == "auth_attempt") \
            .filter(col("result") == "failed") \
            .withWatermark("timestamp", "10 minutes") \
            .groupBy(
                window(col("timestamp"), "5 minutes", "1 minute").alias("window"),
                col("source_ip"),
                col("destination_ip"),
                col("username")
            ) \
            .agg(
                count("*").alias("failed_attempts"),
                min("timestamp").alias("first_seen"),
                max("timestamp").alias("last_seen"),
                first("severity").alias("severity")
            ) \
            .filter(col("failed_attempts") > 10) \
            .select(
                col("window.start").alias("window_start"),
                col("window.end").alias("window_end"),
                col("source_ip"),
                col("destination_ip"), 
                col("username"),
                col("failed_attempts"),
                col("severity"),
                col("first_seen"),
                col("last_seen")
            )
        # STUDENT IMPLEMENTATION ENDS HERE
        
        return brute_force_alerts

    def detect_ddos_attacks(self, events_df):
        """
        Task 2: Detect DDoS attacks
        
        TODO for students:
        1. Filter for network connection events
        2. Group by time windows and destination
        3. Count requests and unique sources
        4. Identify traffic spikes
        """
        
        # STUDENT IMPLEMENTATION STARTS HERE
        ddos_alerts = events_df \
            .filter(col("event_type") == "network_connection") \
            .withWatermark("timestamp", "5 minutes") \
            .groupBy(
                window(col("timestamp"), "1 minute", "30 seconds").alias("window"),
                col("destination_ip"),
                col("port")
            ) \
            .agg(
                count("*").alias("total_requests"),
                approx_count_distinct("source_ip").alias("unique_source_ips"),
                avg("requests_per_second").alias("avg_rps"),
                max("requests_per_second").alias("max_rps")
            ) \
            .filter(col("total_requests") > 1000) \
            .select(
                col("window.start").alias("window_start"),
                col("window.end").alias("window_end"),
                col("destination_ip").alias("target_ip"),
                col("port").alias("target_port"),
                col("avg_rps").cast("integer").alias("requests_per_second"),
                col("unique_source_ips"),
                col("total_requests"),
                lit("critical").alias("severity"),
                lit("volumetric").alias("attack_type")
            )
        # STUDENT IMPLEMENTATION ENDS HERE
        
        return ddos_alerts

    def detect_geographic_anomalies(self, events_df):
        """
        Task 3: Detect geographic anomalies (impossible travel)
        
        TODO for students:
        1. Track user login locations over time
        2. Calculate distances between login locations  
        3. Identify impossible travel scenarios
        4. This is an advanced task requiring stateful processing
        """
        
        # STUDENT IMPLEMENTATION STARTS HERE
        # This is a simplified version - students should enhance it
        geographic_anomalies = events_df \
            .filter(col("event_type") == "auth_attempt") \
            .filter(col("result") == "success") \
            .withWatermark("timestamp", "1 hour") \
            .groupBy(
                window(col("timestamp"), "1 hour", "30 minutes").alias("window"),
                col("username")
            ) \
            .agg(
                collect_set("geo_location.country").alias("countries"),
                collect_set("source_ip").alias("source_ips"),
                count("*").alias("login_count")
            ) \
            .filter(size(col("countries")) > 1) \
            .select(
                col("window.start").alias("window_start"),
                col("window.end").alias("window_end"),
                col("username"),
                col("countries"),
                col("source_ips"),
                lit(0).alias("max_distance_km"),  # Students should calculate this
                lit(60).alias("time_diff_minutes"),
                lit(7.5).alias("risk_score")
            )
        # STUDENT IMPLEMENTATION ENDS HERE
        
        return geographic_anomalies

    def write_to_postgres(self, df, table_name, mode="append"):
        """Write DataFrame to PostgreSQL using foreachBatch for streaming compatibility"""
        
        def write_batch_to_postgres(batch_df, batch_id):
            """Function to write each batch to PostgreSQL"""
            try:
                if batch_df.count() > 0:  # Only write non-empty batches
                    batch_df.write \
                        .mode(mode) \
                        .format("jdbc") \
                        .options(**self.db_properties) \
                        .option("dbtable", table_name) \
                        .save()
                    print(f"📝 Batch {batch_id}: Wrote {batch_df.count()} records to {table_name}")
                else:
                    print(f"📝 Batch {batch_id}: No records to write to {table_name}")
            except Exception as e:
                print(f"❌ Error writing batch {batch_id} to {table_name}: {e}")
        
        return df.writeStream \
            .foreachBatch(write_batch_to_postgres) \
            .outputMode("append") \
            .option("checkpointLocation", f"/tmp/spark-checkpoints/{table_name}") \
            .trigger(processingTime="30 seconds")

    def start_analytics(self):
        """Main analytics pipeline"""
        logger.info("🚀 Starting security analytics pipeline...")
        
        # Create input stream
        events_df = self.create_kafka_stream()
        
        # Task 1: Brute force detection
        brute_force_alerts = self.detect_brute_force_attacks(events_df)
        brute_force_query = self.write_to_postgres(
            brute_force_alerts, 
            "brute_force_alerts"
        ).start()
        
        # Task 2: DDoS detection  
        ddos_alerts = self.detect_ddos_attacks(events_df)
        ddos_query = self.write_to_postgres(
            ddos_alerts,
            "ddos_alerts" 
        ).start()
        
        # Task 3: Geographic anomalies
        geo_anomalies = self.detect_geographic_anomalies(events_df)
        geo_query = self.write_to_postgres(
            geo_anomalies,
            "geographic_anomalies"
        ).start()
        
        # Optional: Debug output to console
        debug_query = events_df.writeStream \
            .format("console") \
            .option("truncate", False) \
            .option("numRows", 5) \
            .trigger(processingTime="10 seconds") \
            .start()
        
        logger.info("✅ All streaming queries started")
        
        # Wait for termination
        try:
            brute_force_query.awaitTermination()
            ddos_query.awaitTermination()
            geo_query.awaitTermination()
            debug_query.awaitTermination()
        except KeyboardInterrupt:
            logger.info("🛑 Stopping analytics pipeline...")
        finally:
            self.spark.stop()

if __name__ == "__main__":
    # Create and start analytics
    analytics = SecurityAnalytics()
    analytics.start_analytics()
