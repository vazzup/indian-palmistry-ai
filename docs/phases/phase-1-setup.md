# Phase 1: Setup - Barebones Foundation

## Overview
**Phase 1** establishes the foundational structure and basic functionality of the Indian palmistry application. This phase creates a minimal but functional FastAPI API with health checks, a stub Next.js app, database configuration (Supabase for production, SQLite for development), Redis setup for caching and background jobs, and `.env`-based configuration in a multi-container architecture.

**Duration**: 1-2 weeks  
**Goal**: Create a working foundation (API + frontend stubs) that can be built upon in subsequent phases

## Scope
- Basic repository structure aligned with `project-rules.md`
- Minimal FastAPI application with `/healthz`
- Database setup (Supabase for production, SQLite for development)
- Redis setup for sessions, caching, and background job queuing
- Background worker setup with Celery/RQ
- Local filesystem root for images (`/data/images`)
- Docker-compose configuration for multi-container architecture
- `.env` configuration and example
- Minimal Next.js app scaffold and placeholder pages

## Deliverables
- ✅ Working FastAPI server that responds to `/healthz`
- ✅ Database connection (Supabase/SQLite) with async engine
- ✅ Redis connection for sessions and background jobs
- ✅ Background worker service setup
- ✅ Docker-compose configuration for all services
- ✅ `.env` config and `.env.example` with Redis and database URLs
- ✅ Local image storage root directory exists
- ✅ Minimal Next.js app boots a placeholder page

## Features & Tasks

### 1. Repository and Container Baseline
**Purpose**: Establish directory structure and multi-container architecture baseline

**Tasks**:
1. Create directories per `project-rules.md` (backend `app/*`, `frontend/*`, `_docs/*`)
2. Add `.env.example` with keys: `DATABASE_URL`, `REDIS_URL`, `CELERY_BROKER_URL`, `OPENAI_API_KEY`, `FILE_STORAGE_ROOT`
3. Create separate Dockerfiles for API, frontend, and workers
4. Create `docker-compose.yml` with services: api, frontend, redis, worker
5. Add `.gitignore` for Python/Node artifacts and `/data/*`
6. Create initial `README.md` with docker-compose build/run instructions

**Acceptance Criteria**:
- All directories exist as specified
- `.env.example` present with all required environment variables
- Docker-compose builds and starts all services
- Services can communicate with each other
- `.gitignore` excludes build artifacts and `/data`
- README shows how to use docker-compose for development

### 2. FastAPI Application Foundation
**Purpose**: Create a minimal but functional FastAPI application

**Tasks**:
1. Add `app/main.py` with `FastAPI()` and `/healthz`
2. Configure CORS (locked to Next host via `.env`)
3. Add JSON logging utility
4. Add startup hook to initialize DB pragmas
5. Add `/api/v1` router prefix placeholder

**Acceptance Criteria**:
- FastAPI starts without errors
- `/healthz` returns 200 OK with version
- CORS configured from `.env`
- Logging outputs JSON to stdout

### 3. Database Configuration
**Purpose**: Set up database configuration for both development and production

**Tasks**:
1. Configure dual database support: Supabase for production, SQLite for development
2. Create `app/core/database.py` with async engine and session factory
3. Add environment-specific configuration (connection pooling for Supabase)
4. Create empty `models` package and `Base` for future models
5. Add startup SQLite PRAGMAs when in development mode
6. Verify connection works for both database types

**Acceptance Criteria**:
- Engine connects successfully to both Supabase and SQLite
- Environment-specific configuration works correctly
- Base model imported without issues
- Session factory yields sessions for both database types
- Connection pooling configured for Supabase

### 4. Configuration Management
**Purpose**: Implement flexible configuration system for multi-service architecture

**Tasks**:
1. Create `app/core/config.py` (Pydantic settings) sourced from `.env`
2. Define keys: `DATABASE_URL`, `REDIS_URL`, `CELERY_BROKER_URL`, `ALLOWED_ORIGINS`, `SECRET_KEY`, `FILE_STORAGE_ROOT`
3. Add environment detection (development vs production)
4. Validate required keys on startup; fail fast with clear error
5. Document all keys in `.env.example`
6. Add `settings` singleton import pattern

**Acceptance Criteria**:
- Configuration loads from `.env` with Redis and database URLs
- Environment detection works correctly
- Required keys validated with helpful errors
- `.env.example` documents all keys including Redis configuration
- `settings` importable across modules and workers

### 5. Development Environment
**Purpose**: Set up development tools and code quality standards

