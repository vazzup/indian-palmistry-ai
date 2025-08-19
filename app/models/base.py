"""
Base model for SQLAlchemy models.

This module provides the declarative base and common model utilities
for all database models in the application.
"""

from sqlalchemy.orm import declarative_base

# SQLAlchemy declarative base
Base = declarative_base()