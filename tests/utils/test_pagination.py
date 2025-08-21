"""
Tests for Advanced Pagination Utilities.

This module tests the sophisticated filtering, sorting, and pagination utilities
with query builder pattern and full-text search integration.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch
from typing import Any, Dict, List

from app.utils.pagination import (
    AdvancedQueryBuilder, 
    FilterOperator,
    PaginationParams,
    SortParams, 
    FilterParams,
    SearchParams,
    PaginatedResponse
)
from app.models.analysis import Analysis


class TestPaginationParams:
    """Test suite for PaginationParams class."""

    def test_pagination_params_defaults(self):
        """Test default pagination parameters."""
        params = PaginationParams()
        
        assert params.page == 1
        assert params.limit == 20
        assert params.offset == 0

    def test_pagination_params_custom(self):
        """Test custom pagination parameters."""
        params = PaginationParams(page=3, limit=50)
        
        assert params.page == 3
        assert params.limit == 50
        assert params.offset == 100  # (3-1) * 50

    def test_pagination_params_validation(self):
        """Test pagination parameter validation."""
        # Test minimum values
        params = PaginationParams(page=0, limit=0)
        assert params.page == 1
        assert params.limit == 1
        
        # Test maximum limit
        params = PaginationParams(limit=1000)
        assert params.limit == 100  # Max limit


class TestSortParams:
    """Test suite for SortParams class."""

    def test_sort_params_single_field(self):
        """Test single field sorting."""
        params = SortParams(field="created_at", direction="desc")
        
        assert params.field == "created_at"
        assert params.direction == "desc"

    def test_sort_params_validation(self):
        """Test sort parameter validation."""
        # Invalid direction should default to asc
        params = SortParams(field="name", direction="invalid")
        assert params.direction == "asc"


class TestFilterParams:
    """Test suite for FilterParams class."""

    def test_filter_params_basic(self):
        """Test basic filter parameters."""
        params = FilterParams(field="status", operator=FilterOperator.EQ, value="completed")
        
        assert params.field == "status"
        assert params.operator == FilterOperator.EQ
        assert params.value == "completed"

    def test_filter_params_list_value(self):
        """Test filter with list value."""
        params = FilterParams(field="id", operator=FilterOperator.IN, value=[1, 2, 3])
        
        assert params.field == "id"
        assert params.operator == FilterOperator.IN
        assert params.value == [1, 2, 3]

    def test_filter_params_validation(self):
        """Test filter parameter validation."""
        # IN operator requires list
        with pytest.raises(ValueError, match="IN operator requires a list value"):
            FilterParams(field="id", operator=FilterOperator.IN, value="single_value")
        
        # BETWEEN operator requires list of 2 values
        with pytest.raises(ValueError, match="BETWEEN operator requires a list of exactly 2 values"):
            FilterParams(field="date", operator=FilterOperator.BETWEEN, value=[1, 2, 3])


class TestSearchParams:
    """Test suite for SearchParams class."""

    def test_search_params_basic(self):
        """Test basic search parameters."""
        params = SearchParams(query="palm reading", fields=["title", "content"])
        
        assert params.query == "palm reading"
        assert params.fields == ["title", "content"]

    def test_search_params_validation(self):
        """Test search parameter validation."""
        # Empty query
        with pytest.raises(ValueError, match="Search query cannot be empty"):
            SearchParams(query="", fields=["title"])
        
        # Empty fields
        with pytest.raises(ValueError, match="Search fields cannot be empty"):
            SearchParams(query="test", fields=[])


class TestPaginatedResponse:
    """Test suite for PaginatedResponse class."""

    def test_paginated_response_structure(self):
        """Test paginated response structure."""
        items = [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]
        pagination = PaginationParams(page=2, limit=10)
        
        response = PaginatedResponse(
            items=items,
            total_count=25,
            pagination=pagination
        )
        
        assert response.items == items
        assert response.total_count == 25
        assert response.page == 2
        assert response.limit == 10
        assert response.total_pages == 3  # ceil(25/10)
        assert response.has_next is True
        assert response.has_previous is True

    def test_paginated_response_edge_cases(self):
        """Test paginated response edge cases."""
        # First page
        response = PaginatedResponse(
            items=[],
            total_count=5,
            pagination=PaginationParams(page=1, limit=10)
        )
        
        assert response.has_previous is False
        assert response.has_next is False
        assert response.total_pages == 1

    def test_paginated_response_to_dict(self):
        """Test paginated response dictionary conversion."""
        items = [{"id": 1}]
        response = PaginatedResponse(
            items=items,
            total_count=1,
            pagination=PaginationParams()
        )
        
        result_dict = response.to_dict()
        
        assert "items" in result_dict
        assert "pagination" in result_dict
        assert result_dict["pagination"]["total_count"] == 1
        assert result_dict["pagination"]["has_next"] is False


class TestAdvancedQueryBuilder:
    """Test suite for AdvancedQueryBuilder class."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def query_builder(self, mock_db_session):
        """Create query builder instance."""
        return AdvancedQueryBuilder(mock_db_session, Analysis)

    @pytest.mark.asyncio
    async def test_build_query_no_filters(self, query_builder):
        """Test query building with no filters."""
        pagination = PaginationParams()
        
        query, count_query = await query_builder.build_query(pagination=pagination)
        
        # Should have basic select and count queries
        assert query is not None
        assert count_query is not None

    @pytest.mark.asyncio
    async def test_build_query_with_filters(self, query_builder):
        """Test query building with filters."""
        filters = [
            FilterParams(field="status", operator=FilterOperator.EQ, value="completed"),
            FilterParams(field="cost", operator=FilterOperator.GT, value=0.10)
        ]
        pagination = PaginationParams()
        
        query, count_query = await query_builder.build_query(
            filters=filters,
            pagination=pagination
        )
        
        assert query is not None
        assert count_query is not None

    @pytest.mark.asyncio
    async def test_build_query_with_sorting(self, query_builder):
        """Test query building with sorting."""
        sort = SortParams(field="created_at", direction="desc")
        pagination = PaginationParams()
        
        query, count_query = await query_builder.build_query(
            sort=sort,
            pagination=pagination
        )
        
        assert query is not None
        assert count_query is not None

    @pytest.mark.asyncio
    async def test_build_query_with_search(self, query_builder):
        """Test query building with full-text search."""
        search = SearchParams(query="life line", fields=["result"])
        pagination = PaginationParams()
        
        query, count_query = await query_builder.build_query(
            search=search,
            pagination=pagination
        )
        
        assert query is not None
        assert count_query is not None

    @pytest.mark.asyncio
    async def test_execute_paginated_query(self, query_builder, mock_db_session):
        """Test paginated query execution."""
        # Mock query results
        mock_items = [
            MagicMock(id=1, status="completed"),
            MagicMock(id=2, status="processing")
        ]
        
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_items
        mock_db_session.execute.return_value = mock_result
        
        # Mock count result
        mock_count_result = AsyncMock()
        mock_count_result.scalar.return_value = 25
        mock_db_session.execute.side_effect = [mock_result, mock_count_result]
        
        pagination = PaginationParams(page=1, limit=10)
        
        response = await query_builder.execute_paginated_query(pagination=pagination)
        
        assert isinstance(response, PaginatedResponse)
        assert len(response.items) == 2
        assert response.total_count == 25
        assert response.page == 1

    @pytest.mark.asyncio
    async def test_apply_filters_equal_operator(self, query_builder):
        """Test applying EQ filter operator."""
        mock_query = MagicMock()
        filter_param = FilterParams(field="status", operator=FilterOperator.EQ, value="completed")
        
        result_query = await query_builder._apply_filters(mock_query, [filter_param])
        
        # Should call where method on query
        assert mock_query.where.called

    @pytest.mark.asyncio
    async def test_apply_filters_in_operator(self, query_builder):
        """Test applying IN filter operator."""
        mock_query = MagicMock()
        filter_param = FilterParams(field="status", operator=FilterOperator.IN, value=["completed", "processing"])
        
        result_query = await query_builder._apply_filters(mock_query, [filter_param])
        
        assert mock_query.where.called

    @pytest.mark.asyncio
    async def test_apply_filters_like_operator(self, query_builder):
        """Test applying LIKE filter operator."""
        mock_query = MagicMock()
        filter_param = FilterParams(field="title", operator=FilterOperator.LIKE, value="palm")
        
        result_query = await query_builder._apply_filters(mock_query, [filter_param])
        
        assert mock_query.where.called

    @pytest.mark.asyncio
    async def test_apply_filters_between_operator(self, query_builder):
        """Test applying BETWEEN filter operator."""
        mock_query = MagicMock()
        yesterday = datetime.utcnow() - timedelta(days=1)
        today = datetime.utcnow()
        filter_param = FilterParams(field="created_at", operator=FilterOperator.BETWEEN, value=[yesterday, today])
        
        result_query = await query_builder._apply_filters(mock_query, [filter_param])
        
        assert mock_query.where.called

    @pytest.mark.asyncio
    async def test_apply_filters_null_operators(self, query_builder):
        """Test applying NULL check operators."""
        mock_query = MagicMock()
        
        # Test IS_NULL
        filter_null = FilterParams(field="deleted_at", operator=FilterOperator.IS_NULL, value=None)
        await query_builder._apply_filters(mock_query, [filter_null])
        assert mock_query.where.called
        
        mock_query.reset_mock()
        
        # Test IS_NOT_NULL
        filter_not_null = FilterParams(field="result", operator=FilterOperator.IS_NOT_NULL, value=None)
        await query_builder._apply_filters(mock_query, [filter_not_null])
        assert mock_query.where.called

    @pytest.mark.asyncio
    async def test_apply_search_single_field(self, query_builder):
        """Test applying search to single field."""
        mock_query = MagicMock()
        search = SearchParams(query="life line", fields=["result"])
        
        result_query = await query_builder._apply_search(mock_query, search)
        
        # Should apply search filter
        assert mock_query.where.called

    @pytest.mark.asyncio
    async def test_apply_search_multiple_fields(self, query_builder):
        """Test applying search to multiple fields."""
        mock_query = MagicMock()
        search = SearchParams(query="palm reading", fields=["title", "result"])
        
        result_query = await query_builder._apply_search(mock_query, search)
        
        # Should apply OR condition for multiple fields
        assert mock_query.where.called

    @pytest.mark.asyncio
    async def test_apply_sorting_ascending(self, query_builder):
        """Test applying ascending sort."""
        mock_query = MagicMock()
        sort = SortParams(field="created_at", direction="asc")
        
        result_query = await query_builder._apply_sorting(mock_query, sort)
        
        # Should call order_by
        assert mock_query.order_by.called

    @pytest.mark.asyncio
    async def test_apply_sorting_descending(self, query_builder):
        """Test applying descending sort."""
        mock_query = MagicMock()
        sort = SortParams(field="created_at", direction="desc")
        
        result_query = await query_builder._apply_sorting(mock_query, sort)
        
        assert mock_query.order_by.called

    @pytest.mark.asyncio
    async def test_get_field_attribute_valid(self, query_builder):
        """Test getting valid field attribute."""
        # Analysis model should have 'id' field
        field_attr = query_builder._get_field_attribute("id")
        assert field_attr is not None

    @pytest.mark.asyncio
    async def test_get_field_attribute_invalid(self, query_builder):
        """Test getting invalid field attribute."""
        with pytest.raises(ValueError, match="Invalid field"):
            query_builder._get_field_attribute("nonexistent_field")

    @pytest.mark.asyncio
    async def test_build_search_condition_ilike(self, query_builder):
        """Test building ILIKE search condition."""
        field_attr = MagicMock()
        condition = query_builder._build_search_condition(field_attr, "test query")
        
        # Should use ilike for case-insensitive search
        field_attr.ilike.assert_called_with("%test query%")

    def test_filter_operators_enum(self):
        """Test FilterOperator enum values."""
        expected_operators = [
            "eq", "ne", "gt", "gte", "lt", "lte",
            "in", "not_in", "like", "ilike", 
            "is_null", "is_not_null", "between"
        ]
        
        actual_operators = [op.value for op in FilterOperator]
        
        for expected in expected_operators:
            assert expected in actual_operators

    @pytest.mark.asyncio
    async def test_complex_query_combination(self, query_builder, mock_db_session):
        """Test complex query with multiple filters, search, and sorting."""
        filters = [
            FilterParams(field="status", operator=FilterOperator.EQ, value="completed"),
            FilterParams(field="cost", operator=FilterOperator.GT, value=0.05),
            FilterParams(field="created_at", operator=FilterOperator.BETWEEN, 
                        value=[datetime.utcnow() - timedelta(days=30), datetime.utcnow()])
        ]
        
        search = SearchParams(query="palm reading", fields=["result"])
        sort = SortParams(field="created_at", direction="desc")
        pagination = PaginationParams(page=2, limit=15)
        
        # Mock execution results
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count_result = AsyncMock()
        mock_count_result.scalar.return_value = 0
        mock_db_session.execute.side_effect = [mock_result, mock_count_result]
        
        response = await query_builder.execute_paginated_query(
            filters=filters,
            search=search,
            sort=sort,
            pagination=pagination
        )
        
        assert isinstance(response, PaginatedResponse)
        assert response.page == 2
        assert response.limit == 15

    @pytest.mark.asyncio
    async def test_error_handling(self, query_builder, mock_db_session):
        """Test error handling in query execution."""
        # Mock database error
        mock_db_session.execute.side_effect = Exception("Database connection failed")
        
        pagination = PaginationParams()
        
        with pytest.raises(Exception):
            await query_builder.execute_paginated_query(pagination=pagination)

    @pytest.mark.asyncio
    async def test_empty_results(self, query_builder, mock_db_session):
        """Test handling of empty query results."""
        # Mock empty results
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count_result = AsyncMock()
        mock_count_result.scalar.return_value = 0
        mock_db_session.execute.side_effect = [mock_result, mock_count_result]
        
        pagination = PaginationParams()
        
        response = await query_builder.execute_paginated_query(pagination=pagination)
        
        assert len(response.items) == 0
        assert response.total_count == 0
        assert response.total_pages == 0

    @pytest.mark.asyncio 
    async def test_large_dataset_pagination(self, query_builder, mock_db_session):
        """Test pagination with large dataset."""
        # Mock large dataset
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = [MagicMock() for _ in range(50)]
        mock_count_result = AsyncMock()
        mock_count_result.scalar.return_value = 10000  # Large total count
        mock_db_session.execute.side_effect = [mock_result, mock_count_result]
        
        pagination = PaginationParams(page=100, limit=50)  # Far into the dataset
        
        response = await query_builder.execute_paginated_query(pagination=pagination)
        
        assert response.total_count == 10000
        assert response.total_pages == 200  # ceil(10000/50)
        assert response.has_previous is True
        assert response.has_next is True

    @pytest.mark.asyncio
    async def test_performance_optimization_hints(self, query_builder):
        """Test query optimization hints."""
        # Test that builder uses appropriate indexes and optimizations
        filters = [
            FilterParams(field="user_id", operator=FilterOperator.EQ, value=456),
            FilterParams(field="status", operator=FilterOperator.IN, value=["completed", "processing"])
        ]
        
        sort = SortParams(field="created_at", direction="desc")
        
        query, count_query = await query_builder.build_query(
            filters=filters,
            sort=sort,
            pagination=PaginationParams()
        )
        
        # Query should be constructed to leverage database indexes
        assert query is not None
        assert count_query is not None