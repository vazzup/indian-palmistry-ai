# PalmistTalk VPS Production Deployment Instructions

## Overview
This guide will help you deploy PalmistTalk on a VPS for production use with Docker, using SQLite as the database.

## Prerequisites
- VPS with Ubuntu 20.04+ (8GB RAM, 2 cores, 80GB SSD recommended)
- Domain name pointing to your VPS IP
- OpenAI API key
- SSH access to your VPS

---

## Phase 1: VPS System Setup

### Step 1: Update System & Install Docker
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install prerequisites
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Add Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add your user to docker group
sudo usermod -aG docker $USER

# Log out and log back in, or run:
newgrp docker

# Verify Docker installation
docker --version
docker compose version
```

### Step 2: Install Nginx and UFW Firewall
```bash
# Install nginx and firewall
sudo apt install -y nginx ufw

# Configure firewall
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Start nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Verify nginx is running
sudo systemctl status nginx
```

---

## Phase 2: Application Configuration

### Step 3: Clone Repository and Setup Environment
```bash
# Clone your repository (replace with your repo URL)
git clone https://github.com/yourusername/indian-palmistry-ai.git
cd indian-palmistry-ai

# Create production environment file
cp .env.example .env
```

### Step 4: Configure Production Environment
```bash
# Edit the environment file
nano .env
```

**Update with these production values:**
```env
# Database Configuration (SQLite for production)
DATABASE_URL=sqlite+aiosqlite:///./data/production.db

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/1

# OpenAI Configuration (⚠️ ADD YOUR ACTUAL KEY HERE)
OPENAI_API_KEY=sk-your-actual-openai-api-key-here

# Security Configuration (⚠️ GENERATE SECURE KEYS - see next step)
SECRET_KEY=your-very-secure-secret-key-here-32chars
JWT_SECRET=your-very-secure-jwt-secret-here-32chars

# CORS Configuration (⚠️ REPLACE WITH YOUR DOMAIN)
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
```

### Step 5: Generate Secure Keys
```bash
# Generate SECRET_KEY (copy the output)
openssl rand -hex 32

# Generate JWT_SECRET (copy the output)
openssl rand -hex 32

# Now edit .env again and replace the placeholder keys with the generated ones
nano .env
```

### Step 6: Create Production Docker Compose Override
```bash
nano docker-compose.prod.yml
```

**Add this content:**
```yaml
# Production overrides for docker-compose.yml
services:
  redis:
    restart: unless-stopped
    volumes:
      - ./data/redis:/data

  api:
    build:
      context: .
      target: base
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///./data/production.db
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
      - DEBUG=false
      - ENVIRONMENT=production
      - ALLOWED_ORIGINS=https://yourdomain.com  # ⚠️ Replace with your domain
      - FILE_STORAGE_ROOT=./data/images
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

  worker:
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///./data/production.db
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
      - DEBUG=false
      - ENVIRONMENT=production
      - FILE_STORAGE_ROOT=./data/images
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: production
      args:
        - NEXT_PUBLIC_API_URL=https://yourdomain.com/api  # ⚠️ Replace with your domain
        - NEXT_PUBLIC_ENABLE_ANALYTICS=false
        - NEXT_PUBLIC_SITE_URL=https://yourdomain.com  # ⚠️ Replace with your domain
    environment:
      - NEXT_PUBLIC_API_URL=https://yourdomain.com/api  # ⚠️ Replace with your domain
      - NEXT_PUBLIC_SITE_URL=https://yourdomain.com  # ⚠️ Replace with your domain
      - NODE_ENV=production
    restart: unless-stopped

  # Remove flower service for production
  flower:
    profiles:
      - monitoring
```

### Step 7: Create Required Directories
```bash
# Create data directories
mkdir -p data/images data/redis

# Set proper permissions
chmod 755 data/images data/redis

