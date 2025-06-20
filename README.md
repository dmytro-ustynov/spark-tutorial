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

## Prerequisites & Setup

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


##  Architecture

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

## Quick Start

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

** OPTION A: Containerized Spark (Recommended - No Installation Required)**
```bash
# Everything is pre-installed in containers!

# Interactive Spark shell with all packages pre-loaded
./lab-control.sh spark-shell

# Or use Jupyter Lab for development
./lab-control.sh jupyter
# Then open: http://localhost:8888

```

** OPTION B: Local Spark Installation**
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

### 3. See Detection in Action
```bash
# Start improved detection analytics (recommended for learning)
python examples/detection_analytics.py

# In another terminal, trigger attacks
./lab-control.sh attack-bf      # Brute force (alerts in 2-3 min)
./lab-control.sh attack-ddos    # DDoS attack (alerts in 1-2 min)

# Stop attacks when done
./lab-control.sh stop-attacks
```

**Need detailed guidance?** See **[DETECTION_GUIDE.md](DETECTION_GUIDE.md)** for step-by-step solutions!

## 🎓 Learning Paths & Examples

### **Beginner Level:**
```bash
# 1. Verify events are flowing
python verify_events.py

# 2. Console-only analytics (immediate feedback)
python examples/simple_console_analytics.py

# 3. Improved detection with debugging
python examples/detection_analytics.py
```

### **Intermediate Level:**
```bash
# 1. Full database integration
python examples/security_analytics_template.py

# 2. Containerized development
./lab-control.sh jupyter  # Interactive notebooks

# 3. Custom thresholds and windows
# Edit templates to adjust detection logic
```

## Generated Event Types & Attack Simulations

### Normal Traffic Events
- **Authentication Attempts**: Legitimate user logins (95% success rate)
- **Network Connections**: Regular HTTP/HTTPS traffic 
- **DNS Queries**: Standard domain lookups
- **File Access**: Normal file operations

### Attack Simulation Events

#### 🔥 Brute Force Attack Phases:
1. **Reconnaissance** (1 min): 2 failed logins/second = 120 total
2. **Medium Intensity** (3 min): 8 failed logins/second = 1,440 total  
3. **High Intensity** (2 min): 25 failed logins/second = 3,000 total

#### 💥 DDoS Attack Phases:
1. **Ramp Up** (1 min): 200 requests/second = 12,000 total
2. **Sustained** (3 min): 1,500 requests/second = 270,000 total
3. **Peak** (1 min): 3,000 requests/second = 180,000 total

### **Attack Controls:**
```bash
# Easy attack simulation controls
./lab-control.sh attack-bf      # Start brute force simulation
./lab-control.sh attack-ddos    # Start DDoS simulation
./lab-control.sh stop-attacks   # Stop all attacks

# Monitor real-time event generation
./lab-control.sh logs           # See live attack patterns
```

## Student Tasks & Objectives

### **Task 1: Basic Brute Force Detection**
**Objective**: Detect brute force attacks by counting failed login attempts

**Success Criteria**: 
- Detect IPs with ≥5 failed attempts in 2-minute windows
- Store alerts in `brute_force_alerts` table
- Handle late-arriving events with watermarking

### **Task 2: DDoS Traffic Analysis**
**Objective**: Identify DDoS attacks through traffic volume analysis

**Success Criteria**:
- Detect ≥100 requests/minute to single target
- Track approximate unique source IPs in attacks
- Store results in `ddos_alerts` table

### **Task 3: Geographic Anomaly Detection**
**Objective**: Detect impossible travel scenarios

**Success Criteria**:
- Identify users logging in from multiple countries within short timeframes
- Calculate geographic distances and time differences
- Store anomalies in `geographic_anomalies` table

### **Task 4: Advanced Threat Scoring**
**Objective**: Build composite threat scores

**Success Criteria**:
- Combine multiple event types for risk assessment
- Weight different attack indicators
- Maintain running threat scores per IP/user
- Store in `threat_scores` table

**Detailed task solutions:** See **[DETECTION_GUIDE.md](DETECTION_GUIDE.md)**

## Database Schema

The PostgreSQL database includes these pre-created tables:

- `brute_force_alerts` - Detected brute force attempts
- `ddos_alerts` - DDoS attack detection results  
- `geographic_anomalies` - Impossible travel detection
- `security_metrics` - General security metrics
- `threat_scores` - Composite threat assessments

**View schema details:** Check `init-db.sql` for complete table definitions and sample data.

## Development Tools & Interfaces

### **Web Interfaces:**
- **Kafka UI**: http://localhost:8080 - Monitor real-time event streams
- **Spark UI**: http://localhost:4040 - Monitor streaming jobs (when running)
- **Jupyter Lab**: http://localhost:8888 - Interactive development
- **pgAdmin**: http://localhost:5050 - Database management (admin@example.com/admin)
- **Log Generator**: http://localhost:3000/status - Control attack simulations

### **Command Line Tools:**
```bash
# Lab control (all-in-one management)
./lab-control.sh help           # Show all commands
./lab-control.sh status         # Check service health
./lab-control.sh logs           # View real-time event generation

# Spark development
./lab-control.sh spark-shell    # Interactive Spark
./lab-control.sh jupyter        # Jupyter Lab
./lab-control.sh spark-submit   # Submit applications

# Monitoring & debugging
./lab-control.sh kafka-ui       # Open Kafka monitoring
./lab-control.sh pgadmin        # Open database admin
./lab-control.sh logs-recent    # Recent activity summary
```

## Useful Commands & Examples

