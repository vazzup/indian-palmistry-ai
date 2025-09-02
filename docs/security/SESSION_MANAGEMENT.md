# Session Management Documentation

This document provides detailed information about the enhanced session management system implemented in the Indian Palmistry AI application.

## Overview

The session management system provides secure, scalable session handling with advanced security features including session rotation, rolling expiry, and comprehensive session lifecycle management.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Redis         │
│   (Browser)     │    │   (FastAPI)     │    │   (Session Store)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │ 1. Login Request      │                       │
         ├──────────────────────►│                       │
         │                       │ 2. Create Session    │
         │                       ├──────────────────────►│
         │                       │ 3. Session Data      │
         │                       │◄──────────────────────┤
         │ 4. Set Cookie         │                       │
         │◄──────────────────────┤                       │
         │                       │                       │
         │ 5. API Request        │                       │
         ├──────────────────────►│                       │
         │                       │ 6. Validate Session  │
         │                       ├──────────────────────►│
         │                       │ 7. Refresh Activity  │
         │                       ├──────────────────────►│
         │ 8. Response           │                       │
         │◄──────────────────────┤                       │
```

## Session Service API

### Core Methods

#### `create_session(user_id, user_email, user_name, client_info)`
Creates a new secure session with comprehensive metadata.

```python
from app.services.session_service import session_service

# Create session with client information
session_id, csrf_token = await session_service.create_session(
    user_id=123,
    user_email="user@example.com",
    user_name="John Doe",
    client_info={
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
        "login": True
    }
)
```

**Returns:**
- `session_id`: Cryptographically secure session identifier (384-bit entropy)
- `csrf_token`: Associated CSRF protection token

**Features:**
- Enforces concurrent session limits
- Tracks client information for security
- Generates high-entropy session IDs
- Automatic Redis storage with TTL

#### `rotate_session(old_session_id)`
Rotates session ID while preserving session data (security best practice).

```python
# Rotate session for enhanced security
new_session_id, new_csrf_token = await session_service.rotate_session(
    old_session_id="abc123..."
)
```

**When to Use:**
- After login (automatic)
- After privilege escalation
- Periodically for high-security applications
- After suspicious activity detection

#### `refresh_session_activity(session_id)`
Implements rolling expiry - extends session lifetime based on activity.

```python
# Refresh session activity (called on each authenticated request)
is_active = await session_service.refresh_session_activity(session_id)
```

**Behavior:**
- Returns `True` if session refreshed successfully
- Returns `False` if session expired or not found
- Only refreshes if activity gap > `session_rolling_window`
- Respects absolute maximum age limit

#### `invalidate_user_sessions(user_id, except_session)`
Mass invalidation of user sessions (security operation).

```python
# Invalidate all sessions except current one
invalidated_count = await session_service.invalidate_user_sessions(
    user_id=123,
    except_session=current_session_id
)

# Invalidate ALL user sessions (on password change)
invalidated_count = await session_service.invalidate_user_sessions(user_id=123)
```

**Use Cases:**
- Password changes
- Account compromise
- "Log out from all devices" feature
- Administrative actions

#### `list_user_sessions(user_id)`
Retrieves information about all active user sessions.

```python
sessions = await session_service.list_user_sessions(user_id=123)
```

**Returns:**
```python
[
    {
        "session_id": "abc123...",
        "user_id": 123,
        "email": "user@example.com",
        "created_at": datetime(2024, 1, 1, 12, 0, 0),
        "last_activity": datetime(2024, 1, 1, 14, 30, 0),
        "age_seconds": 9000,
        "idle_seconds": 1800,
        "rotation_count": 2,
        "client_info": {
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0..."
        },
        "expires_in": 595200
    }
]
```

## Session Lifecycle

### 1. Session Creation
```python
# On successful authentication
async def login_user(credentials, request, response):
    user = await authenticate_user(credentials)
    
    # Create new session
    session_id, csrf_token = await session_service.create_session(
        user_id=user.id,
        user_email=user.email,
        user_name=user.name,
        client_info={
            "ip_address": request.client.host,
            "user_agent": request.headers.get("User-Agent"),
            "login": True
        }
    )
    
    # Set hardened cookie
    response.set_cookie(
        key="__Host-session_id",
        value=session_id,
        max_age=settings.session_expire_seconds,
        path="/",
        httponly=True,
        secure=True,
        samesite="lax"
    )
