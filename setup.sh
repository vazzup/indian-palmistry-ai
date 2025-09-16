#!/bin/bash

# PalmistTalk Production Server Setup Script
# This script prepares a fresh VPS for PalmistTalk deployment
# Run once per server: ./setup.sh production

set -euo pipefail  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
        print_status "Run as a regular user with sudo privileges"
        exit 1
    fi
}

# Check if this is a production environment
check_environment() {
    if [[ ${1:-} != "production" ]]; then
        print_error "Usage: $0 production"
        print_status "This script sets up a production server environment"
        exit 1
    fi
}

# Update system packages
update_system() {
    print_header "Updating System Packages"

    print_status "Updating package lists..."
    sudo apt update

    print_status "Upgrading system packages..."
    sudo apt upgrade -y

    print_status "Installing essential packages..."
    sudo apt install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release \
        software-properties-common \
        git \
        htop \
        unzip \
        wget

    print_success "System packages updated"
}

# Install Docker
install_docker() {
    print_header "Installing Docker"

    # Remove old versions if they exist
    print_status "Removing old Docker versions..."
    sudo apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

    # Add Docker GPG key
    print_status "Adding Docker GPG key..."
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

    # Add Docker repository
    print_status "Adding Docker repository..."
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Install Docker
    print_status "Installing Docker packages..."
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    # Start and enable Docker
    print_status "Starting Docker service..."
    sudo systemctl start docker
    sudo systemctl enable docker

    # Add current user to docker group
    print_status "Adding user to docker group..."
    sudo usermod -aG docker $USER

    # Test Docker installation
    print_status "Testing Docker installation..."
    docker --version
    docker compose version

    print_success "Docker installed successfully"
    print_warning "You may need to log out and log back in for docker group membership to take effect"
}

# Install and configure Nginx
install_nginx() {
    print_header "Installing and Configuring Nginx"

    print_status "Installing Nginx..."
    sudo apt install -y nginx

    print_status "Starting and enabling Nginx..."
    sudo systemctl start nginx
    sudo systemctl enable nginx

    print_status "Configuring UFW firewall..."
    sudo ufw allow ssh
    sudo ufw allow 'Nginx Full'
    sudo ufw --force enable

    print_success "Nginx installed and firewall configured"
}

# Install Certbot for SSL certificates
install_certbot() {
    print_header "Installing Certbot for SSL"

    print_status "Installing Certbot..."
    sudo apt install -y certbot python3-certbot-nginx

    print_success "Certbot installed successfully"
}

# Create application directories and set permissions
setup_directories() {
    print_header "Setting Up Application Directories"

    # Ensure we're in the right directory
    if [[ ! -f "docker-compose.yml" ]]; then
        print_error "This script must be run from the PalmistTalk project directory"
        print_status "Please cd to your PalmistTalk directory and run again"
        exit 1
    fi

    print_status "Creating data directories..."
    mkdir -p data/images data/redis

    print_status "Setting directory permissions..."
    chmod 755 data data/images data/redis

    # Set ownership for Docker containers (UID 1000 is the default non-root user in containers)
    print_status "Setting ownership for Docker containers..."
    sudo chown -R 1000:1000 data/

    print_status "Creating .gitkeep files..."
    touch data/images/.gitkeep data/redis/.gitkeep

    print_success "Application directories created with proper permissions"
}

# Create SQLite database with proper permissions
setup_database() {
    print_header "Setting Up Production Database"

    local db_file="data/production.db"

    if [[ -f "$db_file" ]]; then
        print_warning "Database file $db_file already exists, skipping creation"
    else
        print_status "Creating production SQLite database..."
        touch "$db_file"

        print_status "Setting database file permissions..."
        chmod 664 "$db_file"
        sudo chown 1000:1000 "$db_file"

        print_success "Production database created: $db_file"
    fi
}

