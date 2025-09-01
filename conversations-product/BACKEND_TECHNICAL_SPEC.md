# Backend Technical Specification - Analysis Follow-up Questions

## Overview

This document provides detailed technical specifications for backend implementation of the Analysis Follow-up Questions feature. The backend team will implement OpenAI Files API integration, enhanced conversation management, security controls, and new API endpoints.

## Database Schema Changes

### 1. Enhanced Conversation Model

```python
# Add to app/models/conversation.py
class Conversation(Base):
    # ... existing fields ...
    
    # NEW FIELDS for Analysis Follow-up
    openai_file_ids = Column(JSON, nullable=True, comment="OpenAI file IDs for palm images")
    questions_count = Column(Integer, default=0, nullable=False, comment="Number of questions asked")
    max_questions = Column(Integer, default=5, nullable=False, comment="Maximum questions allowed")
    is_analysis_followup = Column(Boolean, default=False, nullable=False, index=True, comment="Flag for analysis follow-up conversations")
    analysis_context = Column(JSON, nullable=True, comment="Cached analysis context for performance")
    
    # Enhanced metadata
    conversation_type = Column(Enum(ConversationType), default=ConversationType.GENERAL, nullable=False, index=True)
    
class ConversationType(enum.Enum):
    GENERAL = "general"
    ANALYSIS_FOLLOWUP = "analysis_followup"
```

### 2. Enhanced Analysis Model

```python
# Add to app/models/analysis.py  
class Analysis(Base):
    # ... existing fields ...
    
    # NEW FIELDS for OpenAI Files API
    openai_file_ids = Column(JSON, nullable=True, comment="OpenAI file IDs for reuse")
    has_followup_conversation = Column(Boolean, default=False, nullable=False, index=True, comment="Quick check for follow-up availability")
    followup_questions_count = Column(Integer, default=0, nullable=False, comment="Total follow-up questions asked")
```

### 3. Database Migration

```python
# Create migration: alembic/versions/add_analysis_followup_fields.py
"""Add analysis followup fields

Revision ID: analysis_followup_001
Revises: previous_revision
Create Date: 2024-XX-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'analysis_followup_001'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None

def upgrade():
    # Add to conversations table
    op.add_column('conversations', sa.Column('openai_file_ids', postgresql.JSON(), nullable=True))
    op.add_column('conversations', sa.Column('questions_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('conversations', sa.Column('max_questions', sa.Integer(), nullable=False, server_default='5'))
    op.add_column('conversations', sa.Column('is_analysis_followup', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('conversations', sa.Column('analysis_context', postgresql.JSON(), nullable=True))
    op.add_column('conversations', sa.Column('conversation_type', sa.Enum('GENERAL', 'ANALYSIS_FOLLOWUP', name='conversationtype'), nullable=False, server_default='GENERAL'))
    
    # Add to analyses table
    op.add_column('analyses', sa.Column('openai_file_ids', postgresql.JSON(), nullable=True))
    op.add_column('analyses', sa.Column('has_followup_conversation', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('analyses', sa.Column('followup_questions_count', sa.Integer(), nullable=False, server_default='0'))
    
    # Add indexes
    op.create_index('ix_conversations_is_analysis_followup', 'conversations', ['is_analysis_followup'])
    op.create_index('ix_conversations_conversation_type', 'conversations', ['conversation_type'])
    op.create_index('ix_analyses_has_followup_conversation', 'analyses', ['has_followup_conversation'])

def downgrade():
    # Remove indexes
    op.drop_index('ix_analyses_has_followup_conversation')
    op.drop_index('ix_conversations_conversation_type')
    op.drop_index('ix_conversations_is_analysis_followup')
    
    # Remove columns
    op.drop_column('analyses', 'followup_questions_count')
    op.drop_column('analyses', 'has_followup_conversation')
    op.drop_column('analyses', 'openai_file_ids')
    op.drop_column('conversations', 'conversation_type')
    op.drop_column('conversations', 'analysis_context')
    op.drop_column('conversations', 'is_analysis_followup')
    op.drop_column('conversations', 'max_questions')
    op.drop_column('conversations', 'questions_count')
    op.drop_column('conversations', 'openai_file_ids')
    
    # Drop enum
    sa.Enum(name='conversationtype').drop(op.get_bind())
```

## New Services Implementation

### 1. OpenAI Files Service

