# Tech Stack Documentation

## Overview
This document defines the technology stack for the Indian palmistry application (FastAPI backend + Next.js frontend), including best practices, limitations, conventions, deployment model, and testing strategies. The MVP will use separate containers with docker-compose, Redis for caching and background jobs, a managed database service (Supabase), and local filesystem for image storage.

## Deployment and Runtime Model

### Multi-container Architecture (MVP)
- Run Next.js, FastAPI, Redis, and background workers in separate containers using docker-compose.
- Include a reverse proxy (Caddy/Nginx) to route `/api/*` to FastAPI and everything else to Next.js.
- Use Redis for session storage, caching, and background job queuing.
- Background workers handle OpenAI processing to avoid request timeouts.

#### Best Practices
- Graceful shutdown: propagate SIGTERM and allow in-flight requests to complete.
- Health endpoints: `/healthz` (API) and `/-/healthz` (Next) for readiness/liveness.
- Separate logs by process but emit JSON to stdout; the orchestrator handles collection/rotation.

#### Benefits
- Independent scaling of API and frontend services.
- Background job processing prevents request timeouts.
- Redis provides persistent sessions and caching across restarts.
- Better resource isolation and monitoring per service.

#### Common Pitfalls
- Not configuring proper service dependencies in docker-compose.
- Missing Redis connection handling and retry logic.
- Over-allocating background workers increases database contention.

## Backend Framework

### FastAPI
**Purpose**: High-performance web framework for building APIs with Python

#### Best Practices
- Use Pydantic models for request/response validation
- Implement proper error handling with HTTPException
- Use dependency injection for database connections and authentication
- Structure routes using APIRouter for modularity
- Implement proper CORS configuration
- Use async/await for I/O operations
- Add comprehensive logging with structured logging
- Use path-based versioning `/api/v1` and stable DTOs; avoid breaking changes.
- Provide a minimal `/healthz` and `/metrics` endpoint (metrics optional for MVP).

#### Limitations
- No built-in admin interface (unlike Django)
- Limited built-in middleware compared to Django
- Requires manual setup for complex authentication flows
- No built-in ORM (use SQLAlchemy or similar)

#### Conventions
```python
# Project structure
app/
├── main.py
├── api/
│   ├── __init__.py
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── palm_reading.py
│   │   └── conversations.py
├── core/
│   ├── __init__.py
│   ├── config.py
│   ├── security.py
│   └── database.py
├── models/
│   ├── __init__.py
│   ├── user.py
│   ├── palm_reading.py
│   └── conversation.py
├── schemas/
│   ├── __init__.py
│   ├── user.py
│   ├── palm_reading.py
│   └── conversation.py
└── services/
    ├── __init__.py
    ├── openai_service.py
    ├── auth_service.py
    └── file_service.py
frontend/
├── app/
│   ├── (marketing)/page.tsx
│   ├── (app)/analyses/page.tsx
│   ├── (app)/analyses/[id]/page.tsx
│   ├── (app)/login/page.tsx
│   └── layout.tsx
├── components/
└── lib/
```

#### Common Pitfalls
- Not using Pydantic for validation
- Mixing sync and async code
- Not implementing proper error handling
- Over-engineering with unnecessary abstractions
- Not using dependency injection properly

## Database

### Managed Database Service (Supabase)
**Purpose**: Managed PostgreSQL database with built-in authentication and real-time features

#### Best Practices
- Use Supabase PostgreSQL for production with connection pooling
- Use SQLAlchemy 2.x (async engine) + Alembic for migrations
- Keep transactions short and use connection pooling effectively
- Add indexes on foreign keys and frequent filters: `user_id`, `analysis_id`, `created_at`
- Configure database connection via `.env` (e.g., `DATABASE_URL=postgresql+asyncpg://...`)
- Use SQLite for local development and testing

#### Limitations
- Requires internet connectivity
- External service dependency
- Cost scales with usage

