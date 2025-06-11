#!/usr/bin/env python3
"""
Spark Version Compatibility Checker
Helps diagnose and fix Spark-Kafka version conflicts
"""

import os
import sys

def check_spark_version():
    """Check installed PySpark version and suggest compatible packages"""
    try:
        import pyspark
        spark_version = pyspark.__version__
        print(f"📦 PySpark version: {spark_version}")
        
        # Version-specific package recommendations
        version_mapping = {
            "3.5.0": {
                "kafka": "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0",
                "postgres": "org.postgresql:postgresql:42.7.1"
            },
            "3.4.0": {
                "kafka": "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0", 
                "postgres": "org.postgresql:postgresql:42.6.0"
            },
            "3.3.0": {
                "kafka": "org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0",
                "postgres": "org.postgresql:postgresql:42.5.0"
            }
        }
        
        # Find compatible packages
        compatible_packages = None
        for version, packages in version_mapping.items():
            if spark_version.startswith(version[:3]):  # Match major.minor
                compatible_packages = packages
                break
        
        if compatible_packages:
            print(f"✅ Compatible packages found for Spark {spark_version}")
            print(f"📦 Kafka: {compatible_packages['kafka']}")
            print(f"🗄️  PostgreSQL: {compatible_packages['postgres']}")
            return compatible_packages
        else:
            print(f"⚠️  No exact match for Spark {spark_version}")
            print("🔧 Using default Spark 3.5.0 packages")
            return version_mapping["3.5.0"]
            
    except ImportError:
        print("❌ PySpark not installed")
        print("💡 Install with: pip install pyspark")
        return None

def test_with_compatible_packages():
    """Test Spark-Kafka with version-compatible packages"""
    packages = check_spark_version()
    if not packages:
        return False
    
    # Set environment variable with compatible packages
    package_list = f"{packages['kafka']},{packages['postgres']}"
    os.environ["PYSPARK_SUBMIT_ARGS"] = f"--packages {package_list} pyspark-shell"
    
    print(f"\n🔧 Using packages: {package_list}")
    print("🚀 Testing Spark-Kafka connection...")
    
    try:
        from pyspark.sql import SparkSession
        from pyspark.sql.functions import col
        
        spark = SparkSession.builder \
            .appName("CompatibilityTest") \
            .config("spark.sql.adaptive.enabled", "true") \
            .getOrCreate()
        
        spark.sparkContext.setLogLevel("WARN")
        
        print("✅ Spark session created successfully")
        
        # Test Kafka stream creation
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
        
        spark.stop()
        
        print("\n🎉 Compatibility test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n🔧 Troubleshooting suggestions:")
        print("1. Try using the containerized Spark: ./lab-control.sh spark-shell")
        print("2. Check if Kafka is running: ./lab-control.sh status") 
        print("3. Try a different PySpark version: pip install pyspark==3.4.0")
        return False

if __name__ == "__main__":
    print("🔍 Spark-Kafka Compatibility Checker")
    print("=" * 50)
    
    success = test_with_compatible_packages()
    
    if success:
        print("\n✅ Your local Spark setup is working!")
        print("📚 You can now run:")
        print("   python examples/security_analytics_template.py")
    else:
        print("\n🐳 Recommendation: Use containerized Spark instead")
        print("📚 Try these commands:")
        print("   ./lab-control.sh spark-shell")
        print("   ./lab-control.sh jupyter")
    
    sys.exit(0 if success else 1)