**Tasks**:
1. Add pytest, black, ruff, mypy configs (backend)
2. Add ESLint/Prettier defaults (frontend)
3. Add pre-commit hooks for formatting/linting
4. Add `make fmt` and `make lint` scripts (optional)
5. Ensure CI locally via `make test` placeholder

**Acceptance Criteria**:
- Black/Prettier formatting runs clean
- Ruff/ESLint linting passes
- MyPy runs in strict mode for backend
- Pre-commit enforces style

### 6. Basic Documentation
**Purpose**: Create essential project documentation

**Tasks**:
1. Update `README.md` with build/run, `.env`, and directory layout
2. Ensure `_docs/*` reflects current tech decisions
3. Add `project-rules.md` link and summaries in README
4. Add troubleshooting section (common Docker issues)
5. Document health endpoints

**Acceptance Criteria**:
- README contains clear setup instructions
- `.env` and directory layout documented
- Health endpoints documented
- Troubleshooting section present

## Technical Implementation

### Dependencies (backend with Redis and background jobs)
```toml
# pyproject.toml
[project]
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "sqlalchemy>=2.0.0",
    "asyncpg>=0.29.0",  # For Supabase/PostgreSQL
    "aiosqlite>=0.19.0",  # For SQLite development
    "alembic>=1.12.0",
    "pydantic>=2.5.0",
    "python-multipart>=0.0.6",
    "redis>=5.0.0",
    "celery>=5.3.0",
    "aioredis>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-redis>=3.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
    "pre-commit>=3.5.0",
]
```

### Basic FastAPI Application
```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Astrology Backend",
    description="AI-powered Indian palmistry backend application",
    version="0.1.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}
```

### Database Configuration
```python
# app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Configure engine based on database type
if "postgresql" in settings.DATABASE_URL:
    # Supabase/PostgreSQL configuration
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True
    )
else:
    # SQLite development configuration
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False}
    )

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Initialize SQLite pragmas for development
async def init_sqlite_pragmas():
    if "sqlite" in settings.DATABASE_URL:
        async with engine.begin() as conn:
            await conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
            await conn.exec_driver_sql("PRAGMA synchronous=NORMAL;")
            await conn.exec_driver_sql("PRAGMA foreign_keys=ON;")

async def get_db():
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

## Testing Strategy

### Unit Tests
- Health check endpoint test
- Database connection test (both Supabase and SQLite)
- Redis connection test
- Configuration loading test
- Background worker task test
- Basic error handling test

### Integration Tests
- Database session management (both database types)
- Redis session management
- Background job queuing and processing
- Service communication in docker-compose
- Configuration validation
- Application startup and shutdown

## Success Metrics

### Functional Metrics
- ✅ All services start without errors in docker-compose
- ✅ Health check endpoint responds correctly
- ✅ Database connection established (both Supabase and SQLite)
- ✅ Redis connection established
- ✅ Background worker connects to Redis and processes test jobs
- ✅ Configuration loads properly for all services
- ✅ Development tools work correctly

### Quality Metrics
- ✅ All linting checks pass
- ✅ Type checking passes
- ✅ Code formatting consistent
- ✅ Documentation complete and accurate
- ✅ Git repository properly configured

## Risk Mitigation

### Technical Risks
- **Multi-service complexity**: Use docker-compose for consistent development environment
- **Database connection issues**: Support both Supabase and SQLite with proper connection pooling
- **Redis connection issues**: Include Redis health checks and connection retry logic
- **Service communication**: Ensure proper service discovery in docker-compose
- **Configuration complexity**: Start with simple environment variables, document all services

### Timeline Risks
- **Over-engineering**: Focus on minimal viable setup
- **Documentation debt**: Document as you go, not at the end
- **Tool configuration**: Use standard configurations, customize later

## Next Phase Preparation

### Handoff to Phase 2
- ✅ Working FastAPI application
- ✅ Database infrastructure ready
- ✅ Development environment configured
- ✅ Basic project structure established
- ✅ Documentation foundation in place

### Dependencies for Phase 2
- Authentication system will build on database models and Redis sessions
- API endpoints will use the established FastAPI structure
- Background job processing ready for OpenAI integration
- File handling will integrate with the configuration system
- Redis-based caching and session management ready
- Testing framework ready for new features including background jobs

## Definition of Done

A feature is considered complete when:
1. ✅ Code is written and follows project standards
2. ✅ Tests are written and passing
3. ✅ Documentation is updated
4. ✅ Code review is completed
5. ✅ Feature is tested manually
6. ✅ No linting or type errors
7. ✅ Integration with existing code works
8. ✅ Performance is acceptable for the scope

This phase establishes the foundation upon which all subsequent phases will build, ensuring a solid and maintainable codebase from the start.