#### Conventions
```python
# Database configuration
DATABASE_URL = "postgresql+asyncpg://user:pass@host:5432/dbname"
# For local development:
DATABASE_URL = "sqlite+aiosqlite:///./dev.db"

# SQLAlchemy setup
engine = create_async_engine(DATABASE_URL, echo=False, pool_size=10, max_overflow=20)

# Model conventions remain the same
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### SQLite (Development Only)
**Purpose**: Local development and testing database

#### Best Practices
- Use for local development and testing only
- Enable WAL mode and sane pragmas: `journal_mode=WAL`, `synchronous=NORMAL`, `cache_size=-20000`
- Keep transactions short; single-writer pattern
- Use same SQLAlchemy models as production for consistency

#### Limitations
- Limited concurrent writes (write lock)
- No built-in user management
- Limited scalability for high-traffic applications
- No built-in replication
- File-based (not suitable for distributed systems)

#### Conventions
```python
# SQLite for development only
DATABASE_URL = "sqlite+aiosqlite:///./dev.db"

async def on_startup_sqlite():
    async with engine.begin() as conn:
        await conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
        await conn.exec_driver_sql("PRAGMA synchronous=NORMAL;")
        await conn.exec_driver_sql("PRAGMA foreign_keys=ON;")
```

#### Common Pitfalls
- Mixing SQLite and PostgreSQL-specific queries
- Not testing migrations on both databases
- Not handling connection pool exhaustion
- Not implementing proper retry logic for connection failures

## Background Job Processing

### Redis + Celery/RQ
**Purpose**: Queue system for handling long-running OpenAI analysis tasks

#### Best Practices
- Use Redis as message broker and result backend
- Process palm analysis in background workers to avoid request timeouts
- Implement proper error handling and retry logic
- Monitor job status and provide user feedback
- Use separate Redis databases for different purposes (sessions: db=0, jobs: db=1)

#### Conventions
```python
# Redis configuration
REDIS_URL = "redis://localhost:6379"
CELERY_BROKER_URL = "redis://localhost:6379/1"
CELERY_RESULT_BACKEND = "redis://localhost:6379/1"

# Background job setup
from celery import Celery

celery_app = Celery(
    "palmistry",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.tasks"]
)

# Task definition
@celery_app.task(bind=True, max_retries=3)
def process_palm_analysis(self, analysis_id: int):
    try:
        # Load images, call OpenAI, save results
        return {"status": "completed", "analysis_id": analysis_id}
    except Exception as exc:
        self.retry(countdown=60 * (self.request.retries + 1))

# API endpoint
@router.post("/analyze")
async def analyze_palm(images: List[UploadFile]):
    analysis_id = await create_analysis_record()
    await save_images(images, analysis_id)
    
    # Queue the background job
    job = process_palm_analysis.delay(analysis_id)
    
    return {"analysis_id": analysis_id, "job_id": job.id, "status": "queued"}
```

## Session Management & Caching

### Redis Sessions
**Purpose**: Distributed session storage and caching layer

#### Best Practices
- Store sessions in Redis with TTL expiration
- Use Redis for frequently accessed data caching
- Implement cache invalidation strategies
- Use connection pooling for Redis connections

#### Conventions
```python
# Session configuration
SESSION_REDIS_URL = "redis://localhost:6379/0"
SESSION_EXPIRE_SECONDS = 86400 * 7  # 1 week

# Session management
import aioredis
from uuid import uuid4

class SessionService:
    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url)
    
    async def create_session(self, user_id: int) -> str:
        session_id = str(uuid4())
        await self.redis.setex(
            f"session:{session_id}",
            SESSION_EXPIRE_SECONDS,
            json.dumps({"user_id": user_id, "created_at": datetime.utcnow().isoformat()})
        )
        return session_id
    
    async def get_session(self, session_id: str) -> dict | None:
        data = await self.redis.get(f"session:{session_id}")
        return json.loads(data) if data else None
