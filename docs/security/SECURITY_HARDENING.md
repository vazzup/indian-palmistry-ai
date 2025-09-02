# Security Hardening Documentation

This document describes the comprehensive security hardening measures implemented in the Indian Palmistry AI application to protect against common web vulnerabilities and attacks.

## Overview

The application implements a defense-in-depth security strategy with multiple layers of protection:

1. **Hardened Cookie-Based Sessions**
2. **Enhanced CSRF Protection** 
3. **Comprehensive Security Headers**
4. **Rate Limiting & Abuse Prevention**
5. **Strict CORS Configuration**
6. **Advanced Session Management**
7. **Comprehensive Audit Logging**

## 1. Cookie Hardening

### Implementation
- **Cookie Name**: `__Host-session_id` (uses `__Host-` prefix for maximum security)
- **Security Flags**:
  - `HttpOnly: true` - Prevents JavaScript access
  - `Secure: true` - Requires HTTPS (enforced in all environments)
  - `SameSite: Lax` - Prevents most CSRF attacks (configurable to Strict)
  - `Path: /` - Restricts cookie scope
  - No `Domain` attribute - Restricts to current domain only

### Configuration
```python
# app/core/config.py
session_cookie_name: str = "__Host-session_id"
session_cookie_samesite: str = "Lax"  # or "Strict"
session_expire_seconds: int = 604800  # 1 week
session_absolute_max_age: int = 2592000  # 30 days absolute maximum
```

### Security Benefits
- `__Host-` prefix prevents subdomain cookie hijacking
- Always secure even in development (requires HTTPS)
- HttpOnly prevents XSS cookie theft
- SameSite prevents cross-site request forgery
- Path restriction limits cookie exposure

## 2. Enhanced Session Management

### Features
- **Session Rotation**: New session ID on login and privilege changes
- **Rolling Expiry**: Sessions stay alive with activity, expire when idle
- **Absolute Maximum Age**: Hard limit prevents indefinite sessions
- **Concurrent Session Limits**: Configurable limit per user
- **Mass Invalidation**: Invalidate all user sessions on security events

### Session Service API
```python
from app.services.session_service import session_service

# Create new session
session_id, csrf_token = await session_service.create_session(
    user_id=user.id,
    user_email=user.email, 
    user_name=user.name,
    client_info={"ip": "1.2.3.4", "user_agent": "..."}
)

# Rotate session ID
new_session_id, new_csrf_token = await session_service.rotate_session(old_session_id)

# Refresh activity (rolling expiry)
is_active = await session_service.refresh_session_activity(session_id)

# Invalidate all user sessions
count = await session_service.invalidate_user_sessions(user_id, except_session=current_session)
```

### Configuration Options
```python
session_expire_seconds: int = 604800      # Session TTL (1 week)
session_absolute_max_age: int = 2592000   # Hard limit (30 days)
session_rolling_window: int = 3600        # Activity refresh window (1 hour)
max_concurrent_sessions: int = 5          # Max sessions per user
```

## 3. CSRF Protection

### Multi-Layer CSRF Defense
1. **SameSite Cookie Protection**: Primary defense against CSRF
2. **CSRF Token Validation**: Secondary defense with origin checking
3. **Origin/Referer Validation**: Additional cross-origin request blocking

### Implementation
```python
async def verify_csrf_token(request: Request, current_user: User):
    # 1. Verify origin/referer headers
    origin = request.headers.get("Origin")
    if origin not in settings.allowed_origins:
        raise HTTPException(403, "Request from unauthorized origin")
    
    # 2. Validate CSRF token
    csrf_token = request.headers.get("X-CSRF-Token")
    session_csrf = session_data.get("csrf_token")
    if csrf_token != session_csrf:
        raise HTTPException(403, "Invalid CSRF token")
    
    # 3. Ensure session belongs to user
    if session_data.get("user_id") != current_user.id:
        raise HTTPException(403, "Session user mismatch")
```

### Frontend Integration
```typescript
// Automatic CSRF token handling
api.interceptors.request.use(async (config) => {
  if (['post', 'put', 'patch', 'delete'].includes(config.method)) {
    const csrfToken = await getCachedCSRFToken();
    config.headers['X-CSRF-Token'] = csrfToken;
  }
  return config;
});
```

## 4. Security Headers Middleware

### Headers Implemented
- **Content-Security-Policy**: Prevents XSS and code injection
- **X-Content-Type-Options**: Prevents MIME-type sniffing
- **X-Frame-Options**: Prevents clickjacking
- **Referrer-Policy**: Controls referrer information leakage
- **Permissions-Policy**: Restricts browser features
- **X-XSS-Protection**: Legacy XSS protection

### CSP Configuration
```
default-src 'self'; 
script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; 
style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; 
font-src 'self' https://fonts.gstatic.com; 
img-src 'self' data: blob: https:; 
media-src 'self'; 
object-src 'none'; 
frame-ancestors 'none'; 
base-uri 'self'; 
form-action 'self'
```

## 5. Rate Limiting

