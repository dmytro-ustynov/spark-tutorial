#!/bin/bash

# Setup script for Spark Kafka integration
echo "🔧 Setting up Spark environment for Kafka integration..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Download Spark if not already present
SPARK_VERSION="3.5.0"
HADOOP_VERSION="3"
SPARK_DIR="spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}"

if [ ! -d "$SPARK_DIR" ]; then
    echo "📥 Downloading Apache Spark ${SPARK_VERSION}..."
    wget "https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/${SPARK_DIR}.tgz"
    tar -xzf "${SPARK_DIR}.tgz"
    rm "${SPARK_DIR}.tgz"
    echo "✅ Spark downloaded and extracted"
else
    echo "✅ Spark already available"
fi

# Set environment variables
export SPARK_HOME="$(pwd)/${SPARK_DIR}"
export PATH="$SPARK_HOME/bin:$PATH"
export PYSPARK_PYTHON=python3

# Create environment setup script
cat > setup_env.sh << EOF
#!/bin/bash
# Environment setup for Spark Kafka integration
export SPARK_HOME="$(pwd)/${SPARK_DIR}"
export PATH="\$SPARK_HOME/bin:\$PATH"
export PYSPARK_PYTHON=python3
export PYTHONPATH="\$SPARK_HOME/python:\$SPARK_HOME/python/lib/py4j-0.10.9.7-src.zip:\$PYTHONPATH"

echo "🚀 Spark environment configured!"
echo "SPARK_HOME: \$SPARK_HOME"
echo ""
echo "To run your analytics:"
echo "1. source venv/bin/activate"
echo "2. source setup_env.sh"
echo "3. python examples/security_analytics_template.py"
EOF

chmod +x setup_env.sh

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To get started:"
echo "1. source venv/bin/activate"
echo "2. source setup_env.sh" 
echo "3. python examples/spark_kafka_config.py  # Test configuration"
echo "4. python examples/security_analytics_template.py  # Run analytics"
echo ""
echo "💡 The setup automatically downloads required JARs when Spark starts"
