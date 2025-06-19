# Detection Task Solution Guide

## Understanding the Attack Simulations

### Brute Force Attack Phases:
1. **Reconnaissance** (1 min): 2 failed logins/second = 120 total
2. **Medium Intensity** (3 min): 8 failed logins/second = 1,440 total  
3. **High Intensity** (2 min): 25 failed logins/second = 3,000 total

### DDoS Attack Phases:
1. **Ramp Up** (1 min): 200 requests/second = 12,000 total
2. **Sustained** (3 min): 1,500 requests/second = 270,000 total
3. **Peak** (1 min): 3,000 requests/second = 180,000 total

## 📊 How to Monitor Attack Rates and Verify Detection

### Step 1: Check Attack Status
```bash
# Verify brute force attack is active
./lab-control.sh status

# Look for: Active Workers: ['normal', 'stats', 'bruteforce']
# If bruteforce is missing, run: ./lab-control.sh attack-bf
```

### Step 2: Calculate Event Rates Manually
```bash
# Monitor real-time event generation
./lab-control.sh logs-recent

# Look for patterns like:
# [6:37:40 PM] Sent 153660 events | Current: 200.0/sec | Type: auth_attempt
# [6:37:41 PM] Sent 153690 events | Current: 85.5/sec | Type: auth_attempt
# [6:37:41 PM] Sent 153700 events | Current: 128.2/sec | Type: auth_attempt
```

**📝 Manual Rate Calculation:**
- **Normal traffic**: auth_attempt events at ~5-15/sec
- **Brute force attack**: auth_attempt events at 50-200+/sec
- **Attack detection**: Look for sustained high rates over 2+ minutes

### Step 3: Verify Events with HTTP API
```bash
# Check attack status programmatically
curl http://localhost:3000/status

# Expected during attack:
# {"isRunning":true,"activeWorkers":["normal","stats","bruteforce"],...}

# Generate test events manually
curl -X POST http://localhost:3000/generate/100
```

## Step-by-Step Detection Process

### Step 1: Verify Event Generation
```bash
# Check if events are being generated
./lab-control.sh logs-recent

# You should see output like:
# 📊 [2:15:30 PM] Sent 50 events | Current: 5.2/sec | Type: network_connection | Severity: info
```

### Step 2: Run Improved Detection Script
```bash
# Use the improved version with debugging
python examples/detection_analytics.py
```

### Step 3: Start Attack Simulation
```bash
# In another terminal, start brute force attack
./lab-control.sh attack-bf

# Watch the console output for:
# - Raw events showing failed auth attempts
# - Failed login monitor showing attack IPs
# - Brute force alerts when threshold exceeded
```

### Step 4: Observe Detection Results
After 30-60 seconds, you should see:

**Failed Login Monitor:**
```
|timestamp          |event_type   |source_ip     |destination_ip|username|failure_reason  |country|
|2025-06-11 19:15:00|auth_attempt |203.0.113.15  |10.0.0.100    |admin   |invalid_password|CN     |
|2025-06-11 19:15:01|auth_attempt |203.0.113.15  |10.0.0.100    |root    |invalid_password|CN     |
```

**Brute Force Alerts:**
```
|window_start       |window_end         |source_ip   |target_ip |failed_attempts|alert_type           |detected_at        |
|2025-06-11 19:15:00|2025-06-11 19:17:00|203.0.113.15|10.0.0.100|240           |🚨 BRUTE_FORCE_DETECTED|2025-06-11 19:17:05|
```

## 🔧 Detection Thresholds Explained

### Brute Force Detection Logic:
```python
# Window: 2 minutes, sliding every 30 seconds
# Threshold: ≥5 failed logins per IP
brute_force_alerts = events_df \
    .filter(col("event_type") == "auth_attempt") \
    .filter(col("result") == "failed") \
    .groupBy(
        window(col("timestamp"), "2 minutes", "30 seconds"),
        col("source_ip"),
        col("destination_ip")
    ) \
    .count() \
    .filter(col("count") >= 5)  # Adjust this threshold
```

