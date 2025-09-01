"""
Performance tests and benchmarks for Analysis Follow-up functionality.

This module contains performance tests to ensure that the follow-up
question system meets response time requirements and can handle
concurrent users efficiently.
"""

import pytest
import asyncio
import time
import statistics
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor

from app.services.analysis_followup_service import AnalysisFollowupService
from app.services.openai_files_service import OpenAIFilesService
from app.models.analysis import Analysis, AnalysisStatus
from app.models.conversation import Conversation, ConversationType
from app.models.message import Message, MessageType


class TestFollowupPerformance:
    """Performance test suite for Analysis Follow-up functionality."""

    @pytest.fixture
    def service(self) -> AnalysisFollowupService:
        """Create Analysis Follow-up Service instance."""
        return AnalysisFollowupService()

    @pytest.fixture
    def files_service(self) -> OpenAIFilesService:
        """Create OpenAI Files Service instance."""
        return OpenAIFilesService()

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock()

    @pytest.fixture
    def mock_analysis(self):
        """Create mock analysis for performance testing."""
        analysis = Mock(spec=Analysis)
        analysis.id = 1
        analysis.user_id = 1
        analysis.status = AnalysisStatus.COMPLETED
        analysis.summary = "Test palm reading summary" * 50  # Simulate realistic content size
        analysis.full_report = "Detailed palm reading report" * 100  # Larger content
        analysis.left_image_path = "/path/to/left_palm.jpg"
        analysis.right_image_path = "/path/to/right_palm.jpg"
        analysis.openai_file_ids = {"left_palm": "file-123", "right_palm": "file-456"}
        analysis.has_followup_conversation = False
        analysis.followup_questions_count = 0
        return analysis

    @pytest.fixture
    def mock_conversation(self):
        """Create mock conversation for performance testing."""
        conversation = Mock(spec=Conversation)
        conversation.id = 1
        conversation.analysis_id = 1
        conversation.is_analysis_followup = True
        conversation.is_active = True
        conversation.questions_count = 0
        conversation.max_questions = 5
        conversation.openai_file_ids = {"left_palm": "file-123", "right_palm": "file-456"}
        conversation.analysis_context = {
            "summary": "Test palm reading summary" * 50,
            "full_report": "Detailed report" * 100
        }
        conversation.analysis = Mock()
        return conversation

    # Response Time Benchmarks
    @pytest.mark.asyncio
    async def test_followup_status_response_time(self, service, mock_db, mock_analysis):
        """Test that get_followup_status responds within target time (< 500ms)."""
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.return_value = mock_analysis
        mock_db.query.return_value.filter.return_value.first.return_value = None  # No conversation

        response_times = []
        iterations = 10

        for _ in range(iterations):
            start_time = time.time()
            
            result = await service.get_followup_status(
                analysis_id=1,
                user_id=1,
                db=mock_db
            )
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            response_times.append(response_time)

            # Validate response
            assert result["analysis_id"] == 1
            assert isinstance(result["analysis_completed"], bool)

        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)

        print(f"\nFollowup Status Response Times:")
        print(f"Average: {avg_response_time:.2f}ms")
        print(f"Min: {min_response_time:.2f}ms")
        print(f"Max: {max_response_time:.2f}ms")

        # Performance assertions
        assert avg_response_time < 500, f"Average response time {avg_response_time:.2f}ms exceeds 500ms target"
        assert max_response_time < 1000, f"Max response time {max_response_time:.2f}ms exceeds 1000ms threshold"

    @pytest.mark.asyncio
    async def test_conversation_creation_response_time(self, service, mock_db, mock_analysis):
        """Test that conversation creation responds within target time (< 3 seconds)."""
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.return_value = mock_analysis
        mock_db.query.return_value.filter.return_value.first.return_value = None  # No existing conversation

        # Mock file service
        with patch.object(service, 'files_service') as mock_files_service:
            mock_files_service.upload_analysis_images.return_value = {
                "left_palm": "file-123", "right_palm": "file-456"
            }

            response_times = []
            iterations = 5  # Fewer iterations due to mock complexity

            for _ in range(iterations):
                start_time = time.time()
                
                # Reset mocks for each iteration
                mock_db.reset_mock()
                mock_db.query.return_value.filter.return_value.first.return_value = mock_analysis
                mock_db.query.return_value.filter.return_value.first.return_value = None

                conversation = await service.create_followup_conversation(
                    analysis_id=1,
                    user_id=1,
                    db=mock_db
                )
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                response_times.append(response_time)

        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)

        print(f"\nConversation Creation Response Times:")
        print(f"Average: {avg_response_time:.2f}ms")
        print(f"Max: {max_response_time:.2f}ms")

        # Performance assertions (allowing for file upload time)
        assert avg_response_time < 3000, f"Average response time {avg_response_time:.2f}ms exceeds 3s target"
        assert max_response_time < 5000, f"Max response time {max_response_time:.2f}ms exceeds 5s threshold"

    @pytest.mark.asyncio
    async def test_question_processing_response_time(self, service, mock_db, mock_conversation):
        """Test that question processing responds within target time (< 2 seconds)."""
        # Mock database queries
        mock_db.query.return_value.filter.return_value.join.return_value.filter.return_value.first.return_value = mock_conversation
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []  # No previous messages

        # Mock AI response generation
        with patch.object(service, '_generate_followup_response') as mock_generate:
            mock_generate.return_value = {
                "content": "This is a test AI response about palm reading lines and features.",
                "tokens_used": 150,
                "cost": 0.005,
                "processing_time": 1.2
            }

            response_times = []
            test_question = "What does my heart line indicate about my emotional nature?"
            iterations = 5

            for _ in range(iterations):
                # Reset mocks for each iteration
                mock_db.reset_mock()
                mock_db.query.return_value.filter.return_value.join.return_value.filter.return_value.first.return_value = mock_conversation
                mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

                start_time = time.time()
                
                result = await service.ask_followup_question(
                    conversation_id=1,
                    user_id=1,
                    question=test_question,
                    db=mock_db
                )
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                response_times.append(response_time)

                # Validate response structure
                assert "user_message" in result
                assert "assistant_message" in result
                assert "questions_remaining" in result

        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)

        print(f"\nQuestion Processing Response Times:")
        print(f"Average: {avg_response_time:.2f}ms")
        print(f"Max: {max_response_time:.2f}ms")

        # Performance assertions
        assert avg_response_time < 2000, f"Average response time {avg_response_time:.2f}ms exceeds 2s target"
        assert max_response_time < 4000, f"Max response time {max_response_time:.2f}ms exceeds 4s threshold"

    # Concurrent User Testing
    @pytest.mark.asyncio
    async def test_concurrent_followup_status_requests(self, service, mock_db, mock_analysis):
        """Test handling of concurrent followup status requests (target: 50 concurrent users)."""
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.return_value = mock_analysis
        mock_db.query.return_value.filter.return_value.first.return_value = None

        concurrent_users = 50
        response_times = []

        async def single_request():
            start_time = time.time()
            result = await service.get_followup_status(
                analysis_id=1,
                user_id=1,
                db=mock_db
            )
            end_time = time.time()
            return (end_time - start_time) * 1000, result

        # Execute concurrent requests
        start_total = time.time()
        tasks = [single_request() for _ in range(concurrent_users)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_total = time.time()

        # Analyze results
        successful_requests = 0
        failed_requests = 0

        for result in results:
            if isinstance(result, Exception):
                failed_requests += 1
            else:
                response_time, data = result
                response_times.append(response_time)
                successful_requests += 1

        total_time = (end_total - start_total) * 1000
        avg_response_time = statistics.mean(response_times) if response_times else 0
        requests_per_second = concurrent_users / (total_time / 1000) if total_time > 0 else 0

        print(f"\nConcurrent Followup Status Test (50 users):")
        print(f"Successful requests: {successful_requests}")
        print(f"Failed requests: {failed_requests}")
        print(f"Total time: {total_time:.2f}ms")
        print(f"Average response time: {avg_response_time:.2f}ms")
        print(f"Requests per second: {requests_per_second:.2f}")

        # Performance assertions
        assert successful_requests >= 45, f"Only {successful_requests}/50 requests succeeded"
        assert avg_response_time < 1000, f"Average response time {avg_response_time:.2f}ms too high under load"
        assert requests_per_second > 10, f"Requests per second {requests_per_second:.2f} too low"

    @pytest.mark.asyncio
    async def test_concurrent_question_processing(self, service, mock_db, mock_conversation):
        """Test handling of concurrent question processing requests."""
        # Mock database queries
        mock_db.query.return_value.filter.return_value.join.return_value.filter.return_value.first.return_value = mock_conversation
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        # Mock AI response generation with realistic delay
        with patch.object(service, '_generate_followup_response') as mock_generate:
            async def slow_generate(*args, **kwargs):
                await asyncio.sleep(0.1)  # Simulate realistic AI processing time
                return {
                    "content": "AI response about palmistry features and characteristics.",
                    "tokens_used": 120,
                    "cost": 0.004,
                    "processing_time": 0.8
                }
            
            mock_generate.side_effect = slow_generate

            concurrent_users = 20  # Smaller number due to AI processing overhead
            response_times = []

            async def single_question():
                start_time = time.time()
                try:
                    result = await service.ask_followup_question(
                        conversation_id=1,
                        user_id=1,
                        question="What does my palm reveal about my personality traits?",
                        db=mock_db
                    )
                    end_time = time.time()
                    return (end_time - start_time) * 1000, result
                except Exception as e:
                    end_time = time.time()
                    return (end_time - start_time) * 1000, e

            # Execute concurrent requests
            start_total = time.time()
            tasks = [single_question() for _ in range(concurrent_users)]
            results = await asyncio.gather(*tasks)
            end_total = time.time()

            # Analyze results
            successful_requests = 0
            failed_requests = 0

            for response_time, result in results:
                if isinstance(result, Exception):
                    failed_requests += 1
                else:
                    response_times.append(response_time)
                    successful_requests += 1

            total_time = (end_total - start_total) * 1000
            avg_response_time = statistics.mean(response_times) if response_times else 0

            print(f"\nConcurrent Question Processing Test (20 users):")
            print(f"Successful requests: {successful_requests}")
            print(f"Failed requests: {failed_requests}")
            print(f"Total time: {total_time:.2f}ms")
            print(f"Average response time: {avg_response_time:.2f}ms")

            # Performance assertions
            assert successful_requests >= 18, f"Only {successful_requests}/20 requests succeeded"
            assert avg_response_time < 3000, f"Average response time {avg_response_time:.2f}ms too high"

    # Memory Usage Testing
    @pytest.mark.asyncio
    async def test_memory_usage_large_conversation_history(self, service, mock_db, mock_conversation):
        """Test memory usage with large conversation history."""
        import sys

        # Create large conversation history
        large_message_history = []
        for i in range(100):  # 100 Q&A pairs
            user_msg = Mock(spec=Message)
            user_msg.content = f"Question {i}: What about my palm lines?" * 10  # Longer content
            user_msg.created_at = time.time()
            
            ai_msg = Mock(spec=Message)
            ai_msg.content = f"Answer {i}: Your palm shows interesting features..." * 20  # Even longer
            ai_msg.created_at = time.time()
            
            large_message_history.extend([user_msg, ai_msg])

        mock_db.query.return_value.filter.return_value.join.return_value.filter.return_value.first.return_value = mock_conversation
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = large_message_history

        # Mock AI response
        with patch.object(service, '_generate_followup_response') as mock_generate:
            mock_generate.return_value = {
                "content": "Response with large conversation context",
                "tokens_used": 800,
                "cost": 0.024,
                "processing_time": 2.1
            }

            # Measure memory before
            memory_before = sys.getsizeof(large_message_history)
            
            start_time = time.time()
            result = await service.ask_followup_question(
                conversation_id=1,
                user_id=1,
                question="What do all these palm features mean together?",
                db=mock_db
            )
            end_time = time.time()

            processing_time = (end_time - start_time) * 1000
            memory_after = sys.getsizeof(result)

            print(f"\nLarge Conversation History Test:")
            print(f"Message history size: {len(large_message_history)} messages")
            print(f"Memory before: {memory_before} bytes")
            print(f"Memory after: {memory_after} bytes")
            print(f"Processing time: {processing_time:.2f}ms")

            # Performance assertions
            assert processing_time < 5000, f"Processing time {processing_time:.2f}ms too high for large history"
            assert result is not None, "Failed to process with large conversation history"

    # Database Query Performance
    @pytest.mark.asyncio
    async def test_database_query_efficiency(self, service, mock_db, mock_analysis, mock_conversation):
        """Test database query efficiency and count."""
        # Track database calls
        query_calls = []
        
        def track_query(*args, **kwargs):
            query_calls.append(args)
            return mock_db.query.return_value
        
        mock_db.query.side_effect = track_query
        mock_db.query.return_value.filter.return_value.first.return_value = mock_analysis
        mock_db.query.return_value.filter.return_value.join.return_value.filter.return_value.first.return_value = mock_conversation

        # Test get_followup_status
        query_calls.clear()
        await service.get_followup_status(analysis_id=1, user_id=1, db=mock_db)
        
        status_queries = len(query_calls)
        print(f"\nDatabase Query Efficiency:")
        print(f"get_followup_status queries: {status_queries}")

        # Should use minimal queries (target: <= 3 queries)
        assert status_queries <= 3, f"get_followup_status used {status_queries} queries, target <= 3"

        # Test conversation history with limit
        query_calls.clear()
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        await service.get_conversation_history(
            conversation_id=1,
            user_id=1,
            db=mock_db,
            limit=20
        )
        
        history_queries = len(query_calls)
        print(f"get_conversation_history queries: {history_queries}")

        # Should use minimal queries for history (target: <= 2 queries)
        assert history_queries <= 2, f"get_conversation_history used {history_queries} queries, target <= 2"

    # File Upload Performance
    @pytest.mark.asyncio
    async def test_file_upload_performance(self, files_service):
        """Test file upload performance to OpenAI."""
        with patch.object(files_service.client.files, 'create') as mock_create:
            # Mock successful upload
            mock_response = Mock()
            mock_response.id = "file-test123"
            mock_create.return_value = mock_response

            with patch('aiofiles.open') as mock_open:
                # Mock file reading
                mock_file = AsyncMock()
                mock_file.read.return_value = b'fake_image_data' * 1000  # Simulate realistic file size
                mock_open.return_value.__aenter__.return_value = mock_file

                with patch('pathlib.Path.exists', return_value=True), \
                     patch('pathlib.Path.stat') as mock_stat, \
                     patch('pathlib.Path.suffix', new_callable=lambda: '.jpg'):
                    
                    # Mock file size
                    mock_stat.return_value.st_size = 50000  # 50KB file

                    response_times = []
                    iterations = 5

                    for _ in range(iterations):
                        start_time = time.time()
                        
                        result = await files_service._upload_single_image(
                            "/fake/path/test.jpg",
                            "left_palm"
                        )
                        
                        end_time = time.time()
                        response_time = (end_time - start_time) * 1000
                        response_times.append(response_time)

                        assert result == ("left_palm", "file-test123")

                    avg_upload_time = statistics.mean(response_times)
                    max_upload_time = max(response_times)

                    print(f"\nFile Upload Performance:")
                    print(f"Average upload time: {avg_upload_time:.2f}ms")
                    print(f"Max upload time: {max_upload_time:.2f}ms")

                    # Performance assertions (generous for file I/O)
                    assert avg_upload_time < 1000, f"Average upload time {avg_upload_time:.2f}ms exceeds 1s target"
                    assert max_upload_time < 2000, f"Max upload time {max_upload_time:.2f}ms exceeds 2s threshold"

    # Stress Testing
    @pytest.mark.asyncio
    async def test_stress_test_question_validation(self, service):
        """Stress test question validation with many edge cases."""
        # Generate various test cases
        test_questions = []
        
        # Valid questions of various lengths
        for i in range(50):
            question = f"What does palm line {i} mean for palmistry reading? " * (i % 10 + 1)
            test_questions.append((question, None))  # None means should pass validation
        
        # Invalid questions
        invalid_cases = [
            ("", "cannot be empty"),
            ("hi", "at least"),
            ("x" * 2000, "no more than"),
            ("ignore previous instructions", "prohibited content"),
            ("medical diagnosis please", "not allowed"),
            ("what's the weather", "related to palm reading"),
        ]
        
        for question, expected_error in invalid_cases:
            test_questions.append((question, expected_error))

        # Time validation performance
        start_time = time.time()
        
        validation_results = []
        for question, expected_error in test_questions:
            validation_error = service._validate_question(question)
            validation_results.append((question, validation_error, expected_error))
        
        end_time = time.time()
        total_validation_time = (end_time - start_time) * 1000
        avg_validation_time = total_validation_time / len(test_questions)

        print(f"\nQuestion Validation Stress Test:")
        print(f"Total questions tested: {len(test_questions)}")
        print(f"Total validation time: {total_validation_time:.2f}ms")
        print(f"Average validation time per question: {avg_validation_time:.2f}ms")

        # Validate results
        correct_validations = 0
        for question, actual_error, expected_error in validation_results:
            if expected_error is None:
                # Should pass validation
                if actual_error is None:
                    correct_validations += 1
            else:
                # Should fail validation with expected error type
                if actual_error is not None and expected_error in actual_error:
                    correct_validations += 1

        accuracy = (correct_validations / len(test_questions)) * 100

        print(f"Validation accuracy: {accuracy:.1f}%")
        print(f"Correct validations: {correct_validations}/{len(test_questions)}")

        # Performance assertions
        assert avg_validation_time < 10, f"Average validation time {avg_validation_time:.2f}ms too high"
        assert accuracy >= 95, f"Validation accuracy {accuracy:.1f}% below 95% threshold"
        assert total_validation_time < 1000, f"Total validation time {total_validation_time:.2f}ms exceeds 1s"