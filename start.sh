#!/bin/bash

# Indian Palmistry AI - Project Startup Script
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
    echo -e "  Indian Palmistry AI Startup"
    echo -e "================================${NC}\n"
}

# Function to check if Docker is running
check_docker() {
    print_status "Checking Docker..."
    if ! docker --version > /dev/null 2>&1; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker Desktop and try again."
        exit 1
    fi
    
    print_success "Docker is running"
}

# Function to check if Node.js is installed
check_node() {
    print_status "Checking Node.js..."
    if ! node --version > /dev/null 2>&1; then
        print_error "Node.js is not installed. Please install Node.js 18+ and try again."
        exit 1
    fi
    
    NODE_VERSION=$(node --version | sed 's/v//')
    print_success "Node.js $NODE_VERSION is installed"
}

# Function to check environment file
check_env() {
    print_status "Checking environment configuration..."
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            print_warning ".env file not found. Creating from .env.example..."
            cp .env.example .env
            print_warning "Please edit .env file and add your OpenAI API key if needed"
        else
            print_error ".env.example file not found. Cannot create environment configuration."
            exit 1
        fi
    fi
    print_success "Environment configuration ready"
}

# Function to start backend services
start_backend() {
    print_status "Starting backend services (API, Redis, Worker)..."
    
    # Stop any existing containers
    docker compose down > /dev/null 2>&1 || true
    
    # Start backend services
    if docker compose up -d --no-deps redis api worker; then
        print_success "Backend services started"
    else
        print_error "Failed to start backend services"
        exit 1
    fi
    
    # Wait for services to be healthy
    print_status "Waiting for services to be healthy..."
    sleep 10
    
    # Check API health
    local retries=12  # 60 seconds total (5 seconds * 12)
    local count=0
    
    while [ $count -lt $retries ]; do
        if curl -s http://localhost:8000/healthz > /dev/null 2>&1; then
            print_success "Backend API is healthy"
            break
        fi
        
        count=$((count + 1))
        if [ $count -eq $retries ]; then
            print_error "Backend API failed to become healthy"
            print_status "Checking API logs..."
            docker logs indian-palmistry-ai-api-1 --tail 20
            exit 1
        fi
        
        print_status "Waiting for API to be ready... ($count/$retries)"
        sleep 5
    done
}

# Function to run database migrations
setup_database() {
    print_status "Setting up database..."
    
    # Run database migrations
    if docker exec indian-palmistry-ai-api-1 python -m alembic upgrade 819e95294bd3 > /dev/null 2>&1; then
        print_success "Database migrations completed"
    else
        print_warning "Database migrations may have failed, but continuing..."
        # Don't exit here as the database might already be set up
    fi
}

# Function to start frontend
start_frontend() {
    print_status "Starting frontend application..."
    
    # Kill any existing processes on port 3000
    local existing_pid=$(lsof -ti :3000 2>/dev/null)
    if [ ! -z "$existing_pid" ]; then
        print_status "Stopping existing process on port 3000 (PID: $existing_pid)..."
        kill $existing_pid 2>/dev/null || true
        sleep 2
    fi
    
    cd frontend
    
    # Install dependencies if node_modules doesn't exist or package.json is newer
    if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules" ]; then
        print_status "Installing frontend dependencies..."
        if npm install; then
            print_success "Frontend dependencies installed"
        else
            print_error "Failed to install frontend dependencies"
            exit 1
        fi
    fi
    
    print_status "Starting Next.js development server..."
    print_warning "Frontend will start in the background. Check for compilation errors."
    
    # Start frontend in background
    npm run dev > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../frontend.pid
    
    cd ..
    
    # Wait for frontend to be ready and detect the actual port
    local retries=24  # 60 seconds total (2.5 seconds * 24)
    local count=0
    local frontend_port=""
    
    # Wait a moment for the frontend to start and write logs
    sleep 3
    
    # Try to detect the actual port from logs
    if [ -f "frontend.log" ]; then
        frontend_port=$(grep -o "http://localhost:[0-9]*" frontend.log 2>/dev/null | head -1 | grep -o "[0-9]*" | head -1)
    fi
    
    # Default to 3000 if no port detected
    if [ -z "$frontend_port" ]; then
        frontend_port="3000"
    fi
    
    local frontend_url="http://localhost:$frontend_port"
    print_status "Checking frontend at $frontend_url..."
    
    while [ $count -lt $retries ]; do
        if curl -s "$frontend_url" > /dev/null 2>&1; then
            print_success "Frontend is ready at $frontend_url"
            break
        fi
        
        count=$((count + 1))
        if [ $count -eq $retries ]; then
            print_error "Frontend failed to start"
            print_status "Checking frontend logs..."
            tail -20 frontend.log
            exit 1
        fi
        
        sleep 2.5
    done
}

# Function to display final status
show_status() {
    echo -e "\n${GREEN}================================"
    echo -e "   🎉 STARTUP COMPLETE! 🎉"
    echo -e "================================${NC}\n"
    
    # Detect frontend port from logs
    local frontend_port="3000"
    if [ -f "frontend.log" ]; then
        local detected_port=$(grep -o "http://localhost:[0-9]*" frontend.log 2>/dev/null | head -1 | grep -o "[0-9]*" | head -1)
        if [ ! -z "$detected_port" ]; then
            frontend_port="$detected_port"
        fi
    fi
    
    echo -e "${BLUE}📱 Application URLs:${NC}"
    echo -e "   • Frontend (Main App): ${GREEN}http://localhost:$frontend_port${NC}"
    echo -e "   • Backend API:         ${GREEN}http://localhost:8000${NC}"
    echo -e "   • API Documentation:   ${GREEN}http://localhost:8000/docs${NC}"
    echo -e "   • Health Check:        ${GREEN}http://localhost:8000/healthz${NC}"
    
    echo -e "\n${BLUE}🔧 Running Services:${NC}"
    echo -e "   • ✅ Redis Database (port 6379)"
    echo -e "   • ✅ FastAPI Backend (port 8000)" 
    echo -e "   • ✅ Celery Worker (background jobs)"
    echo -e "   • ✅ Next.js Frontend (port $frontend_port)"
    
    echo -e "\n${BLUE}📋 Usage Instructions:${NC}"
    echo -e "   1. Open ${GREEN}http://localhost:$frontend_port${NC} in your browser"
    echo -e "   2. Upload palm images using the interface"
    echo -e "   3. Wait for AI analysis to complete"
    echo -e "   4. View your palmistry reading results"
    
    echo -e "\n${BLUE}🛠️  Management Commands:${NC}"
    echo -e "   • View logs:           ${YELLOW}./logs.sh${NC}"
    echo -e "   • Stop all services:   ${YELLOW}./stop.sh${NC}"
    echo -e "   • Restart services:    ${YELLOW}./restart.sh${NC}"
    
    echo -e "\n${YELLOW}💡 Note:${NC} Frontend runs in background. Check 'frontend.log' for any compilation errors."
    echo -e "${YELLOW}💡 Note:${NC} Make sure to add your OpenAI API key to .env file for AI analysis to work."
}

# Function to handle cleanup on exit
cleanup() {
    print_status "Cleaning up..."
    # Don't stop services on script exit - they should keep running
    exit 0
}

# Trap cleanup function
trap cleanup EXIT INT TERM

# Main execution
main() {
    print_header
    
    # Pre-flight checks
    check_docker
    check_node
    check_env
    
    # Start services
    start_backend
    setup_database
    start_frontend
    
    # Show final status
    show_status
}

# Run main function
main "$@"