```

## AI Integration

### OpenAI gpt-4.1-mini
**Purpose**: AI-powered palm reading analysis and conversation (processed in background)

#### Best Practices
- Process all AI requests in background workers to avoid timeouts
- Implement proper rate limiting across worker processes
- Use async calls within workers
- Implement retry logic with exponential backoff
- Cache analysis results in Redis when appropriate
- Implement proper error handling and user notification
- Use structured prompts for consistent responses
- Store job status and progress in Redis for user feedback

#### Limitations
- API rate limits
- Cost per request
- Response time variability
- No guaranteed response quality
- Token limits for conversations

#### Conventions
```python
class OpenAIService:
    def __init__(self, api_key: str, redis_client):
        self.client = AsyncOpenAI(api_key=api_key)
        self.redis = redis_client

    async def analyze_palm_images(self, analysis_id: int, left_image: bytes | None, right_image: bytes | None) -> dict:
        # Update job status
        await self.redis.setex(f"job:{analysis_id}", 3600, json.dumps({"status": "processing", "progress": 10}))
        
        try:
            # send up to two images; return structured summary and full report
            result = await self._call_openai_vision_api(left_image, right_image)
            
            # Update completion status
            await self.redis.setex(f"job:{analysis_id}", 3600, json.dumps({"status": "completed", "progress": 100}))
            
            return result
        except Exception as e:
            await self.redis.setex(f"job:{analysis_id}", 3600, json.dumps({"status": "failed", "error": str(e)}))
            raise

    async def continue_conversation(self, analysis_id: int, messages: list[dict]) -> str:
        # continue chat grounded on analysis context (also backgrounded)
        ...
```

#### Common Pitfalls
- Processing OpenAI requests synchronously (causes timeouts)
- Not providing user feedback during long-running jobs
- Not handling Redis connection failures in workers
- Not implementing proper job cleanup and TTL
- Not coordinating rate limits across multiple workers

## File Handling

### Local Filesystem (MVP)
**Purpose**: Store palm images on local disk within the single server/container

#### Best Practices
- Validate file type (magic bytes) and size (<= 15 MB)
- Accept JPEG/PNG; strip EXIF; normalize color profile (sRGB)
- Store under volume path `/data/images/{user_id}/{analysis_id}/`
- Generate UUID filenames and store metadata in DB (hand=left/right, size, mime)
- Create thumbnails asynchronously; cleanup temp files
- Enforce per-user quota to protect disk

#### Limitations
- Disk growth requires monitoring and backups
- Not horizontally scalable without shared storage
- Single-node file availability

#### Conventions
```python
class FileService:
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
    MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB

    async def validate_and_store(self, file: UploadFile, user_id: int, analysis_id: int, hand: str) -> str:
        # validate content-type and magic bytes
        # write to /data/images/{user_id}/{analysis_id}/{uuid}.{ext}
        ...

    async def remove_analysis_files(self, user_id: int, analysis_id: int) -> None:
        # remove directory recursively
        ...
```

#### Common Pitfalls
- Trusting client MIME type instead of checking magic bytes
- Doing heavy image processing in request thread (blocks event loop)
- Not cleaning up temp files and thumbnails
- Path traversal via untrusted filenames

## Authentication

### Session-based Email/Password (MVP)
**Purpose**: Server-side login/logout with secure cookies per overview; login gate after analysis summary

#### Best Practices
- Hash passwords with bcrypt; store only salted hashes
- HTTP-only, Secure, SameSite=Lax cookies; rotate session IDs on login
- CSRF protection on state-changing endpoints (double submit token)
- Rate limit login and password reset
- Centralized auth dependency for route protection

#### Limitations
- Requires password reset flow and email delivery (can stub for MVP)
- Cookie handling across subdomains requires care

#### Conventions
```python
class AuthService:
    async def register_user(self, email: str, password: str) -> User: ...
    async def login(self, email: str, password: str) -> Session: ...
    async def logout(self, session_id: str) -> None: ...

def require_auth(session: Session = Depends(get_session)) -> User: ...
```

#### Common Pitfalls
- Storing plaintext passwords
- Exposing cookies to JavaScript (missing HttpOnly)
- Missing CSRF protection for cookie-based sessions
- Not rotating session on privilege changes

## Testing

### pytest
**Purpose**: Unit and integration testing for backend functionality

#### Best Practices
- Use fixtures for common setup
- Implement proper mocking for external services
- Use parametrized tests for multiple scenarios
- Implement proper test isolation
- Use async test helpers for async code
- Implement proper test coverage

#### Conventions
```python
# Test structure
tests/
├── __init__.py
├── conftest.py
├── test_api/
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_palm_reading.py
│   └── test_conversations.py
├── test_services/
│   ├── __init__.py
│   ├── test_openai_service.py
│   └── test_auth_service.py
└── test_models/
    ├── __init__.py
    └── test_user.py

