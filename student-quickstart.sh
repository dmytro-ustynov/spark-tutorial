#!/bin/bash

# Quick start script for students
echo "🎓 Cybersecurity Analytics Lab - Student Quick Start"
echo "=================================================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install --user -r requirements.txt

# Test the setup
echo "🔧 Testing Spark-Kafka integration..."
python3 check_spark_compatibility.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Setup successful! You're ready to start the lab."
    echo ""
    echo "📚 What to do next:"
    echo "1. Make sure the lab environment is running: ./lab-control.sh status"
    echo "2. View live event streaming: ./lab-control.sh logs"
    echo "3. Start with the template: python3 examples/security_analytics_template.py"
    echo "4. Or test the configuration: python3 examples/spark_kafka_config.py"
    echo ""
    echo "💡 If you get package errors, try:"
    echo "   export PYSPARK_SUBMIT_ARGS=\"--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.1 pyspark-shell\""
else
    echo ""
    echo "❌ Local Spark setup has compatibility issues."
    echo ""
    echo "🐳 Recommended solution: Use containerized Spark"
    echo "1. Make sure containers are running: ./lab-control.sh start"
    echo "2. Use Spark shell: ./lab-control.sh spark-shell"
    echo "3. Or use Jupyter: ./lab-control.sh jupyter"
    echo ""
    echo "🔧 Alternative fixes:"
    echo "1. Check Kafka is accessible: telnet localhost 9092"
    echo "2. Verify log generator is working: curl http://localhost:3000/health"
    echo "3. Try reinstalling: pip uninstall pyspark && pip install pyspark==3.5.0"
fi