```

### 2. Session Validation & Activity Refresh
```python
# On each authenticated request
async def get_current_user(request):
    session_id = request.cookies.get("__Host-session_id")
    
    # Refresh activity (rolling expiry)
    if not await session_service.refresh_session_activity(session_id):
        return None  # Session expired
    
    # Get session data
    session_data = await session_manager.get_session(session_id)
    user = await user_service.get_user_by_id(session_data["user_id"])
    
    return user
```

### 3. Session Rotation
```python
# Rotate session after sensitive operations
async def rotate_current_session(request, response):
    current_session = request.cookies.get("__Host-session_id")
    
    # Rotate session ID
    new_session_id, new_csrf_token = await session_service.rotate_session(
        current_session
    )
    
    # Update cookie with new session ID
    response.set_cookie(
        key="__Host-session_id",
        value=new_session_id,
        # ... other secure flags
    )
```

### 4. Session Cleanup
```python
# On logout
async def logout_user(request, response):
    session_id = request.cookies.get("__Host-session_id")
    
    if session_id:
        await session_manager.delete_session(session_id)
    
    # Clear cookie
    response.delete_cookie("__Host-session_id", path="/")
```

## Configuration

### Settings
```python
# app/core/config.py
class Settings:
    # Basic session settings
    session_expire_seconds: int = 604800      # 1 week default TTL
    session_absolute_max_age: int = 2592000   # 30 days hard limit
    session_rolling_window: int = 3600        # 1 hour activity refresh
    
    # Security settings
    session_cookie_name: str = "__Host-session_id"
    session_cookie_samesite: str = "Lax"      # or "Strict"
    max_concurrent_sessions: int = 5          # Per user limit
```

### Environment Variables
```bash
# Production
SESSION_EXPIRE_SECONDS=604800
SESSION_ABSOLUTE_MAX_AGE=2592000
SESSION_ROLLING_WINDOW=3600
MAX_CONCURRENT_SESSIONS=3
SESSION_COOKIE_SAMESITE=Strict

# Development  
SESSION_EXPIRE_SECONDS=86400
SESSION_ROLLING_WINDOW=900
MAX_CONCURRENT_SESSIONS=10
SESSION_COOKIE_SAMESITE=Lax
```

## Session Data Structure

### Redis Storage Format
```python
# Key: session:{session_id}
# Value: JSON object
{
    "user_id": 123,
    "email": "user@example.com",
    "name": "John Doe",
    "csrf_token": "xyz789...",
    "created_at": "2024-01-01T12:00:00Z",
    "last_activity": "2024-01-01T14:30:00Z",
    "login_time": "2024-01-01T12:00:00Z",
    "rotation_count": 2,
    "client_info": {
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0...",
        "login": True
    }
}

# User session tracking
# Key: user_sessions:{user_id}  
# Value: Set of session_ids
{
    "session_abc123",
    "session_def456",
    "session_ghi789"
}
```

## Security Features

### 1. High-Entropy Session IDs
- **384-bit entropy** using `secrets.token_urlsafe(48)`
- **URL-safe base64 encoding**
- **Cryptographically secure random generation**

### 2. Session Binding
- **Client IP tracking** (with proxy support)
- **User-Agent binding** for device identification
- **CSRF token binding** to session

### 3. Activity Monitoring
- **Last activity timestamp** tracking
- **Rolling expiry** based on activity
- **Absolute maximum age** enforcement
- **Idle timeout** detection

### 4. Concurrent Session Management
- **Configurable limits** per user
- **Oldest session eviction** when limit exceeded
- **Session enumeration** for user visibility

## Frontend Integration

### Enhanced Auth Hook
```typescript
const auth = useAuth();

// List all active sessions
const sessions = await auth.getSessions();

// Rotate current session
const result = await auth.rotateSession();

// Invalidate all other sessions
const result = await auth.invalidateAllSessions();

// Enhanced auth checking with retry
const isAuthenticated = await auth.checkAuthWithRetry();
```

### Session Management UI
```typescript
function SessionManagement() {
    const auth = useAuth();
    const [sessions, setSessions] = useState([]);
    
    const loadSessions = async () => {
        try {
            const sessionList = await auth.getSessions();
            setSessions(sessionList);
        } catch (error) {
            console.error('Failed to load sessions:', error);
        }
    };
    
    const logoutAllDevices = async () => {
        try {
            await auth.invalidateAllSessions();
            await loadSessions(); // Refresh list
        } catch (error) {
            console.error('Failed to logout all devices:', error);
        }
    };
    
    return (
        <div>
            <h3>Active Sessions</h3>
            {sessions.map(session => (
                <div key={session.session_id}>
                    <p>Device: {session.client_info.user_agent}</p>
                    <p>IP: {session.client_info.ip_address}</p>
                    <p>Last Active: {session.last_activity}</p>
                </div>
            ))}
            <button onClick={logoutAllDevices}>
                Logout All Other Devices
            </button>
        </div>
    );
}
```

## Monitoring & Alerting

### Key Metrics
```python
# Session creation rate
sessions_created_per_hour = Counter('sessions_created_total')

