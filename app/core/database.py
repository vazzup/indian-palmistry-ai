"""
Database configuration and session management.

This module provides SQLAlchemy async engine configuration that supports
both SQLite (development) and PostgreSQL (production/Supabase) databases.

Features:
- Environment-specific database configuration
- Connection pooling for PostgreSQL
- SQLite WAL mode configuration for development
- Async session management
- Database dependency injection

Usage:
    from app.core.database import get_db
    
    @router.get("/users")
    async def get_users(db: AsyncSession = Depends(get_db)):
        ...
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.base import Base

# Global engine instance
_engine: AsyncEngine = None


def create_database_engine() -> AsyncEngine:
    """
    Create SQLAlchemy async engine based on database URL.
    
    Returns:
        AsyncEngine: Configured database engine
    """
    if settings.is_postgresql:
        # PostgreSQL/Supabase configuration with connection pooling
        return create_async_engine(
            settings.database_url,
            echo=settings.debug,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,  # Recycle connections after 1 hour
        )
    else:
        # SQLite development configuration
        return create_async_engine(
            settings.database_url,
            echo=settings.debug,
            connect_args={"check_same_thread": False},
        )


def get_engine() -> AsyncEngine:
    """Get or create database engine."""
    global _engine
    if _engine is None:
        _engine = create_database_engine()
    return _engine


# Session factory
AsyncSessionLocal = sessionmaker(
    bind=get_engine(),
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False,
)


async def init_sqlite_pragmas() -> None:
    """
    Initialize SQLite pragmas for development mode.
    
    This function sets up WAL mode, foreign keys, and other optimizations
    for SQLite databases. Only called when using SQLite.
    """
    if settings.is_sqlite:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
            await conn.exec_driver_sql("PRAGMA synchronous=NORMAL;")
            await conn.exec_driver_sql("PRAGMA foreign_keys=ON;")
            await conn.exec_driver_sql("PRAGMA cache_size=-20000;")  # 20MB cache


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session dependency for FastAPI routes.
    
    Yields:
        AsyncSession: Database session
        
    Usage:
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """
    Create all database tables.
    
    This function creates all tables defined by SQLAlchemy models
    that inherit from Base. Used for development and testing.
    """
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
    """
    Drop all database tables.
    
    This function drops all tables. Used for testing cleanup.
    """
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def check_database_connection() -> bool:
    """
    Check if database connection is working.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.exec_driver_sql("SELECT 1")
        return True
    except Exception:
        return False


def get_db_session():
    """
    Get database session context manager for service classes.
    
    Returns:
        AsyncSessionLocal: Session context manager
        
    Usage:
        async with get_db_session() as db:
            result = await db.execute(query)
    """
    return AsyncSessionLocal()