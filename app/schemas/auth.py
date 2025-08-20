"""
Authentication schemas for request/response validation.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator, field_serializer
import re


class UserRegisterRequest(BaseModel):
    """Request schema for user registration."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=100, description="User password")
    name: Optional[str] = Field(None, max_length=255, description="User display name")
    
    @validator("password")
    def validate_password(cls, password: str) -> str:
        """Validate password complexity."""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Check for at least one digit, one letter
        if not re.search(r"\d", password):
            raise ValueError("Password must contain at least one digit")
        
        if not re.search(r"[a-zA-Z]", password):
            raise ValueError("Password must contain at least one letter")
        
        return password


class UserLoginRequest(BaseModel):
    """Request schema for user login."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, max_length=100, description="User password")


class UserResponse(BaseModel):
    """Response schema for user data."""
    
    id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email address")
    name: Optional[str] = Field(None, description="User display name")
    picture: Optional[str] = Field(None, description="Profile picture URL")
    is_active: bool = Field(..., description="Whether user account is active")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    @field_serializer('created_at')
    def serialize_created_at(self, created_at: datetime) -> str:
        """Serialize datetime to ISO string."""
        return created_at.isoformat() if created_at else None
    
    @field_serializer('updated_at')
    def serialize_updated_at(self, updated_at: Optional[datetime]) -> Optional[str]:
        """Serialize datetime to ISO string."""
        return updated_at.isoformat() if updated_at else None
    
    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """Response schema for authentication endpoints."""
    
    success: bool = Field(..., description="Whether authentication was successful")
    message: str = Field(..., description="Response message")
    user: Optional[UserResponse] = Field(None, description="User data if successful")
    csrf_token: Optional[str] = Field(None, description="CSRF token for subsequent requests")


class LoginResponse(AuthResponse):
    """Response schema for login endpoint."""
    
    session_expires: Optional[str] = Field(None, description="Session expiration timestamp")


class LogoutResponse(BaseModel):
    """Response schema for logout endpoint."""
    
    success: bool = Field(..., description="Whether logout was successful")
    message: str = Field(..., description="Response message")


class UserProfileUpdateRequest(BaseModel):
    """Request schema for updating user profile."""
    
    name: Optional[str] = Field(None, max_length=255, description="Updated display name")
    picture: Optional[str] = Field(None, max_length=500, description="Updated profile picture URL")
    
    @validator("picture")
    def validate_picture_url(cls, picture: Optional[str]) -> Optional[str]:
        """Validate picture URL format."""
        if picture and not picture.startswith(("http://", "https://")):
            raise ValueError("Picture must be a valid HTTP/HTTPS URL")
        return picture