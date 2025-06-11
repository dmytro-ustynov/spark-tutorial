# Cybersecurity Analytics with Apache Spark

This educational project simulates real-world cybersecurity events and teaches students how to detect attacks using Apache Spark streaming analytics.

## Learning Objectives

Students will learn to:
- Process real-time security event streams with Spark Structured Streaming
- Detect brute force attacks using time-based aggregations
- Identify DDoS attacks through traffic pattern analysis
- Store analytical results in PostgreSQL
- Handle late-arriving data and implement watermarking
- Build scalable threat detection systems

## 📋 Prerequisites & Setup

### What You Need:
- **Docker & Docker Compose** (for running the lab environment)
- **Python 3.7+** (only if using local Spark option)

### What's Included:
- ✅ **Kafka** (event streaming) - containerized
- ✅ **PostgreSQL** (results storage) - containerized  
- ✅ **Log Generator** (security events) - containerized
- ✅ **Apache Spark** (analytics engine) - containerized with all JARs
- ✅ **Jupyter Lab** (interactive development) - containerized
- ✅ **All required packages** (Kafka connectors, PostgreSQL drivers)

### What You DON'T Need to Install:
- ❌ Apache Spark (included in container)
- ❌ Java/Scala (included in container)
- ❌ Kafka (included in container)  
- ❌ PostgreSQL (included in container)

**TL;DR**: Just Docker is required. Everything else runs in containers! 🐳

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Log Generator │───▶│      Kafka      │───▶│  Spark Streaming│
│   (Node.js)     │    │   (Event Bus)   │    │   (Analytics)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                                              ┌─────────────────┐
                                              │   PostgreSQL    │
                                              │ (Aggregations)  │
                                              └─────────────────┘
```

## 🚀 Quick Start

### 1. Start the Lab Environment
```bash
# Clone and navigate to project
cd spark-tutorial

# Start all services (Kafka, PostgreSQL, Log Generator, Spark)
docker-compose up -d

# Check that all services are running
./lab-control.sh status
```

### 2. Choose Your Spark Approach

**🐳 OPTION A: Containerized Spark (Recommended - No Installation Required)**
```bash
# Everything is pre-installed in containers!

# Interactive Spark shell with all packages pre-loaded
./lab-control.sh spark-shell

# Or use Jupyter Lab for development
./lab-control.sh jupyter
# Then open: http://localhost:8888

# Run example analytics
./lab-control.sh spark-submit examples/containerized_analytics.py
```

**💻 OPTION B: Local Spark Installation**
```bash
# Install Python dependencies  
pip install -r requirements.txt

# Test Spark-Kafka integration (auto-downloads JARs)
python test_spark_kafka.py

# Quick start with console output (no database needed)
python examples/simple_console_analytics.py

# Full analytics with PostgreSQL
python examples/security_analytics_template.py
```

### 3. Verify Event Generation
```bash
# Check log generator status
curl http://localhost:3000/status

# View generated events in Kafka UI
open http://localhost:8080
```

### 3. Setup Spark Environment for Students
```bash
# Install Python dependencies
pip install -r requirements.txt

# Test Spark-Kafka integration
python test_spark_kafka.py

# If successful, run the analytics template
python examples/security_analytics_template.py
```

### 4. Start Attack Simulations

**Option A: Via API**
```bash
# Start brute force attack
curl -X POST http://localhost:3000/attack/bruteforce

# Start DDoS attack  
curl -X POST http://localhost:3000/attack/ddos

# Stop specific attack
curl -X DELETE http://localhost:3000/attack/bruteforce
```

**Option B: Via Docker Command**
```bash
# Start container with immediate brute force attack
docker-compose run --rm log-generator node server.js -mode=bruteforce

# Start container with immediate DDoS attack
docker-compose run --rm log-generator node server.js -mode=ddos
```

## Generated Event Types

### Normal Traffic Events
- **Authentication Attempts**: Legitimate user logins
- **Network Connections**: Regular HTTP/HTTPS traffic
- **DNS Queries**: Standard domain lookups
- **File Access**: Normal file operations

### Attack Simulation Events

#### Brute Force Attack
```json
{
  "timestamp": "2025-06-11T10:31:12.456Z",
  "event_type": "auth_attempt",
  "source_ip": "203.0.113.15",
  "destination_ip": "10.0.0.100",
  "username": "admin",
  "result": "failed",
  "protocol": "SSH",
  "failure_reason": "invalid_password",
  "attempt_count": 45,
  "geo_location": {"country": "CN", "city": "Beijing"},
  "severity": "high"
}
```

#### DDoS Attack
```json
{
  "timestamp": "2025-06-11T10:32:01.234Z",
  "event_type": "network_connection",
  "source_ip": "198.51.100.42",
  "destination_ip": "10.0.0.200",
  "protocol": "HTTP",
  "port": 80,
  "requests_per_second": 1500,
  "response_code": 503,
  "severity": "critical"
}
```

##  Student Tasks

### Task 1: Basic Brute Force Detection
**Objective**: Detect brute force attacks by counting failed login attempts

```python
# Expected detection logic
failed_logins = df.filter(col("event_type") == "auth_attempt") \
  .filter(col("result") == "failed") \
  .groupBy(
    window(col("timestamp"), "5 minutes"),
    col("source_ip")
  ) \
  .count() \
  .filter(col("count") > 10)