# Active sessions
active_sessions_gauge = Gauge('active_sessions_total')

# Session rotation events  
session_rotations = Counter('session_rotations_total')

# Concurrent session violations
concurrent_session_violations = Counter('concurrent_session_limit_exceeded')
```

### Log Analysis
```python
# Successful session creation
logger.info(f"Session created for user {user_id}", extra={
    "user_id": user_id,
    "session_id": session_id[:8] + "...",
    "client_ip": client_info.get("ip_address"),
    "concurrent_sessions": len(existing_sessions)
})

# Session rotation
logger.info(f"Session rotated for user {user_id}", extra={
    "user_id": user_id, 
    "rotation_count": session_data.get("rotation_count"),
    "reason": "periodic_rotation"
})

# Mass invalidation
logger.warning(f"All sessions invalidated for user {user_id}", extra={
    "user_id": user_id,
    "sessions_invalidated": invalidated_count,
    "reason": "password_change"
})
```

## Performance Considerations

### Redis Optimization
- **Session TTL alignment** with cookie max-age
- **Efficient key patterns** for user session tracking  
- **Pipeline operations** for batch updates
- **Connection pooling** for high throughput

### Caching Strategy
- **Session data caching** to reduce Redis queries
- **User session enumeration** caching
- **CSRF token caching** on frontend

## Error Handling

### Graceful Degradation
```python
try:
    sessions = await session_service.list_user_sessions(user_id)
except Exception as e:
    logger.error(f"Failed to list sessions for user {user_id}: {e}")
    # Continue with empty session list
    sessions = []
```

### Recovery Mechanisms
- **Session recreation** on Redis failures
- **Cookie cleanup** on invalid sessions
- **Automatic retry** for transient errors

## Testing

### Unit Tests
```python
async def test_session_creation():
    session_id, csrf_token = await session_service.create_session(
        user_id=1, user_email="test@example.com", user_name="Test User"
    )
    
    assert len(session_id) > 32  # High entropy
    assert csrf_token is not None
    
    # Verify session exists in Redis
    session_data = await session_manager.get_session(session_id)
    assert session_data["user_id"] == 1

async def test_session_rotation():
    # Create initial session
    old_session_id, _ = await session_service.create_session(1, "test@example.com", "Test")
    
    # Rotate session
    new_session_id, new_csrf_token = await session_service.rotate_session(old_session_id)
    
    # Verify old session is gone
    assert await session_manager.get_session(old_session_id) is None
    
    # Verify new session exists
    new_session_data = await session_manager.get_session(new_session_id)
    assert new_session_data is not None
    assert new_session_data["rotation_count"] == 1
```

### Integration Tests
```python
async def test_rolling_expiry():
    # Create session
    session_id, _ = await session_service.create_session(1, "test@example.com", "Test")
    
    # Simulate activity after rolling window
    await asyncio.sleep(settings.session_rolling_window + 1)
    
    # Should refresh activity
    refreshed = await session_service.refresh_session_activity(session_id)
    assert refreshed is True
    
    # Session should still exist
    session_data = await session_manager.get_session(session_id)
    assert session_data is not None
```

## Migration Guide

### From Basic Sessions
1. Update session creation calls to use `session_service.create_session()`
2. Add client info collection at login
3. Update authentication middleware to use `refresh_session_activity()`
4. Add session management endpoints
5. Update frontend to handle enhanced session features

### Database Schema Changes
No database changes required - all session data stored in Redis.

## Troubleshooting

### Common Issues
1. **High session creation rate**: Check for authentication loops
2. **Sessions not expiring**: Verify Redis TTL settings
3. **Concurrent limit issues**: Monitor user session counts
4. **CSRF token mismatches**: Check session rotation timing

### Debug Commands
```python
# Check user sessions
sessions = await session_service.list_user_sessions(user_id)
print(f"User {user_id} has {len(sessions)} active sessions")

# Session info
info = await session_service.get_session_info(session_id)
print(f"Session age: {info['age_seconds']}s, idle: {info['idle_seconds']}s")

# Redis inspection
keys = await redis.keys("session:*")  
print(f"Total sessions in Redis: {len(keys)}")
```