# Configure Nginx rate limiting
configure_nginx_rate_limiting() {
    print_header "Configuring Nginx Rate Limiting"

    local nginx_conf="/etc/nginx/nginx.conf"

    # Check if rate limiting is already configured
    if grep -q "limit_req_zone.*zone=api" "$nginx_conf"; then
        print_warning "Nginx rate limiting already configured, skipping"
        return
    fi

    print_status "Adding rate limiting configuration to nginx.conf..."

    # Create a temporary file with the rate limiting configuration
    cat > /tmp/nginx_rate_limit.conf << 'EOF'

    ##
    # Rate Limiting for PalmistTalk
    ##
    limit_req_zone $binary_remote_addr zone=api:10m rate=30r/s;
    limit_req_zone $binary_remote_addr zone=analysis:10m rate=5r/s;
EOF

    # Insert the rate limiting configuration into nginx.conf
    # We'll add it just before the Virtual Host Configs section
    sudo sed -i '/Virtual Host Configs/i\    ##\n    # Rate Limiting for PalmistTalk\n    ##\n    limit_req_zone $binary_remote_addr zone=api:10m rate=30r/s;\n    limit_req_zone $binary_remote_addr zone=analysis:10m rate=5r/s;\n' "$nginx_conf"

    # Test nginx configuration
    print_status "Testing Nginx configuration..."
    sudo nginx -t

    print_success "Nginx rate limiting configured"
}

# Create environment file template
create_env_template() {
    print_header "Creating Environment Template"

    local env_file=".env.production.example"

    if [[ -f "$env_file" ]]; then
        print_warning "Environment template already exists, skipping"
        return
    fi

    print_status "Creating production environment template..."

    cat > "$env_file" << 'EOF'
# PalmistTalk Production Environment Configuration
# Copy this file to .env.production and update with your actual values

# Database Configuration (SQLite for production)
DATABASE_URL=sqlite+aiosqlite:///./data/production.db

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/1

# OpenAI Configuration - REPLACE WITH YOUR ACTUAL KEY
OPENAI_API_KEY=sk-your-actual-openai-api-key-here

# Security Configuration - GENERATE SECURE KEYS
# Run: openssl rand -hex 32
SECRET_KEY=your-very-secure-secret-key-here-32chars
JWT_SECRET=your-very-secure-jwt-secret-here-32chars

# CORS Configuration - REPLACE WITH YOUR DOMAIN
ALLOWED_ORIGINS=https://yourdomain.com

# File Storage Configuration
FILE_STORAGE_ROOT=./data/images

# Application Configuration
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=production

# Session Configuration
SESSION_EXPIRE_SECONDS=604800
SESSION_COOKIE_NAME=palmistry_session
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_SAMESITE=Strict

# Domain Configuration - REPLACE WITH YOUR DOMAIN
DOMAIN=yourdomain.com
EOF

    print_success "Environment template created: $env_file"
}

# Display next steps
show_next_steps() {
    print_header "Setup Complete! Next Steps"

    echo -e "${GREEN}✅ Server setup completed successfully!${NC}"
    echo ""
    echo -e "${YELLOW}Important: You may need to log out and log back in for Docker permissions to take effect.${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Copy the environment template:"
    echo "   ${YELLOW}cp .env.production.example .env.production${NC}"
    echo ""
    echo "2. Edit the production environment file:"
    echo "   ${YELLOW}nano .env.production${NC}"
    echo "   - Replace 'yourdomain.com' with your actual domain"
    echo "   - Add your OpenAI API key"
    echo "   - Generate secure keys: ${YELLOW}openssl rand -hex 32${NC}"
    echo ""
    echo "3. Configure your domain's DNS to point to this server"
    echo ""
    echo "4. Run the deployment script:"
    echo "   ${YELLOW}./deploy.sh production${NC}"
    echo ""
    echo -e "${GREEN}Your server is now ready for PalmistTalk deployment!${NC}"
}

# Main execution
main() {
    print_header "PalmistTalk Production Server Setup"

    check_user
    check_environment "$@"

    update_system
    install_docker
    install_nginx
    install_certbot
    setup_directories
    setup_database
    configure_nginx_rate_limiting
    create_env_template

    show_next_steps
}

# Run main function with all arguments
main "$@"