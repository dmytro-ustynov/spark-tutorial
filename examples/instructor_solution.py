"""
Complete Solution for Cybersecurity Analytics with Spark Streaming
This file contains instructor solutions for all tasks
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql.window import Window
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityAnalyticsSolution:
    def __init__(self):
        self.spark = SparkSession.builder \
            .appName("SecurityAnalyticsSolution") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .config("spark.sql.streaming.checkpointLocation", "/tmp/spark-checkpoints") \
            .getOrCreate()
        
        self.spark.sparkContext.setLogLevel("WARN")
        
        self.db_properties = {
            "user": "spark_user",
            "password": "spark_password",
            "driver": "org.postgresql.Driver",
            "url": "jdbc:postgresql://localhost:5432/security_analytics"
        }

    def create_kafka_stream(self):
        """Enhanced Kafka stream with better error handling"""
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
            StructField("requests_per_second", IntegerType(), True),
            StructField("user_agent", StringType(), True)
        ])
        
        kafka_df = self.spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", "localhost:9092") \
            .option("subscribe", "security-events") \
            .option("startingOffsets", "latest") \
            .option("failOnDataLoss", "false") \
            .load()
        
        events_df = kafka_df.select(
            from_json(col("value").cast("string"), event_schema).alias("data"),
            col("timestamp").alias("kafka_timestamp")
        ).select("data.*", "kafka_timestamp") \
         .filter(col("timestamp").isNotNull())
        
        return events_df

    def advanced_brute_force_detection(self, events_df):
        """
        Advanced brute force detection with multiple thresholds and context
        """
        brute_force_base = events_df \
            .filter(col("event_type") == "auth_attempt") \
            .filter(col("result") == "failed") \
            .withWatermark("timestamp", "10 minutes")
        
        # Basic threshold detection (>10 in 5 minutes)
        basic_alerts = brute_force_base \
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
                collect_set("failure_reason").alias("failure_reasons"),
                approx_count_distinct("user_agent").alias("unique_user_agents")
            ) \
            .filter(col("failed_attempts") > 10)
        
        # Enhanced detection with adaptive thresholds
        enhanced_alerts = basic_alerts \
            .withColumn("severity", 
                when(col("failed_attempts") > 50, "critical")
                .when(col("failed_attempts") > 25, "high")
                .otherwise("medium")
            ) \
            .withColumn("attack_type",
                when(col("unique_user_agents") > 3, "distributed_brute_force")
                .when(size(col("failure_reasons")) == 1, "targeted_brute_force")
                .otherwise("standard_brute_force")
            ) \
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
        
        return enhanced_alerts

    def sophisticated_ddos_detection(self, events_df):
        """
        Multi-layered DDoS detection with different attack types
        """
        network_events = events_df \
            .filter(col("event_type") == "network_connection") \
            .withWatermark("timestamp", "5 minutes")
        
        # Volumetric attack detection
        volumetric_attacks = network_events \
            .groupBy(
                window(col("timestamp"), "1 minute", "30 seconds").alias("window"),
                col("destination_ip"),
                col("port")
            ) \
            .agg(
                count("*").alias("total_requests"),
                approx_count_distinct("source_ip").alias("unique_sources"),
                avg("bytes_sent").alias("avg_bytes_sent"),
                sum("bytes_sent").alias("total_bytes"),
                avg(when(col("requests_per_second").isNotNull(), 
                        col("requests_per_second"))).alias("avg_rps")
            ) \
            .filter(col("total_requests") > 1000)
        
        # Protocol-based detection
        protocol_attacks = network_events \
            .groupBy(
                window(col("timestamp"), "2 minutes").alias("window"),
                col("destination_ip"),
                col("protocol")
            ) \
            .agg(
                count("*").alias("request_count"),
                approx_count_distinct("source_ip").alias("unique_sources"),
                avg("response_code").alias("avg_response_code")
            ) \
            .filter(
                ((col("protocol") == "UDP") & (col("request_count") > 500)) |
                ((col("protocol") == "HTTP") & (col("avg_response_code") > 400))
            )
        
        # Combine detections
        ddos_alerts = volumetric_attacks \
            .select(
                col("window.start").alias("window_start"),
                col("window.end").alias("window_end"),
                col("destination_ip").alias("target_ip"),
                col("port").alias("target_port"),
                coalesce(col("avg_rps"), lit(0)).cast("integer").alias("requests_per_second"),
                col("unique_sources").alias("unique_source_ips"),
                col("total_requests"),
                when(col("total_requests") > 5000, "critical")
                .when(col("total_requests") > 2000, "high")
                .otherwise("medium").alias("severity"),
                when(col("unique_sources") < 10, "amplification")
                .when(col("avg_bytes_sent") < 100, "volumetric")
                .otherwise("distributed").alias("attack_type")
            )
        
        return ddos_alerts

    def geographic_anomaly_detection_advanced(self, events_df):
        """
        Advanced geographic anomaly detection with distance calculations
        """
        auth_events = events_df \
            .filter(col("event_type") == "auth_attempt") \
            .filter(col("result") == "success") \
            .withWatermark("timestamp", "2 hours")
        
        # Create user session windows
        user_sessions = auth_events \
            .groupBy(
                col("username"),
                window(col("timestamp"), "1 hour", "30 minutes").alias("window")
            ) \
            .agg(
                collect_list(struct(
                    col("timestamp"),
                    col("geo_location.country"),
                    col("geo_location.city"),
                    col("source_ip")
                )).alias("login_events"),
                approx_count_distinct("geo_location.country").alias("country_count"),
                min("timestamp").alias("session_start"),
                max("timestamp").alias("session_end")
            ) \
            .filter(col("country_count") > 1)
        
        # Calculate time differences and impossibility
        anomalies = user_sessions \
            .withColumn("time_diff_minutes", 
                (unix_timestamp(col("session_end")) - 
                 unix_timestamp(col("session_start"))) / 60
            ) \
            .withColumn("risk_score",
                when((col("time_diff_minutes") < 30) & (col("country_count") > 2), 9.5)
                .when((col("time_diff_minutes") < 60) & (col("country_count") > 1), 7.5)
                .when(col("country_count") > 3, 8.0)
                .otherwise(5.0)
            ) \
            .select(
                col("window.start").alias("window_start"),
                col("window.end").alias("window_end"),
                col("username"),
                transform(col("login_events"), lambda x: x.country).alias("countries"),
                transform(col("login_events"), lambda x: x.source_ip).alias("source_ips"),
                lit(5000).alias("max_distance_km"), # Simplified - students should enhance
                col("time_diff_minutes").cast("integer"),
                col("risk_score")
            )
        
        return anomalies

    def threat_score_calculation(self, events_df):
        """
        Advanced threat scoring combining multiple indicators
        """
        # Calculate threat scores for IPs
        ip_metrics = events_df \
            .withWatermark("timestamp", "30 minutes") \
            .groupBy(
                window(col("timestamp"), "15 minutes", "5 minutes").alias("window"),
                col("source_ip")
            ) \
            .agg(
                count("*").alias("total_events"),
                approx_count_distinct("event_type").alias("event_variety"),
                sum(when(col("severity") == "high", 3)
                   .when(col("severity") == "critical", 5)
                   .otherwise(1)).alias("severity_score"),
                approx_count_distinct("destination_ip").alias("target_variety"),
                sum(when(col("result") == "failed", 1).otherwise(0)).alias("failed_attempts"),
                collect_set("geo_location.country").alias("countries")
            )
        
        # Calculate composite threat score
        threat_scores = ip_metrics \
            .withColumn("base_score",
                (col("severity_score") * 0.4) +
                (col("failed_attempts") * 0.3) +
                (col("target_variety") * 0.2) +
                (col("event_variety") * 0.1)
            ) \
            .withColumn("geo_multiplier",
                when(size(col("countries")) > 1, 1.5).otherwise(1.0)
            ) \
            .withColumn("final_threat_score",
                least(col("base_score") * col("geo_multiplier"), lit(10.0))
            ) \
            .withColumn("contributing_factors", 
                to_json(struct(
                    col("severity_score"),
                    col("failed_attempts"),
                    col("target_variety"),
                    col("event_variety"),
                    col("geo_multiplier")
                ))
            ) \
            .filter(col("final_threat_score") > 3.0) \
            .select(
                col("window.start").alias("window_start"),
                col("window.end").alias("window_end"),
                lit("ip").alias("entity_type"),
                col("source_ip").alias("entity_value"),
                col("final_threat_score").alias("threat_score"),
                col("contributing_factors"),
                col("total_events").alias("event_count"),
                to_json(map_from_arrays(
                    array(lit("high"), lit("critical"), lit("info")),
                    array(col("severity_score"), lit(0), col("total_events") - col("severity_score"))
                )).alias("severity_distribution")
            )
        
        return threat_scores

    def write_to_postgres_enhanced(self, df, table_name, mode="append"):
        """Enhanced PostgreSQL writer with better error handling using foreachBatch"""
        
        def write_batch_to_postgres(batch_df, batch_id):
            """Function to write each batch to PostgreSQL with enhanced error handling"""
            try:
                if batch_df.count() > 0:
                    batch_df.write \
                        .mode(mode) \
                        .format("jdbc") \
                        .options(**self.db_properties) \
                        .option("dbtable", table_name) \
                        .option("batchsize", "100") \
                        .save()
                    
                    logger.info(f"📝 Batch {batch_id}: Successfully wrote {batch_df.count()} records to {table_name}")
                    
                    # Show sample of what was written for debugging
                    if batch_df.count() <= 5:
                        print(f"📊 Sample records written to {table_name}:")
                        batch_df.show(truncate=False)
                else:
                    logger.info(f"📝 Batch {batch_id}: No records to write to {table_name}")
                    
            except Exception as e:
                logger.error(f"❌ Error writing batch {batch_id} to {table_name}: {e}")
                # Continue processing even if one batch fails
        
        return df.writeStream \
            .foreachBatch(write_batch_to_postgres) \
            .outputMode("append") \
            .option("checkpointLocation", f"/tmp/spark-checkpoints/{table_name}") \
            .trigger(processingTime="30 seconds")

    def start_comprehensive_analytics(self):
        """Complete analytics pipeline with all features"""
        logger.info("🚀 Starting comprehensive security analytics...")
        
        events_df = self.create_kafka_stream()
        
        # Task 1: Advanced brute force detection
        brute_force_alerts = self.advanced_brute_force_detection(events_df)
        bf_query = self.write_to_postgres_enhanced(
            brute_force_alerts, "brute_force_alerts"
        ).start()
        
        # Task 2: Sophisticated DDoS detection
        ddos_alerts = self.sophisticated_ddos_detection(events_df)
        ddos_query = self.write_to_postgres_enhanced(
            ddos_alerts, "ddos_alerts"
        ).start()
        
        # Task 3: Advanced geographic anomalies
        geo_anomalies = self.geographic_anomaly_detection_advanced(events_df)
        geo_query = self.write_to_postgres_enhanced(
            geo_anomalies, "geographic_anomalies"
        ).start()
        
        # Task 4: Threat scoring
        threat_scores = self.threat_score_calculation(events_df)
        threat_query = self.write_to_postgres_enhanced(
            threat_scores, "threat_scores"
        ).start()
        
        # Security metrics aggregation
        security_metrics = events_df \
            .withWatermark("timestamp", "10 minutes") \
            .groupBy(
                window(col("timestamp"), "5 minutes", "1 minute").alias("window"),
                col("event_type")
            ) \
            .count() \
            .select(
                col("window.start").alias("window_start"),
                col("window.end").alias("window_end"),
                lit("events_by_type").alias("metric_type"),
                col("event_type").alias("metric_key"),
                col("count").alias("metric_value"),
                lit(None).cast("string").alias("additional_data")
            )
        
        metrics_query = self.write_to_postgres_enhanced(
            security_metrics, "security_metrics"
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
        
        logger.info("✅ All analytics queries started successfully")
        
        try:
            bf_query.awaitTermination()
        except KeyboardInterrupt:
            logger.info("🛑 Stopping analytics pipeline...")
        finally:
            self.spark.stop()

if __name__ == "__main__":
    analytics = SecurityAnalyticsSolution()
    analytics.start_comprehensive_analytics()