```python
# Create: app/services/openai_files_service.py
import logging
import asyncio
from typing import Dict, List, Optional
from pathlib import Path
import aiofiles
from openai import AsyncOpenAI
from app.core.config import settings
from app.models.analysis import Analysis

logger = logging.getLogger(__name__)

class OpenAIFilesService:
    """Service for managing OpenAI Files API operations."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.max_file_size = 20 * 1024 * 1024  # 20MB limit
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
    
    async def upload_analysis_images(self, analysis: Analysis) -> Dict[str, str]:
        """
        Upload palm images to OpenAI Files API.
        
        Args:
            analysis: Analysis object with image paths
            
        Returns:
            Dict mapping image_type -> file_id
        """
        try:
            file_ids = {}
            upload_tasks = []
            
            # Prepare upload tasks
            if analysis.left_image_path:
                upload_tasks.append(
                    self._upload_single_image(analysis.left_image_path, 'left_palm')
                )
            
            if analysis.right_image_path:
                upload_tasks.append(
                    self._upload_single_image(analysis.right_image_path, 'right_palm')
                )
            
            # Execute uploads concurrently
            if upload_tasks:
                results = await asyncio.gather(*upload_tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"File upload failed: {result}")
                        continue
                    
                    image_type, file_id = result
                    file_ids[image_type] = file_id
            
            logger.info(f"Uploaded {len(file_ids)} files for analysis {analysis.id}")
            return file_ids
            
        except Exception as e:
            logger.error(f"Failed to upload images for analysis {analysis.id}: {e}")
            raise
    
    async def _upload_single_image(self, image_path: str, image_type: str) -> tuple:
        """Upload a single image file."""
        try:
            # Validate file
            path = Path(image_path)
            if not path.exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            if path.suffix.lower() not in self.supported_formats:
                raise ValueError(f"Unsupported file format: {path.suffix}")
            
            if path.stat().st_size > self.max_file_size:
                raise ValueError(f"File too large: {path.stat().st_size} bytes")
            
            # Upload to OpenAI
            async with aiofiles.open(image_path, 'rb') as file:
                file_content = await file.read()
                
                response = await self.client.files.create(
                    file=(path.name, file_content),
                    purpose='vision'
                )
                
                logger.info(f"Uploaded {image_type} image: {response.id}")
                return image_type, response.id
                
        except Exception as e:
            logger.error(f"Failed to upload {image_type} image: {e}")
            raise
    
    async def delete_files(self, file_ids: List[str]) -> None:
        """Delete files from OpenAI."""
        try:
            delete_tasks = [
                self.client.files.delete(file_id) 
                for file_id in file_ids
            ]
            
            await asyncio.gather(*delete_tasks, return_exceptions=True)
            logger.info(f"Deleted {len(file_ids)} files from OpenAI")
            
        except Exception as e:
            logger.error(f"Failed to delete files: {e}")
    
    async def get_file_info(self, file_id: str) -> Optional[dict]:
        """Get file information from OpenAI."""
        try:
            file_info = await self.client.files.retrieve(file_id)
            return {
                'id': file_info.id,
                'filename': file_info.filename,
                'purpose': file_info.purpose,
                'status': file_info.status,
                'created_at': file_info.created_at
            }
        except Exception as e:
            logger.error(f"Failed to get file info for {file_id}: {e}")
            return None
```

### 2. Enhanced Analysis Follow-up Service

