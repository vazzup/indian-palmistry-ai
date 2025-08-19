# Phase 2: MVP - Minimal Viable Product

## Overview
**Phase 2** delivers a minimal but fully functional Indian palmistry application with core features that provide the primary value proposition. This phase builds upon the foundation established in Phase 1 to create a working application that users can interact with. It follows the user flow: unauthenticated upload → AI analysis → summary → login gate → full results → conversations nested under analyses.

**Duration**: 3-4 weeks  
**Goal**: Deliver a functional application with core palm reading capabilities

## Scope
- Session-based authentication (email/password) using Redis sessions
- Palm image upload (max 2 images: left/right), validation and local storage
- Background job processing for AI-powered analysis using OpenAI gpt-4.1-mini
- Conversation interface scoped to an analysis
- User and data persistence (Supabase/SQLite)
- Redis-based caching and session management
- Background worker system for long-running tasks
- Core API endpoints under `/api/v1`

## Deliverables
- ✅ User registration and authentication system with Redis sessions
- ✅ Palm image upload and processing
- ✅ Background job system for AI-powered palm reading analysis
- ✅ Job status monitoring and user feedback
- ✅ Basic conversation functionality
- ✅ User data management with database flexibility
- ✅ Redis-based caching and session management
- ✅ Core API documentation
- ✅ Basic error handling and validation

## Features & Tasks

### 1. User Authentication System
**Purpose**: Enable user registration and login with Redis-based sessions

**Tasks**:
1. Create User model (email unique, password hash via bcrypt)
2. Implement register, login, logout endpoints with Redis session storage
3. Add CSRF token for state-changing requests
4. Session storage in Redis with TTL and rotation on login
5. Protect authenticated routes with dependency
6. Configure session management service with Redis

**Acceptance Criteria**:
- Users can register/login/logout successfully
- Session data stored in Redis with proper TTL
- Session cookie is HTTP-only, Secure, SameSite=Lax
- CSRF validation works on POST/PUT/DELETE
- Protected routes reject unauthenticated requests
- Sessions rotate on login and persist across server restarts

### 2. Database Models and Migrations
**Purpose**: Define data structure for users, palm readings, and conversations with database flexibility

**Tasks**:
1. Create `users`, `analyses`, `conversations`, `messages` tables
2. Add FKs and indexes (`user_id`, `analysis_id`, `created_at`)
3. Add status fields for analysis state (queued, processing, completed, failed)
4. Define on-delete cascades per `project-rules.md`
5. Create Alembic migration scripts that work with both PostgreSQL and SQLite
6. Add job tracking fields for background processing

**Acceptance Criteria**:
- All models created with proper relationships
- Database migrations run successfully on both Supabase and SQLite
- Data integrity constraints in place
- Models support the application's data needs including job status tracking
- Proper indexes for query performance

### 3. Palm Image Upload System
**Purpose**: Handle palm image uploads with validation and processing

**Tasks**:
1. Create endpoint to upload up to 2 files (left/right)
2. Validate magic bytes, type (JPEG/PNG), size (<= 15 MB)
3. Store files under `/data/images/{user_id}/{analysis_id}/`
4. Strip EXIF and generate thumbnails (background task)
5. Enforce per-user quotas and handle errors

**Acceptance Criteria**:
- Users can upload up to two images and see validation errors when invalid
- Files stored on disk with metadata in DB
- Thumbnails generated asynchronously
- Errors surfaced clearly (400/413)
- Quotas enforced to prevent abuse

### 4. Background AI Palm Analysis Service
**Purpose**: Integrate OpenAI gpt-4.1-mini for palm reading analysis via background jobs

**Tasks**:
1. Create OpenAI service with timeouts/retries/backoff
2. Implement Celery/RQ tasks for background processing
3. Update job status in Redis during processing
4. Analyze up to 2 images and persist results
5. Expose summary unauthenticated; full report behind login
6. Add job status polling endpoint for frontend
7. Implement distributed rate limiting across workers

**Acceptance Criteria**:
- Background jobs process OpenAI requests without blocking API
- Job status updates available for frontend polling
- OpenAI integration works and returns structured summary/full report
- Errors handled with retries and job failure states
- Summary visible pre-login; full results gated by login
- Rate limiting prevents abuse across multiple workers
- Token usage logged for monitoring
- Failed jobs can be retried manually or automatically

### 5. Conversation Interface
**Purpose**: Enable users to ask follow-up questions about their palm readings

**Tasks**:
1. Create endpoints under `/analyses/{id}/conversations`
2. Persist messages; append on continue; allow rename/edit metadata
3. Generate AI responses grounded on the analysis
4. List conversations (most recent first, page size 5)
5. Delete conversation (cascade data)

