# Security Implementation Guide

This document provides a comprehensive overview of the security enhancements implemented in the Indian Palmistry AI application, including setup instructions, configuration options, and maintenance procedures.

## 🔒 Security Features Overview

The application implements enterprise-grade security features:

### ✅ **Authentication & Session Security**
- Cookie-based sessions with `__Host-` prefix
- Rolling expiry with absolute maximum age
- Session rotation on privilege changes
- Concurrent session limits
- Mass session invalidation

### ✅ **CSRF Protection**
- Double-submit cookie pattern
- Origin/Referer header validation
- Session-bound CSRF tokens
- Automatic token rotation

### ✅ **Security Headers**
- Content Security Policy (CSP)
- X-Frame-Options, X-Content-Type-Options
- Referrer-Policy, Permissions-Policy
- XSS Protection headers

### ✅ **Rate Limiting**
- Endpoint-specific rate limits
- Burst protection mechanisms
- IP-based tracking with proxy support
- Redis-backed sliding windows

### ✅ **CORS Security**
- Exact origin matching (no wildcards)
- Credential support with proper headers
- Vary header for cache control

## 🚀 Quick Start

### 1. Environment Configuration

Create or update your `.env` file:

```bash
# Session Security
SESSION_COOKIE_NAME="__Host-session_id"
SESSION_EXPIRE_SECONDS=604800
SESSION_ABSOLUTE_MAX_AGE=2592000
SESSION_ROLLING_WINDOW=3600
SESSION_COOKIE_SAMESITE="Lax"
MAX_CONCURRENT_SESSIONS=5

# CORS Configuration
ALLOWED_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"

# Redis Configuration (required for sessions and rate limiting)
REDIS_URL="redis://localhost:6379/0"

# Production Security
DEBUG=False
ENVIRONMENT="production"
```

### 2. Database Migration

No database migrations required - all session data is stored in Redis.

### 3. Dependencies

Ensure all security dependencies are installed:

```bash
# Backend
pip install redis fastapi-security-headers

# Frontend  
npm install axios @types/js-cookie
```

### 4. Verification

Test the security implementation:

```bash
# Test authentication flow
python scripts/test_auth_security.py

# Test CSRF protection
python scripts/test_csrf_protection.py

# Test rate limiting
python scripts/test_rate_limits.py
```

## ⚙️ Configuration Options

### Session Management

```python
# app/core/config.py
class Settings:
    # Basic session settings
    session_expire_seconds: int = 604800      # 1 week
    session_absolute_max_age: int = 2592000   # 30 days hard limit
    session_rolling_window: int = 3600        # 1 hour activity refresh
    
    # Security settings
    session_cookie_name: str = "__Host-session_id"
    session_cookie_samesite: str = "Lax"      # or "Strict"
    max_concurrent_sessions: int = 5          # Per user limit
```

### Rate Limiting Rules

```python
# app/middleware/rate_limiting.py
rate_limits = {
    "/api/v1/auth/login": (5, 300, 2),      # 5 attempts per 5min, burst 2
    "/api/v1/auth/register": (3, 300, 1),   # 3 attempts per 5min, burst 1
    "/api/v1/auth/logout": (10, 60, 5),     # 10 attempts per min, burst 5
    "/api/v1/analyses/": (50, 3600, 20),    # 50 per hour, burst 20
    "default": (1000, 3600, 100)            # Default limits
}
```

### Security Headers

```python
# app/middleware/security.py
security_headers = {
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'...",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), location=()",
    "X-XSS-Protection": "1; mode=block"
}
```

### CORS Configuration

```python
# Environment-specific CORS origins
DEVELOPMENT_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001"
]

PRODUCTION_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
    "https://api.yourdomain.com"
]
```

## 🔧 Development Setup

### Local Development

1. **Start Redis**:
```bash
redis-server
```

2. **Configure Development Settings**:
```bash
export ALLOWED_ORIGINS="http://localhost:3000,http://localhost:3001"
export SESSION_COOKIE_SAMESITE="Lax"
export DEBUG=True
```

3. **Test HTTPS Locally** (recommended):
```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Run with HTTPS
uvicorn app.main:app --ssl-keyfile=key.pem --ssl-certfile=cert.pem --port 8000
```