```python
# Create: app/services/analysis_followup_service.py
import logging
from typing import Dict, List, Optional, Tuple
import json
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.analysis import Analysis
from app.models.conversation import Conversation, ConversationType
from app.models.message import Message, MessageType
from app.services.openai_files_service import OpenAIFilesService
from app.services.openai_service import OpenAIService
from app.schemas.conversation import FollowupConversationCreate

logger = logging.getLogger(__name__)

class AnalysisFollowupService:
    """Service for managing analysis follow-up conversations."""
    
    def __init__(self):
        self.files_service = OpenAIFilesService()
        self.openai_service = OpenAIService()
        self.max_questions_per_analysis = 5
    
    async def create_followup_conversation(
        self, 
        analysis_id: int, 
        user_id: int, 
        db: Session
    ) -> Conversation:
        """
        Create a new follow-up conversation for an analysis.
        
        This includes uploading palm images to OpenAI Files API.
        """
        try:
            # Get analysis
            analysis = db.query(Analysis).filter(
                Analysis.id == analysis_id,
                Analysis.user_id == user_id,
                Analysis.status == "completed"
            ).first()
            
            if not analysis:
                raise ValueError("Analysis not found or not completed")
            
            # Check if follow-up conversation already exists
            existing_conversation = db.query(Conversation).filter(
                Conversation.analysis_id == analysis_id,
                Conversation.is_analysis_followup == True
            ).first()
            
            if existing_conversation:
                return existing_conversation
            
            # Upload images to OpenAI if not already done
            openai_file_ids = analysis.openai_file_ids or {}
            if not openai_file_ids:
                openai_file_ids = await self.files_service.upload_analysis_images(analysis)
                
                # Update analysis with file IDs
                analysis.openai_file_ids = openai_file_ids
                db.commit()
            
            # Create follow-up conversation
            conversation = Conversation(
                analysis_id=analysis_id,
                title=f"Questions about your palm reading",
                is_analysis_followup=True,
                conversation_type=ConversationType.ANALYSIS_FOLLOWUP,
                openai_file_ids=openai_file_ids,
                questions_count=0,
                max_questions=self.max_questions_per_analysis,
                analysis_context={
                    "summary": analysis.summary[:1000] if analysis.summary else None,
                    "created_at": analysis.created_at.isoformat()
                }
            )
            
            db.add(conversation)
            
            # Update analysis flags
            analysis.has_followup_conversation = True
            
            db.commit()
            db.refresh(conversation)
            
            logger.info(f"Created follow-up conversation {conversation.id} for analysis {analysis_id}")
            return conversation
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create follow-up conversation: {e}")
            raise
    
    async def ask_followup_question(
        self,
        conversation_id: int,
        user_id: int,
        question: str,
        db: Session
    ) -> Dict:
        """
        Process a follow-up question with full context.
        """
        try:
            # Get conversation
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.analysis.has(Analysis.user_id == user_id),
                Conversation.is_analysis_followup == True
            ).first()
            
            if not conversation:
                raise ValueError("Follow-up conversation not found")
            
            # Check question limit
            if conversation.questions_count >= conversation.max_questions:
                raise ValueError(f"Maximum {conversation.max_questions} questions allowed")
            
            # Validate question
            if not self._validate_question(question):
                raise ValueError("Question must be about palm reading and palmistry")
            
            # Get previous Q&A for context
            previous_messages = db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at.asc()).all()
            
            # Build conversation history
            qa_history = []
            for i in range(0, len(previous_messages), 2):
                if i + 1 < len(previous_messages):
                    qa_history.append({
                        "question": previous_messages[i].content,
                        "answer": previous_messages[i + 1].content
                    })
            
            # Generate AI response
            response = await self._generate_followup_response(
                conversation, question, qa_history
            )
            
            # Save user question
            user_message = Message(
                conversation_id=conversation_id,
                content=question,
                message_type=MessageType.USER
            )
            db.add(user_message)
            
            # Save AI response  
            ai_message = Message(
                conversation_id=conversation_id,
                content=response['content'],
                message_type=MessageType.ASSISTANT,
                tokens_used=response.get('tokens_used', 0)
            )
            db.add(ai_message)
            
            # Update conversation
            conversation.questions_count += 1
            conversation.last_message_at = ai_message.created_at
            
            # Update analysis question count
            conversation.analysis.followup_questions_count += 1
            
            db.commit()
            db.refresh(user_message)
            db.refresh(ai_message)
            
            logger.info(f"Processed follow-up question {conversation.questions_count}/{conversation.max_questions} for conversation {conversation_id}")
            
            return {
                "user_message": user_message,
                "assistant_message": ai_message,
                "questions_remaining": conversation.max_questions - conversation.questions_count,
                "tokens_used": response.get('tokens_used', 0),
                "cost": response.get('cost', 0.0)
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to process follow-up question: {e}")
            raise
    
    async def _generate_followup_response(
        self, 
        conversation: Conversation, 
        question: str, 
        qa_history: List[Dict]
    ) -> Dict:
        """Generate AI response with full context."""
        try:
            # Build conversation context
            context_parts = []
            
            # Add original analysis summary
            if conversation.analysis_context and conversation.analysis_context.get('summary'):
                context_parts.append(f"Original palm reading analysis: {conversation.analysis_context['summary']}")
            
            # Add previous Q&A
            if qa_history:
                context_parts.append("Previous questions and answers:")
                for i, qa in enumerate(qa_history, 1):
                    context_parts.append(f"Q{i}: {qa['question']}")
                    context_parts.append(f"A{i}: {qa['answer']}")
            
            context_text = "\n\n".join(context_parts)
            
            # Prepare messages for OpenAI
            messages = [
                {
                    "role": "system",
                    "content": self._get_followup_system_prompt()
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": context_text},
                        {"type": "text", "text": f"New question: {question}"}
                    ]
                }
            ]
            
            # Add palm images if available
            if conversation.openai_file_ids:
                for image_type, file_id in conversation.openai_file_ids.items():
                    messages[1]["content"].append({
                        "type": "image_url",
                        "image_url": {"url": f"file-{file_id}"}
                    })
            
            # Call OpenAI
            response = await self.openai_service.chat_completion(
                messages=messages,
                model="gpt-4o",
                max_tokens=500,
                temperature=0.7
            )
            
            return {
                "content": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens,
                "cost": self._calculate_cost(response.usage.total_tokens)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate follow-up response: {e}")
            raise
    
    def _validate_question(self, question: str) -> bool:
        """Validate that question is about palm reading."""
        question_lower = question.lower()
        
        # Length checks
        if len(question) < 10 or len(question) > 500:
            return False
        
        # Forbidden topics
        forbidden_terms = [
            "ignore previous", "system", "prompt", "instructions",
            "medical advice", "diagnosis", "health condition",
            "future", "prediction", "when will", "how long will"
        ]
        
        for term in forbidden_terms:
            if term in question_lower:
                return False
        
        # Required palmistry relevance
        palmistry_terms = [
            "palm", "hand", "finger", "thumb", "line", "mount",
            "reading", "palmistry", "chiromancy"
        ]
        
        if not any(term in question_lower for term in palmistry_terms):
            return False
        
        return True
    
    def _get_followup_system_prompt(self) -> str:
        """Get the system prompt for follow-up questions."""
        return """
        You are an expert palmist providing follow-up answers about a specific palm reading.
        
        Context: The user has received a complete palm reading analysis and is now asking follow-up questions about specific aspects of their reading.
        
        Guidelines:
        1. Reference the original analysis and palm images when answering
        2. Be specific about what you see in their particular palm features
        3. Connect answers to the original reading for consistency
        4. Focus only on palmistry - no medical advice or future predictions
        5. Keep responses informative but concise (max 300 words)
        6. If you can't see specific features clearly, acknowledge this limitation
        
        Answer the follow-up question based on the palm images and previous context provided.
        """
    
    def _calculate_cost(self, tokens: int) -> float:
        """Calculate cost based on token usage."""
        # GPT-4o pricing (approximate)
        cost_per_1k_tokens = 0.03
        return (tokens / 1000) * cost_per_1k_tokens
    
    async def get_followup_status(
        self, 
        analysis_id: int, 
        user_id: int, 
        db: Session
    ) -> Dict:
        """Get follow-up conversation status for an analysis."""
        try:
            analysis = db.query(Analysis).filter(
                Analysis.id == analysis_id,
                Analysis.user_id == user_id
            ).first()
            
            if not analysis:
                raise ValueError("Analysis not found")
            
            conversation = db.query(Conversation).filter(
                Conversation.analysis_id == analysis_id,
                Conversation.is_analysis_followup == True
            ).first()
            
            return {
                "analysis_completed": analysis.status == "completed",
                "followup_available": analysis.status == "completed",
                "followup_conversation_exists": conversation is not None,
                "questions_asked": conversation.questions_count if conversation else 0,
                "questions_remaining": (conversation.max_questions - conversation.questions_count) if conversation else 5,
                "conversation_id": conversation.id if conversation else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get follow-up status: {e}")
            raise
```

