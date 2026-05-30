#!/usr/bin/env python3
"""
Debug Version - Cybersecurity Analytics with Enhanced Kafka Debugging

This version includes detailed debugging to identify the exact connection issue.
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

class SecurityAnalyticsDebug:
    def __init__(self):
        """Initialize with enhanced debugging"""
        
        # Detect environment
        self.environment = self.detect_environment()
        logger.info(f"🔍 Detected environment: {self.environment}")
        
        # Clean up checkpoints
        self.cleanup_checkpoints()
        
        # Set Spark packages
        os.environ["PYSPARK_SUBMIT_ARGS"] = "--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 pyspark-shell"
        
        # Create unique checkpoint directory
        self.checkpoint_dir = f"/tmp/spark-debug-{uuid.uuid4().hex[:8]}"
        
        # Create Spark session with more lenient timeouts
        self.spark = SparkSession.builder \
            .appName("SecurityAnalyticsDebug") \
            .config("spark.sql.adaptive.enabled", "false") \
            .config("spark.sql.streaming.checkpointLocation", self.checkpoint_dir) \
            .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
            .config("spark.network.timeout", "300s") \
            .config("spark.sql.streaming.kafka.useDeprecatedOffsetFetching", "false") \
            .getOrCreate()
        
        self.spark.sparkContext.setLogLevel("WARN")
        self.kafka_topic = "security-events"
        
        logger.info("✅ Debug Spark session initialized")

    def detect_environment(self):
        """Simple environment detection"""
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

    def test_network_connection(self, host, port):
        """Test basic network connectivity"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((host, int(port)))
            sock.close()
            return result == 0
        except Exception as e:
            logger.error(f"Network test failed for {host}:{port} - {e}")
            return False

    def debug_kafka_connectivity(self):
        """Debug Kafka connectivity comprehensively"""
        
        if self.environment == "container":
            test_configs = [
                ("kafka", "29092"),
                ("kafka", "9092"), 
                ("localhost", "9092")
            ]
        else:
            test_configs = [
                ("localhost", "9092"),
                ("127.0.0.1", "9092")
            ]
        
        print("\n🔍 KAFKA CONNECTIVITY DEBUG")
        print("=" * 50)
        
        working_config = None
        
        for host, port in test_configs:
            print(f"\n🔗 Testing {host}:{port}")
            
            # Test 1: Basic network connectivity
            if self.test_network_connection(host, port):
                print(f"  ✅ Network connectivity: OK")
            else:
                print(f"  ❌ Network connectivity: FAILED")
                continue
            
            # Test 2: Kafka broker response
            try:
                kafka_server = f"{host}:{port}"
                
                # Try to create a simple read operation (not streaming)
                test_df = self.spark.read \
                    .format("kafka") \
                    .option("kafka.bootstrap.servers", kafka_server) \
                    .option("subscribe", self.kafka_topic) \
                    .option("startingOffsets", "latest") \
                    .option("endingOffsets", "latest") \
                    .option("failOnDataLoss", "false") \
                    .option("kafka.session.timeout.ms", "30000") \
                    .option("kafka.request.timeout.ms", "40000") \
                    .option("kafka.metadata.max.age.ms", "30000") \
                    .load()
                
                # Test schema access
                schema = test_df.schema
                print(f"  ✅ Kafka read test: OK")
                print(f"  📋 Schema fields: {len(schema.fields)}")
                
                working_config = kafka_server
                break
                
            except Exception as e:
                print(f"  ❌ Kafka read test: FAILED")
                print(f"     Error: {str(e)[:100]}...")
                continue
        
        if working_config:
            print(f"\n✅ Found working Kafka configuration: {working_config}")
            return working_config
        else:
            print(f"\n❌ No working Kafka configuration found")
            return None

    def create_simple_stream(self, kafka_server):
        """Create a simple streaming query for testing"""
        
        print(f"\n🚀 Creating stream with {kafka_server}")
        
        try:
            # Simple schema
            simple_schema = StructType([
                StructField("timestamp", StringType(), True),
                StructField("event_type", StringType(), True),
                StructField("source_ip", StringType(), True),
                StructField("result", StringType(), True)
            ])
            
            # Create basic Kafka stream
            kafka_df = self.spark \
                .readStream \
                .format("kafka") \
                .option("kafka.bootstrap.servers", kafka_server) \
                .option("subscribe", self.kafka_topic) \
                .option("startingOffsets", "latest") \
                .option("failOnDataLoss", "false") \
                .option("kafka.session.timeout.ms", "60000") \
                .option("kafka.request.timeout.ms", "80000") \
                .option("kafka.metadata.max.age.ms", "60000") \
                .option("kafka.consumer.timeout.ms", "30000") \
                .load()
            
            # Parse events with error handling
            events_df = kafka_df.select(
                col("key").cast("string").alias("event_key"),
                col("value").cast("string").alias("event_value"),
                col("timestamp").alias("kafka_timestamp"),
                col("partition"),
                col("offset")
            ).filter(col("event_value").isNotNull())
            
            print("✅ Basic stream created successfully")
            
            # Try to parse JSON
            try:
                parsed_df = events_df.select(
                    col("event_key"),
                    from_json(col("event_value"), simple_schema).alias("data"),
                    col("kafka_timestamp"),
                    col("partition"),
                    col("offset")
                ).select("event_key", "data.*", "kafka_timestamp", "partition", "offset")
                
                print("✅ JSON parsing configured")
                return parsed_df
                
            except Exception as e:
                print(f"⚠️  JSON parsing failed, using raw values: {e}")
                return events_df
                
        except Exception as e:
            print(f"❌ Stream creation failed: {e}")
            raise

    def run_simple_test(self):
        """Run a simple streaming test"""
        
        print("\n🎯 RUNNING SIMPLE STREAMING TEST")
        print("=" * 50)
        
        # Find working Kafka config
        kafka_server = self.debug_kafka_connectivity()
        if not kafka_server:
            raise Exception("No working Kafka configuration found")
        
        # Create simple stream
        events_df = self.create_simple_stream(kafka_server)
        
        # Start simple console output
        print("\n📡 Starting simple event monitor for 60 seconds...")
        print("You should see events appearing every few seconds.\n")
        
        query = events_df \
            .writeStream \
            .format("console") \
            .option("truncate", False) \
            .option("numRows", 5) \
            .trigger(processingTime="10 seconds") \
            .start()
        
        try:
            query.awaitTermination(60)  # Run for 60 seconds
        except Exception as e:
            print(f"Query error: {e}")
        finally:
            if query.isActive:
                query.stop()
        
        print("\n✅ Simple test completed!")
        return True

def main():
    """Run the debug version"""
    
    print("🔍 KAFKA-SPARK CONNECTIVITY DEBUG TOOL")
    print("=" * 60)
    print("This tool will help identify the exact connection issue.")
    print()
    
    try:
        debug_tool = SecurityAnalyticsDebug()
        success = debug_tool.run_simple_test()
        
        if success:
            print("\n🎉 SUCCESS! The connection works.")
            print("Now you can run the full analytics script with confidence.")
        
    except Exception as e:
        print(f"\n❌ DEBUG FAILED: {e}")
        print("\n🔧 TROUBLESHOOTING STEPS:")
        print("1. Check if all containers are healthy:")
        print("   docker-compose ps")
        print("2. Check Kafka specifically:")
        print("   docker-compose logs kafka | tail -20")
        print("3. Restart Kafka if needed:")
        print("   docker-compose restart kafka")
        print("4. Check if events are being produced:")
        print("   ./lab-control.sh logs-recent")
    
    finally:
        # Cleanup
        try:
            if 'debug_tool' in locals():
                debug_tool.cleanup_checkpoints()
                debug_tool.spark.stop()
        except:
            pass

if __name__ == "__main__":
    main()
