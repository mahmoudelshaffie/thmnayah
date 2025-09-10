"""
Common Pydantic Models

This module contains shared Pydantic models and base classes used across
the CMS API for consistent data validation and serialization.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, Generic, TypeVar, List, Iterator, Tuple
from pydantic import BaseModel as PydanticBaseModel, Field, validator, RootModel, model_validator
from enum import Enum

# Type variable for generic pagination
T = TypeVar('T')


class BaseModel(PydanticBaseModel):
    """Base Pydantic model with common configuration"""
    
    class Config:
        # Allow using field names in snake_case but serialize to camelCase
        validate_by_name = True
        # Use enum values instead of names
        use_enum_values = True
        # Validate assignment to prevent invalid data
        validate_assignment = True
        # Generate schema for OpenAPI documentation
        json_schema_extra = {
            "example": {}
        }


class TimestampMixin(BaseModel):
    """Mixin for models that include timestamp fields"""
    
    created_at: datetime = Field(
        ..., 
        description="Timestamp when the record was created",
        example="2024-01-15T10:30:00Z"
    )
    updated_at: datetime = Field(
        ..., 
        description="Timestamp when the record was last updated",
        example="2024-01-15T10:30:00Z"
    )


class MultilingualText(RootModel[Dict[str, str]]):
    """Model for multilingual text fields supporting any language codes"""

    @model_validator(mode="after")
    def validate_languages(self) -> "MultilingualText":
        v = self.root
        if not v:
            raise ValueError("At least one language must be provided")

        for lang_code, text in v.items():
            if not isinstance(lang_code, str) or len(lang_code) < 2:
                raise ValueError("Language code must be at least 2 characters")
            if not isinstance(text, str) or len(text.strip()) == 0:
                raise ValueError(f"Text for language '{lang_code}' cannot be empty")
            if len(text) > 1000:
                raise ValueError(f"Text for language '{lang_code}' cannot exceed 1000 characters")
        return self

    # ✅ Dict-like behavior
    def __getitem__(self, key: str) -> str:
        return self.root[key]

    def __setitem__(self, key: str, value: str) -> None:
        self.root[key] = value

    def __iter__(self) -> Iterator[str]:
        return iter(self.root)

    def __len__(self) -> int:
        return len(self.root)

    def keys(self) -> List[str]:
        return list(self.root.keys())

    def values(self) -> List[str]:
        return list(self.root.values())

    def items(self) -> List[Tuple[str, str]]:
        return list(self.root.items())

    # ------------------------
    # Convenience methods
    # ------------------------
    def get(self, lang_code: str, default: Optional[str] = None) -> Optional[str]:
        return self.root.get(lang_code, default)

    def get_available_languages(self) -> List[str]:
        return list(self.root.keys())

    def has_language(self, lang_code: str) -> bool:
        return lang_code in self.root

    def get_fallback_text(self, preferred_languages: List[str] = None) -> Optional[str]:
        if not preferred_languages:
            preferred_languages = ["en", "ar"]  # Default fallback order

        for lang in preferred_languages:
            if lang in self.root:
                return self.root[lang]

        return next(iter(self.root.values()), None)


class OptionalMultilingualText(RootModel[Dict[str, str]]):
    """Model for multilingual text fields supporting any language codes"""

    @model_validator(mode="after")
    def validate_languages(self) -> "OptionalMultilingualText":
        v = self.root
        if not v:
            raise ValueError("At least one language must be provided")

        for lang_code, text in v.items():
            if not isinstance(lang_code, str) or len(lang_code) < 2:
                raise ValueError("Language code must be at least 2 characters")
            if not isinstance(text, str) or len(text.strip()) == 0:
                raise ValueError(f"Text for language '{lang_code}' cannot be empty")
            if len(text) > 1000:
                raise ValueError(f"Text for language '{lang_code}' cannot exceed 1000 characters")
        return self

    # ✅ Dict-like behavior
    def __getitem__(self, key: str) -> str:
        return self.root[key]

    def __setitem__(self, key: str, value: str) -> None:
        self.root[key] = value

    def __iter__(self) -> Iterator[str]:
        return iter(self.root)

    def __len__(self) -> int:
        return len(self.root)

    def keys(self) -> List[str]:
        return list(self.root.keys())

    def values(self) -> List[str]:
        return list(self.root.values())

    def items(self) -> List[Tuple[str, str]]:
        return list(self.root.items())

    # ------------------------
    # Convenience methods
    # ------------------------
    def get(self, lang_code: str, default: Optional[str] = None) -> Optional[str]:
        return self.root.get(lang_code, default)

    def get_available_languages(self) -> List[str]:
        return list(self.root.keys())

    def has_language(self, lang_code: str) -> bool:
        return lang_code in self.root

    def get_fallback_text(self, preferred_languages: List[str] = None) -> Optional[str]:
        if not preferred_languages:
            preferred_languages = ["en", "ar"]  # Default fallback order

        for lang in preferred_languages:
            if lang in self.root:
                return self.root[lang]

        return next(iter(self.root.values()), None)


class PaginationParams(BaseModel):
    """Standard pagination parameters"""
    
    page: int = Field(
        1, 
        ge=1,
        description="Page number (1-based)",
        example=1
    )
    limit: int = Field(
        20, 
        ge=1, 
        le=100,
        description="Number of items per page",
        example=20
    )
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries"""
        return (self.page - 1) * self.limit