**Acceptance Criteria**:
- Authenticated users can start/continue/delete conversations for an analysis
- History maintained and responses are contextual
- Pagination works as specified
- Cascading deletes remove all conversation data
- Update operations persist properly

### 6. Core API Endpoints
**Purpose**: Provide RESTful API for all core functionality including background jobs

**Tasks**:
1. Create `/auth` (register, login, logout) with Redis session management
2. Create `/analyses` (POST create with job queuing, GET list, GET by id with status)
3. Create `/analyses/{id}/status` endpoint for job status polling
4. Create `/analyses/{id}/conversations` (CRUD + talk with background processing)
5. Add Pydantic request/response models including job status schemas
6. Implement consistent error responses and job failure handling

**Acceptance Criteria**:
- All endpoints return proper HTTP status codes
- Background job endpoints provide real-time status updates
- Request/response validation works correctly
- Error responses are consistent and helpful
- Job status polling works efficiently
- API documentation is auto-generated including job schemas
- Endpoints follow RESTful conventions

### 7. Basic User Interface Integration
**Purpose**: Ensure API works with frontend applications including background job feedback

**Tasks**:
1. Next.js pages: upload flow (max 2 files) with real-time progress via job status polling
2. Show processing status, then summary post-analysis; prompt login for full report
3. Login/register screens with Redis session cookie handling
4. Analyses list (most recent first, page size 5) with job status indicators
5. Conversations UI under analysis detail (start/continue/delete)
6. Job status polling with user-friendly progress indicators

**Acceptance Criteria**:
- Frontend can communicate with API and poll job status
- Real-time progress feedback during analysis processing
- Session persistence works across browser restarts
- API documentation is accessible
- Content types are properly set
- CORS is configured correctly
- API versioning is in place

## Technical Implementation

### User Model (example)
```python
# app/models/user.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.models.base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    picture = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)  # bcrypt hash
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### Analysis Model (example)
```python
# app/models/analysis.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base
import enum

class AnalysisStatus(enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Analysis(Base):
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null for anonymous
    left_image_path = Column(String, nullable=True)
    right_image_path = Column(String, nullable=True)
    summary = Column(Text, nullable=True)  # Available pre-login
    full_report = Column(Text, nullable=True)  # Available post-login
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.QUEUED)
    job_id = Column(String, nullable=True)  # Celery job ID
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="analyses")
    conversations = relationship("Conversation", back_populates="analysis", cascade="all, delete-orphan")
```

### Background Job Tasks (example)
```python
# app/tasks/analysis_tasks.py
import logging
from typing import Dict, Any
from celery import current_task
from app.core.celery_app import celery_app
from app.services.openai_service import OpenAIService
from app.models.analysis import Analysis, AnalysisStatus
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3)
def process_palm_analysis(self, analysis_id: int):
    """Background task to process palm analysis with OpenAI."""
    try:
        # Update job status to processing
        async with AsyncSessionLocal() as db:
            analysis = await db.get(Analysis, analysis_id)
            if not analysis:
                raise ValueError(f"Analysis {analysis_id} not found")
            
            analysis.status = AnalysisStatus.PROCESSING
            analysis.job_id = self.request.id
            await db.commit()
        
        # Load images and call OpenAI
        openai_service = OpenAIService()
        result = await openai_service.analyze_palm_images(
            analysis.left_image_path,
            analysis.right_image_path
        )
        
        # Update analysis with results
        async with AsyncSessionLocal() as db:
            analysis = await db.get(Analysis, analysis_id)
            analysis.summary = result["summary"]
            analysis.full_report = result["full_report"]
            analysis.status = AnalysisStatus.COMPLETED
            await db.commit()
        
        return {"status": "completed", "analysis_id": analysis_id}
        
    except Exception as exc:
        logger.error(f"Analysis task failed: {exc}")
        
        # Update analysis with error
        async with AsyncSessionLocal() as db:
            analysis = await db.get(Analysis, analysis_id)
            analysis.status = AnalysisStatus.FAILED
            analysis.error_message = str(exc)
            await db.commit()
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            countdown = 60 * (2 ** self.request.retries)
            raise self.retry(countdown=countdown, exc=exc)
        
        raise exc
```

### Analysis Endpoints (example)
```python
# app/api/v1/analyses.py
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import List, Optional
from app.schemas.analysis import AnalysisCreate, AnalysisResponse, AnalysisStatus
from app.services.analysis_service import AnalysisService
from app.tasks.analysis_tasks import process_palm_analysis
from app.dependencies.auth import get_current_user_optional

