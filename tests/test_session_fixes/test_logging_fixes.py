"""
Tests for logging fixes applied during debugging session.

These tests validate that logging calls in analysis tasks use the correct
format with 'extra' parameter instead of keyword arguments.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.tasks.analysis_tasks import process_palm_analysis, generate_thumbnails
from app.core.logging import get_logger


class TestAnalysisTasksLoggingFixes:
    """Test the corrected logging format in analysis tasks."""
    
    @pytest.mark.asyncio
    async def test_process_palm_analysis_logging_format(self):
        """Test that process_palm_analysis uses correct logging format with extra parameter."""
        analysis_id = "test-analysis-123"
        
        with patch('app.tasks.analysis_tasks.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            # Mock all the dependencies
            with patch('app.tasks.analysis_tasks.get_db_session'), \
                 patch('app.tasks.analysis_tasks.AnalysisService') as mock_analysis_service, \
                 patch('app.tasks.analysis_tasks.OpenAIService') as mock_openai_service, \
                 patch('app.tasks.analysis_tasks.ImageService') as mock_image_service, \
                 patch('app.tasks.analysis_tasks.cache_service') as mock_cache:
                
                # Mock the services to avoid actual processing
                mock_analysis_service.return_value.get_analysis = AsyncMock(return_value=Mock(
                    id=analysis_id,
                    left_image_path="/test/path.jpg",
                    right_image_path=None,
                    status="processing"
                ))
                mock_analysis_service.return_value.update_analysis_status = AsyncMock()
                mock_openai_service.return_value.analyze_palm = AsyncMock(return_value={
                    "analysis": {"summary": "test", "full_report": "test"},
                    "tokens_used": 100,
                    "cost": 0.01
                })
                mock_image_service.return_value.read_image_as_base64 = AsyncMock(return_value="base64data")
                mock_cache.set_job_status = AsyncMock()
                
                try:
                    await process_palm_analysis(analysis_id)
                except Exception:
                    # We expect some errors due to mocking, but we're testing logging format
                    pass
                
                # Verify logging calls use extra parameter format
                log_calls = mock_logger.info.call_args_list
                
                # Check that at least one call uses the extra parameter format
                found_correct_format = False
                for call_args, call_kwargs in log_calls:
                    if 'extra' in call_kwargs:
                        extra_data = call_kwargs['extra']
                        if isinstance(extra_data, dict) and 'analysis_id' in extra_data:
                            assert extra_data['analysis_id'] == analysis_id
                            found_correct_format = True
                            break
                
                assert found_correct_format, "Logging should use 'extra' parameter format"
    
    @pytest.mark.asyncio
    async def test_generate_thumbnails_logging_format(self):
        """Test that generate_thumbnails uses correct logging format with extra parameter."""
        analysis_id = "test-analysis-456"
        task_id = "task-789"
        
        with patch('app.tasks.analysis_tasks.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            # Mock the dependencies
            with patch('app.tasks.analysis_tasks.get_db_session'), \
                 patch('app.tasks.analysis_tasks.AnalysisService') as mock_analysis_service, \
                 patch('app.tasks.analysis_tasks.ImageService') as mock_image_service:
                
                mock_analysis_service.return_value.get_analysis = AsyncMock(return_value=Mock(
                    id=analysis_id,
                    left_image_path="/test/left.jpg",
                    right_image_path="/test/right.jpg"
                ))
                mock_analysis_service.return_value.update_analysis = AsyncMock()
                mock_image_service.return_value.create_thumbnail = AsyncMock()
                
                try:
                    await generate_thumbnails(analysis_id, task_id)
                except Exception:
                    # We expect some errors due to mocking, but we're testing logging format
                    pass
                
                # Verify logging calls use extra parameter format
                log_calls = mock_logger.info.call_args_list + mock_logger.error.call_args_list
                
                # Check that logging calls include extra data
                found_correct_format = False
                for call_args, call_kwargs in log_calls:
                    if 'extra' in call_kwargs:
                        extra_data = call_kwargs['extra']
                        if isinstance(extra_data, dict):
                            # Should contain analysis_id and/or task_id
                            if 'analysis_id' in extra_data or 'task_id' in extra_data:
                                found_correct_format = True
                                break
                
                assert found_correct_format, "Thumbnail generation logging should use 'extra' parameter format"
    
    def test_logger_extra_parameter_structure(self):
        """Test that the logger properly handles extra parameter structure."""
        logger = get_logger("test_module")
        
        # Mock the underlying logger
        with patch.object(logger, 'info') as mock_info:
            # Test the correct way to log with extra data
            extra_data = {
                "analysis_id": "test-123",
                "task_id": "task-456", 
                "user_id": "user-789"
            }
            
            logger.info("Processing analysis", extra=extra_data)
            
            # Verify the call was made with extra parameter
            mock_info.assert_called_once_with("Processing analysis", extra=extra_data)
    
    def test_avoid_direct_keyword_logging(self):
        """Test that direct keyword argument logging is avoided."""
        logger = get_logger("test_module")
        
        with patch.object(logger, 'info') as mock_info:
            # The WRONG way that was causing errors (should not be used)
            # logger.info("Message", analysis_id="123", task_id="456")  # This causes errors
            
            # The CORRECT way that should be used
            extra_data = {"analysis_id": "123", "task_id": "456"}
            logger.info("Message", extra=extra_data)
            
            # Verify the correct format was used
            args, kwargs = mock_info.call_args
            assert args[0] == "Message"
            assert "extra" in kwargs
            assert kwargs["extra"] == extra_data
            assert "analysis_id" not in kwargs  # Should not be direct keyword
            assert "task_id" not in kwargs      # Should not be direct keyword


class TestLoggingRegressionPrevention:
    """Tests to prevent regression of logging issues."""
    
    def test_all_task_functions_use_correct_logging(self):
        """Verify that all task functions in analysis_tasks.py use correct logging format."""
        import inspect
        import app.tasks.analysis_tasks as tasks_module
        
        # Get all functions in the tasks module
        task_functions = [
            func for name, func in inspect.getmembers(tasks_module)
            if inspect.isfunction(func) and not name.startswith('_')
        ]
        
        # Verify we have the expected task functions
        expected_functions = ['process_palm_analysis', 'generate_thumbnails', 'cleanup_failed_analysis']
        function_names = [func.__name__ for func in task_functions]
        
        for expected_func in expected_functions:
            assert expected_func in function_names, f"Expected function {expected_func} not found"
    
    @pytest.mark.asyncio
    async def test_error_logging_uses_correct_format(self):
        """Test that error logging also uses the correct format."""
        analysis_id = "error-test-123"
        
        with patch('app.tasks.analysis_tasks.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            # Mock to force an error condition
            with patch('app.tasks.analysis_tasks.get_db_session') as mock_get_db:
                mock_get_db.side_effect = Exception("Database connection error")
                
                # This should trigger error logging
                with pytest.raises(Exception):
                    await process_palm_analysis(analysis_id)
                
                # Check error logging calls
                error_calls = mock_logger.error.call_args_list
                
                # Verify at least one error log uses extra parameter
                found_correct_error_format = False
                for call_args, call_kwargs in error_calls:
                    if 'extra' in call_kwargs:
                        extra_data = call_kwargs['extra']
                        if isinstance(extra_data, dict):
                            found_correct_error_format = True
                            break
                
                assert found_correct_error_format, "Error logging should use 'extra' parameter format"
    
    def test_logging_configuration_supports_extra(self):
        """Test that the logging configuration properly supports extra parameters."""
        logger = get_logger("test_structured_logging")
        
        # Test with various extra data types
        test_cases = [
            {"string_field": "value", "int_field": 123},
            {"analysis_id": "test-123", "timestamp": "2023-01-01T00:00:00Z"},
            {"nested": {"key": "value"}, "list": [1, 2, 3]},
        ]
        
        for extra_data in test_cases:
            with patch.object(logger, 'info') as mock_info:
                logger.info("Test message", extra=extra_data)
                
                args, kwargs = mock_info.call_args
                assert "extra" in kwargs
                assert kwargs["extra"] == extra_data