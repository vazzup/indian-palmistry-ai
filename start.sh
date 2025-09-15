#!/bin/bash

# PalmistTalk - Project Startup Script
# This script starts the complete application stack

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "\n${BLUE}================================"
    echo -e "  PalmistTalk Startup"
    echo -e "================================${NC}\n"
}

# Function to check system requirements
check_system_requirements() {
    print_status "Checking system requirements..."
    
    # Check operating system
    case "$(uname -s)" in
        Darwin*) OS="macOS" ;;
        Linux*)  OS="Linux" ;;
        CYGWIN*|MINGW32*|MSYS*|MINGW*) OS="Windows" ;;
        *) OS="Unknown" ;;
    esac
    print_status "Operating System: $OS"
    
    # Check available disk space (minimum 2GB)
    if command -v df > /dev/null 2>&1; then
        available_space=$(df . | awk 'NR==2 {print $4}')
        if [ "$available_space" -lt 2000000 ]; then
            print_warning "Low disk space detected. At least 2GB recommended."
        fi
    fi
    
    # Check available memory (minimum 2GB)
    if [[ "$OS" == "macOS" ]]; then
        memory_gb=$(($(sysctl -n hw.memsize) / 1024 / 1024 / 1024))
    elif [[ "$OS" == "Linux" ]]; then
        memory_gb=$(free -g | awk '/^Mem:/{print $2}')
    fi
    
    if [ ! -z "$memory_gb" ] && [ "$memory_gb" -lt 2 ]; then
        print_warning "Low system memory detected ($memory_gb GB). At least 2GB recommended."
    fi
    
    print_success "System requirements check completed"
}