# Test conventions
@pytest.mark.asyncio
async def test_analyze_palm_image_success():
    # Test implementation
    pass

@pytest.fixture
async def mock_openai_client():
    # Mock implementation
    pass
```

### Frontend Testing
**Purpose**: Validate UI flows (upload, login gate, analyses list, conversations)

#### Best Practices
- Use Playwright for E2E (uploads, auth gate, pagination)
- Use Vitest + React Testing Library for component and hooks tests
- Mock network with MSW for deterministic tests

#### Conventions
```ts
// e2e/upload.spec.ts
test('unauthenticated user can upload and see summary, then login gate', async ({ page }) => { /* ... */ })
```

### Black (Code Formatter)
**Purpose**: Consistent code formatting (backend)

#### Best Practices
- Use consistent line length (88 characters)
- Configure pre-commit hooks
- Use in CI/CD pipeline
- Configure IDE integration

#### Conventions
```toml
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py39']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''
```

### Ruff (Linter)
**Purpose**: Fast Python linter and formatter (backend)

#### Best Practices
- Configure rules based on project needs
- Use in pre-commit hooks
- Configure IDE integration
- Use for import sorting

#### Conventions
```toml
# pyproject.toml
[tool.ruff]
target-version = "py39"
line-length = 88
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501",  # line too long, handled by black
    "B008",  # do not perform function calls in argument defaults
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]
"tests/**/*" = ["B011"]
```

### mypy (Type Checker)
**Purpose**: Static type checking for Python (backend)

#### Best Practices
- Use strict mode for better type safety
- Configure proper ignore patterns
- Use type stubs for external libraries
- Implement gradual typing

#### Conventions
```toml
# pyproject.toml
[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[[tool.mypy.overrides]]
module = [
    "sqlalchemy.*",
    "alembic.*",
]
ignore_missing_imports = true
```

## Configuration with .env

### Best Practices
- Use `.env` for local development; mount environment variables in container for production.
- Provide `.env.example` with placeholder values; do not commit real secrets.
- Separate files per stage: `.env.development`, `.env.production`.

### Example Keys
```
# Database (production: Supabase, development: SQLite)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
# DATABASE_URL=sqlite+aiosqlite:///./dev.db

# Redis for sessions and background jobs
REDIS_URL=redis://localhost:6379
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Application secrets
SECRET_KEY=change-me
OPENAI_API_KEY=sk-...
ALLOWED_ORIGINS=https://your-next-host

# Session configuration (Redis-based)
SESSION_EXPIRE_SECONDS=604800
SESSION_REDIS_DB=0

# File storage
FILE_STORAGE_ROOT=/data/images
```

## Security Considerations

### Best Practices
- Use environment variables for sensitive data
- Implement proper input validation
- Use HTTPS in production
- Implement rate limiting
- Use secure session management
- Regular security updates

### Common Pitfalls
- Hardcoding secrets
- Not validating user input
- Not implementing rate limiting
- Not using HTTPS
- Not updating dependencies

## Performance Considerations

### Best Practices
- Use async/await for I/O operations
- Implement Redis caching for hot endpoints and frequently accessed data
- Use background workers for long-running operations (OpenAI calls)
- Keep DB sessions short; use connection pooling effectively
- Monitor job queue depth and worker performance
- Cache analysis results and conversation context in Redis
- Monitor latency percentiles (p95/p99) and error rates
- Optimize DB queries and add needed indexes

### Common Pitfalls
- Processing long-running operations synchronously
- Not implementing proper Redis connection pooling
- Not handling background job failures gracefully
- Redis connection leaks in worker processes
- Not monitoring job queue and worker health
- N+1 query problems
- Not implementing proper cache invalidation

## Monitoring and Logging

### Best Practices
- Use structured JSON logging to stdout
- Implement proper log levels; avoid noisy debug in prod
- Basic metrics endpoint (optional for MVP)
- Health checks for readiness/liveness
- Centralize error handling and sanitize logs

### Conventions
```python
# Logging configuration (backend)
import logging, json, sys

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(message)s'))

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

def log_json(event: str, **kwargs):
    logger.info(json.dumps({"event": event, **kwargs}))
```

This tech stack provides a solid foundation for building a scalable, maintainable, and secure backend application for the Indian palmistry service.
