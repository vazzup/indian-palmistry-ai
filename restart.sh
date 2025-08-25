#!/bin/bash

# Indian Palmistry AI - Restart Script
# This script restarts the entire application

set -e

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${BLUE}================================"
    echo -e " Restarting Indian Palmistry AI"
    echo -e "================================${NC}\n"
}

main() {
    print_header
    
    echo -e "${BLUE}🛑 Stopping all services...${NC}"
    ./stop.sh
    
    echo -e "\n${BLUE}⏳ Waiting 3 seconds...${NC}"
    sleep 3
    
    echo -e "\n${BLUE}🚀 Starting all services...${NC}"
    ./start.sh
    
    echo -e "\n${GREEN}✅ Restart completed!${NC}\n"
}

main "$@"