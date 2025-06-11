const { Kafka } = require('kafkajs');
const crypto = require('crypto');

class LogGenerator {
  constructor(kafkaBroker = 'kafka:29092', topic = 'security-events') {
    this.kafka = new Kafka({
      clientId: 'log-generator',
      brokers: [kafkaBroker]
    });
    
    this.producer = this.kafka.producer();
    this.topic = topic;
    this.isRunning = false;
    this.workers = new Map();
    this.eventCounter = 0;
    this.lastLogTime = Date.now();
    
    // Base configuration
    this.config = {
      baselineRate: 50, // events per second for normal traffic
      burstMultiplier: 10,
      attackDuration: 300000, // 5 minutes default
      consoleLogging: process.env.CONSOLE_LOGGING !== 'false', // Enable by default
      logInterval: 10, // Log every N events
    };
    
    // IP pools for different traffic types
    this.ipPools = {
      legitimate: this.generateIPPool('192.168.1', 100),
      internal: this.generateIPPool('10.0.0', 50),
      attackers: [
        '203.0.113.15', '198.51.100.42', '172.16.254.100',
        '185.220.101.42', '89.248.167.131', '45.144.225.119'
      ],
      botnet: this.generateIPPool('103.224.182', 200, 'random')
    };
    
    // Geographic data for realism
    this.geoData = {
      legitimate: [
        { country: 'US', city: 'New York' },
        { country: 'CA', city: 'Toronto' },
        { country: 'GB', city: 'London' },
        { country: 'DE', city: 'Berlin' },
        { country: 'UA', city: 'kyiv' }
      ],
      malicious: [
        { country: 'CN', city: 'Beijing' },
        { country: 'RU', city: 'Moscow' },
        { country: 'RU', city: 'Rostov' },
        { country: 'IR', city: 'Tehran' },
        { country: 'KP', city: 'Pyongyang' }
      ]
    };
  }
  
  generateIPPool(base, count, type = 'sequential') {
    const ips = [];
    for (let i = 1; i <= count; i++) {
      if (type === 'random') {
        ips.push(`${base}.${Math.floor(Math.random() * 255)}`);
      } else {
        ips.push(`${base}.${i}`);
      }
    }
    return ips;
  }
  
  async start() {
    await this.producer.connect();
    this.isRunning = true;
    console.log('🚀 Log Generator started - Normal traffic mode');
    console.log(`📈 Baseline rate: ${this.config.baselineRate} events/second`);
    console.log(`📋 Event types: auth_attempt, network_connection, dns_query, file_access`);
    console.log(`🌍 Geographic distribution: US, CA, GB, DE (legitimate) vs CN, RU, IR, KP (attacks)`);
    console.log(`🔧 Console logging: ${this.config.consoleLogging ? 'ENABLED' : 'DISABLED'} (every ${this.config.logInterval} events)`);
    
    // Start normal traffic generation
    this.startNormalTraffic();
  }
  
  async stop() {
    this.isRunning = false;
    
    // Stop all workers
    for (const [mode, worker] of this.workers) {
      clearInterval(worker);
      console.log(`Stopped ${mode} worker`);
    }
    this.workers.clear();
    
    await this.producer.disconnect();
    console.log('Log Generator stopped');
  }
  
  startNormalTraffic() {
    const normalWorker = setInterval(() => {
      if (!this.isRunning) return;
      
      // Generate multiple events per interval to maintain baseline rate
      const eventsCount = Math.floor(this.config.baselineRate / 10); // 10 intervals per second
      
      for (let i = 0; i < eventsCount; i++) {
        const event = this.generateNormalEvent();
        this.sendEvent(event);
      }
    }, 100); // Every 100ms
    
    this.workers.set('normal', normalWorker);
    
    // Add periodic statistics logging
    const statsWorker = setInterval(() => {
      if (!this.isRunning) return;
      
      const activeWorkers = Array.from(this.workers.keys());
      const workerStatus = activeWorkers.length > 1 ? 
        `🎯 ATTACK MODE: ${activeWorkers.filter(w => w !== 'normal').join(', ').toUpperCase()}` : 
        '🟢 NORMAL MODE';
      
      console.log(`\n📊 === LOG GENERATOR STATS ===`);
      console.log(`⏰ Time: ${new Date().toLocaleTimeString()}`);
      console.log(`📈 Total events sent: ${this.eventCounter}`);
      console.log(`🔧 Status: ${workerStatus}`);
      console.log(`🎛️  Active workers: ${activeWorkers.join(', ')}`);
      console.log(`================================\n`);
    }, 30000); // Every 30 seconds
    
    this.workers.set('stats', statsWorker);
  }
  