## New API Endpoints

### 1. Follow-up Endpoints

```python
# Add to app/api/v1/analyses.py or create new followup.py
from fastapi import APIRouter, HTTPException, Depends, status
from app.services.analysis_followup_service import AnalysisFollowupService
from app.schemas.conversation import FollowupStatusResponse, FollowupQuestionRequest, FollowupQuestionResponse

router = APIRouter()

@router.post("/analyses/{analysis_id}/followup/start", response_model=ConversationResponse)
async def start_followup_conversation(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ConversationResponse:
    """
    Start a follow-up conversation for an analysis.
    
    Creates a new conversation thread for asking questions about the palm reading.
    Uploads palm images to OpenAI Files API for context in responses.
    """
    try:
        followup_service = AnalysisFollowupService()
        
        conversation = await followup_service.create_followup_conversation(
            analysis_id=analysis_id,
            user_id=current_user.id,
            db=db
        )
        
        return ConversationResponse.model_validate(conversation)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error starting follow-up conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start follow-up conversation"
        )

@router.post("/analyses/{analysis_id}/followup/{conversation_id}/ask", response_model=FollowupQuestionResponse)
async def ask_followup_question(
    analysis_id: int,
    conversation_id: int,
    question_data: FollowupQuestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> FollowupQuestionResponse:
    """
    Ask a follow-up question about the palm reading.
    
    Processes the question with full context from original palm images
    and previous Q&A history. Enforces question limits.
    """
    try:
        followup_service = AnalysisFollowupService()
        
        result = await followup_service.ask_followup_question(
            conversation_id=conversation_id,
            user_id=current_user.id,
            question=question_data.question,
            db=db
        )
        
        return FollowupQuestionResponse(
            user_message=MessageResponse.model_validate(result["user_message"]),
            assistant_message=MessageResponse.model_validate(result["assistant_message"]),
            questions_remaining=result["questions_remaining"],
            tokens_used=result["tokens_used"],
            cost=result["cost"]
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing follow-up question: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process question"
        )

@router.get("/analyses/{analysis_id}/followup/status", response_model=FollowupStatusResponse)
async def get_followup_status(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> FollowupStatusResponse:
    """
    Get follow-up conversation status for an analysis.
    
    Returns information about whether follow-up questions are available,
    how many questions have been asked, and remaining questions.
    """
    try:
        followup_service = AnalysisFollowupService()
        
        status_info = await followup_service.get_followup_status(
            analysis_id=analysis_id,
            user_id=current_user.id,
            db=db
        )
        
        return FollowupStatusResponse(**status_info)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting follow-up status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get follow-up status"
        )
```

