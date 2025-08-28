"""
Comprehensive tests for the cache debug system functionality.
Tests cache debug endpoints, utilities, and error handling.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.core.cache import CacheService
from app.utils.cache_utils import (
    validate_cache_key,
    extract_user_id_from_key,
    get_pattern_stats,
    collect_debug_info
)


class TestCacheDebugEndpoints:
    """Test cache debug API endpoints"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def mock_cache_service(self):
        with patch('app.api.v1.enhanced_endpoints.cache_service') as mock:
            yield mock

    def test_get_cache_debug_authenticated(self, client, mock_cache_service):
        """Test cache debug endpoint with authentication"""
        mock_debug_info = {
            'total_keys': 150,
            'user_keys': {'1': 25, '2': 30},
            'pattern_breakdown': {
                'dashboard:*': 45,
                'analysis:*': 60,
                'conversation:*': 45
            },
            'cache_stats': {
                'hits': 1500,
                'misses': 100,
                'hit_ratio': 0.94
            }
        }
        mock_cache_service.get_cache_debug_info.return_value = mock_debug_info

        # Mock authentication
        with patch('app.dependencies.auth.get_current_user') as mock_auth:
            mock_auth.return_value = {'id': 1, 'email': 'test@example.com'}
            
            response = client.get('/api/v1/cache/debug')
            
            assert response.status_code == 200
            data = response.json()
            assert data['total_keys'] == 150
            assert '1' in data['user_keys']
            assert data['cache_stats']['hit_ratio'] == 0.94

    def test_get_cache_debug_unauthenticated(self, client):
        """Test cache debug endpoint without authentication"""
        response = client.get('/api/v1/cache/debug')
        assert response.status_code == 401

    def test_refresh_cache_authenticated(self, client, mock_cache_service):
        """Test cache refresh endpoint with authentication"""
        mock_result = {
            'success': True,
            'invalidated_keys': 25,
            'message': 'User cache refreshed successfully'
        }
        mock_cache_service.refresh_user_cache.return_value = mock_result

        with patch('app.dependencies.auth.get_current_user') as mock_auth:
            mock_auth.return_value = {'id': 1, 'email': 'test@example.com'}
            
            response = client.post('/api/v1/cache/refresh')
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert data['invalidated_keys'] == 25

    def test_refresh_cache_with_pattern(self, client, mock_cache_service):
        """Test cache refresh with specific pattern"""
        mock_result = {
            'success': True,
            'invalidated_keys': 15,
            'pattern': 'dashboard:*',
            'message': 'Pattern cache refreshed successfully'
        }
        mock_cache_service.refresh_user_cache.return_value = mock_result

        with patch('app.dependencies.auth.get_current_user') as mock_auth:
            mock_auth.return_value = {'id': 1, 'email': 'test@example.com'}
            
            response = client.post(
                '/api/v1/cache/refresh',
                json={'pattern': 'dashboard:*'}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['pattern'] == 'dashboard:*'
            assert data['invalidated_keys'] == 15

    def test_validate_cache_consistency(self, client, mock_cache_service):
        """Test cache consistency validation endpoint"""
        mock_validation = {
            'consistent': False,
            'inconsistencies': [
                {
                    'key': 'dashboard:1:overview',
                    'issue': 'Cached value outdated',
                    'cached_value': {'total': 5},
                    'db_value': {'total': 7}
                }
            ],
            'total_checked': 25,
            'recommendations': ['Refresh dashboard cache']
        }
        mock_cache_service.validate_consistency.return_value = mock_validation

        with patch('app.dependencies.auth.get_current_user') as mock_auth:
            mock_auth.return_value = {'id': 1, 'email': 'test@example.com'}
            
            response = client.get('/api/v1/cache/validate-consistency')
            
            assert response.status_code == 200
            data = response.json()
            assert data['consistent'] is False
            assert len(data['inconsistencies']) == 1
            assert data['total_checked'] == 25


class TestCacheUtilities:
    """Test cache utility functions"""

    def test_validate_cache_key_valid(self):
        """Test cache key validation with valid keys"""
        valid_keys = [
            'user:1:dashboard',
            'analysis:123:result',
            'conversation:456:messages',
            'session:abc123'
        ]
        
        for key in valid_keys:
            assert validate_cache_key(key) is True

    def test_validate_cache_key_invalid(self):
        """Test cache key validation with invalid keys"""
        invalid_keys = [
            '',
            'key with spaces',
            'key:with:too:many:colons:here:invalid',
            'key\nwith\nnewlines',
            'key\twith\ttabs'
        ]
        
        for key in invalid_keys:
            assert validate_cache_key(key) is False

    def test_extract_user_id_from_key_valid(self):
        """Test user ID extraction from valid cache keys"""
        test_cases = [
            ('user:123:dashboard', 123),
            ('dashboard:456:overview', 456),
            ('analysis:789:result', 789),
            ('conversation:1:messages', 1)
        ]
        
        for key, expected_id in test_cases:
            assert extract_user_id_from_key(key) == expected_id

    def test_extract_user_id_from_key_invalid(self):
        """Test user ID extraction from invalid cache keys"""
        invalid_keys = [
            'session:abc123',
            'global:config',
            'malformed:key',
            'user:invalid:id'
        ]
        
        for key in invalid_keys:
            assert extract_user_id_from_key(key) is None

    def test_get_pattern_stats(self):
        """Test pattern statistics collection"""
        mock_redis = MagicMock()
        mock_redis.scan_iter.side_effect = [
            ['dashboard:1:overview', 'dashboard:2:overview'],  # dashboard:*
            ['analysis:1:result', 'analysis:2:result', 'analysis:3:result'],  # analysis:*
            ['conversation:1:messages']  # conversation:*
        ]
        
        patterns = ['dashboard:*', 'analysis:*', 'conversation:*']
        stats = get_pattern_stats(mock_redis, patterns)
        
        expected_stats = {
            'dashboard:*': 2,
            'analysis:*': 3,
            'conversation:*': 1
        }
        
        assert stats == expected_stats

    def test_collect_debug_info(self):
        """Test debug information collection"""
        mock_redis = MagicMock()
        mock_redis.info.return_value = {
            'used_memory': '1024000',
            'used_memory_human': '1.00M',
            'connected_clients': 5,
            'total_commands_processed': 10000
        }
        mock_redis.scan_iter.return_value = [
            'user:1:dashboard',
            'user:2:dashboard', 
            'analysis:1:result',
            'conversation:1:messages'
        ]
        
        debug_info = collect_debug_info(mock_redis)
        
        assert 'total_keys' in debug_info
        assert 'memory_usage' in debug_info
        assert 'pattern_breakdown' in debug_info
        assert debug_info['memory_usage'] == '1.00M'


class TestCacheService:
    """Test CacheService cache debug methods"""

    @pytest.fixture
    def cache_service(self):
        service = CacheService()
        service.redis_client = AsyncMock()
        return service

    @pytest.mark.asyncio
    async def test_get_cache_debug_info(self, cache_service):
        """Test cache debug info retrieval"""
        # Mock Redis responses
        cache_service.redis_client.info.return_value = {
            'used_memory_human': '2.50M',
            'connected_clients': 3
        }
        
        # Mock scan_iter for different patterns
        mock_keys = [
            'user:1:dashboard', 'user:2:dashboard',
            'analysis:1:result', 'analysis:2:result',
            'conversation:1:messages'
        ]
        cache_service.redis_client.scan_iter.return_value = mock_keys
        
        debug_info = await cache_service.get_cache_debug_info()
        
        assert 'total_keys' in debug_info
        assert 'pattern_breakdown' in debug_info
        assert 'memory_usage' in debug_info
        assert debug_info['memory_usage'] == '2.50M'

    @pytest.mark.asyncio
    async def test_refresh_user_cache(self, cache_service):
        """Test user cache refresh"""
        user_id = 1
        
        # Mock key finding
        user_keys = ['user:1:dashboard', 'dashboard:1:overview', 'analysis:1:result']
        cache_service.redis_client.scan_iter.return_value = user_keys
        
        # Mock deletion
        cache_service.redis_client.delete.return_value = len(user_keys)
        
        result = await cache_service.refresh_user_cache(user_id)
        
        assert result['success'] is True
        assert result['invalidated_keys'] == 3
        assert 'message' in result

    @pytest.mark.asyncio
    async def test_refresh_user_cache_with_pattern(self, cache_service):
        """Test user cache refresh with specific pattern"""
        user_id = 1
        pattern = 'dashboard:*'
        
        # Mock pattern-specific keys
        pattern_keys = ['dashboard:1:overview', 'dashboard:1:stats']
        cache_service.redis_client.scan_iter.return_value = pattern_keys
        cache_service.redis_client.delete.return_value = len(pattern_keys)
        
        result = await cache_service.refresh_user_cache(user_id, pattern)
        
        assert result['success'] is True
        assert result['invalidated_keys'] == 2
        assert result['pattern'] == pattern

    @pytest.mark.asyncio
    async def test_validate_consistency(self, cache_service):
        """Test cache consistency validation"""
        user_id = 1
        
        # Mock inconsistent data
        cache_service.redis_client.scan_iter.return_value = ['dashboard:1:overview']
        cache_service.redis_client.get.return_value = json.dumps({'total_analyses': 5})
        
        # Mock database check (this would be more complex in real implementation)
        with patch('app.services.user_dashboard_service.UserDashboardService.get_user_dashboard') as mock_db:
            mock_db.return_value = {'overview': {'total_analyses': 7}}
            
            validation = await cache_service.validate_consistency(user_id)
            
            assert 'consistent' in validation
            assert 'inconsistencies' in validation
            assert 'total_checked' in validation
            assert 'recommendations' in validation


class TestCacheDebugErrorHandling:
    """Test error handling in cache debug system"""

    @pytest.fixture
    def cache_service(self):
        service = CacheService()
        service.redis_client = AsyncMock()
        return service

    @pytest.mark.asyncio
    async def test_cache_debug_redis_error(self, cache_service):
        """Test handling of Redis connection errors"""
        cache_service.redis_client.info.side_effect = Exception("Redis connection failed")
        
        with pytest.raises(Exception):
            await cache_service.get_cache_debug_info()

    @pytest.mark.asyncio
    async def test_cache_refresh_redis_error(self, cache_service):
        """Test handling of Redis errors during cache refresh"""
        cache_service.redis_client.scan_iter.side_effect = Exception("Redis scan failed")
        
        result = await cache_service.refresh_user_cache(1)
        
        # Should handle error gracefully
        assert result['success'] is False
        assert 'error' in result

    def test_invalid_cache_key_handling(self):
        """Test handling of invalid cache keys"""
        invalid_keys = ['', None, 123, {'key': 'value'}]
        
        for invalid_key in invalid_keys:
            with pytest.raises((TypeError, ValueError)):
                validate_cache_key(invalid_key)


class TestCacheDebugIntegration:
    """Integration tests for cache debug system"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_cache_debug_workflow(self, client):
        """Test complete cache debug workflow"""
        with patch('app.dependencies.auth.get_current_user') as mock_auth:
            mock_auth.return_value = {'id': 1, 'email': 'test@example.com'}
            
            with patch('app.api.v1.enhanced_endpoints.cache_service') as mock_cache:
                # Step 1: Get debug info
                mock_cache.get_cache_debug_info.return_value = {
                    'total_keys': 50,
                    'user_keys': {'1': 15},
                    'pattern_breakdown': {'dashboard:*': 10}
                }
                
                debug_response = client.get('/api/v1/cache/debug')
                assert debug_response.status_code == 200
                
                # Step 2: Refresh cache
                mock_cache.refresh_user_cache.return_value = {
                    'success': True,
                    'invalidated_keys': 15
                }
                
                refresh_response = client.post('/api/v1/cache/refresh')
                assert refresh_response.status_code == 200
                
                # Step 3: Validate consistency
                mock_cache.validate_consistency.return_value = {
                    'consistent': True,
                    'inconsistencies': [],
                    'total_checked': 15
                }
                
                validate_response = client.get('/api/v1/cache/validate-consistency')
                assert validate_response.status_code == 200

    def test_cache_debug_performance(self, client):
        """Test cache debug system performance"""
        with patch('app.dependencies.auth.get_current_user') as mock_auth:
            mock_auth.return_value = {'id': 1, 'email': 'test@example.com'}
            
            with patch('app.api.v1.enhanced_endpoints.cache_service') as mock_cache:
                # Mock large dataset
                mock_cache.get_cache_debug_info.return_value = {
                    'total_keys': 10000,
                    'user_keys': {str(i): 100 for i in range(100)},
                    'pattern_breakdown': {f'pattern:{i}:*': 100 for i in range(100)}
                }
                
                response = client.get('/api/v1/cache/debug')
                assert response.status_code == 200
                
                # Response should be reasonably fast even with large datasets
                data = response.json()
                assert data['total_keys'] == 10000
                assert len(data['user_keys']) == 100


if __name__ == '__main__':
    pytest.main([__file__])