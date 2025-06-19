#!/usr/bin/env python3
"""
Attack Rate Monitor

This script helps students manually verify attack patterns by monitoring 
event generation rates and calculating attack statistics in real-time.
"""

import requests
import time
import json
from datetime import datetime

class AttackRateMonitor:
    def __init__(self):
        self.log_generator_url = "http://localhost:3000"
        self.prev_event_count = 0
        self.start_time = time.time()
        
    def get_status(self):
        """Get current status from log generator"""
        try:
            response = requests.get(f"{self.log_generator_url}/status")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def calculate_attack_metrics(self, status):
        """Calculate real-time attack metrics"""
        metrics = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "is_running": status.get("isRunning", False),
            "active_workers": status.get("activeWorkers", []),
            "attack_active": False,
            "attack_types": [],
            "expected_rates": {}
        }
        
        workers = status.get("activeWorkers", [])
        
        if "bruteforce" in workers:
            metrics["attack_active"] = True
            metrics["attack_types"].append("Brute Force")
            metrics["expected_rates"]["auth_attempt"] = "50-200+ events/sec"
            
        if "ddos" in workers:
            metrics["attack_active"] = True
            metrics["attack_types"].append("DDoS")
            metrics["expected_rates"]["network_connection"] = "200-3000+ events/sec"
            
        if not metrics["attack_active"]:
            metrics["expected_rates"]["all_events"] = "~50 events/sec (normal)"
            
        return metrics
    
    def display_metrics(self, metrics):
        """Display formatted metrics"""
        print(f"\n🕒 [{metrics['timestamp']}] System Status:")
        print(f"   📊 Generator Running: {'✅' if metrics['is_running'] else '❌'}")
        print(f"   🔧 Active Workers: {metrics['active_workers']}")
        
        if metrics["attack_active"]:
            print(f"   🔥 ACTIVE ATTACKS: {', '.join(metrics['attack_types'])}")
            for event_type, rate in metrics["expected_rates"].items():
                print(f"      • {event_type}: {rate}")
        else:
            print(f"   ✅ Normal Operations")
            print(f"      • Expected rate: {metrics['expected_rates'].get('all_events', 'Unknown')}")
            
    def monitor_attack_phases(self):
        """Monitor and explain attack phases"""
        print("\n📊 ATTACK PHASE ANALYSIS")
        print("=" * 50)
        print("🎯 Brute Force Attack Phases:")
        print("   Phase 1 (0-1 min):  2 attempts/sec  = 120 total")
        print("   Phase 2 (1-4 min):  8 attempts/sec  = 1,440 total") 
        print("   Phase 3 (4-6 min): 25 attempts/sec  = 3,000 total")
        print("   📈 Total Expected: ~4,560 failed attempts over 6 minutes")
        
        print("\n🎯 DDoS Attack Phases:")
        print("   Phase 1 (0-1 min):   200 requests/sec = 12,000 total")
        print("   Phase 2 (1-4 min): 1,500 requests/sec = 270,000 total")
        print("   Phase 3 (4-5 min): 3,000 requests/sec = 180,000 total") 
        print("   📈 Total Expected: ~462,000 requests over 5 minutes")
        
    def manual_calculation_helper(self):
        """Help students calculate rates manually"""
        print("\n🧮 MANUAL RATE CALCULATION HELPER")
        print("=" * 50)
        print("📝 How to Calculate Event Rates from Logs:")
        print("   1. Watch ./lab-control.sh logs-recent")
        print("   2. Look for lines like: 'Current: 175.4/sec | Type: auth_attempt'")
        print("   3. Compare rates during normal vs attack periods:")
        print("      • Normal auth_attempt: ~5-15 events/sec")
        print("      • Attack auth_attempt: 50-200+ events/sec")
        print("      • Normal network_connection: ~10-30 events/sec")
        print("      • Attack network_connection: 200-3000+ events/sec")
        
        print("\n📊 Expected Detection Timeline:")
        print("   • 0-60 seconds: Attack ramps up")
        print("   • 60-120 seconds: Should trigger first alerts")
        print("   • 120+ seconds: Consistent alerts every 30 seconds")
        
    def run_monitoring(self, duration_minutes=5):
        """Run continuous monitoring"""
        print("🔍 ATTACK RATE MONITORING DASHBOARD")
        print("=" * 60)
        print(f"⏱️  Monitoring for {duration_minutes} minutes...")
        print("💡 Commands to try in another terminal:")
        print("   • ./lab-control.sh attack-bf    (start brute force)")
        print("   • ./lab-control.sh attack-ddos  (start DDoS)")
        print("   • ./lab-control.sh stop-attacks (stop all attacks)")
        print("   • ./lab-control.sh logs-recent  (view event rates)")
        
        # Show attack phase information
        self.monitor_attack_phases()
        self.manual_calculation_helper()
        
        print(f"\n🚀 Starting {duration_minutes}-minute monitoring session...")
        print("=" * 60)
        
        end_time = time.time() + (duration_minutes * 60)
        
        while time.time() < end_time:
            status = self.get_status()
            
            if "error" in status:
                print(f"❌ Error connecting to log generator: {status['error']}")
                print("💡 Make sure the lab environment is running: docker-compose up -d")
            else:
                metrics = self.calculate_attack_metrics(status)
                self.display_metrics(metrics)
                
                # Provide recommendations
                if not metrics["attack_active"]:
                    print("   💡 No attacks detected. Try: ./lab-control.sh attack-bf")
                else:
                    print("   🎯 Attack active! Check analytics output for alerts.")
            
            time.sleep(10)  # Update every 10 seconds
            
        print(f"\n✅ Monitoring session complete!")
        print("📊 Summary: Check your analytics script output for detection results")

def main():
    """Main entry point"""
    print("🎯 CYBERSECURITY ATTACK RATE MONITOR")
    print("=" * 50)
    print("This tool helps you understand attack patterns and verify detection logic.")
    print("\n🎓 Learning Objectives:")
    print("   • Understand normal vs attack traffic patterns")
    print("   • Calculate attack rates manually")
    print("   • Verify detection thresholds are appropriate")
    print("   • Monitor attack phase transitions")
    
    monitor = AttackRateMonitor()
    
    # Quick status check first
    print("\n🔍 Quick Status Check:")
    status = monitor.get_status()
    if "error" not in status:
        metrics = monitor.calculate_attack_metrics(status)
        monitor.display_metrics(metrics)
    else:
        print(f"❌ Cannot connect to log generator: {status['error']}")
        print("💡 Make sure lab is running: docker-compose up -d")
        return
    
    # Ask user for monitoring duration
    try:
        duration = input("\n⏱️  How many minutes to monitor? (default: 5): ").strip()
        duration = int(duration) if duration else 5
    except ValueError:
        duration = 5
    
    # Start monitoring
    monitor.run_monitoring(duration_minutes=duration)

if __name__ == "__main__":
    main()
