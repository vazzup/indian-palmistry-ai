# Enhanced Authentication API Documentation

This document describes the enhanced authentication API endpoints with comprehensive security features including session management, CSRF protection, and hardened cookie handling.

## Overview

The authentication system provides secure, scalable user authentication with the following security features:

- **Cookie-based sessions** with `__Host-` prefix security
- **Rolling session expiry** with absolute maximum age limits
- **CSRF protection** with origin validation
- **Session rotation** for enhanced security
- **Concurrent session management**
- **Comprehensive audit logging**

## Base URL

```
https://api.yourdomain.com/api/v1/auth
```

## Authentication Method

The API uses **secure HTTP-only cookies** for authentication. No bearer tokens or API keys are required for authenticated endpoints.

### Cookie Security Features

- **Name**: `__Host-session_id` (secure prefix)
- **Attributes**: `HttpOnly`, `Secure`, `SameSite=Lax`, `Path=/`
- **Lifetime**: Configurable (default: 7 days, max: 30 days)

## Endpoints

### User Registration

Creates a new user account and automatically logs them in.

```http
POST /register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "name": "John Doe"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "User registered successfully",
  "user": {
    "id": 123,
    "email": "user@example.com",
    "name": "John Doe",
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  },
  "csrf_token": "abc123...def456"
}
```

**Response Headers:**
```http
Set-Cookie: __Host-session_id=xyz789...; Max-Age=604800; Path=/; HttpOnly; Secure; SameSite=Lax
```

**Error Responses:**
- `400 Bad Request`: User with email already exists
- `422 Unprocessable Entity`: Invalid input data
- `500 Internal Server Error`: Registration failed

### User Login

Authenticates user credentials and creates a new session.

```http
POST /login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Login successful",
  "user": {
    "id": 123,
    "email": "user@example.com",
    "name": "John Doe",
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  },
  "csrf_token": "abc123...def456",
  "session_expires": "2024-01-08T12:00:00Z"
}
```

**Response Headers:**
```http
Set-Cookie: __Host-session_id=xyz789...; Max-Age=604800; Path=/; HttpOnly; Secure; SameSite=Lax
```

**Error Responses:**
- `401 Unauthorized`: Invalid email or password
- `429 Too Many Requests`: Too many login attempts
- `500 Internal Server Error`: Login failed

### User Logout

Terminates the current session and clears the session cookie.

```http
POST /logout
```

**Request Headers:**
```http
Cookie: __Host-session_id=xyz789...
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Logout successful"
}
```

**Response Headers:**
```http
Set-Cookie: __Host-session_id=; Max-Age=0; Path=/; HttpOnly; Secure; SameSite=Lax
```

**Error Responses:**
- `500 Internal Server Error`: Logout failed (cookie still cleared)

### Get Current User

Retrieves information about the currently authenticated user.

```http
GET /me
```

**Request Headers:**
```http
Cookie: __Host-session_id=xyz789...
```

