#!/usr/bin/env python3

import json
import time
import requests

def check_attack_status():
    """Check if attacks are running via the log generator API"""
    try:
        response = requests.get('http://localhost:3000/status')
        data = response.json()
        print("🔍 Attack Status:")
        print(f"  Running: {data.get('isRunning', False)}")
        print(f"  Active Workers: {data.get('activeWorkers', [])}")
        print(f"  Config: {data.get('config', {})}")
        print()
        return data
    except Exception as e:
        print(f"❌ Error checking attack status: {e}")
        return None

def generate_and_check_events():
    """Generate some test events and see what's produced"""
    try:
        print("🎯 Generating 50 test events...")
        response = requests.post('http://localhost:3000/generate/50')
        
        if response.status_code == 200:
            print("✅ Events generated successfully")
        else:
            print(f"❌ Failed to generate events: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error generating events: {e}")

def main():
    print("=== Spark Tutorial Event Inspector ===\n")
    
    # Check attack status
    status = check_attack_status()
    
    if status and 'bruteforce' in status.get('activeWorkers', []):
        print("🔥 Brute force attack is ACTIVE")
        print("   This means auth_attempt events should be generated at high rates")
        print("   Expected: 2-25 failed login attempts per second")
    else:
        print("⚠️  Brute force attack is NOT active")
        print("   Run: ./lab-control.sh attack-bf to start it")
    
    print()
    
    # Generate test events to verify system is working
    generate_and_check_events()
    
    print("\n📊 What you should see in the logs:")
    print("  • Normal events: ~50 events/sec of mixed types")
    print("  • Brute force: 200+ auth_attempt events/sec during attack")
    print("  • Check with: ./lab-control.sh logs-recent")
    
    print("\n🎓 What students should observe:")
    print("  1. Run an analytics script (e.g., detection_analytics.py)")
    print("  2. Start brute force: ./lab-control.sh attack-bf")
    print("  3. Within 2-3 minutes, alerts should appear showing:")
    print("     - Multiple failed login attempts from same IP")
    print("     - Source IPs with >5 failed attempts in 2-minute windows")
    print("     - Targeted usernames (admin, root, etc.)")
    
    print("\n🔧 Expected Detection Results:")
    print("  • Failed Login Monitor: Shows individual failed attempts")
    print("  • Brute Force Alerts: Aggregated alerts when threshold exceeded")
    print("  • Database: brute_force_alerts table populated")

if __name__ == "__main__":
    main()
