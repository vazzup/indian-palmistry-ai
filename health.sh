#!/bin/bash

# Indian Palmistry AI - Health Check Script
# Quick health check for all services

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${BLUE}================================"
    echo -e "    Health Check Results"
    echo -e "================================${NC}\n"
}

# Function to check service health
check_service() {
    local name="$1"
    local url="$2"
    local expected="$3"
    
    if curl -s "$url" | grep -q "$expected" 2>/dev/null; then
        echo -e "${GREEN}✅ $name${NC} - Healthy"
        return 0
    else
        echo -e "${RED}❌ $name${NC} - Not responding"
        return 1
    fi
}

# Function to check docker service
check_docker_service() {
    local name="$1"
    local container="$2"
    
    if docker ps --filter "name=$container" --filter "status=running" | grep -q "$container" 2>/dev/null; then
        echo -e "${GREEN}✅ $name${NC} - Running"
        return 0
    else
        echo -e "${RED}❌ $name${NC} - Not running"
        return 1
    fi
}

main() {
    print_header
    
    local all_healthy=true
    
    # Check Docker services
    echo -e "${BLUE}🐳 Docker Services:${NC}"
    check_docker_service "Redis Database" "indian-palmistry-ai-redis-1" || all_healthy=false
    check_docker_service "Backend API" "indian-palmistry-ai-api-1" || all_healthy=false
    check_docker_service "Background Worker" "indian-palmistry-ai-worker-1" || all_healthy=false
    
    echo ""
    
    # Check service endpoints
    echo -e "${BLUE}🌐 Service Endpoints:${NC}"
    check_service "Backend API Health" "http://localhost:8000/healthz" "healthy" || all_healthy=false
    
    # Detect frontend port from logs
    local frontend_port="3000"
    if [ -f "frontend.log" ]; then
        local detected_port=$(grep -o "http://localhost:[0-9]*" frontend.log 2>/dev/null | head -1 | grep -o "[0-9]*" | head -1)
        if [ ! -z "$detected_port" ]; then
            frontend_port="$detected_port"
        fi
    fi
    
    check_service "Frontend Application" "http://localhost:$frontend_port" "Palmistry" || all_healthy=false
    check_service "API Documentation" "http://localhost:8000/docs" "FastAPI" || all_healthy=false
    
    echo ""
    
    # Check frontend process
    echo -e "${BLUE}⚛️  Frontend Process:${NC}"
    if [ -f "frontend.pid" ]; then
        FRONTEND_PID=$(cat frontend.pid)
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Next.js Process${NC} - Running (PID: $FRONTEND_PID)"
        else
            echo -e "${RED}❌ Next.js Process${NC} - Not running (stale PID)"
            all_healthy=false
        fi
    else
        echo -e "${YELLOW}⚠️  Next.js Process${NC} - PID file not found"
    fi
    
    echo ""
    
    # Overall status
    if $all_healthy; then
        echo -e "${GREEN}🎉 All systems healthy!${NC}"
        echo -e "${BLUE}📱 Ready to use:${NC} ${GREEN}http://localhost:$frontend_port${NC}"
        exit 0
    else
        echo -e "${RED}⚠️  Some services have issues${NC}"
        echo -e "${YELLOW}💡 Try running:${NC} ${BLUE}./restart.sh${NC}"
        exit 1
    fi
}

main "$@"