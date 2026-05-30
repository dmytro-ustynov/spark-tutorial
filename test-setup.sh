#!/bin/bash

# Test script to verify the complete setup
echo "🔧 Testing Cybersecurity Analytics Setup..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if service is responding
check_service() {
    local service_name=$1
    local url=$2
    local expected_code=${3:-200}
    
    echo -n "Testing $service_name... "
    
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "$expected_code"; then
        echo -e "${GREEN}✅ OK${NC}"
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}"
        return 1
    fi
}

# Function to check docker service
check_docker_service() {
    local service_name=$1
    echo -n "Checking Docker service $service_name... "
    
    if docker compose ps | grep -q "$service_name.*Up"; then
        echo -e "${GREEN}✅ Running${NC}"
        return 0
    else
        echo -e "${RED}❌ Not running${NC}"
        return 1
    fi
}

echo ""
echo "🐳 Checking Docker services..."

# Check if Docker Compose (V2 plugin) is available
if ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ 'docker compose' not found (Docker Compose V2 plugin required)${NC}"
    exit 1
fi

# Check individual services
check_docker_service "zookeeper"
check_docker_service "kafka" 
check_docker_service "postgres"
check_docker_service "log-generator"

echo ""
echo "🌐 Testing HTTP endpoints..."

# Test log generator health
check_service "Log Generator Health" "http://localhost:3000/health"

# Test log generator status
check_service "Log Generator Status" "http://localhost:3000/status"

# Test Kafka UI
check_service "Kafka UI" "http://localhost:8080"

# Test pgAdmin
check_service "pgAdmin" "http://localhost:5050/login"

echo ""
echo "📊 Testing event generation..."

# Generate some test events
echo -n "Generating test events... "
response=$(curl -s -X POST http://localhost:3000/generate/10)
if echo "$response" | grep -q "Generated 10 events"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi

echo ""
echo "🔍 Testing database connectivity..."

# Test PostgreSQL connection
echo -n "Testing PostgreSQL connection... "
if docker compose exec -T postgres psql -U spark_user -d security_analytics -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Connected${NC}"
else
    echo -e "${RED}❌ Connection failed${NC}"
fi

# Check if tables exist
echo -n "Checking database tables... "
table_count=$(docker compose exec -T postgres psql -U spark_user -d security_analytics -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' \n')
if [ "$table_count" -gt 5 ]; then
    echo -e "${GREEN}✅ $table_count tables found${NC}"
else
    echo -e "${RED}❌ Only $table_count tables found${NC}"
fi

echo ""
echo "⚡ Testing attack simulations..."

# Test brute force attack
echo -n "Starting brute force simulation... "
bf_response=$(curl -s -X POST http://localhost:3000/attack/bruteforce)
if echo "$bf_response" | grep -q "Brute force attack simulation started"; then
    echo -e "${GREEN}✅ Started${NC}"
    
    # Wait a bit and stop it
    sleep 3
    echo -n "Stopping brute force simulation... "
    stop_response=$(curl -s -X DELETE http://localhost:3000/attack/bruteforce)
    if echo "$stop_response" | grep -q "stopped"; then
        echo -e "${GREEN}✅ Stopped${NC}"
    else
        echo -e "${YELLOW}⚠️  May still be running${NC}"
    fi
else
    echo -e "${RED}❌ Failed to start${NC}"
fi

echo ""
echo "📈 System status summary:"

# Get final status
status_response=$(curl -s http://localhost:3000/status)
echo "$status_response" | python3 -m json.tool 2>/dev/null || echo "$status_response"

echo ""
echo "🎓 Ready for student exercises!"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Students can now develop Spark analytics using examples/security_analytics_template.py"
echo "2. Monitor events at: http://localhost:8080 (Kafka UI)"
echo "3. View database at: http://localhost:5050 (pgAdmin - admin@example.com/admin)"
echo "4. Check analytics results in PostgreSQL tables"
echo ""
echo -e "${GREEN}Setup verification complete! 🎉${NC}"