**Response (200 OK):**
```json
{
  "id": 123,
  "email": "user@example.com",
  "name": "John Doe",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated or session expired

### Update User Profile

Updates the current user's profile information.

```http
PUT /profile
```

**Request Headers:**
```http
Cookie: __Host-session_id=xyz789...
X-CSRF-Token: abc123...def456
```

**Request Body:**
```json
{
  "name": "Jane Doe",
  "picture": "https://example.com/avatar.jpg"
}
```

**Response (200 OK):**
```json
{
  "id": 123,
  "email": "user@example.com",
  "name": "Jane Doe",
  "picture": "https://example.com/avatar.jpg",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T14:30:00Z"
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Invalid or missing CSRF token
- `404 Not Found`: User not found
- `422 Unprocessable Entity`: Invalid input data

### Get CSRF Token

Retrieves a CSRF token for the current session.

```http
GET /csrf-token
```

**Request Headers:**
```http
Cookie: __Host-session_id=xyz789...
```

**Response (200 OK):**
```json
{
  "csrf_token": "abc123...def456"
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated or invalid session

## Session Management Endpoints

### List Active Sessions

Retrieves all active sessions for the current user.

```http
GET /sessions
```

**Request Headers:**
```http
Cookie: __Host-session_id=xyz789...
```

**Response (200 OK):**
```json
{
  "sessions": [
    {
      "session_id": "session_123...",
      "created_at": "2024-01-01T12:00:00Z",
      "last_activity": "2024-01-01T14:30:00Z",
      "age_seconds": 9000,
      "idle_seconds": 1800,
      "expires_in": 595200,
      "rotation_count": 1,
      "client_info": {
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
      }
    }
  ],
  "total": 1
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `500 Internal Server Error`: Failed to retrieve sessions

### Rotate Current Session

Rotates the current session ID for enhanced security.

```http
POST /sessions/rotate
```

**Request Headers:**
```http
Cookie: __Host-session_id=xyz789...
X-CSRF-Token: abc123...def456
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Session rotated successfully",
  "csrf_token": "new_csrf_token_abc123"
}
```

**Response Headers:**
```http
Set-Cookie: __Host-session_id=new_session_xyz...; Max-Age=604800; Path=/; HttpOnly; Secure; SameSite=Lax
```

**Error Responses:**
- `400 Bad Request`: Session rotation failed
- `401 Unauthorized`: No active session
- `403 Forbidden`: Invalid or missing CSRF token

### Invalidate All Other Sessions

Invalidates all user sessions except the current one.

```http
POST /sessions/invalidate-all
```

**Request Headers:**
```http
Cookie: __Host-session_id=xyz789...
X-CSRF-Token: abc123...def456
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Invalidated 3 sessions",
  "sessions_invalidated": 3
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Invalid or missing CSRF token
- `500 Internal Server Error`: Invalidation failed

## Security Features

### CSRF Protection

All state-changing endpoints (POST, PUT, DELETE) require CSRF token validation:

1. **CSRF Token**: Include `X-CSRF-Token` header
2. **Origin Validation**: Request origin must match allowed origins
3. **Session Binding**: CSRF token is bound to the user's session

**Example Request:**
```http
POST /api/v1/auth/profile
Cookie: __Host-session_id=xyz789...
X-CSRF-Token: abc123...def456
Origin: https://yourdomain.com
Content-Type: application/json

{
  "name": "Updated Name"
}
```

### Rate Limiting

Authentication endpoints have strict rate limits:

- **Login**: 5 attempts per 5 minutes (burst: 2)
- **Register**: 3 attempts per 5 minutes (burst: 1)
- **General Auth**: 20 requests per 5 minutes (burst: 10)

**Rate Limit Headers:**
```http
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 3
X-RateLimit-Reset: 1640995200
Retry-After: 300
```

### Session Security

Sessions include comprehensive security features:

- **Rolling Expiry**: Sessions extend with activity
- **Absolute Maximum Age**: Hard limit prevents indefinite sessions
- **Concurrent Limits**: Configurable maximum sessions per user
- **Client Tracking**: IP address and user agent logging
- **Session Rotation**: Periodic session ID changes

## Error Handling

### Error Response Format

All errors follow a consistent format:

```json
{
  "detail": "Error description",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Common Error Codes

- `AUTHENTICATION_REQUIRED`: User must be authenticated
- `INVALID_CREDENTIALS`: Login credentials are incorrect
- `CSRF_TOKEN_REQUIRED`: CSRF token missing or invalid
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `SESSION_EXPIRED`: User session has expired
- `ORIGIN_NOT_ALLOWED`: Request from unauthorized origin

## Client Implementation

### JavaScript/TypeScript Example

```typescript
// Configure axios for secure authentication
const api = axios.create({
  baseURL: 'https://api.yourdomain.com/api/v1',
  withCredentials: true, // Include cookies
});

// Automatic CSRF token handling
api.interceptors.request.use(async (config) => {
  if (['post', 'put', 'patch', 'delete'].includes(config.method)) {
    try {
      const response = await api.get('/auth/csrf-token');
      config.headers['X-CSRF-Token'] = response.data.csrf_token;
    } catch (error) {
      console.warn('Failed to get CSRF token:', error);
    }
  }
  return config;
});

// Automatic logout on 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear local auth state
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Usage examples
const authAPI = {
  async login(email: string, password: string) {
    const response = await api.post('/auth/login', { email, password });
    return response.data;
  },

  async getCurrentUser() {
    const response = await api.get('/auth/me');
    return response.data;
  },

  async getSessions() {
    const response = await api.get('/auth/sessions');
    return response.data;
  },

  async rotateSession() {
    const response = await api.post('/auth/sessions/rotate');
    return response.data;
  },

  async logout() {
    await api.post('/auth/logout');
  }
};
```

### Python Example

```python
import requests

# Configure session for secure authentication
session = requests.Session()
session.headers.update({
    'Content-Type': 'application/json',
    'Origin': 'https://yourdomain.com'
})

BASE_URL = 'https://api.yourdomain.com/api/v1'

def get_csrf_token():
    """Get CSRF token for requests."""
    response = session.get(f'{BASE_URL}/auth/csrf-token')
    response.raise_for_status()
    return response.json()['csrf_token']

def login(email: str, password: str):
    """Login user and store session cookie."""
    response = session.post(f'{BASE_URL}/auth/login', json={
        'email': email,
        'password': password
    })
    response.raise_for_status()
    return response.json()

def make_authenticated_request(method: str, endpoint: str, **kwargs):
    """Make authenticated request with CSRF token."""
    if method.upper() in ['POST', 'PUT', 'PATCH', 'DELETE']:
        csrf_token = get_csrf_token()
        headers = kwargs.get('headers', {})
        headers['X-CSRF-Token'] = csrf_token
        kwargs['headers'] = headers
    
    response = session.request(method, f'{BASE_URL}{endpoint}', **kwargs)
    response.raise_for_status()
    return response.json()

# Usage
login('user@example.com', 'password123')
user = make_authenticated_request('GET', '/auth/me')
sessions = make_authenticated_request('GET', '/auth/sessions')
```

## Testing

### Authentication Flow Testing

```bash
# Register new user
curl -X POST https://api.yourdomain.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -H "Origin: https://yourdomain.com" \
  -d '{"email":"test@example.com","password":"test123","name":"Test User"}' \
  -c cookies.txt

# Login user  
curl -X POST https://api.yourdomain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -H "Origin: https://yourdomain.com" \
  -d '{"email":"test@example.com","password":"test123"}' \
  -c cookies.txt

# Get current user
curl -X GET https://api.yourdomain.com/api/v1/auth/me \
  -b cookies.txt

# Get CSRF token
CSRF_TOKEN=$(curl -s -X GET https://api.yourdomain.com/api/v1/auth/csrf-token \
  -b cookies.txt | jq -r '.csrf_token')

# Update profile (requires CSRF token)
curl -X PUT https://api.yourdomain.com/api/v1/auth/profile \
  -H "Content-Type: application/json" \
  -H "Origin: https://yourdomain.com" \
  -H "X-CSRF-Token: $CSRF_TOKEN" \
  -d '{"name":"Updated Name"}' \
  -b cookies.txt

# List sessions
curl -X GET https://api.yourdomain.com/api/v1/auth/sessions \
  -b cookies.txt

# Rotate session
curl -X POST https://api.yourdomain.com/api/v1/auth/sessions/rotate \
  -H "Origin: https://yourdomain.com" \
  -H "X-CSRF-Token: $CSRF_TOKEN" \
  -b cookies.txt \
  -c cookies.txt  # Save new session cookie

# Logout
curl -X POST https://api.yourdomain.com/api/v1/auth/logout \
  -b cookies.txt
```

## Security Considerations

### Production Deployment

1. **HTTPS Only**: All authentication endpoints require HTTPS
2. **Origin Validation**: Configure allowed origins strictly
3. **Rate Limiting**: Monitor and adjust rate limits based on usage
4. **Session Monitoring**: Log and monitor authentication events
5. **Regular Security Updates**: Keep dependencies updated

### Security Headers

The API automatically includes comprehensive security headers:

```http
Content-Security-Policy: default-src 'self'; ...
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), ...
X-XSS-Protection: 1; mode=block
```

### Compliance

This authentication system addresses:

- **OWASP Top 10** security risks
- **PCI DSS** requirements (if handling payments)
- **GDPR** data protection requirements
- **SOC 2** security controls

## Migration Guide

### From Token-Based Authentication

If migrating from JWT or API key authentication:

1. **Remove Token Storage**: Clear localStorage/sessionStorage
2. **Update API Client**: Configure `withCredentials: true`
3. **Add CSRF Handling**: Implement CSRF token requests
4. **Update Error Handling**: Handle 401s by redirecting to login
5. **Test Cross-Origin**: Verify CORS configuration

### Session Management Migration

1. **Update Login Flow**: Handle session cookie setting
2. **Implement Session APIs**: Add session management endpoints
3. **Add Security Features**: Implement rotation and invalidation
4. **Update Logout**: Clear session cookies properly

## Troubleshooting

### Common Issues

1. **CORS Errors**: Verify `Origin` header matches allowed origins
2. **CSRF Failures**: Ensure CSRF token in `X-CSRF-Token` header
3. **Cookie Issues**: Verify HTTPS and `__Host-` prefix support
4. **Rate Limiting**: Check rate limit headers and implement backoff

### Debug Mode

Enable debug logging in development:

```bash
export DEBUG=True
export LOG_LEVEL=DEBUG
```

### Support

For support with authentication implementation:

- **Documentation**: https://docs.yourdomain.com/auth
- **Examples**: https://github.com/yourdomain/auth-examples
- **Issues**: https://github.com/yourdomain/api/issues