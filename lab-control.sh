#!/bin/bash

# Control script for the Cybersecurity Analytics Lab
# Usage: ./lab-control.sh [command]

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

show_help() {
    echo -e "${BLUE}Cybersecurity Analytics Lab - Control Script${NC}"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo -e "  ${GREEN}start${NC}           Start all services"
    echo -e "  ${GREEN}stop${NC}            Stop all services"
    echo -e "  ${GREEN}restart${NC}         Restart all services"
    echo -e "  ${GREEN}status${NC}          Show service status"
    echo -e "  ${GREEN}test${NC}            Run setup verification tests"
    echo -e "  ${GREEN}logs${NC}            Show log generator logs"
    echo -e "  ${GREEN}logs-recent${NC}     Show recent logs (last 30 lines)"
    echo -e "  ${GREEN}clean${NC}           Stop and remove all containers/volumes"
    echo ""
    echo "Attack simulations:"
    echo -e "  ${YELLOW}attack-bf${NC}       Start brute force attack simulation"
    echo -e "  ${YELLOW}attack-ddos${NC}     Start DDoS attack simulation"
    echo -e "  ${YELLOW}stop-attacks${NC}    Stop all attack simulations"
    echo ""
    echo "Utilities:"
    echo -e "  ${BLUE}spark-shell${NC}     Open interactive Spark shell"
    echo -e "  ${BLUE}jupyter${NC}         Start Jupyter Lab for analytics"
    echo -e "  ${BLUE}spark-submit${NC}    Submit Spark application"
    echo -e "  ${BLUE}kafka-ui${NC}        Open Kafka UI in browser"
    echo -e "  ${BLUE}pgadmin${NC}         Open pgAdmin in browser"
    echo -e "  ${BLUE}generate${NC}        Generate test events"
    echo ""
}

start_services() {
    echo -e "${GREEN}🚀 Starting Cybersecurity Analytics Lab...${NC}"
    docker-compose up -d
    echo ""
    echo -e "${GREEN}✅ Services started! Waiting for initialization...${NC}"
    sleep 10
    
    echo "📊 Service Status:"
    docker-compose ps
}

stop_services() {
    echo -e "${YELLOW}🛑 Stopping all services...${NC}"
    docker-compose down
    echo -e "${GREEN}✅ Services stopped${NC}"
}

restart_services() {
    echo -e "${YELLOW}🔄 Restarting services...${NC}"
    docker-compose restart
    echo -e "${GREEN}✅ Services restarted${NC}"
}