### DDoS Detection Logic:
```python
# Window: 1 minute, sliding every 30 seconds  
# Threshold: ≥100 requests per target
# Note: Use approx_count_distinct for streaming compatibility
ddos_alerts = events_df \
    .filter(col("event_type") == "network_connection") \
    .groupBy(
        window(col("timestamp"), "1 minute", "30 seconds"),
        col("destination_ip")
    ) \
    .agg(
        count("*").alias("request_count"),
        approx_count_distinct("source_ip").alias("unique_sources")  # Approximate count for streaming
    ) \
    .filter(col("count") >= 100)  # Adjust this threshold
```

## 🎯 Attack Pattern Recognition

### **Identifying Brute Force Attacks Manually:**

1. **Check Event Rates**:
   ```bash
   # During normal operation:
   # [6:36:50 PM] Current: 15.0/sec | Type: auth_attempt
   
   # During brute force attack:
   # [6:36:50 PM] Current: 200.0/sec | Type: auth_attempt
   # [6:36:51 PM] Current: 175.4/sec | Type: auth_attempt
   ```

2. **Calculate Attack Volume**:
   - **Phase 1 (Reconnaissance)**: 2 attempts/sec × 60 sec = 120 failed attempts
   - **Phase 2 (Medium)**: 8 attempts/sec × 180 sec = 1,440 failed attempts  
   - **Phase 3 (High)**: 25 attempts/sec × 120 sec = 3,000 failed attempts
   - **Total Attack**: ~4,560 failed login attempts over 6 minutes

3. **Expected Detection Timeline**:
   - **0-60 seconds**: Attack ramps up, may not trigger alerts yet
   - **60-120 seconds**: Medium intensity, should start triggering alerts
   - **120+ seconds**: High intensity, consistent alerts every 30 seconds

### **Verifying Database Persistence:**

```bash
# Check if alerts are being written to database
docker-compose exec -T postgres psql -U spark_user -d security_analytics -c "
SELECT 
    window_start,
    source_ip,
    failed_attempts,
    alert_type,
    detected_at 
FROM brute_force_alerts 
ORDER BY detected_at DESC 
LIMIT 5;"
```

**Expected Output During Active Attack:**
```
     window_start     |  source_ip   | failed_attempts |      alert_type       |     detected_at     
----------------------+--------------+-----------------+-----------------------+---------------------
 2025-06-19 18:45:00  | 203.0.113.15 |             240 | BRUTE_FORCE_DETECTED  | 2025-06-19 18:47:05
 2025-06-19 18:44:30  | 203.0.113.15 |             180 | BRUTE_FORCE_DETECTED  | 2025-06-19 18:46:35
```

## 🎓 Student Tasks

### Task 1: Adjust Detection Thresholds
**Goal**: Find the right balance between catching attacks and avoiding false positives

**Experiment**:
```python
# Try different thresholds:
.filter(col("count") >= 10)    # More strict
.filter(col("count") >= 3)     # More sensitive
```

### Task 2: Improve Detection Windows
**Goal**: Optimize detection speed vs. accuracy

**Experiment**:
```python
# Different window sizes:
window(col("timestamp"), "1 minute", "15 seconds")   # Faster detection
window(col("timestamp"), "5 minutes", "1 minute")    # More stable
```

### Task 3: Add Context to Alerts
**Goal**: Provide more useful information in alerts

**Enhancement**:
```python
.select(
    col("window.start").alias("window_start"),
    col("source_ip"),
    col("count").alias("failed_attempts"),
    collect_set("username").alias("targeted_users"),      # NEW
    collect_set("failure_reason").alias("failure_types"), # NEW
    max("attempt_count").alias("max_attempts")             # NEW
)
```

### Task 4: Geographic Analysis
**Goal**: Detect attacks from suspicious countries

**Enhancement**:
```python
geo_analysis = events_df \
    .filter(col("event_type") == "auth_attempt") \
    .filter(col("result") == "failed") \
    .filter(col("geo_location.country").isin(["CN", "RU", "IR", "KP"])) \
    .groupBy(
        window(col("timestamp"), "3 minutes"),
        col("geo_location.country")
    ) \
    .count() \
    .filter(col("count") >= 5)
```

