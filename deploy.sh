#!/bin/bash

# PalmistTalk Production Deployment Script
# This script deploys the PalmistTalk application to production
# Run for each deployment: ./deploy.sh production

set -euo pipefail  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.production"
BACKUP_DIR="backups"
MAX_WAIT_TIME=300  # 5 minutes

# Print functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_status() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running as root (we don't want that)
check_user() {
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root!"
        print_status "Run as a regular user with docker group membership"
        exit 1
    fi
}

# Check if this is a production environment
check_environment() {
    if [[ ${1:-} != "production" ]]; then
        print_error "Usage: $0 production"
        print_status "This script deploys to a production environment"
        exit 1
    fi
}

# Validate prerequisites
validate_prerequisites() {
    print_header "Validating Prerequisites"

    # Check if we're in the right directory
    if [[ ! -f "docker-compose.yml" ]] || [[ ! -f "$COMPOSE_FILE" ]]; then
        print_error "Missing required Docker Compose files"
        print_status "Ensure you're in the PalmistTalk project directory"
        print_status "Required files: docker-compose.yml, $COMPOSE_FILE"
        exit 1
    fi

    # Check if environment file exists
    if [[ ! -f "$ENV_FILE" ]]; then
        print_error "Production environment file not found: $ENV_FILE"
        print_status "Create it by copying: cp .env.production.example $ENV_FILE"
        print_status "Then edit it with your production values"
        exit 1
    fi

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        print_status "Run ./setup.sh production first"
        exit 1
    fi

    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not available"
        print_status "Run ./setup.sh production first"
        exit 1
    fi

    # Check if user is in docker group
    if ! groups | grep -q docker; then
        print_error "Current user is not in docker group"
        print_status "Run ./setup.sh production first, then log out and log back in"
        exit 1
    fi

    # Check if required directories exist
    if [[ ! -d "data" ]]; then
        print_error "Data directory not found"
        print_status "Run ./setup.sh production first"
        exit 1
    fi

    print_success "All prerequisites validated"
}

# Clean up ports and processes
cleanup_ports() {
    print_header "Cleaning Up Ports"

    local ports=(3000 8000)

    for port in "${ports[@]}"; do
        if command -v lsof > /dev/null 2>&1; then
            local existing_pids=$(lsof -ti :$port 2>/dev/null || true)
            if [[ ! -z "$existing_pids" ]]; then
                print_status "Cleaning up processes on port $port..."
                echo "$existing_pids" | xargs -r kill -9 2>/dev/null || true
                sleep 2

                # Double check
                local remaining_pids=$(lsof -ti :$port 2>/dev/null || true)
                if [[ ! -z "$remaining_pids" ]]; then
                    print_warning "Some processes still running on port $port, forcing kill..."
                    echo "$remaining_pids" | xargs -r kill -9 2>/dev/null || true
                    sleep 2
                fi
            fi
        elif command -v pkill > /dev/null 2>&1; then
            # Alternative for systems without lsof
            pkill -f "port.*$port" 2>/dev/null || true
            sleep 1
        fi
    done

    print_success "Port cleanup completed"
}

# Create backup of current state
create_backup() {
    print_header "Creating Backup"

    # Create backup directory
    mkdir -p "$BACKUP_DIR"

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_name="backup_${timestamp}"

    print_status "Creating backup: $backup_name"

    # Backup database if it exists
    if [[ -f "data/production.db" ]]; then
        cp "data/production.db" "$BACKUP_DIR/production_db_${timestamp}.db"
        print_status "Database backed up"
    fi

    # Backup images if they exist
    if [[ -d "data/images" ]] && [[ "$(ls -A data/images)" ]]; then
        tar -czf "$BACKUP_DIR/images_${timestamp}.tar.gz" -C "data" images/
        print_status "Images backed up"
    fi

    # Backup environment file
    cp "$ENV_FILE" "$BACKUP_DIR/env_${timestamp}.backup"

    # Keep only last 5 backups
    print_status "Cleaning old backups (keeping last 5)..."
    find "$BACKUP_DIR" -name "production_db_*.db" | sort | head -n -5 | xargs -r rm
    find "$BACKUP_DIR" -name "images_*.tar.gz" | sort | head -n -5 | xargs -r rm
    find "$BACKUP_DIR" -name "env_*.backup" | sort | head -n -5 | xargs -r rm

    print_success "Backup created: $backup_name"
}

# Stop existing containers
stop_containers() {
    print_header "Stopping Existing Containers"

    if docker compose -f "$COMPOSE_FILE" ps -q > /dev/null 2>&1; then
        print_status "Stopping running containers..."
        docker compose -f "$COMPOSE_FILE" down --timeout 30

        # Wait for containers to fully stop
        sleep 5
    else
        print_status "No containers currently running"
    fi

    print_success "Containers stopped"
}

