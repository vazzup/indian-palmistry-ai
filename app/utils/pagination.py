"""
Advanced pagination and filtering utilities for API endpoints.
"""
from typing import Dict, List, Any, Optional, Union, Type, Tuple
from datetime import datetime, date
from enum import Enum
import math

from pydantic import BaseModel, Field, validator
from sqlalchemy import select, func, desc, asc, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import Select

class SortDirection(Enum):
    """Sort direction options."""
    ASC = "asc"
    DESC = "desc"

class FilterOperator(Enum):
    """Filter operators for advanced filtering."""
    EQ = "eq"          # equals
    NE = "ne"          # not equals
    GT = "gt"          # greater than
    GTE = "gte"        # greater than or equal
    LT = "lt"          # less than
    LTE = "lte"        # less than or equal
    IN = "in"          # in list
    NOT_IN = "not_in"  # not in list
    LIKE = "like"      # like (contains)
    ILIKE = "ilike"    # case-insensitive like
    IS_NULL = "is_null"   # is null
    IS_NOT_NULL = "is_not_null"  # is not null
    BETWEEN = "between"   # between two values

class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset from page and limit."""
        return (self.page - 1) * self.limit

class SortParams(BaseModel):
    """Sort parameters."""
    field: str = Field(description="Field to sort by")
    direction: SortDirection = Field(default=SortDirection.DESC)

class FilterParams(BaseModel):
    """Filter parameters."""
    field: str = Field(description="Field to filter")
    operator: FilterOperator = Field(description="Filter operator")
    value: Optional[Union[str, int, float, bool, List[Union[str, int, float]]]] = Field(description="Filter value")
    
    @validator('value')
    def validate_value_for_operator(cls, v, values):
        """Validate value based on operator."""
        operator = values.get('operator')
        
        if operator == FilterOperator.IS_NULL or operator == FilterOperator.IS_NOT_NULL:
            return None  # No value needed for null checks
        elif operator == FilterOperator.BETWEEN:
            if not isinstance(v, list) or len(v) != 2:
                raise ValueError("Between operator requires a list of exactly 2 values")
        elif operator in [FilterOperator.IN, FilterOperator.NOT_IN]:
            if not isinstance(v, list):
                raise ValueError(f"{operator.value} operator requires a list of values")
        elif v is None:
            raise ValueError(f"{operator.value} operator requires a value")
        
        return v

class SearchParams(BaseModel):
    """Search parameters."""
    query: str = Field(description="Search query")
    fields: Optional[List[str]] = Field(default=None, description="Fields to search in")

class PaginatedResponse(BaseModel):
    """Standardized paginated response."""
    items: List[Any]
    pagination: Dict[str, Any]
    filters_applied: Optional[List[Dict[str, Any]]] = None
    sort_applied: Optional[Dict[str, Any]] = None
    search_applied: Optional[Dict[str, Any]] = None
    total_count: int
    page_count: int

class AdvancedQueryBuilder:
    """Advanced query builder with filtering, sorting, and pagination."""
    
    def __init__(self, model: Type[DeclarativeBase]):
        self.model = model
        self.base_query = select(model)
        self.count_query = select(func.count(model.id))
        self.filters = []
        self.sorts = []
        self.search_terms = []
    
    def add_filter(self, filter_param: FilterParams, allowed_fields: List[str] = None) -> 'AdvancedQueryBuilder':
        """Add filter to query."""
        
        if allowed_fields and filter_param.field not in allowed_fields:
            raise ValueError(f"Field '{filter_param.field}' not allowed for filtering")
        
        if not hasattr(self.model, filter_param.field):
            raise ValueError(f"Field '{filter_param.field}' does not exist on model")
        
        field = getattr(self.model, filter_param.field)
        condition = self._build_filter_condition(field, filter_param)
        
        if condition is not None:
            self.filters.append(condition)
        
        return self
    
    def add_sort(self, sort_param: SortParams, allowed_fields: List[str] = None) -> 'AdvancedQueryBuilder':
        """Add sort to query."""
        
        if allowed_fields and sort_param.field not in allowed_fields:
            raise ValueError(f"Field '{sort_param.field}' not allowed for sorting")
        
        if not hasattr(self.model, sort_param.field):
            raise ValueError(f"Field '{sort_param.field}' does not exist on model")
        
        field = getattr(self.model, sort_param.field)
        
        if sort_param.direction == SortDirection.DESC:
            self.sorts.append(desc(field))
        else:
            self.sorts.append(asc(field))
        
        return self
    
    def add_search(self, search_param: SearchParams, allowed_fields: List[str] = None) -> 'AdvancedQueryBuilder':
        """Add search to query."""
        
        search_fields = search_param.fields or allowed_fields
        if not search_fields:
            raise ValueError("No search fields specified")
        
        search_conditions = []
        for field_name in search_fields:
            if not hasattr(self.model, field_name):
                continue
            
            field = getattr(self.model, field_name)
            # Use ILIKE for case-insensitive search
            search_conditions.append(field.ilike(f"%{search_param.query}%"))
        
        if search_conditions:
            self.filters.append(or_(*search_conditions))
        
        return self
    
    def build(self) -> Tuple[Select, Select]:
        """Build the final query and count query."""
        
        # Apply filters
        if self.filters:
            filter_condition = and_(*self.filters)
            self.base_query = self.base_query.where(filter_condition)
            self.count_query = self.count_query.where(filter_condition)
        
        # Apply sorting
        if self.sorts:
            self.base_query = self.base_query.order_by(*self.sorts)
        
        return self.base_query, self.count_query
    
    def _build_filter_condition(self, field, filter_param: FilterParams):
        """Build filter condition for field."""
        
        operator = filter_param.operator
        value = filter_param.value
        
        if operator == FilterOperator.EQ:
            return field == value
        elif operator == FilterOperator.NE:
            return field != value
        elif operator == FilterOperator.GT:
            return field > value
        elif operator == FilterOperator.GTE:
            return field >= value
        elif operator == FilterOperator.LT:
            return field < value
        elif operator == FilterOperator.LTE:
            return field <= value
        elif operator == FilterOperator.IN:
            return field.in_(value)
        elif operator == FilterOperator.NOT_IN:
            return ~field.in_(value)
        elif operator == FilterOperator.LIKE:
            return field.like(f"%{value}%")
        elif operator == FilterOperator.ILIKE:
            return field.ilike(f"%{value}%")
        elif operator == FilterOperator.IS_NULL:
            return field.is_(None)
        elif operator == FilterOperator.IS_NOT_NULL:
            return field.isnot(None)
        elif operator == FilterOperator.BETWEEN:
            return field.between(value[0], value[1])
        
        return None

class PaginationService:
    """Service for handling pagination with advanced filtering."""
    
    @staticmethod
    async def paginate(
        db: AsyncSession,
        query_builder: AdvancedQueryBuilder,
        pagination: PaginationParams,
        serialize_item: Optional[callable] = None
    ) -> PaginatedResponse:
        """Execute paginated query with filtering and sorting."""
        
        # Build queries
        data_query, count_query = query_builder.build()
        
        # Get total count
        count_result = await db.execute(count_query)
        total_count = count_result.scalar() or 0
        
        # Apply pagination
        data_query = data_query.offset(pagination.offset).limit(pagination.limit)
        
        # Execute data query
        data_result = await db.execute(data_query)
        items = data_result.scalars().all()
        
        # Serialize items if serializer provided
        if serialize_item:
            serialized_items = [serialize_item(item) for item in items]
        else:
            serialized_items = [item for item in items]
        
        # Calculate pagination info
        page_count = math.ceil(total_count / pagination.limit) if total_count > 0 else 1
        has_next = pagination.page < page_count
        has_prev = pagination.page > 1
        
        pagination_info = {
            "current_page": pagination.page,
            "page_size": pagination.limit,
            "total_items": total_count,
            "total_pages": page_count,
            "has_next": has_next,
            "has_previous": has_prev,
            "next_page": pagination.page + 1 if has_next else None,
            "previous_page": pagination.page - 1 if has_prev else None
        }
        
        return PaginatedResponse(
            items=serialized_items,
            pagination=pagination_info,
            total_count=total_count,
            page_count=page_count
        )
    
    @staticmethod
    def parse_filters_from_params(filter_params: Dict[str, Any]) -> List[FilterParams]:
        """Parse filter parameters from query parameters."""
        
        filters = []
        
        # Parse filter parameters in format: filter[field][operator]=value
        for key, value in filter_params.items():
            if key.startswith('filter[') and key.endswith(']'):
                # Extract field and operator
                filter_part = key[7:-1]  # Remove 'filter[' and ']'
                
                if '][' in filter_part:
                    field, operator = filter_part.split('][', 1)
                    try:
                        filter_operator = FilterOperator(operator)
                        filters.append(FilterParams(
                            field=field,
                            operator=filter_operator,
                            value=value
                        ))
                    except ValueError:
                        # Invalid operator, skip
                        continue
        
        return filters
    
    @staticmethod
    def parse_sorts_from_params(sort_params: Dict[str, Any]) -> List[SortParams]:
        """Parse sort parameters from query parameters."""
        
        sorts = []
        
        # Parse sort parameters in format: sort=field1:desc,field2:asc
        sort_string = sort_params.get('sort', '')
        
        if sort_string:
            for sort_item in sort_string.split(','):
                sort_item = sort_item.strip()
                if ':' in sort_item:
                    field, direction = sort_item.split(':', 1)
                    try:
                        sort_direction = SortDirection(direction.lower())
                        sorts.append(SortParams(field=field, direction=sort_direction))
                    except ValueError:
                        # Invalid direction, use default
                        sorts.append(SortParams(field=field))
                else:
                    # No direction specified, use default
                    sorts.append(SortParams(field=sort_item))
        
        return sorts
    
    @staticmethod
    def parse_search_from_params(search_params: Dict[str, Any]) -> Optional[SearchParams]:
        """Parse search parameters from query parameters."""
        
        query = search_params.get('q') or search_params.get('search')
        if not query:
            return None
        
        fields = search_params.get('search_fields')
        if fields:
            if isinstance(fields, str):
                fields = [f.strip() for f in fields.split(',')]
        
        return SearchParams(query=query, fields=fields)

class APIFilterMixin:
    """Mixin for API endpoints to add advanced filtering capabilities."""
    
    @staticmethod
    def get_allowed_filter_fields() -> List[str]:
        """Override in subclass to specify allowed filter fields."""
        return []
    
    @staticmethod
    def get_allowed_sort_fields() -> List[str]:
        """Override in subclass to specify allowed sort fields."""
        return []
    
    @staticmethod
    def get_allowed_search_fields() -> List[str]:
        """Override in subclass to specify allowed search fields."""
        return []
    
    @staticmethod
    def get_default_sort() -> List[SortParams]:
        """Override in subclass to specify default sort."""
        return []

# Pre-defined filter sets for common use cases
class CommonFilters:
    """Common filter configurations for different entities."""
    
    # User filters
    USER_FILTERS = {
        'allowed_filter_fields': ['is_active', 'created_at', 'updated_at'],
        'allowed_sort_fields': ['id', 'name', 'email', 'created_at', 'updated_at'],
        'allowed_search_fields': ['name', 'email'],
        'default_sort': [SortParams(field='created_at', direction=SortDirection.DESC)]
    }
    
    # Analysis filters
    ANALYSIS_FILTERS = {
        'allowed_filter_fields': ['status', 'user_id', 'created_at', 'updated_at', 'cost'],
        'allowed_sort_fields': ['id', 'created_at', 'updated_at', 'cost', 'tokens_used'],
        'allowed_search_fields': ['summary'],
        'default_sort': [SortParams(field='created_at', direction=SortDirection.DESC)]
    }
    
    # Conversation filters
    CONVERSATION_FILTERS = {
        'allowed_filter_fields': ['user_id', 'analysis_id', 'created_at', 'updated_at'],
        'allowed_sort_fields': ['id', 'title', 'created_at', 'updated_at'],
        'allowed_search_fields': ['title'],
        'default_sort': [SortParams(field='updated_at', direction=SortDirection.DESC)]
    }
    
    # Message filters
    MESSAGE_FILTERS = {
        'allowed_filter_fields': ['conversation_id', 'role', 'created_at', 'cost'],
        'allowed_sort_fields': ['id', 'created_at', 'cost', 'tokens_used'],
        'allowed_search_fields': ['content'],
        'default_sort': [SortParams(field='created_at', direction=SortDirection.ASC)]
    }

def create_pagination_params(
    page: int = 1,
    limit: int = 20,
    max_limit: int = 100
) -> PaginationParams:
    """Create pagination parameters with validation."""
    
    # Ensure limits are within bounds
    limit = min(max(1, limit), max_limit)
    page = max(1, page)
    
    return PaginationParams(page=page, limit=limit)

def build_filter_description(allowed_fields: List[str], allowed_operators: List[FilterOperator] = None) -> str:
    """Build filter description for API documentation."""
    
    if not allowed_operators:
        allowed_operators = list(FilterOperator)
    
    operator_examples = {
        FilterOperator.EQ: "filter[field][eq]=value",
        FilterOperator.IN: "filter[field][in]=value1,value2",
        FilterOperator.GT: "filter[field][gt]=100",
        FilterOperator.LIKE: "filter[field][like]=search_term",
        FilterOperator.BETWEEN: "filter[field][between]=start_date,end_date"
    }
    
    description = f"Filter by fields: {', '.join(allowed_fields)}\n"
    description += "Available operators:\n"
    
    for operator in allowed_operators:
        if operator in operator_examples:
            description += f"- {operator.value}: {operator_examples[operator]}\n"
        else:
            description += f"- {operator.value}: filter[field][{operator.value}]=value\n"
    
    return description

# Global pagination service instance
pagination_service = PaginationService()