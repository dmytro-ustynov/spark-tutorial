# 🎓 Student Quick Start Guide

## What You Need
- ✅ Docker & Docker Compose installed
- ✅ This project folder

## What's Provided  
- ✅ Complete Spark environment (no installation needed!)
- ✅ Kafka, PostgreSQL, and event generator
- ✅ All required packages and connectors

---

## 🚀 Get Started in 3 Steps

### 1. Start Everything
```bash
docker-compose up -d
./lab-control.sh status
```

### 2. Choose Your Path

**🐳 Easy Mode (Recommended)** - Zero installation issues:
```bash
./lab-control.sh spark-shell    # Interactive Spark
./lab-control.sh jupyter        # Jupyter Lab at http://localhost:8888
```

**💻 Local Mode** - May have version conflicts:
```bash
pip install -r requirements.txt
python check_spark_compatibility.py     # Check compatibility first
python test_spark_kafka.py             # Test setup
```

> **💡 Having Scala/version errors?** Use containerized mode - it's pre-configured and guaranteed to work!

### 3. Run Analytics
```bash
# Container: 
./lab-control.sh spark-submit examples/containerized_analytics.py

# Local - Simple console output (recommended for learning):
python examples/improved_detection_analytics.py

# Local - Full database integration:
python examples/security_analytics_template.py
```

## 🎯 See Detection in Action
```bash
# 1. Start detection analytics
python examples/improved_detection_analytics.py

# 2. In another terminal, trigger attacks
./lab-control.sh attack-bf      # Brute force (watch for alerts in 2-3 min)
./lab-control.sh attack-ddos    # DDoS attack (watch for alerts in 1-2 min)

# 3. See detailed detection guide
# Read DETECTION_GUIDE.md for step-by-step solutions
```

---

## 🎯 See It Working
- **Live Events**: `./lab-control.sh logs`
- **Kafka UI**: http://localhost:8080
- **Spark UI**: http://localhost:4040 (when running)
- **Database**: http://localhost:5050 (admin@example.com/admin)

## 🔥 Simulate Attacks
```bash
./lab-control.sh attack-bf      # Brute force
./lab-control.sh attack-ddos    # DDoS attack
```

**Questions?** Check the full README.md for detailed explanations!
