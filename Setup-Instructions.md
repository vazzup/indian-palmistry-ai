# PalmistTalk Production Deployment Guide

## Overview
This guide provides a **simplified, automated approach** to deploy PalmistTalk on a production VPS. We've learned from common deployment issues and created two scripts that handle everything:

- **`setup.sh`** - One-time server preparation (install Docker, nginx, create directories, etc.)
- **`deploy.sh`** - Application deployment (can be run multiple times for updates)

## Prerequisites
- VPS with Ubuntu 20.04+ (8GB RAM, 2 cores, 80GB SSD recommended)
- Domain name pointing to your VPS IP address
- OpenAI API key
- SSH access to your VPS with sudo privileges

## Development vs Production

### For Local Development
Use the existing development setup (no changes needed):
```bash
./start.sh  # Runs at http://localhost:3000
```

### For Production Deployment
Use the new automated scripts:
```bash
./setup.sh production    # One-time server setup
./deploy.sh production   # Deploy application
```

---

## Quick Start (Automated Setup)

### Step 1: Initial Server Setup
```bash
# On your VPS, clone the repository
git clone https://github.com/your-username/indian-palmistry-ai.git
cd indian-palmistry-ai

# Run the automated server setup (one-time only)
./setup.sh production
```

This script automatically:
- ✅ Installs Docker, nginx, Certbot, and dependencies
- ✅ Creates application directories with proper permissions
- ✅ Sets up SQLite database with correct ownership
- ✅ Configures firewall and nginx rate limiting
- ✅ Creates environment template

### Step 2: Configure Your Environment
```bash
# Copy the environment template
cp .env.production.example .env.production

# Edit with your actual values
nano .env.production
```

**Required changes in `.env.production`:**
```bash
# 1. Set your domain
DOMAIN=yourdomain.com

# 2. Add your OpenAI API key
OPENAI_API_KEY=sk-your-actual-key-here

# 3. Generate secure keys
openssl rand -hex 32  # Copy for SECRET_KEY
openssl rand -hex 32  # Copy for JWT_SECRET

# 4. Update CORS origins
ALLOWED_ORIGINS=https://yourdomain.com
```

### Step 3: Deploy Application
```bash
# Deploy the application
./deploy.sh production
```

This script automatically:
- ✅ Creates backups of existing data
- ✅ Cleans up port conflicts
- ✅ Builds and starts all containers
- ✅ Configures nginx with your domain
- ✅ Sets up SSL certificates with Let's Encrypt
- ✅ Performs health checks
- ✅ Shows deployment status

**That's it!** Your application should now be running at `https://yourdomain.com`

---

## Manual Steps (Alternative)

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

## Management & Monitoring

### 🔧 Common Commands:

```bash
# Check application status
docker compose -f docker-compose.prod.yml ps

# View real-time logs
docker compose -f docker-compose.prod.yml logs -f

# View specific service logs
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml logs -f frontend
docker compose -f docker-compose.prod.yml logs -f worker

# Restart specific service
docker compose -f docker-compose.prod.yml restart api

# Update application (after git pull)
./deploy.sh production

# Stop application
docker compose -f docker-compose.prod.yml down

# Manual backup
mkdir -p backups
cp data/production.db backups/backup_$(date +%Y%m%d_%H%M%S).db

# Check SSL certificate expiry
sudo certbot certificates

# Renew SSL certificate manually
sudo certbot renew
```

### 📊 Health Checks:

```bash
# Check API health
curl https://yourdomain.com/api/healthz

# Check if all containers are running
docker compose -f docker-compose.prod.yml ps

# Check system resources
htop
df -h
docker stats
```

### ✅ Pre-Launch Checklist:

1. **DNS Configuration:**
   - [ ] Domain A record points to your VPS IP
   - [ ] DNS propagation completed (check with: `dig yourdomain.com`)

2. **Environment Configuration:**
   - [ ] `.env.production` created with actual values
   - [ ] OpenAI API key added and working
   - [ ] Secure keys generated (32+ characters)
   - [ ] Domain set correctly