# Create .gitkeep files to preserve directory structure
touch data/images/.gitkeep data/redis/.gitkeep
```

---

## Phase 3: Domain & SSL Setup

### Step 8A: Configure Rate Limiting (Main Nginx Config)
```bash
# First, add rate limiting zones to main nginx config
sudo nano /etc/nginx/nginx.conf
```

**Find the `http` block and add these rate limiting zones inside it:**
```nginx
http {
    ##
    # Basic Settings
    ##
    sendfile on;
    tcp_nopush on;
    # ... other existing settings ...

    ##
    # Rate Limiting for PalmistTalk
    ##
    limit_req_zone $binary_remote_addr zone=api:10m rate=30r/s;
    limit_req_zone $binary_remote_addr zone=analysis:10m rate=5r/s;

    ##
    # Virtual Host Configs
    ##
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
```

### Step 8B: Configure Nginx Reverse Proxy (HTTP-only first)
```bash
# Create nginx site configuration (HTTP-only for now)
sudo nano /etc/nginx/sites-available/palmisttalk
```

**Add this configuration (⚠️ replace `yourdomain.com` with your actual domain):**
```nginx
# PalmistTalk Nginx Configuration - Stage 1 (HTTP only)
# SSL will be added automatically by Certbot in Step 10

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy strict-origin-when-cross-origin;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Analysis endpoints (more restrictive due to AI processing cost)
    location ~ ^/api/(analyses|analysis)/ {
        limit_req zone=analysis burst=10 nodelay;
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Longer timeout for AI processing
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    # General API endpoints with generous rate limiting for polling
    location /api/ {
        limit_req zone=api burst=60 nodelay;
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint (no rate limiting)
    location /api/healthz {
        proxy_pass http://localhost:8000/healthz;
        proxy_set_header Host $host;
        access_log off;
    }

    # Certbot challenge location (needed for SSL verification)
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
}
```

#### 📝 Rate Limiting Explanation

The nginx configuration above uses **two-tier rate limiting** optimized for PalmistTalk's polling behavior:

1. **General API Zone** (`rate=30r/s`, `burst=60`):
   - Handles status polling (every 2 seconds)
   - Dashboard updates and general API calls
   - Generous limits to prevent polling interference

2. **Analysis Zone** (`rate=5r/s`, `burst=10`):
   - Restricts expensive AI processing endpoints
   - Prevents abuse of OpenAI API calls
   - Still allows normal analysis workflow

**Why This Won't Break Polling:**
- Normal polling: 0.5 requests/second (well under 30r/s limit)
- Initial burst: 3-5 requests handled by burst allowance
- Different zones prevent analysis limits affecting status checks

### Step 9: Enable Nginx Site and Test
```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/palmisttalk /etc/nginx/sites-enabled/

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# If test passes, restart nginx
sudo systemctl restart nginx

# Verify nginx is running
sudo systemctl status nginx
```

### Step 10: Install SSL Certificate (Automatic HTTPS Setup)
```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate and automatically configure HTTPS
# (⚠️ replace with your actual domain)
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# This will automatically:
# 1. Get SSL certificates from Let's Encrypt
# 2. Update your nginx config with SSL settings
# 3. Add HTTP to HTTPS redirect
# 4. Configure auto-renewal

# Test auto-renewal
sudo certbot renew --dry-run

# Check certificate status
sudo certbot certificates
```

---

## Phase 4: Production Deployment

### Step 11: Build and Start Application
```bash
# Navigate to your app directory
cd ~/indian-palmistry-ai

# Build and start with production override
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Wait for services to start (about 2-3 minutes)
sleep 30

# Check if all services are running
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

**Expected output should show all services as "Up":**
```
NAME                          COMMAND                  SERVICE             STATUS
indian-palmistry-ai-api-1     "uvicorn app.main:ap…"   api                 running
indian-palmistry-ai-frontend-1 "docker-entrypoint.s…"   frontend            running
indian-palmistry-ai-redis-1   "docker-entrypoint.s…"   redis               running
indian-palmistry-ai-worker-1  "celery -A app.core.…"   worker              running
```

### Step 12: Initialize Database and Test
```bash
# Check application logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f api

# Test API health (⚠️ replace with your domain)
curl https://yourdomain.com/api/healthz

# Test frontend (⚠️ replace with your domain)
curl -I https://yourdomain.com

# If everything is working, you should see:
# - API: {"status": "healthy"}
# - Frontend: HTTP/2 200
```

---

## Phase 5: Monitoring & Maintenance

### Step 13: Setup Log Rotation
```bash
# Create log rotation configuration
sudo nano /etc/logrotate.d/docker-palmisttalk
```

**Add:**
```
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    size=10M
    missingok
    delaycompress
    copytruncate
}
```

### Step 14: Create Backup Script
```bash
# Create backup script
nano ~/backup-palmisttalk.sh
chmod +x ~/backup-palmisttalk.sh
```

**Add this content:**
```bash
#!/bin/bash
APP_DIR="$HOME/indian-palmistry-ai"
BACKUP_DIR="$HOME/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

echo "Starting backup at $(date)"

# Backup SQLite database
if [ -f "$APP_DIR/data/production.db" ]; then
    cp "$APP_DIR/data/production.db" "$BACKUP_DIR/production_db_$DATE.db"
    echo "Database backed up: production_db_$DATE.db"
fi

# Backup uploaded images
if [ -d "$APP_DIR/data/images" ]; then
    tar -czf "$BACKUP_DIR/images_$DATE.tar.gz" -C "$APP_DIR/data" images/
    echo "Images backed up: images_$DATE.tar.gz"
fi

# Backup environment configuration
cp "$APP_DIR/.env" "$BACKUP_DIR/env_$DATE.backup"
echo "Environment backed up: env_$DATE.backup"

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.backup" -mtime +7 -delete

echo "Backup completed at $(date)"
echo "Backup directory: $BACKUP_DIR"
```

### Step 15: Setup Automated Backups
```bash
# Setup cron job for daily backups
crontab -e
```

**Add this line (backups run daily at 3 AM):**
```
0 3 * * * /home/$USER/backup-palmisttalk.sh >> /home/$USER/backup.log 2>&1
```

### Step 16: Create Management Aliases
```bash
# Add helpful aliases to your shell
echo '# PalmistTalk Management Aliases' >> ~/.bashrc
echo 'alias palmist-logs="docker compose -f ~/indian-palmistry-ai/docker-compose.yml -f ~/indian-palmistry-ai/docker-compose.prod.yml logs -f"' >> ~/.bashrc
echo 'alias palmist-status="docker compose -f ~/indian-palmistry-ai/docker-compose.yml -f ~/indian-palmistry-ai/docker-compose.prod.yml ps"' >> ~/.bashrc
echo 'alias palmist-restart="docker compose -f ~/indian-palmistry-ai/docker-compose.yml -f ~/indian-palmistry-ai/docker-compose.prod.yml restart"' >> ~/.bashrc
echo 'alias palmist-stop="docker compose -f ~/indian-palmistry-ai/docker-compose.yml -f ~/indian-palmistry-ai/docker-compose.prod.yml down"' >> ~/.bashrc
echo 'alias palmist-start="docker compose -f ~/indian-palmistry-ai/docker-compose.yml -f ~/indian-palmistry-ai/docker-compose.prod.yml up -d"' >> ~/.bashrc

# Reload bashrc
source ~/.bashrc
```

---

## Final Checklist

### ✅ Before Going Live:

1. **Replace all placeholders:**
   - [ ] `yourdomain.com` → Your actual domain in all files
   - [ ] `OPENAI_API_KEY` → Your real OpenAI API key
   - [ ] `SECRET_KEY` → Generated secure key (32 characters)
   - [ ] `JWT_SECRET` → Generated secure key (32 characters)

2. **DNS Configuration:**
   - [ ] Point your domain's A record to your VPS IP address
   - [ ] Wait for DNS propagation (can take 24-48 hours)

3. **SSL Certificate:**
   - [ ] SSL certificate installed successfully
   - [ ] Auto-renewal configured and tested

4. **Application Tests:**
   - [ ] Frontend loads at `https://yourdomain.com`
   - [ ] API responds at `https://yourdomain.com/api/healthz`
   - [ ] Upload and palm reading functionality works
   - [ ] All services are running (`palmist-status`)

### 🔧 Common Management Commands:

```bash
# Check application status
palmist-status

# View real-time logs
palmist-logs

# Restart all services
palmist-restart

# Stop application
palmist-stop

# Start application
palmist-start

# Manual backup
~/backup-palmisttalk.sh

# Check SSL certificate expiry
sudo certbot certificates

# Renew SSL certificate manually
sudo certbot renew
```

### 🚨 Troubleshooting:

#### If services won't start:
```bash
# Check Docker daemon
sudo systemctl status docker

# Check logs for errors
palmist-logs api
palmist-logs frontend
```

#### If SSL certificate fails:
```bash
# Check if domain points to your server
dig yourdomain.com

# Check nginx configuration
sudo nginx -t

# Check certbot logs
sudo tail -f /var/log/letsencrypt/letsencrypt.log
```

#### If application is slow:
```bash
# Check server resources
htop
df -h

# Check Docker container resources
docker stats
```

### 📱 Your Production URLs:
- **Frontend**: `https://yourdomain.com`
- **API**: `https://yourdomain.com/api`
- **Health Check**: `https://yourdomain.com/api/healthz`

---

## Security Notes

1. **Regular Updates**: Update your system and Docker images regularly
2. **Backup Verification**: Test your backups periodically
3. **Monitor Logs**: Check application logs regularly for errors or suspicious activity
4. **SSL Monitoring**: Ensure SSL certificates renew automatically
5. **Firewall**: Keep UFW enabled and only necessary ports open

Your PalmistTalk application is now running in production! 🎉

---

*Created: January 2025*
*For: PalmistTalk Production Deployment*