show_status() {
    echo -e "${BLUE}📊 Service Status:${NC}"
    docker-compose ps
    echo ""
    
    echo -e "${BLUE}🌐 Web Interfaces:${NC}"
    echo "  • Log Generator: http://localhost:3000/status"
    echo "  • Kafka UI: http://localhost:8080"
    echo "  • pgAdmin: http://localhost:5050"
    echo "  • Spark UI: http://localhost:4040 (when analytics running)"
    echo "  • Jupyter Lab: http://localhost:8888 (when started)"
    echo ""
    
    echo -e "${BLUE}🎓 Student Quick Start:${NC}"
    echo "  1. Use containerized Spark (recommended):"
    echo "     ./lab-control.sh spark-shell"
    echo "     ./lab-control.sh jupyter"
    echo ""
    echo "  2. Or install locally:"
    echo "     pip install -r requirements.txt"
    echo "     python test_spark_kafka.py"
    echo ""
    
    # Check log generator status
    if curl -s http://localhost:3000/status > /dev/null 2>&1; then
        echo -e "${BLUE}🎯 Attack Simulation Status:${NC}"
        curl -s http://localhost:3000/status | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f\"  • Running: {data.get('isRunning', False)}\")
    print(f\"  • Active Workers: {', '.join(data.get('activeWorkers', []))}\")
except:
    print('  • Status unavailable')
"
    fi
}

run_tests() {
    echo -e "${BLUE}🔧 Running setup verification tests...${NC}"
    ./test-setup.sh
}

show_logs() {
    echo -e "${BLUE}📝 Log Generator Logs (Press Ctrl+C to exit):${NC}"
    echo -e "${YELLOW}💡 TIP: Watch for real-time event streaming and attack simulations!${NC}"
    echo ""
    docker-compose logs -f log-generator
}

clean_all() {
    echo -e "${RED}🧹 Cleaning up all containers and volumes...${NC}"
    echo -e "${YELLOW}⚠️  This will delete all data. Continue? (y/N)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        docker-compose down -v --remove-orphans
        docker system prune -f
        echo -e "${GREEN}✅ Cleanup complete${NC}"
    else
        echo "Cleanup cancelled"
    fi
}

start_bruteforce() {
    echo -e "${YELLOW}🔥 Starting brute force attack simulation...${NC}"
    response=$(curl -s -X POST http://localhost:3000/attack/bruteforce)
    if echo "$response" | grep -q "started"; then
        echo -e "${GREEN}✅ Brute force attack simulation started${NC}"
        echo "Monitor at: http://localhost:3000/status"
    else
        echo -e "${RED}❌ Failed to start brute force simulation${NC}"
        echo "$response"
    fi
}

start_ddos() {
    echo -e "${YELLOW}💥 Starting DDoS attack simulation...${NC}"
    response=$(curl -s -X POST http://localhost:3000/attack/ddos)
    if echo "$response" | grep -q "started"; then
        echo -e "${GREEN}✅ DDoS attack simulation started${NC}"
        echo "Monitor at: http://localhost:3000/status"
    else
        echo -e "${RED}❌ Failed to start DDoS simulation${NC}"
        echo "$response"
    fi
}

stop_attacks() {
    echo -e "${YELLOW}🛑 Stopping all attack simulations...${NC}"
    curl -s -X DELETE http://localhost:3000/attack/bruteforce > /dev/null
    curl -s -X DELETE http://localhost:3000/attack/ddos > /dev/null
    echo -e "${GREEN}✅ All attack simulations stopped${NC}"
}

open_spark_ui() {
    echo -e "${BLUE}🔥 Opening Spark UI...${NC}"
    if command -v open >/dev/null 2>&1; then
        open http://localhost:4040
    elif command -v xdg-open >/dev/null 2>&1; then
        xdg-open http://localhost:4040
    else
        echo "Open manually: http://localhost:4040"
    fi
}

start_jupyter() {
    echo -e "${BLUE}📊 Starting Jupyter Lab for analytics...${NC}"
    echo "Access at: http://localhost:8888"
    docker-compose exec spark-analytics jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --notebook-dir=/workspace
}

start_spark_shell() {
    echo -e "${BLUE}🔥 Starting interactive Spark shell...${NC}"
    echo "💡 Kafka and PostgreSQL packages are pre-loaded"
    docker-compose exec spark-analytics pyspark
}

submit_spark_app() {
    echo -e "${BLUE}🚀 Submit Spark application...${NC}"
    echo -n "Enter Python file path (e.g., examples/security_analytics_template.py): "
    read -r app_path
    
    if [ -z "$app_path" ]; then
        echo "❌ No file path provided"
        return 1
    fi
    
    docker-compose exec spark-analytics spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.1 "$app_path"
}

open_kafka_ui() {
    echo -e "${BLUE}🌐 Opening Kafka UI...${NC}"
    if command -v open >/dev/null 2>&1; then
        open http://localhost:8080
    elif command -v xdg-open >/dev/null 2>&1; then
        xdg-open http://localhost:8080
    else
        echo "Open manually: http://localhost:8080"
    fi
}

open_pgadmin() {
    echo -e "${BLUE}🗄️  Opening pgAdmin...${NC}"
    echo "Credentials: admin@example.com / admin"
    if command -v open >/dev/null 2>&1; then
        open http://localhost:5050
    elif command -v xdg-open >/dev/null 2>&1; then
        xdg-open http://localhost:5050
    else
        echo "Open manually: http://localhost:5050"
    fi
}

generate_events() {
    echo -e "${BLUE}📊 Generating test events...${NC}"
    echo -n "How many events to generate? (default: 50): "
    read -r count
    count=${count:-50}
    
    response=$(curl -s -X POST "http://localhost:3000/generate/$count")
    if echo "$response" | grep -q "Generated"; then
        echo -e "${GREEN}✅ Generated $count test events${NC}"
    else
        echo -e "${RED}❌ Failed to generate events${NC}"
        echo "$response"
    fi
}

# Main command processing
case "${1:-help}" in
    "start")
        start_services
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        restart_services
        ;;
    "status")
        show_status
        ;;
    "test")
        run_tests
        ;;
    "logs")
        show_logs
        ;;
    "logs-recent")
        echo -e "${BLUE}📝 Recent Log Generator Activity:${NC}"
        docker-compose logs --tail=30 log-generator
        ;;
    "clean")
        clean_all
        ;;
    "attack-bf")
        start_bruteforce
        ;;
    "attack-ddos")
        start_ddos
        ;;
    "stop-attacks")
        stop_attacks
        ;;
    "kafka-ui")
        open_kafka_ui
        ;;
    "pgadmin")
        open_pgadmin
        ;;
    "generate")
        generate_events
        ;;
    "spark-shell")
        start_spark_shell
        ;;
    "jupyter")
        start_jupyter
        ;;
    "spark-submit")
        submit_spark_app
        ;;
    "spark-ui")
        open_spark_ui
        ;;
    "help"|*)
        show_help
        ;;
esac
