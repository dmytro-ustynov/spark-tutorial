"""
Containerized Security Analytics with Apache Spark Streaming
This version is designed to run inside the Docker Spark container
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContainerizedSecurityAnalytics:
    def __init__(self):
        # Initialize Spark Session with container-optimized configuration
        self.spark = SparkSession.builder \
            .appName("ContainerizedSecurityAnalytics") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .config("spark.sql.streaming.checkpointLocation", "/tmp/spark-checkpoints") \
            .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
            .getOrCreate()
        
        # Set log level to reduce noise
        self.spark.sparkContext.setLogLevel("WARN")
        
        # Database connection properties (using container network)
        self.db_properties = {
            "user": os.getenv("POSTGRES_USER", "spark_user"),
            "password": os.getenv("POSTGRES_PASSWORD", "spark_password"),
            "driver": "org.postgresql.Driver",
            "url": os.getenv("POSTGRES_URL", "jdbc:postgresql://postgres:5432/security_analytics")
        }
        
        # Kafka configuration (using container network)
        self.kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
        self.kafka_topic = "security-events"
        
        logger.info("✅ Containerized Spark Session initialized")

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
        
        # Read from Kafka using container network
        kafka_df = self.spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", self.kafka_servers) \
            .option("subscribe", self.kafka_topic) \
            .option("startingOffsets", "latest") \
            .option("failOnDataLoss", "false") \
            .load()
        
        # Parse JSON messages
        events_df = kafka_df.select(
            from_json(col("value").cast("string"), event_schema).alias("data"),
            col("timestamp").alias("kafka_timestamp")
        ).select("data.*", "kafka_timestamp")
        
        logger.info(f"📡 Kafka stream reader created for {self.kafka_servers}")
        return events_df

    def detect_brute_force_attacks(self, events_df):
        """Task 1: Detect brute force attacks - STUDENT IMPLEMENTATION"""
        
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
        
        return brute_force_alerts

    def detect_ddos_attacks(self, events_df):
        """Task 2: Detect DDoS attacks - STUDENT IMPLEMENTATION"""
        
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
                avg("requests_per_second").alias("avg_rps")
            ) \
            .filter(col("total_requests") > 1000) \
            .select(
                col("window.start").alias("window_start"),
                col("window.end").alias("window_end"),
                col("destination_ip").alias("target_ip"),
                col("port").alias("target_port"),
                coalesce(col("avg_rps"), lit(0)).cast("integer").alias("requests_per_second"),
                col("unique_source_ips"),
                col("total_requests"),
                lit("critical").alias("severity"),
                lit("volumetric").alias("attack_type")
            )
        
        return ddos_alerts

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
        logger.info("🚀 Starting containerized security analytics pipeline...")
        
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
        
        # Console output for monitoring
        console_query = events_df \
            .filter(col("severity").isin(["high", "critical"])) \
            .writeStream \
            .format("console") \
            .option("truncate", False) \
            .option("numRows", 3) \
            .trigger(processingTime="15 seconds") \
            .start()
        
        logger.info("✅ All streaming queries started")
        logger.info("🌐 Spark UI available at: http://localhost:4040")
        logger.info("🗄️  Database results viewable at: http://localhost:5050")
        
        # Wait for termination
        try:
            brute_force_query.awaitTermination()
        except KeyboardInterrupt:
            logger.info("🛑 Stopping analytics pipeline...")
        finally:
            self.spark.stop()

if __name__ == "__main__":
    # Create and start analytics
    analytics = ContainerizedSecurityAnalytics()
    analytics.start_analytics()