## Updated Schemas

```python
# Add to app/schemas/conversation.py
from typing import Dict, Optional
from pydantic import BaseModel, Field

class FollowupStatusResponse(BaseModel):
    analysis_completed: bool
    followup_available: bool
    followup_conversation_exists: bool
    questions_asked: int
    questions_remaining: int
    conversation_id: Optional[int] = None

class FollowupQuestionRequest(BaseModel):
    question: str = Field(..., min_length=10, max_length=500, description="Follow-up question about the palm reading")

class FollowupQuestionResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse
    questions_remaining: int
    tokens_used: int
    cost: float
```

## Configuration Updates

```python
# Add to app/core/config.py
class Settings(BaseSettings):
    # ... existing settings ...
    
    # OpenAI Files API settings
    OPENAI_FILES_MAX_SIZE: int = 20 * 1024 * 1024  # 20MB
    OPENAI_FILES_CLEANUP_DAYS: int = 30  # Clean up files after 30 days
    
    # Follow-up conversation settings
    FOLLOWUP_MAX_QUESTIONS_PER_ANALYSIS: int = 5
    FOLLOWUP_QUESTION_MIN_LENGTH: int = 10
    FOLLOWUP_QUESTION_MAX_LENGTH: int = 500
```

## Testing Requirements

### Unit Tests
- [ ] OpenAI Files Service upload/delete operations
- [ ] Question validation logic
- [ ] Question limit enforcement
- [ ] Context building for follow-up responses
- [ ] Database operations for follow-up conversations

### Integration Tests
- [ ] Complete follow-up conversation flow
- [ ] OpenAI API integration with files
- [ ] Error handling for API failures
- [ ] Concurrent user scenarios
- [ ] Security validation for prompt injection

### Performance Tests
- [ ] Response time under 2 seconds
- [ ] Concurrent follow-up questions (100+ users)
- [ ] File upload performance
- [ ] Database query optimization

## Security Considerations

### Input Validation
- Strict question length limits (10-500 characters)
- Palmistry keyword requirements
- Forbidden topic detection
- SQL injection prevention in all queries

### API Security
- CSRF token validation on all POST endpoints
- Rate limiting for follow-up questions
- User authorization for analysis access
- OpenAI API key protection

### Data Privacy
- Secure file handling for palm images
- Automatic cleanup of OpenAI files
- User data isolation
- Audit logging for security events

## Monitoring & Observability

### Metrics to Track
- Follow-up conversation creation rate
- Question processing time
- OpenAI API success/failure rates
- Token usage and costs
- Question validation failure rates

### Alerts to Configure
- OpenAI API errors
- High token usage costs
- Follow-up question processing failures
- File upload failures
- Security validation violations

## Deployment Checklist

### Pre-deployment
- [ ] Run all tests and ensure 95%+ coverage
- [ ] Database migration tested in staging
- [ ] OpenAI API credentials configured
- [ ] Security review completed
- [ ] Performance testing passed

### Deployment
- [ ] Feature flag enabled for gradual rollout
- [ ] Monitoring dashboards configured
- [ ] Error alerting setup
- [ ] Database migration executed
- [ ] Documentation updated

### Post-deployment
- [ ] Monitor error rates and performance
- [ ] Validate OpenAI API integration
- [ ] Check user adoption metrics
- [ ] Review security logs
- [ ] Gather user feedback

This comprehensive technical specification provides the backend team with detailed implementation guidance, security considerations, and testing requirements for the Analysis Follow-up Questions feature.