# Function to check if Docker is running
check_docker() {
    print_status "Checking Docker..."
    
    # Check if Docker is installed
    if ! command -v docker > /dev/null 2>&1; then
        print_error "Docker is not installed!"
        echo -e "Please install Docker from: ${BLUE}https://docs.docker.com/get-docker/${NC}"
        exit 1
    fi
    
    # Check Docker version
    docker_version=$(docker --version | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+' | head -1)
    print_status "Docker version: $docker_version"
    
    # Check if Docker daemon is running
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker daemon is not running!"
        echo -e "Please start Docker Desktop and try again."
        echo -e "Or run: ${YELLOW}sudo systemctl start docker${NC} (Linux)"
        exit 1
    fi
    
    # Check Docker Compose
    if ! docker compose version > /dev/null 2>&1; then
        print_error "Docker Compose is not available!"
        echo -e "Please ensure Docker Compose is installed with Docker."
        exit 1
    fi
    
    print_success "Docker is ready"
}

# Function to check if Node.js is installed
check_node() {
    print_status "Checking Node.js..."
    
    if ! command -v node > /dev/null 2>&1; then
        print_error "Node.js is not installed!"
        echo -e "Please install Node.js 18+ from: ${BLUE}https://nodejs.org/${NC}"
        echo -e "Or use a version manager like nvm: ${BLUE}https://github.com/nvm-sh/nvm${NC}"
        exit 1
    fi
    
    # Check Node version
    NODE_VERSION=$(node --version | sed 's/v//')
    NODE_MAJOR=$(echo $NODE_VERSION | cut -d. -f1)
    
    if [ "$NODE_MAJOR" -lt 18 ]; then
        print_error "Node.js version $NODE_VERSION is too old!"
        print_error "This application requires Node.js 18 or higher."
        echo -e "Please upgrade Node.js from: ${BLUE}https://nodejs.org/${NC}"
        exit 1
    fi
    
    # Check npm
    if ! command -v npm > /dev/null 2>&1; then
        print_error "npm is not installed! Please install Node.js with npm."
        exit 1
    fi
    
    NPM_VERSION=$(npm --version)
    print_success "Node.js $NODE_VERSION and npm $NPM_VERSION are ready"
}

# Function to check ports availability
check_ports() {
    print_status "Checking port availability..."
    
    # Check if ports are available
    local ports=(3000 8000 6379 5555)
    local port_issues=()
    
    for port in "${ports[@]}"; do
        if command -v lsof > /dev/null 2>&1; then
            if lsof -Pi :$port -sTCP:LISTEN -t > /dev/null 2>&1; then
                port_issues+=("$port")
            fi
        elif command -v netstat > /dev/null 2>&1; then
            if netstat -lnt | grep -q ":$port "; then
                port_issues+=("$port")
            fi
        fi
    done
    
    if [ ${#port_issues[@]} -gt 0 ]; then
        print_warning "The following ports are already in use: ${port_issues[*]}"
        print_warning "This script will stop existing services on these ports."
        
        # Give user option to continue
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Startup cancelled by user"
            exit 0
        fi
    fi
    
    print_success "Port availability check completed"
}

# Function to create required directories
setup_directories() {
    print_status "Setting up required directories..."
    
    # Create data directory if it doesn't exist
    if [ ! -d "data" ]; then
        mkdir -p data/images
        print_status "Created data/images directory"
    fi
    
    # Create logs directory if it doesn't exist
    if [ ! -d "logs" ]; then
        mkdir -p logs
        print_status "Created logs directory"
    fi
    
    # Set proper permissions (Linux/macOS)
    if [[ "$OS" != "Windows" ]]; then
        chmod -R 755 data logs 2>/dev/null || true
    fi
    
    print_success "Directory setup completed"
}

# Function to check environment file
check_env() {
    print_status "Checking environment configuration..."
    
    # Check for .env file
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            print_warning ".env file not found. Creating from .env.example..."
            cp .env.example .env
            print_warning "⚠️  IMPORTANT: Please edit .env file and add your OpenAI API key!"
            print_warning "   Without OpenAI API key, AI analysis will not work."
            
            # Ask if user wants to edit now
            if command -v nano > /dev/null 2>&1; then
                read -p "Would you like to edit .env file now? (y/N): " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    nano .env
                fi
            fi
        else
            print_error ".env.example file not found!"
            print_error "Cannot create environment configuration."
            exit 1
        fi
    fi
    
    # Check for required environment variables
    if [ -f ".env" ]; then
        if ! grep -q "OPENAI_API_KEY=" .env || grep -q "OPENAI_API_KEY=$" .env || grep -q "OPENAI_API_KEY=\"\"" .env; then
            print_warning "OpenAI API key not found in .env file!"
            print_warning "AI analysis features will not work without it."
        fi
    fi
    
    print_success "Environment configuration ready"
}

# Function to clean up previous runs
cleanup_previous_run() {
    print_status "Cleaning up any previous runs..."
    
    # Stop any existing Docker containers
    if docker compose ps -q > /dev/null 2>&1; then
        docker compose down > /dev/null 2>&1 || true
    fi
    
    # Clean up frontend PID file and logs
    if [ -f "frontend.pid" ]; then
        if [ -s "frontend.pid" ]; then
            OLD_PID=$(cat frontend.pid)
            if kill -0 "$OLD_PID" 2>/dev/null; then
                print_status "Stopping previous frontend process (PID: $OLD_PID)"
                kill "$OLD_PID" 2>/dev/null || true
                sleep 2
            fi
        fi
        rm -f frontend.pid
    fi
    
    # Clean up old log file
    if [ -f "frontend.log" ]; then
        mv frontend.log "logs/frontend-$(date +%Y%m%d-%H%M%S).log" 2>/dev/null || rm -f frontend.log
    fi
    
    print_success "Cleanup completed"
}

# Function to start backend services
start_backend() {
    print_status "Starting backend services (Redis, API, Worker)..."
    
    # Build and start services with better error handling
    if ! docker compose up -d --no-deps redis; then
        print_error "Failed to start Redis service"
        docker compose logs redis --tail 20
        exit 1
    fi
    
    # Wait for Redis to be ready
    print_status "Waiting for Redis to be ready..."
    local redis_retries=12
    local redis_count=0
    
    while [ $redis_count -lt $redis_retries ]; do
        if docker exec indian-palmistry-ai-redis-1 redis-cli ping > /dev/null 2>&1; then
            print_success "Redis is ready"
            break
        fi
        
        redis_count=$((redis_count + 1))
        if [ $redis_count -eq $redis_retries ]; then
            print_error "Redis failed to start"
            docker compose logs redis --tail 20
            exit 1
        fi
        
        sleep 2
    done
    
    # Start API service
    if ! docker compose up -d --no-deps api; then
        print_error "Failed to start API service"
        docker compose logs api --tail 20
        exit 1
    fi
    
    # Wait for API to be healthy
    print_status "Waiting for API to be healthy..."
    local api_retries=24  # 2 minutes total
    local api_count=0
    
    while [ $api_count -lt $api_retries ]; do
        if curl -s -f http://localhost:8000/healthz > /dev/null 2>&1; then
            print_success "API is healthy"
            break
        fi
        
        api_count=$((api_count + 1))
        if [ $api_count -eq $api_retries ]; then
            print_error "API failed to become healthy"
            print_status "API logs:"
            docker compose logs api --tail 20
            exit 1
        fi
        
        print_status "Waiting for API... ($api_count/$api_retries)"
        sleep 5
    done
    
    # Start worker service
    if ! docker compose up -d --no-deps worker; then
        print_error "Failed to start Worker service"
        docker compose logs worker --tail 20
        exit 1
    fi
    
    print_success "All backend services started successfully"
}

# Function to run database setup
setup_database() {
    print_status "Setting up database..."
    
    # Wait a moment for API to be fully ready
    sleep 2
    
    # Check if database tables exist
    tables_exist=$(docker exec indian-palmistry-ai-api-1 python -c "
import sqlite3
import os
db_path = './data/dev.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='analyses';\")
    result = cursor.fetchone()
    conn.close()
    print('yes' if result else 'no')
else:
    print('no')
" 2>/dev/null || echo "no")
    
    if [ "$tables_exist" = "yes" ]; then
        # Verify table has all required columns
        print_status "Verifying database schema..."
        schema_valid=$(docker exec indian-palmistry-ai-api-1 python -c "
import sqlite3
import os
db_path = './data/dev.db'
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check analyses table
    cursor.execute('PRAGMA table_info(analyses);')
    analyses_columns = [col[1] for col in cursor.fetchall()]
    analyses_required = ['left_file_id', 'right_file_id', 'key_features', 'strengths', 'guidance']
    analyses_missing = [col for col in analyses_required if col not in analyses_columns]
    
    # Check conversations table for new columns
    cursor.execute('PRAGMA table_info(conversations);')
    conversations_columns = [col[1] for col in cursor.fetchall()]
    conversations_required = ['mode', 'has_initial_message']
    conversations_missing = [col for col in conversations_required if col not in conversations_columns]
    
    # Check messages table for new columns
    cursor.execute('PRAGMA table_info(messages);')
    messages_columns = [col[1] for col in cursor.fetchall()]
    messages_required = ['message_type', 'analysis_data']
    messages_missing = [col for col in messages_required if col not in messages_columns]
    
    conn.close()
    all_missing = analyses_missing + conversations_missing + messages_missing
    print('no' if all_missing else 'yes')
except:
    print('no')
" 2>/dev/null || echo "no")
        
        if [ "$schema_valid" = "yes" ]; then
            print_success "Database schema is up to date"
            return
        else
            print_warning "Database schema is outdated, recreating tables..."
        fi
    fi
    
    # Run database migrations using Alembic
    print_status "Running database migrations..."
    if docker exec indian-palmistry-ai-api-1 python -m alembic upgrade head > /dev/null 2>&1; then
        print_success "Database migrations completed successfully"
    else
        print_error "Database migrations failed"
        exit 1
    fi
}

# Function to start frontend
start_frontend() {
    print_status "Setting up frontend application..."
    
    # Kill any existing processes on port 3000 (more aggressive cleanup)
    if command -v lsof > /dev/null 2>&1; then
        local existing_pids=$(lsof -ti :3000 2>/dev/null || true)
        if [ ! -z "$existing_pids" ]; then
            print_status "Stopping existing processes on port 3000..."
            echo "$existing_pids" | xargs -r kill -9 2>/dev/null || true
            sleep 3
            # Double check
            local remaining_pids=$(lsof -ti :3000 2>/dev/null || true)
            if [ ! -z "$remaining_pids" ]; then
                print_warning "Some processes still running on port 3000, forcing kill..."
                echo "$remaining_pids" | xargs -r kill -9 2>/dev/null || true
                sleep 2
            fi
        fi
    elif command -v pkill > /dev/null 2>&1; then
        # Alternative for systems without lsof
        pkill -f "next.*dev.*3000" 2>/dev/null || true
        sleep 2
    fi
    
    # Check if frontend directory exists
    if [ ! -d "frontend" ]; then
        print_error "Frontend directory not found!"
        exit 1
    fi
    
    cd frontend
    
    # Check if package.json exists
    if [ ! -f "package.json" ]; then
        print_error "Frontend package.json not found!"
        exit 1
    fi
    
    # Install dependencies with better error handling
    print_status "Checking frontend dependencies..."
    if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules" ] || [ "package-lock.json" -nt "node_modules" ]; then
        print_status "Installing frontend dependencies... (this may take a few minutes)"
        
        # Clear npm cache if install fails
        if ! npm install; then
            print_warning "npm install failed, clearing cache and retrying..."
            npm cache clean --force
            if ! npm install; then
                print_error "Failed to install frontend dependencies"
                cd ..
                exit 1
            fi
        fi
        print_success "Frontend dependencies installed"
    else
        print_success "Frontend dependencies are up to date"
    fi
    
    print_status "Starting Next.js development server..."
    print_warning "Frontend will start in the background. Monitor frontend.log for any issues."
    
    # Start frontend in background with proper logging
    nohup npm run dev > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../frontend.pid
    
    cd ..
    
    # Wait for frontend to be ready with better detection
    local frontend_retries=30  # 75 seconds total
    local frontend_count=0
    local frontend_url="http://localhost:3000"
    
    # Give frontend time to start
    sleep 5
    
    # Try to detect actual port from logs if different
    if [ -f "frontend.log" ]; then
        detected_port=$(grep -o "http://localhost:[0-9]*" frontend.log 2>/dev/null | head -1 | grep -o "[0-9]*" | head -1)
        if [ ! -z "$detected_port" ] && [ "$detected_port" != "3000" ]; then
            frontend_url="http://localhost:$detected_port"
            print_status "Frontend detected on port $detected_port"
        fi
    fi
    
    print_status "Waiting for frontend at $frontend_url..."
    
    while [ $frontend_count -lt $frontend_retries ]; do
        # Check if frontend process is still running
        if ! kill -0 $FRONTEND_PID 2>/dev/null; then
            print_error "Frontend process died unexpectedly!"
            print_status "Frontend logs:"
            tail -20 frontend.log
            exit 1
        fi
        
        # Check if frontend is responding
        if curl -s -f "$frontend_url" > /dev/null 2>&1; then
            print_success "Frontend is ready at $frontend_url"
            break
        fi
        
        frontend_count=$((frontend_count + 1))
        if [ $frontend_count -eq $frontend_retries ]; then
            print_error "Frontend failed to start within expected time"
            print_status "Frontend logs:"
            tail -20 frontend.log
            
            # Check for common issues in logs
            if grep -q "Error: listen EADDRINUSE" frontend.log; then
                print_error "Port already in use. Try killing processes on port 3000."
            elif grep -q "Module not found" frontend.log; then
                print_error "Missing dependencies. Try deleting node_modules and running again."
            fi
            
            exit 1
        fi
        
        if [ $((frontend_count % 5)) -eq 0 ]; then
            print_status "Still waiting for frontend... ($frontend_count/$frontend_retries)"
        fi
        sleep 2.5
    done
}

# Function to run post-startup health checks
health_check() {
    print_status "Running final health checks..."
    
    # Check all services
    local services=("redis" "api" "worker")
    local healthy_services=0
    
    for service in "${services[@]}"; do
        if docker compose ps $service | grep -q "healthy\|running"; then
            healthy_services=$((healthy_services + 1))
        else
            print_warning "$service appears unhealthy"
        fi
    done
    
    # Check API endpoints
    if curl -s -f http://localhost:8000/healthz > /dev/null 2>&1; then
        healthy_services=$((healthy_services + 1))
        api_status="✅"
    else
        api_status="⚠️"
    fi
    
    # Check frontend
    local frontend_port="3000"
    if [ -f "frontend.log" ]; then
        detected_port=$(grep -o "http://localhost:[0-9]*" frontend.log 2>/dev/null | head -1 | grep -o "[0-9]*" | head -1)
        if [ ! -z "$detected_port" ]; then
            frontend_port="$detected_port"
        fi
    fi
    
    if curl -s -f "http://localhost:$frontend_port" > /dev/null 2>&1; then
        frontend_status="✅"
    else
        frontend_status="⚠️"
    fi
    
    print_success "Health check completed ($healthy_services/4 services healthy)"
}

# Function to display final status
show_status() {
    # Detect frontend port
    local frontend_port="3000"
    if [ -f "frontend.log" ]; then
        detected_port=$(grep -o "http://localhost:[0-9]*" frontend.log 2>/dev/null | head -1 | grep -o "[0-9]*" | head -1)
        if [ ! -z "$detected_port" ]; then
            frontend_port="$detected_port"
        fi
    fi
    
    echo -e "\n${GREEN}================================"
    echo -e "   🎉 STARTUP COMPLETE! 🎉"
    echo -e "================================${NC}\n"
    
    echo -e "${BLUE}📱 Application URLs:${NC}"
    echo -e "   • ${GREEN}Main Application:      http://localhost:$frontend_port${NC}"
    echo -e "   • ${GREEN}API Backend:           http://localhost:8000${NC}"
    echo -e "   • ${GREEN}API Documentation:     http://localhost:8000/docs${NC}"
    echo -e "   • ${GREEN}Health Check:          http://localhost:8000/healthz${NC}"
    
    echo -e "\n${BLUE}🔧 Running Services:${NC}"
    echo -e "   • ✅ Redis Database (port 6379)"
    echo -e "   • ✅ FastAPI Backend (port 8000)" 
    echo -e "   • ✅ Celery Worker (background jobs)"
    echo -e "   • ✅ Next.js Frontend (port $frontend_port)"
    
    echo -e "\n${BLUE}📋 Getting Started:${NC}"
    echo -e "   1. Open ${GREEN}http://localhost:$frontend_port${NC} in your browser"
    echo -e "   2. Upload palm images for AI analysis"
    echo -e "   3. Wait for analysis to complete"
    echo -e "   4. View your palmistry reading results"
    
    echo -e "\n${BLUE}🛠️  Management Commands:${NC}"
    if [ -f "./logs.sh" ]; then
        echo -e "   • View logs:           ${YELLOW}./logs.sh${NC}"
    fi
    if [ -f "./stop.sh" ]; then
        echo -e "   • Stop all services:   ${YELLOW}./stop.sh${NC}"
    fi
    if [ -f "./restart.sh" ]; then
        echo -e "   • Restart services:    ${YELLOW}./restart.sh${NC}"
    fi
    echo -e "   • View backend logs:   ${YELLOW}docker compose logs -f api${NC}"
    echo -e "   • View frontend logs:  ${YELLOW}tail -f frontend.log${NC}"
    
    echo -e "\n${BLUE}📁 Important Files:${NC}"
    echo -e "   • Application logs:    ${YELLOW}frontend.log${NC}"
    echo -e "   • Configuration:       ${YELLOW}.env${NC}"
    echo -e "   • Database:            ${YELLOW}data/dev.db${NC}"
    
    # Check for common issues and provide tips
    echo -e "\n${BLUE}💡 Tips:${NC}"
    if [ -f ".env" ]; then
        if grep -q "OPENAI_API_KEY=$" .env || grep -q "OPENAI_API_KEY=\"\"" .env; then
            echo -e "   • ${YELLOW}Add your OpenAI API key to .env file for AI features to work${NC}"
        fi
    fi
    echo -e "   • Monitor logs with: ${YELLOW}tail -f frontend.log${NC}"
    echo -e "   • For issues, check: ${YELLOW}docker compose logs${NC}"
    echo -e "   • Frontend runs in background - check frontend.log for errors"
    
    echo -e "\n${GREEN}🚀 Your PalmistTalk application is now running!${NC}\n"
}

# Function to handle cleanup on exit
cleanup() {
    if [ $? -ne 0 ]; then
        print_error "Startup failed! Check the logs above for details."
        echo -e "\n${BLUE}Troubleshooting:${NC}"
        echo -e "   • Check Docker is running: ${YELLOW}docker info${NC}"
        echo -e "   • Check ports are free: ${YELLOW}lsof -i :3000,8000,6379${NC}"
        echo -e "   • View service logs: ${YELLOW}docker compose logs${NC}"
        echo -e "   • Check frontend logs: ${YELLOW}cat frontend.log${NC}"
    fi
}

# Trap cleanup function
trap cleanup EXIT

# Main execution
main() {
    print_header
    
    # System checks
    check_system_requirements
    check_docker
    check_node
    check_ports
    
    # Setup
    setup_directories
    check_env
    cleanup_previous_run
    
    # Start services
    start_backend
    setup_database
    start_frontend
    
    # Final checks and status
    health_check
    show_status
}

# Run main function with all arguments
main "$@"