3. **Application Tests:**
   - [ ] Frontend loads: `https://yourdomain.com`
   - [ ] API responds: `https://yourdomain.com/api/healthz`
   - [ ] Upload functionality works
   - [ ] Palm reading analysis completes
   - [ ] All containers healthy: `docker compose -f docker-compose.prod.yml ps`

4. **SSL & Security:**
   - [ ] SSL certificate installed and valid
   - [ ] Auto-renewal configured: `sudo certbot renew --dry-run`
   - [ ] HTTPS redirect working
   - [ ] Rate limiting configured

### 🚨 Troubleshooting:

#### Common Issues We've Solved:

**1. Port 3000 Already in Use:**
```bash
# The deploy.sh script handles this automatically, but if needed:
sudo lsof -ti :3000 | xargs -r kill -9
```

**2. Frontend Build Fails (clientReferenceManifest error):**
- ✅ Fixed: Added `export const dynamic = 'force-dynamic'` to disable prerendering
- ✅ Fixed: Removed PWA and bundle analyzer plugins
- ✅ Fixed: Added proper browser API guards

**3. Database Permission Errors:**
```bash
# Fixed automatically by setup.sh, but if needed:
sudo chown -R 1000:1000 ./data
chmod 664 ./data/production.db
```

**4. Mixed Content Errors (HTTP/HTTPS):**
- ✅ Fixed: deploy.sh automatically configures frontend URLs based on domain
- ✅ Fixed: All services use HTTPS in production

**5. API Connection Refused:**
```bash
# Check if API is running
curl http://localhost:8000/healthz

# Check API logs
docker compose -f docker-compose.prod.yml logs api
```

#### General Troubleshooting:

**Services won't start:**
```bash
# Check Docker daemon
sudo systemctl status docker

# Check logs for specific service
docker compose -f docker-compose.prod.yml logs api
docker compose -f docker-compose.prod.yml logs frontend

# Restart specific service
docker compose -f docker-compose.prod.yml restart api
```

**SSL certificate issues:**
```bash
# Check if domain points to your server
dig yourdomain.com

# Check nginx configuration
sudo nginx -t

# Check certbot logs
sudo tail -f /var/log/letsencrypt/letsencrypt.log

# Manually run certbot
sudo certbot --nginx -d yourdomain.com
```

**Application is slow:**
```bash
# Check server resources
htop
df -h

# Check Docker container resources
docker stats

# Check database size
ls -lh data/production.db
```

**Need to rollback:**
```bash
# deploy.sh includes automatic rollback on failure
# Or manually restore from backup:
cp backups/production_db_TIMESTAMP.db data/production.db
./deploy.sh production
```

### 📱 Your Production URLs:
- **Frontend**: `https://yourdomain.com`
- **API**: `https://yourdomain.com/api`
- **Health Check**: `https://yourdomain.com/api/healthz`

---

## What We Learned

This simplified deployment approach solves all the common issues encountered during manual setup:

✅ **No More Port Conflicts**: Automated port cleanup
✅ **No Environment Variable Confusion**: Single source of truth
✅ **No Database Permission Issues**: Proper ownership setup
✅ **No Mixed Content Errors**: Automatic HTTPS configuration
✅ **No Build Failures**: Pre-configured Next.js optimizations
✅ **Easy Updates**: Simple `./deploy.sh production` command
✅ **Automatic Backups**: Built-in backup and rollback
✅ **Health Monitoring**: Comprehensive health checks

## Security & Maintenance

1. **Automated Updates**:
   ```bash
   # Update application
   git pull && ./deploy.sh production
   ```

2. **Regular Backups**: Automatically created before each deployment

3. **SSL Monitoring**: Auto-renewal configured with Let's Encrypt

4. **Rate Limiting**: Configured to prevent API abuse

5. **Firewall**: UFW configured with minimal required ports

---

## Support

If you encounter issues not covered in the troubleshooting section:

1. Check the logs: `docker compose -f docker-compose.prod.yml logs -f`
2. Verify environment: `cat .env.production` (be careful not to expose secrets)
3. Test health endpoints: `curl https://yourdomain.com/api/healthz`

---

**🎉 Your PalmistTalk application is now production-ready!**

*Automated deployment approach - January 2025*