  startBruteForceAttack() {
    if (this.workers.has('bruteforce')) {
      console.log('⚠️  Brute force attack already running');
      return;
    }
    
    console.log('🔥 Starting brute force attack simulation');
    console.log(`🎯 Target IPs: 10.0.0.100, 10.0.0.101, 10.0.0.102`);
    console.log(`👤 Testing usernames: admin, root, administrator, user, test, guest`);
    console.log(`⏱️  Attack phases: 1min recon → 3min medium → 2min intense`);
    
    const attackConfig = {
      targetIPs: ['10.0.0.100', '10.0.0.101', '10.0.0.102'],
      attackerIPs: this.ipPools.attackers,
      usernames: ['admin', 'root', 'administrator', 'user', 'test', 'guest'],
      phases: [
        { duration: 60000, rate: 2 },   // 1min - reconnaissance
        { duration: 180000, rate: 8 },  // 3min - medium intensity  
        { duration: 120000, rate: 25 }  // 2min - high intensity
      ]
    };
    
    let phaseIndex = 0;
    let phaseStart = Date.now();
    
    const bruteForceWorker = setInterval(() => {
      if (!this.isRunning) return;
      
      const currentPhase = attackConfig.phases[phaseIndex];
      if (!currentPhase) return;
      
      const elapsed = Date.now() - phaseStart;
      
      // Check if we need to move to next phase
      if (elapsed > currentPhase.duration) {
        phaseIndex++;
        phaseStart = Date.now();
        if (phaseIndex >= attackConfig.phases.length) {
          this.stopAttack('bruteforce');
          return;
        }
        console.log(`🔄 Brute force attack - Phase ${phaseIndex + 1}`);
      }
      
      // Generate attack events based on current phase rate
      const eventsCount = Math.floor(currentPhase.rate / 10);
      for (let i = 0; i < eventsCount; i++) {
        const event = this.generateBruteForceEvent(attackConfig);
        this.sendEvent(event);
      }
    }, 100);
    
    this.workers.set('bruteforce', bruteForceWorker);
    
    // Auto-stop after total duration
    setTimeout(() => {
      this.stopAttack('bruteforce');
    }, this.config.attackDuration);
  }
  
  startDDoSAttack() {
    if (this.workers.has('ddos')) {
      console.log('⚠️  DDoS attack already running');
      return;
    }
    
    console.log('💥 Starting DDoS attack simulation');
    console.log(`🎯 Targets: Web (10.0.0.200:80), HTTPS (10.0.0.201:443), DNS (10.0.0.202:53)`);
    console.log(`🤖 Botnet size: ~200 unique IPs`);
    console.log(`⏱️  Attack phases: 1min ramp → 3min sustained → 1min peak`);
    
    const attackConfig = {
      targets: [
        { ip: '10.0.0.200', port: 80, service: 'web' },
        { ip: '10.0.0.201', port: 443, service: 'https' },
        { ip: '10.0.0.202', port: 53, service: 'dns' }
      ],
      botnetIPs: this.ipPools.botnet,
      phases: [
        { duration: 60000, rps: 200 },   // 1min - ramp up
        { duration: 180000, rps: 1500 }, // 3min - sustained
        { duration: 60000, rps: 3000 }   // 1min - peak
      ]
    };
    
    let phaseIndex = 0;
    let phaseStart = Date.now();
    
    const ddosWorker = setInterval(() => {
      if (!this.isRunning) return;
      
      const currentPhase = attackConfig.phases[phaseIndex];
      if (!currentPhase) return;
      
      const elapsed = Date.now() - phaseStart;
      
      if (elapsed > currentPhase.duration) {
        phaseIndex++;
        phaseStart = Date.now();
        if (phaseIndex >= attackConfig.phases.length) {
          this.stopAttack('ddos');
          return;
        }
        console.log(`🔄 DDoS attack - Phase ${phaseIndex + 1}`);
      }
      
      // Generate DDoS events
      const eventsCount = Math.floor(currentPhase.rps / 10);
      for (let i = 0; i < eventsCount; i++) {
        const event = this.generateDDoSEvent(attackConfig);
        this.sendEvent(event);
      }
    }, 100);
    
    this.workers.set('ddos', ddosWorker);
    
    setTimeout(() => {
      this.stopAttack('ddos');
    }, this.config.attackDuration);
  }
  
  stopAttack(mode) {
    if (this.workers.has(mode)) {
      clearInterval(this.workers.get(mode));
      this.workers.delete(mode);
      console.log(`🛑 Stopped ${mode} attack simulation`);
    }
  }
  
