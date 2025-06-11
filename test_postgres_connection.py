#!/usr/bin/env python3
"""
PostgreSQL Connection Test
Verifies that Spark can connect to and write to PostgreSQL
"""

import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

def test_postgres_connection():
    """Test PostgreSQL connection and basic operations"""
    
    print("🔧 Testing PostgreSQL connection...")
    
    # Set up packages
    os.environ["PYSPARK_SUBMIT_ARGS"] = "--packages org.postgresql:postgresql:42.7.1 pyspark-shell"
    
    try:
        # Create Spark session
        spark = SparkSession.builder \
            .appName("PostgreSQLTest") \
            .config("spark.sql.adaptive.enabled", "true") \
            .getOrCreate()
        
        spark.sparkContext.setLogLevel("WARN")
        
        # Database connection properties
        db_properties = {
            "user": "spark_user",
            "password": "spark_password",
            "driver": "org.postgresql.Driver",
            "url": "jdbc:postgresql://localhost:5432/security_analytics"
        }
        
        print("✅ Spark session created")
        
        # Test 1: Read existing data
        print("📖 Testing read from PostgreSQL...")
        try:
            existing_data = spark.read \
                .format("jdbc") \
                .options(**db_properties) \
                .option("dbtable", "security_metrics") \
                .load()
            
            count = existing_data.count()
            print(f"✅ Successfully read {count} records from security_metrics table")
            
            if count > 0:
                print("📋 Sample data:")
                existing_data.show(5, truncate=False)
            
        except Exception as e:
            print(f"⚠️  Could not read existing data (table might be empty): {e}")
        
        # Test 2: Write test data
        print("📝 Testing write to PostgreSQL...")
        
        # Create test data
        test_data = [
            ("2025-06-11 19:00:00", "2025-06-11 19:05:00", "test_metric", "test_event", 42),
            ("2025-06-11 19:05:00", "2025-06-11 19:10:00", "test_metric", "test_auth", 24)
        ]
        
        schema = StructType([
            StructField("window_start", StringType(), True),
            StructField("window_end", StringType(), True),
            StructField("metric_type", StringType(), True),
            StructField("metric_key", StringType(), True),
            StructField("metric_value", IntegerType(), True)
        ])
        
        test_df = spark.createDataFrame(test_data, schema) \
            .withColumn("window_start", to_timestamp(col("window_start"))) \
            .withColumn("window_end", to_timestamp(col("window_end"))) \
            .withColumn("additional_data", lit(None).cast("string"))
        
        print("📊 Test data to write:")
        test_df.show(truncate=False)
        
        # Write test data
        test_df.write \
            .mode("append") \
            .format("jdbc") \
            .options(**db_properties) \
            .option("dbtable", "security_metrics") \
            .save()
        
        print("✅ Successfully wrote test data to PostgreSQL")
        
        # Test 3: Verify write
        print("🔍 Verifying written data...")
        verification_df = spark.read \
            .format("jdbc") \
            .options(**db_properties) \
            .option("dbtable", "security_metrics") \
            .load() \
            .filter(col("metric_type") == "test_metric")
        
        written_count = verification_df.count()
        print(f"✅ Verified: {written_count} test records found in database")
        
        if written_count > 0:
            print("📋 Written test data:")
            verification_df.show(truncate=False)
        
        spark.stop()
        
        print("\n🎉 PostgreSQL connection test passed!")
        print("📚 You can now run streaming analytics that write to PostgreSQL")
        
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL connection test failed: {e}")
        print("\n🔧 Troubleshooting steps:")
        print("1. Check if PostgreSQL container is running: docker-compose ps")
        print("2. Check if database is accessible: docker-compose exec postgres psql -U spark_user -d security_analytics -c 'SELECT 1;'")
        print("3. Verify network connectivity: docker network ls")
        return False

if __name__ == "__main__":
    print("🗄️  PostgreSQL Connection Test")
    print("=" * 40)
    
    success = test_postgres_connection()
    
    if not success:
        print("\n💡 Consider using the containerized Spark environment:")
        print("   ./lab-control.sh spark-shell")
    
    exit(0 if success else 1)