## 🔍 Troubleshooting Common Issues

### "Analytics Script Won't Connect to Kafka"

**Problem**: Networking configuration in containers
```
WARN NetworkClient: Connection to node -1 (localhost/127.0.0.1:9092) could not be established
```

**Solution 1**: Use containerized Spark approach
```bash
# Fix Kafka connection for container environment
# Replace localhost:9092 with kafka:29092 in scripts
```

**Solution 2**: Run outside container
```bash
# Install Spark locally and use localhost:9092
pip install -r requirements.txt
python examples/detection_analytics.py
```

### "No Events Appearing"
1. **Check thresholds**: May be too high for simulation
2. **Verify timing**: Attack phases take time to build up
3. **Check data parsing**: Timestamp conversion issues
4. **Monitor raw events**: Ensure events are flowing

### "Too Many False Positives"  
1. **Increase thresholds**: Higher count requirements
2. **Lengthen windows**: More data for analysis
3. **Add filters**: Geographic, time-based filters

### "Detection Too Slow"
1. **Shorter windows**: Faster but less stable
2. **Lower thresholds**: Earlier detection
3. **Multiple thresholds**: Severity levels

## 📈 Performance Monitoring

### **Event Rate Analysis**
Create a simple script to monitor event rates:

```python
import time
import requests

def monitor_attack_rates():
    """Monitor and display real-time attack statistics"""
    prev_count = 0
    while True:
        try:
            response = requests.get('http://localhost:3000/status')
            status = response.json()
            
            print(f"Active Workers: {status.get('activeWorkers', [])}")
            
            if 'bruteforce' in status.get('activeWorkers', []):
                print("🔥 BRUTE FORCE ATTACK ACTIVE")
                print("   Expected: 50-200+ auth_attempt events/sec")
            else:
                print("✅ Normal traffic (no active attacks)")
                print("   Expected: 5-15 auth_attempt events/sec")
                
            time.sleep(10)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_attack_rates()
```

### **Database Query Examples**

```sql
-- Count total brute force alerts
SELECT COUNT(*) as total_alerts FROM brute_force_alerts;

-- Show most targeted IPs
SELECT destination_ip, COUNT(*) as attack_count 
FROM brute_force_alerts 
GROUP BY destination_ip 
ORDER BY attack_count DESC;

-- Show attack timeline
SELECT 
    DATE_TRUNC('minute', window_start) as minute,
    COUNT(*) as alerts_per_minute
FROM brute_force_alerts 
GROUP BY DATE_TRUNC('minute', window_start)
ORDER BY minute;
```

##  Success Criteria

✅ **Brute Force Detection**: Alerts within 2-3 minutes of attack start
✅ **DDoS Detection**: Alerts within 1-2 minutes of attack start  
✅ **Low False Positives**: <10% false positive rate
✅ **Actionable Information**: Alerts include source, target, severity
✅ **Real-time Processing**: Streaming updates every 30 seconds
✅ **Database Persistence**: Alerts stored for historical analysis

## 🚀 Advanced Challenges

### **Challenge 1**: Multi-Phase Detection
Detect different phases of brute force attacks with varying sensitivity:
- Phase 1: Loose thresholds for early warning
- Phase 2: Medium thresholds for confirmed attack
- Phase 3: Strict thresholds for high-confidence alerts

### **Challenge 2**: Machine Learning Integration
Use Spark ML to detect anomalous patterns:
- Baseline normal behavior
- Detect deviations from normal patterns
- Adaptive thresholds based on historical data

### **Challenge 3**: Real-time Alerting
Integrate with external systems:
- Send alerts to Slack/Teams
- Email notifications
- Security dashboard updates

##  Next Steps

1. **Persistence**: Write alerts to PostgreSQL using foreachBatch
2. **Alerting**: Integration with notification systems
3. **Machine Learning**: Anomaly detection for unknown attacks
4. **Performance**: Optimize for high-volume streams