  generateNormalEvent() {
    const eventTypes = ['auth_attempt', 'network_connection', 'dns_query', 'file_access'];
    const eventType = eventTypes[Math.floor(Math.random() * eventTypes.length)];
    
    const baseEvent = {
      timestamp: new Date().toISOString(),
      event_id: crypto.randomUUID(),
      event_type: eventType,
      severity: 'info'
    };
    
    switch (eventType) {
      case 'auth_attempt':
        return {
          ...baseEvent,
          source_ip: this.randomItem(this.ipPools.legitimate),
          destination_ip: this.randomItem(this.ipPools.internal),
          username: this.randomItem(['john.doe', 'jane.smith', 'mike.wilson', 'sarah.davis']),
          result: Math.random() > 0.05 ? 'success' : 'failed', // 5% failure rate
          protocol: this.randomItem(['SSH', 'RDP', 'LDAP']),
          port: 22,
          geo_location: this.randomItem(this.geoData.legitimate),
          user_agent: 'OpenSSH_8.0'
        };
        
      case 'network_connection':
        return {
          ...baseEvent,
          source_ip: this.randomItem(this.ipPools.legitimate),
          destination_ip: this.randomItem(this.ipPools.internal),
          protocol: 'HTTP',
          port: Math.random() > 0.5 ? 80 : 443,
          bytes_sent: Math.floor(Math.random() * 5000) + 500,
          bytes_received: Math.floor(Math.random() * 10000) + 1000,
          response_code: Math.random() > 0.1 ? 200 : 404,
          request_method: this.randomItem(['GET', 'POST', 'PUT'])
        };
        
      case 'dns_query':
        return {
          ...baseEvent,
          source_ip: this.randomItem(this.ipPools.legitimate),
          query: this.randomItem(['google.com', 'github.com', 'stackoverflow.com', 'company.internal']),
          query_type: 'A',
          response_code: 'NOERROR'
        };
        
      default:
        return {
          ...baseEvent,
          source_ip: this.randomItem(this.ipPools.legitimate),
          file_path: this.randomItem(['/var/log/auth.log', '/home/user/document.pdf', '/etc/passwd']),
          action: this.randomItem(['read', 'write', 'execute']),
          user: this.randomItem(['user1', 'user2', 'service_account'])
        };
    }
  }
  
  generateBruteForceEvent(config) {
    return {
      timestamp: new Date().toISOString(),
      event_id: crypto.randomUUID(),
      event_type: 'auth_attempt',
      source_ip: this.randomItem(config.attackerIPs),
      destination_ip: this.randomItem(config.targetIPs),
      username: this.randomItem(config.usernames),
      result: 'failed',
      protocol: 'SSH',
      port: 22,
      failure_reason: this.randomItem(['invalid_password', 'invalid_username', 'account_locked']),
      attempt_count: Math.floor(Math.random() * 100) + 1,
      geo_location: this.randomItem(this.geoData.malicious),
      severity: 'high',
      user_agent: 'automated_tool'
    };
  }
  
  generateDDoSEvent(config) {
    const target = this.randomItem(config.targets);
    
    return {
      timestamp: new Date().toISOString(),
      event_id: crypto.randomUUID(),
      event_type: 'network_connection',
      source_ip: this.randomItem(config.botnetIPs),
      destination_ip: target.ip,
      protocol: target.service === 'dns' ? 'UDP' : 'HTTP',
      port: target.port,
      bytes_sent: Math.floor(Math.random() * 100) + 10, // Small requests
      bytes_received: 0, // No response due to overload
      connection_duration: 0.001,
      request_method: 'GET',
      response_code: Math.random() > 0.7 ? 503 : null, // Service unavailable
      requests_per_second: Math.floor(Math.random() * 1000) + 500,
      severity: 'critical',
      geo_location: this.randomItem(this.geoData.malicious)
    };
  }
  
  async sendEvent(event) {
    try {
      await this.producer.send({
        topic: this.topic,
        messages: [{
          key: event.event_id,
          value: JSON.stringify(event),
          timestamp: Date.now().toString()
        }]
      });
      
      // Console logging for students to see activity
      this.eventCounter++;
      if (this.config.consoleLogging && this.eventCounter % this.config.logInterval === 0) {
        const now = Date.now();
        const timeDiff = (now - this.lastLogTime) / 1000;
        const eventsPerSec = (this.config.logInterval / timeDiff).toFixed(1);
        
        console.log(`📊 [${new Date().toLocaleTimeString()}] Sent ${this.eventCounter} events | Current: ${eventsPerSec}/sec | Type: ${event.event_type} | Severity: ${event.severity}`);
        
        if (event.severity === 'high' || event.severity === 'critical') {
          console.log(`🚨 ALERT: ${event.event_type} from ${event.source_ip} - ${JSON.stringify(event, null, 2)}`);
        }
        
        this.lastLogTime = now;
      }
      
    } catch (error) {
      console.error('❌ Error sending event:', error.message);
    }
  }
  
  randomItem(array) {
    return array[Math.floor(Math.random() * array.length)];
  }
  
  getStatus() {
    return {
      isRunning: this.isRunning,
      activeWorkers: Array.from(this.workers.keys()),
      config: this.config
    };
  }
}

module.exports = LogGenerator;
