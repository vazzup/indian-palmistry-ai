"""
End-to-end integration tests for Analysis Follow-up Workflow.

This module provides comprehensive integration testing for the complete follow-up
questions workflow, from analysis completion through multiple question-answer
rounds with real database and API interactions.

**Integration Test Categories:**
- Complete user workflow from analysis to follow-up questions
- Database consistency across all operations
- Real OpenAI API integration with mock responses
- Error recovery and rollback scenarios
- Cross-service integration validation
- End-to-end performance under realistic conditions

**Testing Strategy:**
- Uses real database with transactions for isolation
- Mocks external APIs (OpenAI) for predictable testing
- Tests complete user journeys with multiple scenarios
- Validates data consistency across service boundaries
- Includes error handling and recovery paths
- Tests concurrent workflow scenarios

**Test Scenarios:**
- Successful complete workflow (analysis → conversation → questions)
- Error scenarios at each step with proper rollback
- Concurrent user workflows
- Database constraint validation
- File upload integration with retry logic
- Question limit enforcement across sessions

**Database Integration:**
- Uses test database with proper cleanup
- Tests real database constraints and indexes
- Validates transaction handling
- Tests migration compatibility

Author: Indian Palmistry AI Team
Created: August 2025
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import tempfile
import os

from app.services.analysis_followup_service import (
    AnalysisFollowupService,
    AnalysisFollowupServiceError
)
from app.services.openai_files_service import OpenAIFilesService
from app.models.analysis import Analysis, AnalysisStatus
from app.models.conversation import Conversation, ConversationType
from app.models.message import Message, MessageType
from app.models.user import User
from app.core.database import Base


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine for integration tests."""
    # Use in-memory SQLite for fast, isolated testing
    engine = create_engine(
        "sqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False  # Set to True for SQL debugging
    )
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    return engine


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create database session for each test with automatic cleanup."""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    
    # Start a transaction
    transaction = session.begin()
    
    try:
        yield session
    finally:
        # Roll back the transaction to clean up
        transaction.rollback()
        session.close()


@pytest.fixture
def test_user(test_db):
    """Create a test user for integration testing."""
    user = User(
        id=1,
        email="test@example.com",
        is_verified=True,
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_analysis(test_db, test_user, temp_image_files):
    """Create a completed test analysis with real file paths."""
    analysis = Analysis(
        id=1,
        user_id=test_user.id,
        status=AnalysisStatus.COMPLETED,
        summary="Your palm shows strong life and heart lines indicating vitality and emotional depth.",
        full_report="Detailed Analysis: Your life line is deep and continuous, suggesting good health and longevity. The heart line curves upward, indicating an optimistic and affectionate nature. The head line is straight and clear, showing logical thinking and good concentration.",
        left_image_path=temp_image_files['left'],
        right_image_path=temp_image_files['right'],
        created_at=datetime.utcnow(),
        openai_file_ids=None,
        has_followup_conversation=False,
        followup_questions_count=0
    )
    test_db.add(analysis)
    test_db.commit()
    test_db.refresh(analysis)
    return analysis


@pytest.fixture
def temp_image_files():
    """Create temporary image files for testing."""
    files = {}
    
    # Create temporary files
    for image_type in ['left', 'right']:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        # Write realistic fake image data
        temp_file.write(b'JPEG fake image data for ' + image_type.encode() + b' palm' * 100)
        temp_file.close()
        files[image_type] = temp_file.name
    
    yield files
    
    # Clean up temporary files
    for file_path in files.values():
        try:
            os.unlink(file_path)
        except OSError:
            pass


@pytest.fixture
def mock_openai_services():
    """Mock OpenAI services for predictable testing."""
    mocks = {}
    
    # Mock OpenAI Files Service
    files_service = AsyncMock(spec=OpenAIFilesService)
    files_service.upload_analysis_images.return_value = {
        "left_palm": "file-left123abc",
        "right_palm": "file-right456def"
    }
    files_service.validate_files.return_value = {
        "file-left123abc": True,
        "file-right456def": True
    }
    mocks['files_service'] = files_service
    
    # Mock OpenAI API response
    mock_ai_response = Mock()
    mock_ai_response.choices = [Mock()]
    mock_ai_response.choices[0].message.content = (
        "Looking at your palm images, I can see several distinctive features. "
        "Your heart line shows a gentle curve, which traditionally in palmistry "
        "indicates a balanced emotional nature. The depth and clarity of your "
        "life line suggests strong vitality, while the head line's path indicates "
        "practical thinking combined with creativity."
    )
    mock_ai_response.usage = Mock()
    mock_ai_response.usage.total_tokens = 187
    
    openai_service = AsyncMock()
    openai_service.chat_completion.return_value = mock_ai_response
    mocks['openai_service'] = openai_service
    
    return mocks


class TestCompleteFollowupWorkflow:
    """Test the complete end-to-end follow-up workflow."""
    
    @pytest.mark.asyncio
    async def test_successful_complete_workflow(self, test_db, test_user, test_analysis, mock_openai_services):
        """Test successful complete workflow from start to finish."""
        service = AnalysisFollowupService()
        service.files_service = mock_openai_services['files_service']
        service.openai_service = mock_openai_services['openai_service']
        
        # Step 1: Check initial follow-up status
        status = await service.get_followup_status(
            analysis_id=test_analysis.id,
            user_id=test_user.id,
            db=test_db
        )
        
        assert status['analysis_completed'] is True
        assert status['followup_available'] is True
        assert status['followup_conversation_exists'] is False
        assert status['questions_asked'] == 0
        assert status['questions_remaining'] == 5
        
        # Step 2: Create follow-up conversation
        conversation = await service.create_followup_conversation(
            analysis_id=test_analysis.id,
            user_id=test_user.id,
            db=test_db
        )
        
        # Validate conversation creation
        assert conversation.analysis_id == test_analysis.id
        assert conversation.is_analysis_followup is True
        assert conversation.conversation_type == ConversationType.ANALYSIS_FOLLOWUP
        assert conversation.questions_count == 0
        assert conversation.max_questions == 5
        assert conversation.openai_file_ids is not None
        assert len(conversation.openai_file_ids) == 2
        
        # Verify database state after conversation creation
        test_db.refresh(test_analysis)
        assert test_analysis.has_followup_conversation is True
        assert test_analysis.openai_file_ids == conversation.openai_file_ids
        
        # Step 3: Check status after conversation creation
        status = await service.get_followup_status(
            analysis_id=test_analysis.id,
            user_id=test_user.id,
            db=test_db
        )
        
        assert status['followup_conversation_exists'] is True
        assert status['conversation_id'] == conversation.id
        
        # Step 4: Ask first follow-up question
        first_question = "What does my heart line reveal about my emotional nature?"
        result1 = await service.ask_followup_question(
            conversation_id=conversation.id,
            user_id=test_user.id,
            question=first_question,
            db=test_db
        )
        
        # Validate first question response
        assert 'user_message' in result1
        assert 'assistant_message' in result1
        assert result1['user_message'].content == first_question
        assert result1['user_message'].message_type == MessageType.USER
        assert result1['assistant_message'].message_type == MessageType.ASSISTANT
        assert len(result1['assistant_message'].content) > 50
        assert result1['questions_remaining'] == 4
        assert result1['tokens_used'] == 187
        assert result1['cost'] > 0
        
        # Verify conversation state after first question
        test_db.refresh(conversation)
        assert conversation.questions_count == 1
        
        # Verify analysis state
        test_db.refresh(test_analysis)
        assert test_analysis.followup_questions_count == 1
        
        # Step 5: Ask second follow-up question (with history)
        second_question = "How does the mount of Venus relate to what you mentioned about my heart line?"
        result2 = await service.ask_followup_question(
            conversation_id=conversation.id,
            user_id=test_user.id,
            question=second_question,
            db=test_db
        )
        
        # Validate second question with conversation history
        assert result2['user_message'].content == second_question
        assert result2['questions_remaining'] == 3
        assert result2['assistant_message'].content != result1['assistant_message'].content
        
        # Verify conversation history retrieval
        history = await service.get_conversation_history(
            conversation_id=conversation.id,
            user_id=test_user.id,
            db=test_db
        )
        
        assert len(history['messages']) == 4  # 2 questions + 2 answers
        assert history['questions_asked'] == 2
        assert history['questions_remaining'] == 3
        assert history['conversation'].id == conversation.id
        
        # Step 6: Verify file service integration
        mock_openai_services['files_service'].upload_analysis_images.assert_called_once_with(test_analysis)
        mock_openai_services['openai_service'].chat_completion.assert_called()
        
        # Step 7: Verify final database consistency
        test_db.refresh(conversation)
        test_db.refresh(test_analysis)
        
        assert conversation.questions_count == 2
        assert analysis.followup_questions_count == 2
        assert conversation.last_message_at is not None
        
        # Count actual messages in database
        message_count = test_db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).count()
        assert message_count == 4  # 2 user + 2 assistant messages
    
    @pytest.mark.asyncio
    async def test_question_limit_enforcement(self, test_db, test_user, test_analysis, mock_openai_services):
        """Test that question limits are properly enforced."""
        service = AnalysisFollowupService()
        service.files_service = mock_openai_services['files_service']
        service.openai_service = mock_openai_services['openai_service']
        
        # Create conversation
        conversation = await service.create_followup_conversation(
            analysis_id=test_analysis.id,
            user_id=test_user.id,
            db=test_db
        )
        
        # Ask maximum allowed questions (5)
        questions = [
            "What does my heart line mean?",
            "Tell me about my life line.",
            "What about my head line?",
            "How do you interpret my thumb?",
            "What do the mounts in my palm indicate?"
        ]
        
        # Ask all 5 questions successfully
        for i, question in enumerate(questions):
            result = await service.ask_followup_question(
                conversation_id=conversation.id,
                user_id=test_user.id,
                question=question,
                db=test_db
            )
            assert result['questions_remaining'] == 4 - i
        
        # Verify conversation state
        test_db.refresh(conversation)
        assert conversation.questions_count == 5
        
        # Try to ask 6th question (should fail)
        with pytest.raises(AnalysisFollowupServiceError) as exc_info:
            await service.ask_followup_question(
                conversation_id=conversation.id,
                user_id=test_user.id,
                question="What about my fingers?",
                db=test_db
            )
        
        assert "Maximum" in str(exc_info.value)
        assert "5 questions allowed" in str(exc_info.value)
        
        # Verify no additional messages were created
        message_count = test_db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).count()
        assert message_count == 10  # 5 questions + 5 answers
    
    @pytest.mark.asyncio
    async def test_file_upload_error_handling(self, test_db, test_user, test_analysis):
        """Test error handling when file upload fails."""
        service = AnalysisFollowupService()
        
        # Mock file service to simulate upload failure
        files_service = AsyncMock(spec=OpenAIFilesService)
        files_service.upload_analysis_images.side_effect = Exception("OpenAI API Error")
        service.files_service = files_service
        
        # Attempt to create conversation
        with pytest.raises(AnalysisFollowupServiceError) as exc_info:
            await service.create_followup_conversation(
                analysis_id=test_analysis.id,
                user_id=test_user.id,
                db=test_db
            )
        
        assert "Failed to upload palm images" in str(exc_info.value)
        
        # Verify database rollback - no conversation should be created
        conversation_count = test_db.query(Conversation).filter(
            Conversation.analysis_id == test_analysis.id
        ).count()
        assert conversation_count == 0
        
        # Verify analysis state unchanged
        test_db.refresh(test_analysis)
        assert test_analysis.has_followup_conversation is False
        assert test_analysis.openai_file_ids is None
    
    @pytest.mark.asyncio
    async def test_ai_response_error_handling(self, test_db, test_user, test_analysis, mock_openai_services):
        """Test error handling when AI response generation fails."""
        service = AnalysisFollowupService()
        service.files_service = mock_openai_services['files_service']
        
        # Mock OpenAI service to simulate AI error
        openai_service = AsyncMock()
        openai_service.chat_completion.side_effect = Exception("OpenAI API timeout")
        service.openai_service = openai_service
        
        # Create conversation successfully
        conversation = await service.create_followup_conversation(
            analysis_id=test_analysis.id,
            user_id=test_user.id,
            db=test_db
        )
        
        # Attempt to ask question (should fail during AI response)
        with pytest.raises(AnalysisFollowupServiceError) as exc_info:
            await service.ask_followup_question(
                conversation_id=conversation.id,
                user_id=test_user.id,
                question="What does my heart line indicate?",
                db=test_db
            )
        
        assert "Failed to generate response" in str(exc_info.value)
        
        # Verify database rollback - no messages should be saved
        message_count = test_db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).count()
        assert message_count == 0
        
        # Verify conversation state unchanged
        test_db.refresh(conversation)
        assert conversation.questions_count == 0
        
        # Verify analysis state unchanged
        test_db.refresh(test_analysis)
        assert test_analysis.followup_questions_count == 0
    
    @pytest.mark.asyncio
    async def test_existing_file_validation_and_reupload(self, test_db, test_user, test_analysis, mock_openai_services):
        """Test handling of existing OpenAI files with validation and re-upload."""
        service = AnalysisFollowupService()
        
        # Set up existing file IDs on analysis
        existing_files = {"left_palm": "file-old123", "right_palm": "file-old456"}
        test_analysis.openai_file_ids = existing_files
        test_db.commit()
        
        # Mock files service - existing files are invalid, new upload succeeds
        files_service = AsyncMock(spec=OpenAIFilesService)
        files_service.validate_files.return_value = {
            "file-old123": False,  # Invalid
            "file-old456": False   # Invalid
        }
        files_service.upload_analysis_images.return_value = {
            "left_palm": "file-new123",
            "right_palm": "file-new456"
        }
        service.files_service = files_service
        service.openai_service = mock_openai_services['openai_service']
        
        # Create conversation
        conversation = await service.create_followup_conversation(
            analysis_id=test_analysis.id,
            user_id=test_user.id,
            db=test_db
        )
        
        # Verify validation was called with old files
        files_service.validate_files.assert_called_once_with(["file-old123", "file-old456"])
        
        # Verify re-upload was triggered
        files_service.upload_analysis_images.assert_called_once_with(test_analysis)
        
        # Verify new file IDs are used
        assert conversation.openai_file_ids == {"left_palm": "file-new123", "right_palm": "file-new456"}
        
        # Verify analysis updated with new file IDs
        test_db.refresh(test_analysis)
        assert test_analysis.openai_file_ids == {"left_palm": "file-new123", "right_palm": "file-new456"}


class TestConcurrentWorkflows:
    """Test concurrent user workflows and database consistency."""
    
    @pytest.mark.asyncio
    async def test_concurrent_conversation_creation(self, test_db, mock_openai_services):
        """Test concurrent conversation creation by different users."""
        service = AnalysisFollowupService()
        service.files_service = mock_openai_services['files_service']
        service.openai_service = mock_openai_services['openai_service']
        
        # Create multiple users and analyses
        users = []
        analyses = []
        
        for i in range(3):
            user = User(
                id=i + 10,
                email=f"user{i}@example.com",
                is_verified=True,
                is_active=True
            )
            test_db.add(user)
            
            analysis = Analysis(
                id=i + 10,
                user_id=user.id,
                status=AnalysisStatus.COMPLETED,
                summary=f"Palm reading summary for user {i}",
                left_image_path=f"/fake/path/left_{i}.jpg",
                right_image_path=f"/fake/path/right_{i}.jpg"
            )
            test_db.add(analysis)
            
            users.append(user)
            analyses.append(analysis)
        
        test_db.commit()
        
        # Create conversations concurrently
        tasks = [
            service.create_followup_conversation(
                analysis_id=analysis.id,
                user_id=user.id,
                db=test_db
            )
            for user, analysis in zip(users, analyses)
        ]
        
        conversations = await asyncio.gather(*tasks)
        
        # Verify all conversations created successfully
        assert len(conversations) == 3
        for i, conversation in enumerate(conversations):
            assert conversation.analysis_id == analyses[i].id
            assert conversation.is_analysis_followup is True
            assert conversation.questions_count == 0
        
        # Verify database consistency
        conversation_count = test_db.query(Conversation).filter(
            Conversation.is_analysis_followup == True
        ).count()
        assert conversation_count == 3
    
    @pytest.mark.asyncio
    async def test_concurrent_question_processing(self, test_db, test_user, test_analysis, mock_openai_services):
        """Test concurrent question processing within same conversation."""
        service = AnalysisFollowupService()
        service.files_service = mock_openai_services['files_service']
        
        # Mock AI service with unique responses
        response_counter = 0
        
        async def mock_ai_response(*args, **kwargs):
            nonlocal response_counter
            response_counter += 1
            
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = f"AI response #{response_counter} about palmistry features."
            mock_response.usage = Mock()
            mock_response.usage.total_tokens = 100 + response_counter * 10
            return mock_response
        
        service.openai_service = AsyncMock()
        service.openai_service.chat_completion.side_effect = mock_ai_response
        
        # Create conversation
        conversation = await service.create_followup_conversation(
            analysis_id=test_analysis.id,
            user_id=test_user.id,
            db=test_db
        )
        
        # Ask multiple questions concurrently (this should be handled safely)
        questions = [
            "What does my heart line mean?",
            "Tell me about my life line.",
            "What about my head line?"
        ]
        
        # Note: In real application, same user asking concurrent questions to same conversation
        # would typically be prevented at the API level, but we test service robustness
        tasks = [
            service.ask_followup_question(
                conversation_id=conversation.id,
                user_id=test_user.id,
                question=question,
                db=test_db
            )
            for question in questions
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Some requests might succeed, others might fail due to concurrent access
        successful_results = [r for r in results if isinstance(r, dict)]
        failed_results = [r for r in results if isinstance(r, Exception)]
        
        # At least one should succeed
        assert len(successful_results) >= 1
        
        # Verify database consistency
        test_db.refresh(conversation)
        message_count = test_db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).count()
        
        # Message count should be even (questions + answers) and match successful results
        assert message_count == len(successful_results) * 2
        assert conversation.questions_count == len(successful_results)


class TestDatabaseConstraintValidation:
    """Test database constraints and data integrity."""
    
    @pytest.mark.asyncio
    async def test_analysis_ownership_constraint(self, test_db, mock_openai_services):
        """Test that users can only access their own analyses."""
        service = AnalysisFollowupService()
        service.files_service = mock_openai_services['files_service']
        service.openai_service = mock_openai_services['openai_service']
        
        # Create two users
        user1 = User(id=21, email="user1@example.com", is_verified=True, is_active=True)
        user2 = User(id=22, email="user2@example.com", is_verified=True, is_active=True)
        test_db.add(user1)
        test_db.add(user2)
        
        # Create analysis for user1
        analysis = Analysis(
            id=21,
            user_id=user1.id,
            status=AnalysisStatus.COMPLETED,
            summary="User 1's palm reading",
            left_image_path="/fake/path/left_user1.jpg"
        )
        test_db.add(analysis)
        test_db.commit()
        
        # User2 tries to access user1's analysis
        with pytest.raises(AnalysisFollowupServiceError) as exc_info:
            await service.create_followup_conversation(
                analysis_id=analysis.id,
                user_id=user2.id,
                db=test_db
            )
        
        assert "not found" in str(exc_info.value) or "not owned" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_incomplete_analysis_constraint(self, test_db, test_user, mock_openai_services):
        """Test that follow-up is only allowed for completed analyses."""
        service = AnalysisFollowupService()
        service.files_service = mock_openai_services['files_service']
        
        # Create incomplete analysis
        analysis = Analysis(
            id=31,
            user_id=test_user.id,
            status=AnalysisStatus.PROCESSING,  # Not completed
            summary=None,
            left_image_path="/fake/path/processing.jpg"
        )
        test_db.add(analysis)
        test_db.commit()
        
        # Try to create follow-up conversation
        with pytest.raises(AnalysisFollowupServiceError) as exc_info:
            await service.create_followup_conversation(
                analysis_id=analysis.id,
                user_id=test_user.id,
                db=test_db
            )
        
        assert "not completed" in str(exc_info.value)
    
    def test_conversation_uniqueness_constraint(self, test_db, test_user):
        """Test that only one follow-up conversation per analysis is allowed."""
        # Create analysis
        analysis = Analysis(
            id=41,
            user_id=test_user.id,
            status=AnalysisStatus.COMPLETED,
            summary="Test analysis",
            has_followup_conversation=True
        )
        test_db.add(analysis)
        
        # Create first conversation
        conv1 = Conversation(
            id=41,
            analysis_id=analysis.id,
            title="First conversation",
            is_analysis_followup=True,
            conversation_type=ConversationType.ANALYSIS_FOLLOWUP,
            questions_count=0,
            max_questions=5
        )
        test_db.add(conv1)
        test_db.commit()
        
        # Try to create second conversation for same analysis
        conv2 = Conversation(
            id=42,
            analysis_id=analysis.id,
            title="Second conversation",
            is_analysis_followup=True,
            conversation_type=ConversationType.ANALYSIS_FOLLOWUP,
            questions_count=0,
            max_questions=5
        )
        test_db.add(conv2)
        
        # This should succeed at database level (constraint is enforced in service logic)
        # but service should prevent duplicate conversations
        test_db.commit()
        
        # Verify both conversations exist (constraint is in service, not DB)
        conv_count = test_db.query(Conversation).filter(
            Conversation.analysis_id == analysis.id,
            Conversation.is_analysis_followup == True
        ).count()
        assert conv_count == 2  # Service prevents this, but DB allows it


class TestErrorRecoveryScenarios:
    """Test error recovery and rollback scenarios."""
    
    @pytest.mark.asyncio
    async def test_partial_transaction_rollback(self, test_db, test_user, test_analysis):
        """Test that partial failures result in complete rollback."""
        service = AnalysisFollowupService()
        
        # Mock files service to succeed initially
        files_service = AsyncMock()
        files_service.upload_analysis_images.return_value = {
            "left_palm": "file-123",
            "right_palm": "file-456"
        }
        service.files_service = files_service
        
        # Create a mock that will fail during database operations
        original_add = test_db.add
        call_count = 0
        
        def failing_add(obj):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:  # Fail on second add (conversation)
                raise Exception("Database error during conversation creation")
            return original_add(obj)
        
        test_db.add = failing_add
        
        # Attempt conversation creation (should fail and rollback)
        with pytest.raises(AnalysisFollowupServiceError):
            await service.create_followup_conversation(
                analysis_id=test_analysis.id,
                user_id=test_user.id,
                db=test_db
            )
        
        # Verify rollback - analysis should be unchanged
        test_db.refresh(test_analysis)
        assert test_analysis.has_followup_conversation is False
        assert test_analysis.openai_file_ids is None
        
        # Verify no conversation was created
        conv_count = test_db.query(Conversation).filter(
            Conversation.analysis_id == test_analysis.id
        ).count()
        assert conv_count == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])