### **Real-time Monitoring:**
```bash
# View live event streaming
./lab-control.sh logs

# Check detection results in database
docker-compose exec postgres psql -U spark_user -d security_analytics -c "SELECT * FROM brute_force_alerts ORDER BY window_start DESC LIMIT 5;"

# Monitor Kafka topics
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Generate manual test events
curl -X POST http://localhost:3000/generate/100
```

### **Development Workflow:**
```bash
# 1. Start environment
docker-compose up -d

# 2. Verify setup
./lab-control.sh status
python verify_events.py

# 3. Develop analytics
./lab-control.sh jupyter  # Interactive development
# OR
python examples/improved_detection_analytics.py  # Console development

# 4. Test with attacks
./lab-control.sh attack-bf    # Trigger brute force
./lab-control.sh attack-ddos  # Trigger DDoS

# 5. Monitor results
# - Watch console output
# - Check Spark UI (http://localhost:4040)
# - Query database via pgAdmin
```

## 🛠️ Troubleshooting

### **Quick Fixes:**

**"Distinct aggregations are not supported on streaming DataFrames" Error**:
```bash
# Streaming doesn't support exact distinct counts
# Solution: Use approx_count_distinct() instead
# Our templates have been updated to use the correct approach
```

**"Data source jdbc does not support streamed writing" Error**:
```bash
# JDBC doesn't support direct streaming writes
# Solution: Use foreachBatch() pattern (included in our templates)
python examples/security_analytics_template.py
```

**Scala Version Compatibility Error**:
```bash
# Version mismatch between PySpark and Kafka connector
# Solution 1: Use containerized Spark (recommended)
./lab-control.sh spark-shell

# Solution 2: Check compatibility
python check_spark_compatibility.py
```

**No Events Appearing**:
```bash
# Check log generator health
curl http://localhost:3000/health
./lab-control.sh logs-recent

# Restart services if needed
docker-compose restart
```

### **Detailed Troubleshooting:**
- **Detection Problems**: See **[DETECTION_GUIDE.md](DETECTION_GUIDE.md)**  
- **Setup Issues**: See **[GETTING_STARTED.md](GETTING_STARTED.md)**

## Assessment Criteria

Students are evaluated on:

1. **Correctness**: Do detections catch actual attacks?
2. **Performance**: Efficient Spark operations and SQL queries
3. **Completeness**: Handle edge cases and late data
4. **Code Quality**: Clean, readable Spark applications
5. **Understanding**: Explain detection logic and streaming concepts
6. **Problem Solving**: Debug and fix compatibility issues

### **Success Metrics:**
- ✅ **Brute Force Detection**: Alerts within 2-3 minutes of attack start
- ✅ **DDoS Detection**: Alerts within 1-2 minutes of attack start  
- ✅ **Low False Positives**: <10% false positive rate
- ✅ **Actionable Information**: Alerts include source, target, severity
- ✅ **Real-time Processing**: Streaming updates every 30 seconds

## 📖 Additional Resources & Learning

### **Spark Streaming Concepts:**
- [Apache Spark Structured Streaming Guide](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)
- [Kafka Integration Guide](https://spark.apache.org/docs/latest/structured-streaming-kafka-integration.html)
- [Watermarking and Late Data](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html#handling-late-data-and-watermarking)

### **Cybersecurity Analytics:**
- [SIEM Analytics Patterns](https://github.com/topics/cybersecurity-analytics)
- [Real-time Threat Detection](https://www.elastic.co/what-is/siem)
- [Network Security Monitoring](https://zeek.org/)

### **Big Data & Streaming:**
- [Kafka Documentation](https://kafka.apache.org/documentation/)
- [PostgreSQL Streaming](https://www.postgresql.org/docs/current/logical-replication.html)
- [Stream Processing Patterns](https://www.confluent.io/blog/data-dichotomy-batch-versus-stream-processing/)

## Contributing & Support

### **For Instructors:**
- **Complete Solutions**: See `examples/instructor_solution.py`
- **Assessment Rubrics**: Defined in assessment criteria section
- **Custom Scenarios**: Modify `log-generator.js` attack patterns
- **Scaling**: Docker Compose supports multi-node deployment

### **For Students:**
- **Start Here**: Use **[GETTING_STARTED.md](GETTING_STARTED.md)**
- **Get Unstuck**: Check troubleshooting sections in relevant guides
- **Advanced Learning**: Explore instructor solutions after completing tasks
- **Real-world Application**: Consider internships in cybersecurity/data engineering

### **Repository Structure:**
```
spark-tutorial/
├── README.md                    # This comprehensive guide
├── GETTING_STARTED.md          # Quick start for students  
├── DETECTION_GUIDE.md          # Task solutions & explanations
├── docker-compose.yml          # Complete environment setup
├── examples/                   # All code templates & solutions
│   ├── simple_console_analytics.py
│   ├── improved_detection_analytics.py
│   ├── security_analytics_template.py
│   ├── containerized_analytics.py
│   └── instructor_solution.py
├── student-work/               # Student workspace
├── lab-control.sh             # Environment management script
└── init-db.sql               # Database schema & sample data
```

---

## Ready to Start!

### **Simple 5-Step Process:**

1. **🐳 Start**: `docker-compose up -d`
2. **✅ Verify**: `./lab-control.sh status`  
3. **📚 Learn**: Read **[GETTING_STARTED.md](GETTING_STARTED.md)**
4. **🚀 Detect**: `python examples/improved_detection_analytics.py`
5. **🔥 Attack**: `./lab-control.sh attack-bf` and watch the alerts!

### **Next Steps:**
- **Master Detection**: Follow **[DETECTION_GUIDE.md](DETECTION_GUIDE.md)** 
- **Build Custom Analytics**: Develop in `student-work/` directory
- **Scale Up**: Explore production deployment patterns

**Happy Learning!**