router = APIRouter(prefix="/analyses", tags=["analyses"])

@router.post("/", response_model=AnalysisResponse)
async def create_analysis(
    left_image: Optional[UploadFile] = File(None),
    right_image: Optional[UploadFile] = File(None),
    current_user = Depends(get_current_user_optional)
):
    """Create new palm analysis (up to 2 images)."""
    if not left_image and not right_image:
        raise HTTPException(status_code=400, detail="At least one image required")
    
    analysis_service = AnalysisService()
    
    # Create analysis record
    analysis = await analysis_service.create_analysis(
        user_id=current_user.id if current_user else None,
        left_image=left_image,
        right_image=right_image
    )
    
    # Queue background processing job
    job = process_palm_analysis.delay(analysis.id)
    analysis.job_id = job.id
    await analysis_service.update_job_id(analysis.id, job.id)
    
    return analysis

@router.get("/{analysis_id}/status")
async def get_analysis_status(analysis_id: int):
    """Get current status of analysis job."""
    analysis_service = AnalysisService()
    status = await analysis_service.get_analysis_status(analysis_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return {
        "analysis_id": analysis_id,
        "status": status.status.value,
        "progress": _calculate_progress(status.status),
        "error_message": status.error_message
    }

def _calculate_progress(status: AnalysisStatus) -> int:
    """Calculate progress percentage based on status."""
    progress_map = {
        AnalysisStatus.QUEUED: 10,
        AnalysisStatus.PROCESSING: 50,
        AnalysisStatus.COMPLETED: 100,
        AnalysisStatus.FAILED: 0
    }
    return progress_map.get(status, 0)
```

## Testing Strategy

### Unit Tests
- User authentication flow with Redis sessions
- Palm image validation
- Background job processing
- OpenAI service integration
- Job status tracking
- Conversation management
- API endpoint validation

### Integration Tests
- Complete user journey (upload → background processing → analysis → conversation)
- Database operations with both Supabase and SQLite
- Redis session management
- Background job processing with Celery/RQ
- File upload and processing
- Job status polling

### End-to-End Tests
- User registration and login
- Palm reading workflow
- Conversation interface
- Error handling scenarios

## Success Metrics

### Functional Metrics
- ✅ Users can register and login successfully
- ✅ Palm images can be uploaded and analyzed
- ✅ AI analysis provides meaningful results
- ✅ Conversations work end-to-end
- ✅ Data is persisted correctly

### Performance Metrics
- ✅ Image upload and job queuing completes within 5 seconds
- ✅ Background AI analysis completes within 60 seconds
- ✅ Job status polling responses under 1 second
- ✅ API responses under 2 seconds
- ✅ Database and Redis queries optimized
- ✅ Worker processes handle job queue efficiently
- ✅ Error rate under 5%

### Quality Metrics
- ✅ All core features tested
- ✅ API documentation complete
- ✅ Error handling comprehensive
- ✅ Security measures in place
- ✅ Code coverage above 80%

## Risk Mitigation

### Technical Risks
- **Background job complexity**: Use established queue systems (Celery/RQ), implement proper error handling
- **Redis connectivity**: Implement connection pooling, retry logic for Redis operations
- **OpenAI API reliability**: Implement retry logic in background jobs, monitor usage
- **File upload security**: Validate files, implement size limits
- **Database performance**: Use proper indexing, monitor query performance across different databases
- **Job queue management**: Monitor worker health, implement dead letter queues

### Business Risks
- **User adoption**: Focus on core value proposition
- **AI accuracy**: Set expectations, provide disclaimers
- **Cost management**: Monitor OpenAI usage, implement rate limiting
- **Data privacy**: Implement proper data handling, comply with regulations

## Next Phase Preparation

### Handoff to Phase 3
- ✅ Core functionality working
- ✅ User authentication established
- ✅ AI integration functional
- ✅ Basic conversation system
- ✅ Data persistence working

### Dependencies for Phase 3
- Enhanced UI/UX will build on existing API
- Advanced features will extend current models
- Performance optimizations will improve existing functionality
- Additional integrations will use established patterns

## Definition of Done

A feature is considered complete when:
1. ✅ Code is written and follows project standards
2. ✅ Tests are written and passing
3. ✅ Documentation is updated
4. ✅ Code review is completed
5. ✅ Feature is tested manually
6. ✅ Integration with existing features works
7. ✅ Performance meets requirements
8. ✅ Security considerations addressed
9. ✅ Error handling is comprehensive
10. ✅ API documentation is updated

This MVP phase delivers a functional application that provides the core value proposition of AI-powered palm reading, establishing the foundation for future enhancements and polish.