### Rate Limit Rules
```python
rate_limits = {
    "/api/v1/auth/login": (5, 300, 2),      # 5 attempts per 5min, burst 2
    "/api/v1/auth/register": (3, 300, 1),   # 3 attempts per 5min, burst 1
    "/api/v1/auth/logout": (10, 60, 5),     # 10 attempts per min, burst 5
    "/api/v1/analyses/": (50, 3600, 20),    # 50 per hour, burst 20
    "default": (1000, 3600, 100)            # Default limits
}
```

### Implementation Features
- **Sliding Window**: More accurate than fixed windows
- **Burst Protection**: Separate limits for rapid requests
- **Redis-Backed**: Distributed rate limiting
- **IP-Based Tracking**: Handles proxied environments
- **Graceful Degradation**: Continues on Redis errors

## 6. CORS Security

### Strict CORS Configuration
```python
# No wildcards - exact origin matching only
allowed_origins = [
    "https://yourdomain.com",
    "https://www.yourdomain.com", 
    "http://localhost:3000"  # Development only
]

# Headers
"Access-Control-Allow-Origin": exact_origin_only
"Access-Control-Allow-Credentials": "true"
"Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS"
"Vary": "Origin"  # Important for caching
```

### Security Benefits
- Prevents unauthorized cross-origin requests
- Exact origin matching (no wildcards)
- Proper credential handling
- Cache-aware with Vary header

## 7. Authentication Logging

### Logged Events
- Login attempts (success/failure)
- Registration attempts
- Session rotations
- Session invalidations
- Rate limit violations
- CSRF token violations

### Log Format
```python
{
    "event": "authentication_success",
    "user_id": 123,
    "email": "user@example.com",
    "client_ip": "1.2.3.4",
    "user_agent": "Mozilla/5.0...",
    "session_id": "abc123...",
    "timestamp": "2024-01-01T12:00:00Z",
    "method": "POST",
    "path": "/api/v1/auth/login"
}
```

## 8. Session Management Endpoints

### New API Endpoints
```
GET  /api/v1/auth/sessions           - List active sessions
POST /api/v1/auth/sessions/rotate    - Rotate current session  
POST /api/v1/auth/sessions/invalidate-all - Invalidate all other sessions
GET  /api/v1/auth/csrf-token         - Get CSRF token
```

### Frontend Session Management
```typescript
const auth = useAuth();

// List sessions
const sessions = await auth.getSessions();

// Rotate session for security
await auth.rotateSession();

// Log out from all other devices
await auth.invalidateAllSessions();
```

## Security Best Practices Implemented

### 1. **Defense in Depth**
- Multiple layers of security controls
- Graceful degradation when components fail
- No single point of failure

### 2. **Principle of Least Privilege**
- Minimal cookie scope and permissions
- Session-bound CSRF tokens
- Origin-restricted requests

### 3. **Secure by Default**
- Always-secure cookies
- Strict CSP policies
- Conservative rate limits

### 4. **Comprehensive Monitoring**
- Authentication event logging
- Rate limit violation tracking
- CSRF attack detection

## Configuration Guide

### Production Deployment
```bash
# Environment variables
ALLOWED_ORIGINS="https://yourdomain.com,https://api.yourdomain.com"
SESSION_COOKIE_SAMESITE="Strict"  # Strictest setting
MAX_CONCURRENT_SESSIONS="3"       # Limit concurrent logins
```

### Development Setup
```bash
ALLOWED_ORIGINS="http://localhost:3000,http://localhost:3001"
SESSION_COOKIE_SAMESITE="Lax"     # More permissive for development
MAX_CONCURRENT_SESSIONS="5"
```

## Monitoring & Alerting

### Key Metrics to Monitor
- Authentication failure rates
- Rate limit violations
- CSRF token mismatches  
- Session rotation frequency
- Concurrent session counts

### Alert Thresholds
- > 10 auth failures per IP per minute
- > 5 CSRF violations per user per hour
- > 100 rate limit violations per hour
- Session creation rate spikes

## Testing Security Controls

### Manual Testing
```bash
# Test CSRF protection
curl -X POST https://yourapi.com/api/v1/auth/profile \
  -H "Content-Type: application/json" \
  -H "Origin: https://evil.com" \
  -d '{"name":"hacked"}'

# Test rate limiting  
for i in {1..10}; do
  curl -X POST https://yourapi.com/api/v1/auth/login \
    -d '{"email":"test","password":"wrong"}'
done
```

### Automated Security Testing
- CSRF token validation tests
- Rate limiting tests
- Session management tests
- Origin validation tests
- Cookie security flag tests

## Compliance & Standards

This implementation addresses requirements from:
- **OWASP Top 10** (A01, A02, A03, A05, A07)
- **NIST Cybersecurity Framework**
- **PCI DSS** (if handling payments)
- **GDPR** (session data protection)

## Future Enhancements

1. **Device Fingerprinting**: Enhanced session binding
2. **Geolocation Checks**: Detect suspicious logins
3. **Machine Learning**: Behavioral anomaly detection  
4. **Hardware Security Keys**: WebAuthn/FIDO2 support
5. **Session Analytics**: Advanced usage patterns

## Troubleshooting

### Common Issues
1. **CORS errors**: Check allowed_origins configuration
2. **CSRF failures**: Verify origin headers and token handling
3. **Rate limiting**: Check IP detection in proxied environments
4. **Cookie issues**: Ensure HTTPS in production

### Debug Mode
Set `DEBUG=True` to enable additional security logging (development only).