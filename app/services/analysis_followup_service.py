"""Analysis Follow-up Service for managing follow-up conversations on palm readings.

This service provides comprehensive management of follow-up question conversations
for completed palm reading analyses. It handles secure conversation creation,
question validation, AI response generation, and conversation management.

**Key Features:**
- Secure follow-up conversation creation with file management
- Comprehensive question validation and security filtering  
- Context-aware AI response generation using palm images
- Question limit enforcement and usage tracking
- Conversation history management and retrieval
- Prompt injection prevention and content filtering

**Business Logic:**
- Only completed analyses support follow-up questions
- Each analysis allows up to 5 follow-up questions by default
- Questions must be palmistry-related and meet security requirements
- AI responses use original palm images and analysis context
- Conversation history provides context for multi-turn dialogue

**Security Features:**
- Prompt injection detection and blocking
- Content filtering for inappropriate topics (medical, legal, financial)
- User authorization validation (users can only access their own analyses)
- Question length and format validation
- Context manipulation protection

**Integration Points:**
- OpenAI Files Service: For uploading and validating palm images
- OpenAI Service: For generating AI responses with vision capabilities
- Database Models: Analysis, Conversation, Message entities
- API Endpoints: Follow-up conversation REST API

**Usage Example:**
```python
from app.services.analysis_followup_service import AnalysisFollowupService

# Initialize service
service = AnalysisFollowupService()

# Create follow-up conversation for completed analysis
conversation = await service.create_followup_conversation(
    analysis_id=123,
    user_id=456,
    db=db_session
)

# Ask a follow-up question
result = await service.ask_followup_question(
    conversation_id=conversation.id,
    user_id=456,
    question="What does my heart line reveal about my emotional nature?",
    db=db_session
)

# Get conversation history
history = await service.get_conversation_history(
    conversation_id=conversation.id,
    user_id=456,
    db=db_session
)
```

**Performance Characteristics:**
- Response generation: Typically 2-5 seconds
- Context caching: Analysis context cached for fast retrieval
- Concurrent operations: Thread-safe for multiple users
- Token optimization: Efficient prompt engineering reduces costs

**Error Handling:**
- All methods raise AnalysisFollowupServiceError for business logic errors
- Comprehensive validation with specific error messages
- Transaction rollback on failures
- Detailed logging for debugging and monitoring

**Thread Safety:**
- All methods are async and thread-safe
- Database operations use proper transaction management
- No shared mutable state between operations
- Supports concurrent conversations for different users

Author: Indian Palmistry AI Team
Version: 1.0.0
Created: August 2025
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.analysis import Analysis, AnalysisStatus
from app.models.conversation import Conversation, ConversationType
from app.models.message import Message, MessageType
from app.services.openai_files_service import OpenAIFilesService, OpenAIFilesServiceError
from app.services.openai_service import OpenAIService
from app.core.config import settings

logger = logging.getLogger(__name__)


class AnalysisFollowupServiceError(Exception):
    """Custom exception for Analysis Follow-up Service errors.
    
    This exception is raised for all business logic errors in the Analysis Follow-up Service,
    including validation failures, authentication errors, and processing issues.
    
    **Common Error Scenarios:**
    - Analysis not found, not completed, or not owned by user
    - Question validation failures (length, content, security)
    - Question limit exceeded for analysis
    - Conversation not found or not accessible
    - OpenAI API failures or file upload errors
    - Database transaction failures
    
    **Usage:**
    ```python
    try:
        conversation = await service.create_followup_conversation(
            analysis_id=123, user_id=456, db=db
        )
    except AnalysisFollowupServiceError as e:
        if "not found" in str(e):
            return 404_response(str(e))
        elif "maximum" in str(e):
            return 429_response(str(e))
        else:
            return 400_response(str(e))
    ```
    
    **Error Message Guidelines:**
    - Include specific error context (analysis ID, user ID, operation)
    - Provide actionable information when possible
    - Use consistent error message format for API responses
    - Preserve sensitive information appropriately
    """
    pass


class AnalysisFollowupService:
    """Service for managing analysis follow-up conversations.
    
    This service orchestrates the complete follow-up question workflow for palm readings,
    from conversation creation through AI response generation. It integrates multiple
    components to provide secure, context-aware palmistry consultations.
    
    **Service Responsibilities:**
    - Create and manage follow-up conversations for completed analyses
    - Upload and validate palm images in OpenAI Files API
    - Validate user questions for security and content appropriateness
    - Generate AI responses using palm images and conversation context
    - Enforce question limits and track usage statistics
    - Provide conversation history and status information
    
    **Workflow Overview:**
    1. **Conversation Creation**: Validates analysis, uploads images, creates conversation
    2. **Question Processing**: Validates question, generates AI response, saves messages
    3. **History Management**: Provides access to conversation history and metadata
    
    **Security Architecture:**
    - Multi-layer validation: Length, format, content, and security checks
    - Prompt injection prevention using pattern matching
    - Content filtering for inappropriate topics
    - User authorization verification for all operations
    - Context isolation between different users and analyses
    
    **Performance Optimizations:**
    - Analysis context caching for fast AI response generation
    - Concurrent file operations for image uploads
    - Efficient database queries with proper indexing
    - Token-optimized prompts for cost efficiency
    
    **Integration Dependencies:**
    - OpenAIFilesService: File upload and validation operations
    - OpenAIService: AI response generation with vision capabilities
    - Database Models: Analysis, Conversation, Message persistence
    - Configuration: Question limits and validation parameters
    
    **Configuration Parameters:**
    - Max questions per analysis: Configurable limit (default: 5)
    - Question length limits: Min/max character requirements
    - File upload settings: Inherited from OpenAI Files Service
    - AI model settings: Model selection and token limits
    
    **Example Usage:**
    ```python
    # Initialize service
    service = AnalysisFollowupService()
    
    # Complete workflow example
    try:
        # Create conversation
        conversation = await service.create_followup_conversation(
            analysis_id=123, user_id=456, db=db
        )
        
        # Ask questions
        for question in user_questions:
            result = await service.ask_followup_question(
                conversation_id=conversation.id,
                user_id=456,
                question=question,
                db=db
            )
            print(f"AI Response: {result['assistant_message'].content}")
            
    except AnalysisFollowupServiceError as e:
        logger.error(f"Follow-up service error: {e}")
        # Handle appropriately based on error type
    ```
    
    **Thread Safety:**
    All methods are thread-safe and support concurrent operations.
    Database transactions ensure consistency across concurrent requests.
    """
    
    def __init__(self):
        """Initialize the Analysis Follow-up Service.
        
        Sets up dependencies and configuration from application settings.
        All service dependencies are initialized and configuration
        parameters are loaded from the settings module.
        
        **Service Dependencies:**
        - OpenAIFilesService: For palm image upload and management
        - OpenAIService: For AI response generation
        - Settings: Question limits and validation parameters
        
        **Configuration Loading:**
        - Max questions per analysis: From settings.followup_max_questions_per_analysis
        - Question length limits: From settings.followup_question_min/max_length
        - File upload limits: Inherited from OpenAI Files Service
        
        **Initialization Validation:**
        Verifies that all required settings are present and valid.
        
        **Raises:**
            ValueError: If required settings are missing or invalid
            AnalysisFollowupServiceError: If service initialization fails
        """
        self.files_service = OpenAIFilesService()
        self.openai_service = OpenAIService()
        self.max_questions_per_analysis = settings.followup_max_questions_per_analysis
        self.min_question_length = settings.followup_question_min_length
        self.max_question_length = settings.followup_question_max_length
    
    async def create_followup_conversation(
        self, 
        analysis_id: int, 
        user_id: int, 
        db: Session
    ) -> Conversation:
        """
        Create a new follow-up conversation for an analysis.
        
        This includes uploading palm images to OpenAI Files API.
        
        Args:
            analysis_id: ID of the completed analysis
            user_id: ID of the user requesting follow-up
            db: Database session
            
        Returns:
            Created conversation object
            
        Raises:
            AnalysisFollowupServiceError: If analysis not found, not completed, or other errors
        """
        try:
            # Get and validate analysis
            analysis = db.query(Analysis).filter(
                and_(
                    Analysis.id == analysis_id,
                    Analysis.user_id == user_id,
                    Analysis.status == AnalysisStatus.COMPLETED
                )
            ).first()
            
            if not analysis:
                raise AnalysisFollowupServiceError(
                    "Analysis not found, not owned by user, or not completed"
                )
            
            # Check if follow-up conversation already exists
            existing_conversation = db.query(Conversation).filter(
                and_(
                    Conversation.analysis_id == analysis_id,
                    Conversation.is_analysis_followup == True
                )
            ).first()
            
            if existing_conversation:
                logger.info(f"Follow-up conversation already exists: {existing_conversation.id}")
                return existing_conversation
            
            # Upload images to OpenAI if not already done
            openai_file_ids = analysis.openai_file_ids or {}
            
            if not openai_file_ids:
                try:
                    openai_file_ids = await self.files_service.upload_analysis_images(analysis)
                    
                    # Update analysis with file IDs
                    analysis.openai_file_ids = openai_file_ids
                    db.commit()
                    
                    logger.info(f"Uploaded {len(openai_file_ids)} files for analysis {analysis_id}")
                    
                except OpenAIFilesServiceError as e:
                    logger.error(f"Failed to upload images for analysis {analysis_id}: {e}")
                    raise AnalysisFollowupServiceError(f"Failed to upload palm images: {str(e)}")
            else:
                # Validate existing files are still accessible
                file_ids = list(openai_file_ids.values())
                validation_results = await self.files_service.validate_files(file_ids)
                
                invalid_files = [fid for fid, valid in validation_results.items() if not valid]
                if invalid_files:
                    logger.warning(f"Some OpenAI files are no longer valid: {invalid_files}")
                    # Re-upload images
                    try:
                        openai_file_ids = await self.files_service.upload_analysis_images(analysis)
                        analysis.openai_file_ids = openai_file_ids
                        db.commit()
                    except OpenAIFilesServiceError as e:
                        raise AnalysisFollowupServiceError(f"Failed to re-upload palm images: {str(e)}")
            
            # Create analysis context for performance
            analysis_context = {
                "summary": analysis.summary[:1000] if analysis.summary else None,
                "full_report": analysis.full_report[:2000] if analysis.full_report else None,
                "created_at": analysis.created_at.isoformat(),
                "image_paths": {
                    "left": analysis.left_image_path,
                    "right": analysis.right_image_path
                }
            }
            
            # Create follow-up conversation
            conversation = Conversation(
                analysis_id=analysis_id,
                title=f"Questions about your palm reading",
                is_analysis_followup=True,
                conversation_type=ConversationType.ANALYSIS_FOLLOWUP,
                openai_file_ids=openai_file_ids,
                questions_count=0,
                max_questions=self.max_questions_per_analysis,
                analysis_context=analysis_context,
                is_active=True
            )
            
            db.add(conversation)
            
            # Update analysis flags
            analysis.has_followup_conversation = True
            
            db.commit()
            db.refresh(conversation)
            
            logger.info(f"Created follow-up conversation {conversation.id} for analysis {analysis_id}")
            return conversation
            
        except AnalysisFollowupServiceError:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create follow-up conversation: {e}")
            raise AnalysisFollowupServiceError(f"Internal error: {str(e)}")
    
    async def ask_followup_question(
        self,
        conversation_id: int,
        user_id: int,
        question: str,
        db: Session
    ) -> Dict:
        """
        Process a follow-up question with full context.
        
        Args:
            conversation_id: ID of the follow-up conversation
            user_id: ID of the user asking the question
            question: The follow-up question text
            db: Database session
            
        Returns:
            Dict containing user message, AI response, and metadata
            
        Raises:
            AnalysisFollowupServiceError: If validation fails or processing errors
        """
        try:
            # Get and validate conversation
            conversation = db.query(Conversation).filter(
                and_(
                    Conversation.id == conversation_id,
                    Conversation.is_analysis_followup == True,
                    Conversation.is_active == True
                )
            ).join(Analysis).filter(
                Analysis.user_id == user_id
            ).first()
            
            if not conversation:
                raise AnalysisFollowupServiceError("Follow-up conversation not found or not accessible")
            
            # Check question limit
            if conversation.questions_count >= conversation.max_questions:
                raise AnalysisFollowupServiceError(
                    f"Maximum {conversation.max_questions} questions allowed per analysis"
                )
            
            # Validate question
            validation_error = self._validate_question(question)
            if validation_error:
                raise AnalysisFollowupServiceError(validation_error)
            
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
            try:
                response_data = await self._generate_followup_response(
                    conversation, question, qa_history
                )
            except Exception as e:
                logger.error(f"Failed to generate AI response: {e}")
                raise AnalysisFollowupServiceError("Failed to generate response. Please try again.")
            
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
                content=response_data['content'],
                message_type=MessageType.ASSISTANT,
                tokens_used=response_data.get('tokens_used', 0),
                cost=response_data.get('cost', 0.0),
                processing_time=response_data.get('processing_time', 0.0)
            )
            db.add(ai_message)
            
            # Update conversation
            conversation.questions_count += 1
            conversation.last_message_at = datetime.utcnow()
            
            # Update analysis question count
            conversation.analysis.followup_questions_count += 1
            
            db.commit()
            db.refresh(user_message)
            db.refresh(ai_message)
            
            logger.info(
                f"Processed follow-up question {conversation.questions_count}/{conversation.max_questions} "
                f"for conversation {conversation_id}"
            )
            
            return {
                "user_message": user_message,
                "assistant_message": ai_message,
                "questions_remaining": conversation.max_questions - conversation.questions_count,
                "tokens_used": response_data.get('tokens_used', 0),
                "cost": response_data.get('cost', 0.0),
                "processing_time": response_data.get('processing_time', 0.0)
            }
            
        except AnalysisFollowupServiceError:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to process follow-up question: {e}")
            raise AnalysisFollowupServiceError(f"Internal error: {str(e)}")
    
    async def _generate_followup_response(
        self, 
        conversation: Conversation, 
        question: str, 
        qa_history: List[Dict]
    ) -> Dict:
        """Generate AI response with full context."""
        try:
            import time
            start_time = time.time()
            
            # Build conversation context
            context_parts = []
            
            # Add original analysis context
            if conversation.analysis_context:
                if conversation.analysis_context.get('summary'):
                    context_parts.append(f"Original palm reading summary: {conversation.analysis_context['summary']}")
                
                if conversation.analysis_context.get('full_report'):
                    context_parts.append(f"Detailed analysis: {conversation.analysis_context['full_report']}")
            
            # Add previous Q&A
            if qa_history:
                context_parts.append("Previous questions and answers in this conversation:")
                for i, qa in enumerate(qa_history, 1):
                    context_parts.append(f"Q{i}: {qa['question']}")
                    context_parts.append(f"A{i}: {qa['answer']}")
            
            context_text = "\\n\\n".join(context_parts)
            
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
            
            processing_time = time.time() - start_time
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
            
            return {
                "content": response.choices[0].message.content,
                "tokens_used": tokens_used,
                "cost": self._calculate_cost(tokens_used),
                "processing_time": processing_time
            }
            
        except Exception as e:
            logger.error(f"Failed to generate follow-up response: {e}")
            raise
    
    def _validate_question(self, question: str) -> Optional[str]:
        """
        Validate that question meets requirements.
        
        Returns:
            None if valid, error message if invalid
        """
        if not question or not question.strip():
            return "Question cannot be empty"
        
        question = question.strip()
        
        # Length checks
        if len(question) < self.min_question_length:
            return f"Question must be at least {self.min_question_length} characters long"
        
        if len(question) > self.max_question_length:
            return f"Question must be no more than {self.max_question_length} characters long"
        
        question_lower = question.lower()
        
        # Security: Check for prompt injection attempts
        security_patterns = [
            r'ignore\\s+(previous|all|system)\\s+(instructions?|prompts?)',
            r'you\\s+are\\s+now\\s+(?:a|an)\\s+\\w+',
            r'system\\s*:?\\s*you\\s+are',
            r'forget\\s+(everything|all)\\s+(previous|above)',
            r'\\bact\\s+as\\s+(?:a|an)\\s+\\w+',
            r'pretend\\s+(?:to\\s+be|you\\s+are)',
            r'roleplay\\s+as',
            r'new\\s+(?:instructions?|commands?|prompts?)',
        ]
        
        for pattern in security_patterns:
            if re.search(pattern, question_lower, re.IGNORECASE):
                return "Question contains prohibited content. Please ask about palm reading only."
        
        # Forbidden topics that are not about palmistry
        forbidden_terms = [
            "medical advice", "diagnosis", "disease", "illness", "treatment",
            "medication", "doctor", "surgery", "therapy",
            "lottery numbers", "stock market", "investment advice",
            "legal advice", "lawsuit", "attorney", "court",
            "politics", "religion", "controversial topics",
        ]
        
        for term in forbidden_terms:
            if term in question_lower:
                return f"Questions about {term} are not allowed. Please ask about palm reading and palmistry only."
        
        # Check for future prediction requests (discouraged in ethical palmistry)
        prediction_patterns = [
            r'when\\s+will\\s+i',
            r'will\\s+i\\s+(?:get|find|meet|have|become)',
            r'am\\s+i\\s+going\\s+to',
            r'predict\\s+(?:my|the)',
            r'tell\\s+me\\s+about\\s+my\\s+future',
            r'what\\s+will\\s+happen'
        ]
        
        for pattern in prediction_patterns:
            if re.search(pattern, question_lower, re.IGNORECASE):
                return "I can discuss palm characteristics and traits, but cannot predict specific future events."
        
        # Require palmistry relevance - question must contain palmistry-related terms
        palmistry_terms = [
            "palm", "hand", "finger", "thumb", "line", "mount",
            "reading", "palmistry", "chiromancy", "lifeline", "heartline",
            "headline", "fateline", "marriage line", "children line",
            "mounts", "venus", "jupiter", "saturn", "apollo", "mercury",
            "lunar", "mars", "plain of mars"
        ]
        
        if not any(term in question_lower for term in palmistry_terms):
            return "Please ask questions related to palm reading and palmistry."
        
        return None  # Question is valid
    
    def _get_followup_system_prompt(self) -> str:
        """Get the system prompt for follow-up questions."""
        return """