### Frontend Development

Update your frontend development configuration:

```typescript
// next.config.js or equivalent
module.exports = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'https://localhost:8000/api/:path*' // Use HTTPS
      }
    ]
  }
}
```

## 🏭 Production Deployment

### 1. Infrastructure Requirements

- **HTTPS Load Balancer** with valid SSL certificate
- **Redis Cluster** for session storage and rate limiting
- **WAF (Web Application Firewall)** for additional protection
- **CDN** with DDoS protection

### 2. Security Configuration

```bash
# Production environment variables
export ENVIRONMENT="production"
export DEBUG=False
export SESSION_COOKIE_SAMESITE="Strict"
export ALLOWED_ORIGINS="https://yourdomain.com,https://api.yourdomain.com"

# Redis cluster configuration
export REDIS_URL="redis://redis-cluster:6379/0"

# Rate limiting (stricter in production)
export MAX_CONCURRENT_SESSIONS=3
```

### 3. Reverse Proxy Configuration

**Nginx Configuration**:
```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    # SSL configuration
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    
    # Security headers (additional to middleware)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    
    # Rate limiting at proxy level
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Cookie security
        proxy_cookie_flags ~ secure samesite=strict;
    }
}
```

### 4. Health Checks

Set up monitoring for security components:

```python
# app/health/security_checks.py
async def check_security_health():
    checks = {
        "redis_connection": await check_redis_connection(),
        "session_store": await check_session_store_health(),
        "rate_limiting": await check_rate_limiting_health(),
        "csrf_tokens": await check_csrf_token_generation(),
        "security_headers": check_security_headers_config()
    }
    return checks
```

## 🔍 Monitoring & Alerting

### Key Metrics

Monitor these security metrics:

```python
# Authentication metrics
failed_login_attempts_per_minute = Counter('auth_failed_attempts_total')
successful_logins_per_minute = Counter('auth_successful_logins_total')
session_rotations_per_hour = Counter('session_rotations_total')

# Rate limiting metrics
rate_limit_violations = Counter('rate_limit_violations_total')
rate_limit_blocked_requests = Counter('rate_limit_blocked_total')

# CSRF metrics
csrf_token_failures = Counter('csrf_failures_total')
csrf_token_generations = Counter('csrf_generations_total')

# Session metrics
active_sessions = Gauge('active_sessions_total')
concurrent_session_violations = Counter('concurrent_session_limit_exceeded')
```

### Alert Thresholds

Set up alerts for security events:

```yaml
alerts:
  - name: High Authentication Failure Rate
    condition: failed_login_attempts_per_minute > 100
    action: notify_security_team
    
  - name: Rate Limiting Violations
    condition: rate_limit_violations > 1000/hour
    action: investigate_potential_attack
    
  - name: CSRF Attack Detected
    condition: csrf_token_failures > 50/hour
    action: block_suspicious_ips
    
  - name: Mass Session Creation
    condition: session_creations > 10000/hour
    action: check_for_abuse
```

### Log Analysis

Important security events to log and analyze:

```python
# Authentication events
logger.info("User login successful", extra={
    "user_id": user.id,
    "ip_address": request.client.host,
    "user_agent": request.headers.get("User-Agent"),
    "session_id": session_id[:8] + "...",
    "timestamp": datetime.utcnow().isoformat()
})

# Security violations
logger.warning("CSRF token validation failed", extra={
    "user_id": user.id,
    "ip_address": request.client.host,
    "origin": request.headers.get("Origin"),
    "referer": request.headers.get("Referer"),
    "violation_type": "csrf_mismatch"
})
```

## 🧪 Testing

### Security Test Suite

Run comprehensive security tests:

```bash
# Unit tests
pytest tests/security/ -v

# Integration tests  
pytest tests/integration/test_auth_security.py -v

# Load tests
locust -f tests/load/test_auth_performance.py --host=https://api.yourdomain.com
```

### Manual Security Testing

```bash
# Test CSRF protection
curl -X POST https://api.yourdomain.com/api/v1/auth/profile \
  -H "Content-Type: application/json" \
  -H "Origin: https://evil.com" \
  -d '{"name":"hacked"}' \
  --cookie "session=valid_session"

# Test rate limiting
for i in {1..10}; do
  curl -X POST https://api.yourdomain.com/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test","password":"wrong"}'
done

# Test session security
curl -X GET https://api.yourdomain.com/api/v1/auth/sessions \
  --cookie "__Host-session_id=valid_session"
```

