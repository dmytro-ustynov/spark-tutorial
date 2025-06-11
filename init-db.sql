-- Create tables for security analytics aggregations

-- Table for brute force attack alerts
CREATE TABLE IF NOT EXISTS brute_force_alerts (
    id SERIAL PRIMARY KEY,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    source_ip INET NOT NULL,
    target_ip INET,
    username VARCHAR(255),
    failed_attempts INTEGER NOT NULL,
    severity VARCHAR(20) DEFAULT 'high',
    first_seen TIMESTAMP NOT NULL,
    last_seen TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(window_start, source_ip, target_ip, username)
);

-- Index for efficient querying
CREATE INDEX IF NOT EXISTS idx_brute_force_time ON brute_force_alerts(window_start, window_end);
CREATE INDEX IF NOT EXISTS idx_brute_force_ip ON brute_force_alerts(source_ip);

-- Table for DDoS attack detection
CREATE TABLE IF NOT EXISTS ddos_alerts (
    id SERIAL PRIMARY KEY,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    target_ip INET NOT NULL,
    target_port INTEGER,
    requests_per_second INTEGER NOT NULL,
    unique_source_ips INTEGER NOT NULL,
    total_requests INTEGER NOT NULL,
    severity VARCHAR(20) DEFAULT 'critical',
    attack_type VARCHAR(50) DEFAULT 'volumetric',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(window_start, target_ip, target_port)
);

-- Index for DDoS alerts
CREATE INDEX IF NOT EXISTS idx_ddos_time ON ddos_alerts(window_start, window_end);
CREATE INDEX IF NOT EXISTS idx_ddos_target ON ddos_alerts(target_ip, target_port);

-- Table for geographic anomalies
CREATE TABLE IF NOT EXISTS geographic_anomalies (
    id SERIAL PRIMARY KEY,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    username VARCHAR(255) NOT NULL,
    countries TEXT[], -- Array of countries
    source_ips TEXT[], -- Array of IPs
    max_distance_km INTEGER,
    time_diff_minutes INTEGER,
    risk_score DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for geographic anomalies
CREATE INDEX IF NOT EXISTS idx_geo_anom_time ON geographic_anomalies(window_start, window_end);
CREATE INDEX IF NOT EXISTS idx_geo_anom_user ON geographic_anomalies(username);

-- Table for general security metrics
CREATE TABLE IF NOT EXISTS security_metrics (
    id SERIAL PRIMARY KEY,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    metric_type VARCHAR(50) NOT NULL, -- 'events_by_type', 'severity_count', etc.
    metric_key VARCHAR(100) NOT NULL,  -- specific event type or severity level
    metric_value BIGINT NOT NULL,
    additional_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(window_start, metric_type, metric_key)
);

-- Index for metrics
CREATE INDEX IF NOT EXISTS idx_metrics_time ON security_metrics(window_start, window_end);
CREATE INDEX IF NOT EXISTS idx_metrics_type ON security_metrics(metric_type, metric_key);

-- Table for threat scores (advanced analysis)
CREATE TABLE IF NOT EXISTS threat_scores (
    id SERIAL PRIMARY KEY,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    entity_type VARCHAR(50) NOT NULL, -- 'ip', 'user', 'domain'
    entity_value VARCHAR(255) NOT NULL,
    threat_score DECIMAL(5,2) NOT NULL,
    contributing_factors JSONB,
    event_count INTEGER DEFAULT 0,
    severity_distribution JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(window_start, entity_type, entity_value)
);

-- Index for threat scores
CREATE INDEX IF NOT EXISTS idx_threat_scores_time ON threat_scores(window_start, window_end);
CREATE INDEX IF NOT EXISTS idx_threat_scores_entity ON threat_scores(entity_type, entity_value);
CREATE INDEX IF NOT EXISTS idx_threat_scores_score ON threat_scores(threat_score DESC);

-- Sample view for security dashboard
CREATE OR REPLACE VIEW security_dashboard AS
SELECT 
    DATE_TRUNC('hour', window_start) as hour,
    COUNT(DISTINCT bf.id) as brute_force_incidents,
    COUNT(DISTINCT dd.id) as ddos_incidents,
    COUNT(DISTINCT ga.id) as geo_anomalies,
    AVG(ts.threat_score) as avg_threat_score,
    MAX(ts.threat_score) as max_threat_score
FROM generate_series(
    NOW() - INTERVAL '24 hours',
    NOW(),
    INTERVAL '1 hour'
) AS hour_series(hour)
LEFT JOIN brute_force_alerts bf ON DATE_TRUNC('hour', bf.window_start) = hour_series.hour
LEFT JOIN ddos_alerts dd ON DATE_TRUNC('hour', dd.window_start) = hour_series.hour  
LEFT JOIN geographic_anomalies ga ON DATE_TRUNC('hour', ga.window_start) = hour_series.hour
LEFT JOIN threat_scores ts ON DATE_TRUNC('hour', ts.window_start) = hour_series.hour
GROUP BY hour_series.hour
ORDER BY hour_series.hour DESC;

-- Insert some sample data for testing
INSERT INTO security_metrics (window_start, window_end, metric_type, metric_key, metric_value) VALUES
(NOW() - INTERVAL '1 hour', NOW(), 'events_by_type', 'auth_attempt', 1500),
(NOW() - INTERVAL '1 hour', NOW(), 'events_by_type', 'network_connection', 3200),
(NOW() - INTERVAL '1 hour', NOW(), 'events_by_type', 'dns_query', 800),
(NOW() - INTERVAL '1 hour', NOW(), 'severity_count', 'info', 4800),
(NOW() - INTERVAL '1 hour', NOW(), 'severity_count', 'high', 150),
(NOW() - INTERVAL '1 hour', NOW(), 'severity_count', 'critical', 25);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO spark_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO spark_user;
