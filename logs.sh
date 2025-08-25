#!/bin/bash

# Indian Palmistry AI - Logs Viewer
# This script shows logs for different services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${BLUE}================================"
    echo -e "  Indian Palmistry AI Logs"
    echo -e "================================${NC}\n"
}

# Function to show usage
show_usage() {
    echo -e "${YELLOW}Usage:${NC} $0 [service]"
    echo -e "\n${BLUE}Available services:${NC}"
    echo -e "  ${GREEN}api${NC}      - Backend API logs"
    echo -e "  ${GREEN}worker${NC}   - Background worker logs"
    echo -e "  ${GREEN}redis${NC}    - Redis database logs"
    echo -e "  ${GREEN}frontend${NC} - Frontend application logs"
    echo -e "  ${GREEN}all${NC}      - All services logs (default)"
    echo -e "\n${BLUE}Examples:${NC}"
    echo -e "  $0           # Show all logs"
    echo -e "  $0 api       # Show only API logs"
    echo -e "  $0 frontend  # Show only frontend logs"
}

# Function to show API logs
show_api_logs() {
    echo -e "${BLUE}📋 Backend API Logs:${NC}"
    echo -e "${YELLOW}────────────────────${NC}"
    docker logs indian-palmistry-ai-api-1 --tail 50 || echo -e "${RED}API container not running${NC}"
}

# Function to show worker logs
show_worker_logs() {
    echo -e "\n${BLUE}🔧 Background Worker Logs:${NC}"
    echo -e "${YELLOW}──────────────────────────${NC}"
    docker logs indian-palmistry-ai-worker-1 --tail 50 || echo -e "${RED}Worker container not running${NC}"
}

# Function to show Redis logs
show_redis_logs() {
    echo -e "\n${BLUE}💾 Redis Database Logs:${NC}"
    echo -e "${YELLOW}───────────────────────${NC}"
    docker logs indian-palmistry-ai-redis-1 --tail 20 || echo -e "${RED}Redis container not running${NC}"
}

# Function to show frontend logs
show_frontend_logs() {
    echo -e "\n${BLUE}🎨 Frontend Application Logs:${NC}"
    echo -e "${YELLOW}──────────────────────────────${NC}"
    if [ -f "frontend.log" ]; then
        tail -50 frontend.log
    else
        echo -e "${RED}Frontend log file not found${NC}"
        echo -e "${YELLOW}Frontend might be running in a separate terminal${NC}"
    fi
}

# Function to show service status
show_status() {
    echo -e "\n${BLUE}📊 Service Status:${NC}"
    echo -e "${YELLOW}───────────────────${NC}"
    
    # Check Docker services
    if docker compose ps > /dev/null 2>&1; then
        docker compose ps
    else
        echo -e "${RED}Docker Compose services not running${NC}"
    fi
    
    # Check frontend
    echo -e "\n${BLUE}Frontend Status:${NC}"
    if [ -f "frontend.pid" ]; then
        FRONTEND_PID=$(cat frontend.pid)
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Frontend running (PID: $FRONTEND_PID)${NC}"
        else
            echo -e "${RED}❌ Frontend not running (stale PID file)${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Frontend PID file not found${NC}"
    fi
    
    # Check URLs
    echo -e "\n${BLUE}Service Health:${NC}"
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend: http://localhost:3000${NC}"
    else
        echo -e "${RED}❌ Frontend: http://localhost:3000${NC}"
    fi
    
    if curl -s http://localhost:8000/healthz > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend API: http://localhost:8000${NC}"
    else
        echo -e "${RED}❌ Backend API: http://localhost:8000${NC}"
    fi
}

# Main execution
main() {
    print_header
    
    case "${1:-all}" in
        "api")
            show_api_logs
            ;;
        "worker")
            show_worker_logs
            ;;
        "redis")
            show_redis_logs
            ;;
        "frontend")
            show_frontend_logs
            ;;
        "status")
            show_status
            ;;
        "all")
            show_api_logs
            show_worker_logs
            show_redis_logs
            show_frontend_logs
            show_status
            ;;
        "help"|"-h"|"--help")
            show_usage
            ;;
        *)
            echo -e "${RED}Unknown service: $1${NC}"
            show_usage
            exit 1
            ;;
    esac
    
    echo -e "\n${BLUE}💡 Tip:${NC} Use ${YELLOW}./logs.sh status${NC} to check service health"
    echo -e "${BLUE}💡 Tip:${NC} Add ${YELLOW}-f${NC} to docker logs commands for live streaming"
}

main "$@"