### Penetration Testing

Regular security assessments should include:

1. **Authentication Bypass Testing**
2. **Session Management Testing**
3. **CSRF Protection Testing**
4. **Rate Limiting Testing**
5. **Input Validation Testing**
6. **Business Logic Testing**

## 🚨 Incident Response

### Security Incident Playbook

#### Suspected Brute Force Attack

1. **Immediate Actions**:
   ```bash
   # Check failed login patterns
   grep "Authentication failed" /var/log/app.log | tail -1000
   
   # Block suspicious IPs at firewall level
   iptables -A INPUT -s SUSPICIOUS_IP -j DROP
   ```

2. **Investigation**:
   - Analyze rate limiting logs
   - Check geographic patterns
   - Review user account status

3. **Mitigation**:
   - Reduce rate limits temporarily
   - Enable additional logging
   - Consider CAPTCHA implementation

#### CSRF Attack Detected

1. **Immediate Actions**:
   ```bash
   # Check CSRF violation patterns
   grep "CSRF.*failed" /var/log/app.log | tail -500
   
   # Verify origin validation is working
   curl -X POST https://api.yourdomain.com/api/v1/auth/test \
     -H "Origin: https://attacker.com"
   ```

2. **Investigation**:
   - Analyze request origins
   - Check for compromised accounts
   - Review CSRF token generation

#### Session Hijacking Suspected

1. **Immediate Actions**:
   ```python
   # Force session rotation for all users
   await session_service.force_global_session_rotation()
   
   # Invalidate suspicious sessions
   await session_service.invalidate_sessions_by_criteria({
       "client_ip": "suspicious_ip_range"
   })
   ```

2. **Investigation**:
   - Check for session ID patterns
   - Analyze concurrent session violations
   - Review SSL/TLS configuration

## 📚 Maintenance

### Regular Security Tasks

#### Weekly
- Review authentication failure patterns
- Analyze rate limiting effectiveness
- Check for unusual session patterns
- Update security monitoring dashboards

#### Monthly
- Review and update rate limiting rules
- Analyze session duration patterns
- Check for new security vulnerabilities
- Update security headers configuration

#### Quarterly
- Conduct penetration testing
- Review and update security policies
- Analyze security incident trends
- Update security training materials

### Security Updates

Keep security components updated:

```bash
# Update Python security packages
pip install --upgrade fastapi uvicorn redis cryptography

# Update Node.js security packages
npm audit fix

# Update system security patches
apt update && apt upgrade -y
```

### Configuration Backups

Backup security configurations:

```bash
# Backup security configurations
tar -czf security-config-backup.tar.gz \
  app/core/config.py \
  app/middleware/security.py \
  app/middleware/rate_limiting.py \
  docs/security/

# Store backup securely
aws s3 cp security-config-backup.tar.gz s3://secure-backups/
```

## 🔗 Additional Resources

### Documentation
- [Enhanced Authentication API](docs/api/ENHANCED_AUTHENTICATION.md)
- [Session Management Guide](docs/security/SESSION_MANAGEMENT.md)
- [Security Hardening Details](docs/security/SECURITY_HARDENING.md)

### Security Tools
- [OWASP ZAP](https://zaproxy.org/) - Security testing
- [Burp Suite](https://portswigger.net/burp) - Web application security testing
- [Nmap](https://nmap.org/) - Network security scanning

### Compliance Resources
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [PCI DSS Guidelines](https://www.pcisecuritystandards.org/)

### Emergency Contacts
- **Security Team**: security@yourdomain.com
- **DevOps Team**: devops@yourdomain.com
- **Incident Response**: incidents@yourdomain.com

---

## 🆘 Need Help?

If you encounter any issues with the security implementation:

1. **Check the logs**: Review application and security logs
2. **Consult documentation**: Reference the security guides
3. **Test in isolation**: Use the provided test scripts
4. **Contact support**: Reach out to the security team

Remember: Security is everyone's responsibility! 🛡️