```

**Success Criteria**: 
- Detect IPs with >10 failed attempts in 5-minute windows
- Store alerts in `brute_force_alerts` table
- Handle late-arriving events with watermarking

### Task 2: DDoS Traffic Analysis
**Objective**: Identify DDoS attacks through traffic volume analysis

```python
# Expected detection logic
ddos_detection = df.filter(col("event_type") == "network_connection") \
  .groupBy(
    window(col("timestamp"), "1 minute"),
    col("destination_ip"),
    col("port")
  ) \
  .agg(
    count("*").alias("request_count"),
    countDistinct("source_ip").alias("unique_sources")
  ) \
  .filter(col("request_count") > 1000)
```

**Success Criteria**:
- Detect >1000 requests/minute to single target
- Track unique source IPs in attacks
- Store results in `ddos_alerts` table

### Task 3: Geographic Anomaly Detection
**Objective**: Detect impossible travel scenarios

**Success Criteria**:
- Identify users logging in from multiple countries within short timeframes
- Calculate geographic distances and time differences
- Store anomalies in `geographic_anomalies` table

### Task 4: Advanced Threat Scoring
**Objective**: Build composite threat scores

**Success Criteria**:
- Combine multiple event types for risk assessment
- Weight different attack indicators
- Maintain running threat scores per IP/user
- Store in `threat_scores` table

## Database Schema

The PostgreSQL database includes these pre-created tables:

- `brute_force_alerts` - Detected brute force attempts
- `ddos_alerts` - DDoS attack detection results  
- `geographic_anomalies` - Impossible travel detection
- `security_metrics` - General security metrics
- `threat_scores` - Composite threat assessments

## Development Tools

### Kafka UI (http://localhost:8080)
- View real-time event streams
- Monitor topic partitions and consumer lag
- Inspect message contents

### pgAdmin (http://localhost:5050)
- **Email**: admin@example.com
- **Password**: admin
- Query analytical results
- Monitor table performance

## Useful Commands

```bash
# View real-time logs (see event streaming in action!)
docker-compose logs -f log-generator

# View recent activity summary
./lab-control.sh logs-recent

# Connect to PostgreSQL
docker-compose exec postgres psql -U spark_user -d security_analytics

# Generate test events manually
curl -X POST http://localhost:3000/generate/100

# Check Kafka topics
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Monitor event consumption
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic security-events \
  --from-beginning
```

## Attack Simulation Phases

### Brute Force Attack Phases
1. **Reconnaissance** (1 min): 2 attempts/second - slow probing
2. **Medium Intensity** (3 min): 8 attempts/second - active attack
3. **High Intensity** (2 min): 25 attempts/second - aggressive attack

### DDoS Attack Phases  
1. **Ramp Up** (1 min): 200 requests/second - building botnet
2. **Sustained** (3 min): 1500 requests/second - main attack
3. **Peak** (1 min): 3000 requests/second - maximum intensity

## Assessment Criteria

Students are evaluated on:

1. **Correctness**: Do detections catch actual attacks?
2. **Performance**: Efficient Spark operations and SQL queries
3. **Completeness**: Handle edge cases and late data
4. **Code Quality**: Clean, readable Spark applications
5. **Documentation**: Clear explanation of detection logic

##  Troubleshooting

### Common Issues

**"Failed to find data source: kafka" Error**:
```bash
# The error means Spark needs Kafka connector JARs
# Solution 1: Use our test script
python test_spark_kafka.py

# Solution 2: Set environment variable before running
export PYSPARK_SUBMIT_ARGS="--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.1 pyspark-shell"
python examples/security_analytics_template.py

# Solution 3: Use our configuration helper
python examples/spark_kafka_config.py
```

**Scala Version Compatibility Error** (`NoSuchMethodError: scala.collection.mutable.WrappedArray`):
```bash
# This indicates version mismatch between PySpark and Kafka connector
# Solution 1: Check and fix compatibility
python check_spark_compatibility.py

# Solution 2: Use containerized Spark (recommended)
./lab-control.sh spark-shell

# Solution 3: Reinstall with exact version
pip uninstall pyspark
pip install pyspark==3.5.0
```

**"Distinct aggregations are not supported on streaming DataFrames" Error**:
```bash
# Streaming doesn't support exact distinct counts
# Solution: Use approx_count_distinct() instead

# Wrong (causes error):
countDistinct("source_ip")

# Correct (streaming compatible):
approx_count_distinct("source_ip")

# Our templates have been updated to use the correct approach
```

**"Data source jdbc does not support streamed writing" Error**:
```bash
# This is expected - JDBC doesn't support direct streaming writes
# Our templates use foreachBatch() to handle this correctly
# If you see this error, you're using the old direct JDBC approach

# Solution: Use the updated templates with foreachBatch
python examples/security_analytics_template.py
python examples/containerized_analytics.py

# Test PostgreSQL connection separately
python test_postgres_connection.py
```

**Kafka Connection Issues**:
```bash
# Restart Kafka services
docker-compose restart zookeeper kafka
```

**No Events Generated**:
```bash
# Check log generator health
curl http://localhost:3000/health
docker-compose logs log-generator
```

**Database Connection Problems**:
```bash
# Verify PostgreSQL is running
docker-compose exec postgres pg_isready
```

## Additional Resources

- [Apache Spark Structured Streaming Guide](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)
- [Kafka Python Client Documentation](https://kafka-python.readthedocs.io/)
- [Cybersecurity Analytics Patterns](https://github.com/topics/cybersecurity-analytics)

---

**Happy Learning!**
