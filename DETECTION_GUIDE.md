# 🎯 Detection Task Solution Guide

## Understanding the Attack Simulations

### 🔥 Brute Force Attack Phases:
1. **Reconnaissance** (1 min): 2 failed logins/second = 120 total
2. **Medium Intensity** (3 min): 8 failed logins/second = 1,440 total  
3. **High Intensity** (2 min): 25 failed logins/second = 3,000 total

### 💥 DDoS Attack Phases:
1. **Ramp Up** (1 min): 200 requests/second = 12,000 total
2. **Sustained** (3 min): 1,500 requests/second = 270,000 total
3. **Peak** (1 min): 3,000 requests/second = 180,000 total

## 🧪 Step-by-Step Detection Process

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
python examples/improved_detection_analytics.py
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

## 🚨 Troubleshooting

### Streaming Limitations to Know:

**❌ Not Supported in Streaming:**
- `countDistinct()` - Use `approx_count_distinct()` instead
- Direct JDBC writes - Use `foreachBatch()` instead  
- `outputMode("complete")` with joins - Use `outputMode("append")`
- Complex window joins - Simplify or use stateful processing

**✅ Streaming Best Practices:**
- Use approximate aggregations when possible
- Keep window sizes reasonable (avoid very long windows)
- Use watermarking to handle late data
- Monitor checkpoint directory disk usage

### "No Alerts Appearing"
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

## 🏆 Success Criteria

✅ **Brute Force Detection**: Alerts within 2-3 minutes of attack start
✅ **DDoS Detection**: Alerts within 1-2 minutes of attack start  
✅ **Low False Positives**: <10% false positive rate
✅ **Actionable Information**: Alerts include source, target, severity
✅ **Real-time Processing**: Streaming updates every 30 seconds

## 📚 Next Steps

1. **Persistence**: Write alerts to PostgreSQL using foreachBatch
2. **Alerting**: Integration with notification systems
3. **Machine Learning**: Anomaly detection for unknown attacks
4. **Performance**: Optimize for high-volume streams