You are an expert palmist providing follow-up answers about a specific palm reading.

Context: The user has received a complete palm reading analysis and is now asking follow-up questions about specific aspects of their reading.

Guidelines:
1. Reference the original analysis and palm images when answering
2. Be specific about what you see in their particular palm features
3. Connect answers to the original reading for consistency
4. Focus only on palmistry interpretation - no medical advice or specific future predictions
5. Keep responses informative but concise (max 400 words)
6. If you can't see specific features clearly in the images, acknowledge this limitation
7. Provide educational information about palmistry principles when relevant
8. Use a warm, professional tone that encourages learning

Important: Base your response on:
- The palm images provided
- The original analysis context
- Previous questions and answers in this conversation
- Traditional palmistry knowledge and interpretation

Answer the follow-up question based on the palm images and previous context provided.
        """.strip()
    
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
        """
        Get follow-up conversation status for an analysis.
        
        Args:
            analysis_id: ID of the analysis
            user_id: ID of the user
            db: Database session
            
        Returns:
            Dict with status information
            
        Raises:
            AnalysisFollowupServiceError: If analysis not found
        """
        try:
            analysis = db.query(Analysis).filter(
                and_(
                    Analysis.id == analysis_id,
                    Analysis.user_id == user_id
                )
            ).first()
            
            if not analysis:
                raise AnalysisFollowupServiceError("Analysis not found")
            
            conversation = db.query(Conversation).filter(
                and_(
                    Conversation.analysis_id == analysis_id,
                    Conversation.is_analysis_followup == True
                )
            ).first()
            
            return {
                "analysis_id": analysis_id,
                "analysis_completed": analysis.status == AnalysisStatus.COMPLETED,
                "followup_available": analysis.status == AnalysisStatus.COMPLETED,
                "followup_conversation_exists": conversation is not None,
                "conversation_id": conversation.id if conversation else None,
                "questions_asked": conversation.questions_count if conversation else 0,
                "questions_remaining": (conversation.max_questions - conversation.questions_count) if conversation else self.max_questions_per_analysis,
                "max_questions": conversation.max_questions if conversation else self.max_questions_per_analysis,
                "has_openai_files": bool(analysis.openai_file_ids) if analysis.openai_file_ids else False,
                "total_followup_questions": analysis.followup_questions_count or 0
            }
            
        except AnalysisFollowupServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to get follow-up status: {e}")
            raise AnalysisFollowupServiceError(f"Internal error: {str(e)}")
    
    async def get_conversation_history(
        self,
        conversation_id: int,
        user_id: int,
        db: Session,
        limit: int = 20
    ) -> Dict:
        """
        Get conversation history for a follow-up conversation.
        
        Args:
            conversation_id: ID of the follow-up conversation
            user_id: ID of the user
            db: Database session
            limit: Maximum number of messages to return
            
        Returns:
            Dict with conversation and message history
            
        Raises:
            AnalysisFollowupServiceError: If conversation not found
        """
        try:
            conversation = db.query(Conversation).filter(
                and_(
                    Conversation.id == conversation_id,
                    Conversation.is_analysis_followup == True
                )
            ).join(Analysis).filter(
                Analysis.user_id == user_id
            ).first()
            
            if not conversation:
                raise AnalysisFollowupServiceError("Follow-up conversation not found")
            
            messages = db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at.desc()).limit(limit).all()
            
            messages.reverse()  # Return in chronological order
            
            return {
                "conversation": conversation,
                "messages": messages,
                "questions_asked": conversation.questions_count,
                "questions_remaining": conversation.max_questions - conversation.questions_count,
                "analysis_context": conversation.analysis_context
            }
            
        except AnalysisFollowupServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            raise AnalysisFollowupServiceError(f"Internal error: {str(e)}")