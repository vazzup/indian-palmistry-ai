#!/bin/bash

# Indian Palmistry AI - Stop Script
# This script stops all application services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_header() {
    echo -e "\n${BLUE}================================"
    echo -e "  Stopping Indian Palmistry AI"
    echo -e "================================${NC}\n"
}

# Function to stop frontend
stop_frontend() {
    print_status "Stopping frontend application..."
    
    if [ -f "frontend.pid" ]; then
        FRONTEND_PID=$(cat frontend.pid)
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            kill $FRONTEND_PID
            rm -f frontend.pid
            print_success "Frontend stopped"
        else
            print_status "Frontend was not running"
            rm -f frontend.pid
        fi
    else
        # Try to find and kill npm/node processes
        pkill -f "npm run dev" > /dev/null 2>&1 || true
        pkill -f "next dev" > /dev/null 2>&1 || true
        print_success "Frontend processes terminated"
    fi
    
    # Clean up log file
    rm -f frontend.log
}

# Function to stop backend services
stop_backend() {
    print_status "Stopping backend services..."
    
    if docker compose down; then
        print_success "Backend services stopped"
    else
        print_status "Backend services were not running"
    fi
}

# Main execution
main() {
    print_header
    
    stop_frontend
    stop_backend
    
    echo -e "\n${GREEN}✅ All services stopped successfully!${NC}\n"
    echo -e "${BLUE}💡 To start again, run:${NC} ${YELLOW}./start.sh${NC}\n"
}

main "$@"