# Build and start containers
deploy_containers() {
    print_header "Deploying Application"

    print_status "Building and starting containers..."

    # Load environment variables
    export $(grep -v '^#' "$ENV_FILE" | xargs)

    # Get domain from environment file for frontend URLs
    local domain=$(grep "^DOMAIN=" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"')
    if [[ ! -z "$domain" ]]; then
        export NEXT_PUBLIC_API_URL="https://$domain"
        export NEXT_PUBLIC_SITE_URL="https://$domain"
        print_status "Frontend configured for domain: $domain"
    else
        print_warning "DOMAIN not set, using localhost for frontend URLs"
        export NEXT_PUBLIC_API_URL="http://localhost"
        export NEXT_PUBLIC_SITE_URL="http://localhost"
    fi

    # Build and start containers
    docker compose -f "$COMPOSE_FILE" up -d --build

    print_success "Containers deployed"
}

# Wait for services to be healthy
wait_for_services() {
    print_header "Waiting for Services to Start"

    local services=("redis" "api" "frontend")
    local wait_time=0

    for service in "${services[@]}"; do
        print_status "Waiting for $service to be ready..."

        while [[ $wait_time -lt $MAX_WAIT_TIME ]]; do
            if docker compose -f "$COMPOSE_FILE" ps "$service" | grep -q "Up"; then
                print_status "$service is ready"
                break
            fi

            sleep 10
            wait_time=$((wait_time + 10))

            if [[ $wait_time -ge $MAX_WAIT_TIME ]]; then
                print_error "$service failed to start within $MAX_WAIT_TIME seconds"
                return 1
            fi
        done
    done

    print_success "All services are ready"
}

# Run database migrations
run_database_migrations() {
    print_header "Running Database Migrations"

    print_status "Applying Alembic migrations..."

    # Run Alembic migrations in the API container
    if docker compose -f "$COMPOSE_FILE" exec -T api alembic upgrade head; then
        print_success "Database migrations completed successfully"
    else
        print_error "Database migrations failed"
        print_status "Checking migration logs..."
        docker compose -f "$COMPOSE_FILE" logs --tail 20 api
        return 1
    fi
}

# Perform health checks
health_check() {
    print_header "Performing Health Checks"

    # Get domain from environment file
    local domain=$(grep "^DOMAIN=" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"')
    if [[ -z "$domain" ]]; then
        print_warning "DOMAIN not set in environment file, using localhost for health checks"
        domain="localhost"
    fi

    # Check API health
    print_status "Checking API health..."
    local api_url="http://localhost:8000/healthz"

    for i in {1..6}; do  # Try for 60 seconds
        if curl -s -f "$api_url" > /dev/null 2>&1; then
            print_success "API health check passed"
            break
        elif [[ $i -eq 6 ]]; then
            print_error "API health check failed"
            print_status "API logs:"
            docker compose -f "$COMPOSE_FILE" logs --tail 20 api
            return 1
        else
            print_status "API not ready yet, waiting... (attempt $i/6)"
            sleep 10
        fi
    done

    # Check frontend
    print_status "Checking frontend..."
    local frontend_url="http://localhost:3000"

    for i in {1..6}; do  # Try for 60 seconds
        if curl -s -f "$frontend_url" > /dev/null 2>&1; then
            print_success "Frontend health check passed"
            break
        elif [[ $i -eq 6 ]]; then
            print_error "Frontend health check failed"
            print_status "Frontend logs:"
            docker compose -f "$COMPOSE_FILE" logs --tail 20 frontend
            return 1
        else
            print_status "Frontend not ready yet, waiting... (attempt $i/6)"
            sleep 10
        fi
    done

    print_success "All health checks passed"
}

# Configure Nginx for production
configure_nginx() {
    print_header "Configuring Nginx"

    # Get domain from environment file
    local domain=$(grep "^DOMAIN=" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"')
    if [[ -z "$domain" ]]; then
        print_error "DOMAIN not set in environment file"
        print_status "Please set DOMAIN=yourdomain.com in $ENV_FILE"
        return 1
    fi

    local nginx_config="/etc/nginx/sites-available/palmisttalk"

    print_status "Creating Nginx configuration for $domain..."

    # Create Nginx configuration
    sudo tee "$nginx_config" > /dev/null << EOF
# PalmistTalk Nginx Configuration
# SSL will be added automatically by Certbot

server {
    listen 80;
    server_name $domain www.$domain;

    # Allow larger uploads for palm images
    client_max_body_size 50M;

    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy strict-origin-when-cross-origin;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;

        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Analysis endpoints (more restrictive due to AI processing cost)
    location ~ ^/api/(analyses|analysis)/ {
        limit_req zone=analysis burst=10 nodelay;
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # Longer timeout for AI processing
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    # General API endpoints with generous rate limiting for polling
    location /api/ {
        limit_req zone=api burst=60 nodelay;
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint (no rate limiting)
    location /healthz {
        proxy_pass http://localhost:8000/healthz;
        proxy_set_header Host \$host;
        access_log off;
    }

    # Certbot challenge location (needed for SSL verification)
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
}
EOF

    # Enable the site
    print_status "Enabling Nginx site..."
    sudo ln -sf "/etc/nginx/sites-available/palmisttalk" "/etc/nginx/sites-enabled/palmisttalk"

    # Remove default site if it exists
    sudo rm -f /etc/nginx/sites-enabled/default

    # Test nginx configuration
    print_status "Testing Nginx configuration..."
    if sudo nginx -t; then
        print_status "Restarting Nginx..."
        sudo systemctl restart nginx
        print_success "Nginx configured for $domain"
    else
        print_error "Nginx configuration test failed"
        return 1
    fi
}

# Setup SSL certificate
setup_ssl() {
    print_header "Setting Up SSL Certificate"

    # Get domain from environment file
    local domain=$(grep "^DOMAIN=" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"')

    print_status "Requesting SSL certificate for $domain..."

    # Run certbot to get SSL certificate
    if sudo certbot --nginx -d "$domain" -d "www.$domain" --non-interactive --agree-tos --register-unsafely-without-email; then
        print_success "SSL certificate installed successfully"

        # Test auto-renewal
        print_status "Testing SSL auto-renewal..."
        sudo certbot renew --dry-run

        print_success "SSL setup completed"
    else
        print_warning "SSL certificate setup failed"
        print_status "You can set up SSL later by running:"
        print_status "sudo certbot --nginx -d $domain -d www.$domain"
        print_status "Make sure your domain points to this server's IP address"
    fi
}

# Show deployment status
show_status() {
    print_header "Deployment Status"

    # Show running containers
    print_status "Running containers:"
    docker compose -f "$COMPOSE_FILE" ps

    # Get domain
    local domain=$(grep "^DOMAIN=" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"')

    echo ""
    print_success "Deployment completed successfully!"
    echo ""
    print_status "Your PalmistTalk application is now running at:"
    if [[ ! -z "$domain" ]]; then
        echo "  Frontend: https://$domain"
        echo "  API: https://$domain/api"
        echo "  Health Check: https://$domain/api/healthz"
    else
        echo "  Frontend: http://localhost:3000"
        echo "  API: http://localhost:8000"
        echo "  Health Check: http://localhost:8000/healthz"
    fi
    echo ""
    print_status "Useful commands:"
    echo "  Check status: docker compose -f $COMPOSE_FILE ps"
    echo "  View logs: docker compose -f $COMPOSE_FILE logs -f [service]"
    echo "  Restart: docker compose -f $COMPOSE_FILE restart [service]"
    echo "  Stop: docker compose -f $COMPOSE_FILE down"
}

# Rollback function
rollback() {
    print_header "Rolling Back Deployment"

    print_status "Stopping current containers..."
    docker compose -f "$COMPOSE_FILE" down --timeout 30

    # Find latest backup
    local latest_db=$(ls -t "$BACKUP_DIR"/production_db_*.db 2>/dev/null | head -1)
    local latest_images=$(ls -t "$BACKUP_DIR"/images_*.tar.gz 2>/dev/null | head -1)

    if [[ -f "$latest_db" ]]; then
        print_status "Restoring database from backup..."
        cp "$latest_db" "data/production.db"
        sudo chown 1000:1000 "data/production.db"
    fi

    if [[ -f "$latest_images" ]]; then
        print_status "Restoring images from backup..."
        tar -xzf "$latest_images" -C "data/"
    fi

    print_success "Rollback completed"
    print_status "You may need to restart containers manually"
}

# Error handler
handle_error() {
    local exit_code=$?
    print_error "Deployment failed with exit code $exit_code"

    print_status "Showing recent logs for debugging:"
    docker compose -f "$COMPOSE_FILE" logs --tail 20

    read -p "Do you want to rollback to the previous state? (y/N): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rollback
    fi

    exit $exit_code
}

# Main execution
main() {
    print_header "PalmistTalk Production Deployment"

    # Set up error handling
    trap 'handle_error' ERR

    check_user
    check_environment "$@"
    validate_prerequisites
    create_backup
    cleanup_ports
    stop_containers
    deploy_containers
    wait_for_services
    run_database_migrations
    health_check
    configure_nginx
    setup_ssl
    show_status
}

# Run main function with all arguments
main "$@"