class PaginationMeta(BaseModel):
    """Pagination metadata"""
    
    page: int = Field(..., description="Current page number", example=1)
    limit: int = Field(..., description="Items per page", example=20) 
    total: int = Field(..., description="Total number of items", example=150)
    total_pages: int = Field(..., description="Total number of pages", example=8)
    has_next: bool = Field(..., description="Whether there is a next page", example=True)
    has_prev: bool = Field(..., description="Whether there is a previous page", example=False)


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper"""
    
    data: List[T] = Field(..., description="List of items for current page")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": [],
                "pagination": {
                    "page": 1,
                    "limit": 20,
                    "total": 150,
                    "total_pages": 8,
                    "has_next": True,
                    "has_prev": False
                }
            }
        }


class SortOrder(str, Enum):
    """Sorting order enumeration"""
    ASC = "asc"
    DESC = "desc"


class SortParams(BaseModel):
    """Standard sorting parameters"""
    
    sort_by: str = Field(
        "created_at",
        description="Field to sort by",
        example="name"
    )
    sort_order: SortOrder = Field(
        SortOrder.ASC,
        description="Sort order (asc or desc)",
        example="asc"
    )


class LanguageSettings(BaseModel):
    """Language configuration and settings"""
    
    supported_languages: List[str] = Field(
        default=["en", "ar"],
        description="List of supported language codes (ISO 639-1)",
        example=["en", "ar", "fr", "es", "de", "zh", "ja", "ru"]
    )
    default_language: str = Field(
        default="en",
        description="Default/fallback language code",
        example="en"
    )
    fallback_order: List[str] = Field(
        default=["en", "ar"],
        description="Language fallback order when preferred language is not available",
        example=["en", "ar", "fr"]
    )
    
    @validator('supported_languages')
    def validate_supported_languages(cls, v):
        """Validate language codes"""
        if not v:
            raise ValueError("At least one supported language must be specified")
        
        for lang in v:
            if not isinstance(lang, str) or len(lang) < 2:
                raise ValueError(f"Invalid language code: {lang}")
        
        return v
    
    @validator('default_language')
    def validate_default_language(cls, v, values):
        """Ensure default language is in supported languages"""
        supported = values.get('supported_languages', [])
        if v and supported and v not in supported:
            raise ValueError(f"Default language '{v}' must be in supported languages")
        return v


class StatusFilter(str, Enum):
    """Common status filter values"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ALL = "all"


class ErrorDetail(BaseModel):
    """Error detail model for API responses"""
    
    message: str = Field(..., description="Error message", example="Invalid input data")
    field: Optional[str] = Field(None, description="Field that caused the error", example="name")
    code: Optional[str] = Field(None, description="Error code", example="VALIDATION_ERROR")


class ErrorResponse(BaseModel):
    """Standard error response model"""
    
    error: str = Field(..., description="Error type", example="ValidationError")
    message: str = Field(..., description="Error message", example="Request validation failed")
    details: Optional[List[ErrorDetail]] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")


class MessageResponse(BaseModel):
    """Simple message response model"""
    
    message: str = Field(..., description="Response message", example="Operation completed successfully")


class SuccessResponse(BaseModel):
    """Standard success response model"""
    
    success: bool = Field(True, description="Success indicator")
    message: str = Field(..., description="Success message", example="Operation completed successfully")
    data: Optional[Dict[str, Any]] = Field(None, description="Optional response data")


class HealthCheckResponse(BaseModel):
    """Health check response model"""
    
    status: str = Field(..., description="Service status", example="healthy")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp") 
    version: str = Field(..., description="API version", example="1.0.0")
    dependencies: Optional[Dict[str, str]] = Field(None, description="Dependency status")


class BulkOperationRequest(BaseModel):
    """Base model for bulk operations"""
    
    ids: List[uuid.UUID] = Field(
        ..., 
        description="List of resource IDs to operate on",
        min_items=1,
        max_items=100,
        example=["123e4567-e89b-12d3-a456-426614174000", "223e4567-e89b-12d3-a456-426614174001"]
    )


class BulkOperationResponse(BaseModel):
    """Response model for bulk operations"""
    
    success_count: int = Field(..., description="Number of successful operations", example=5)
    error_count: int = Field(..., description="Number of failed operations", example=1)
    total_count: int = Field(..., description="Total number of operations attempted", example=6)
    errors: Optional[List[ErrorDetail]] = Field(None, description="Details of failed operations")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success_count": 5,
                "error_count": 1, 
                "total_count": 6,
                "errors": [
                    {
                        "message": "Category not found",
                        "field": "id",
                        "code": "NOT_FOUND"
                    }
                ]
            }
        }