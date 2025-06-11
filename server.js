const LogGenerator = require('./log-generator');
const express = require('express');

class SecurityLogServer {
  constructor() {
    this.app = express();
    this.port = process.env.PORT || 3000;
    this.logGenerator = new LogGenerator(
      process.env.KAFKA_BROKER || 'kafka:29092',
      process.env.KAFKA_TOPIC || 'security-events'
    );
    
    this.setupMiddleware();
    this.setupRoutes();
    this.setupGracefulShutdown();
  }
  
  setupMiddleware() {
    this.app.use(express.json());
    this.app.use((req, res, next) => {
      console.log(`📝 ${new Date().toISOString()} - ${req.method} ${req.path}`);
      next();
    });
  }
  
  setupRoutes() {
    // Health check
    this.app.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        generator: this.logGenerator.getStatus()
      });
    });
    
    // Start attacks via API
    this.app.post('/attack/bruteforce', async (req, res) => {
      try {
        this.logGenerator.startBruteForceAttack();
        res.json({
          message: 'Brute force attack simulation started',
          timestamp: new Date().toISOString()
        });
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });
    
    this.app.post('/attack/ddos', async (req, res) => {
      try {
        this.logGenerator.startDDoSAttack();
        res.json({
          message: 'DDoS attack simulation started',
          timestamp: new Date().toISOString()
        });
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });
    
    // Stop specific attacks
    this.app.delete('/attack/:mode', (req, res) => {
      const { mode } = req.params;
      this.logGenerator.stopAttack(mode);
      res.json({
        message: `${mode} attack simulation stopped`,
        timestamp: new Date().toISOString()
      });
    });
    
    // Get current status
    this.app.get('/status', (req, res) => {
      res.json({
        ...this.logGenerator.getStatus(),
        timestamp: new Date().toISOString()
      });
    });
    
    // Manual event generation for testing
    this.app.post('/generate/:count', async (req, res) => {
      const count = parseInt(req.params.count) || 10;
      const events = [];
      
      for (let i = 0; i < count; i++) {
        const event = this.logGenerator.generateNormalEvent();
        events.push(event);
        await this.logGenerator.sendEvent(event);
      }
      
      res.json({
        message: `Generated ${count} events`,
        sample: events[0]
      });
    });
  }
  
  setupGracefulShutdown() {
    const gracefulShutdown = async (signal) => {
      console.log(`🔄 Received ${signal}, shutting down gracefully...`);
      
      try {
        await this.logGenerator.stop();
        process.exit(0);
      } catch (error) {
        console.error('❌ Error during shutdown:', error);
        process.exit(1);
      }
    };
    
    process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
    process.on('SIGINT', () => gracefulShutdown('SIGINT'));
  }
  
  async start() {
    try {
      // Wait for Kafka to be ready
      await this.waitForKafka();
      
      // Start log generation
      await this.logGenerator.start();
      
      // Start HTTP server
      this.app.listen(this.port, () => {
        console.log(`🌐 Security Log Server running on port ${this.port}`);
        console.log(`📊 Health check: http://localhost:${this.port}/health`);
        console.log(`📈 Status endpoint: http://localhost:${this.port}/status`);
        console.log(`⚡ Attack endpoints:`);
        console.log(`   POST /attack/bruteforce - Start brute force simulation`);
        console.log(`   POST /attack/ddos - Start DDoS simulation`);
        console.log(`   DELETE /attack/{mode} - Stop attack simulation`);
        
        // Handle command line arguments for immediate attack simulation
        this.handleCommandLineArgs();
      });
      
    } catch (error) {
      console.error('❌ Failed to start server:', error);
      process.exit(1);
    }
  }
  
  async waitForKafka(maxRetries = 30, retryInterval = 2000) {
    console.log('⏳ Waiting for Kafka to be ready...');
    
    for (let i = 0; i < maxRetries; i++) {
      try {
        const kafka = this.logGenerator.kafka;
        const admin = kafka.admin();
        await admin.connect();
        await admin.disconnect();
        console.log('✅ Kafka is ready');
        return;
      } catch (error) {
        console.log(`🔄 Kafka not ready yet (attempt ${i + 1}/${maxRetries}), retrying...`);
        await new Promise(resolve => setTimeout(resolve, retryInterval));
      }
    }
    
    throw new Error('Kafka failed to become ready within timeout period');
  }
  
  handleCommandLineArgs() {
    const args = process.argv.slice(2);
    
    for (const arg of args) {
      if (arg.startsWith('-mode=')) {
        const mode = arg.split('=')[1];
        
        // Start attack after a short delay to ensure everything is initialized
        setTimeout(() => {
          switch (mode) {
            case 'bruteforce':
              console.log('🎯 Auto-starting brute force attack from command line');
              this.logGenerator.startBruteForceAttack();
              break;
            case 'ddos':
              console.log('🎯 Auto-starting DDoS attack from command line');
              this.logGenerator.startDDoSAttack();
              break;
            default:
              console.log(`⚠️  Unknown mode: ${mode}. Available modes: bruteforce, ddos`);
          }
        }, 5000); // 5 second delay
        
        break;
      }
    }
  }
}

// Start the server
if (require.main === module) {
  const server = new SecurityLogServer();
  server.start().catch(error => {
    console.error('💥 Failed to start server:', error);
    process.exit(1);
  });
}

module.exports = SecurityLogServer;
