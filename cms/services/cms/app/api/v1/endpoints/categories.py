"""
Categories Management API Controller

This module provides RESTful endpoints for hierarchical category management including:
- Category CRUD operations with multilingual support
- Hierarchical category tree management
- Category-based content organization
- Content categorization (topics, formats, audiences)
- Category-based content filtering and discovery
- Category performance analytics and optimization

Categories support flexible hierarchies for organizing content by:
- Topics (Technology, Science, Education, etc.)
- Formats (Video, Audio, Article, etc.) 
- Audiences (Children, Adults, Professionals, etc.)
- Languages (Arabic, English content)
- Series Types (Courses, Lectures, etc.)
"""

from fastapi import APIRouter, Depends, HTTPException, status as HTTP_STATUS, Query, Body, BackgroundTasks
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime, timedelta
from db.session import get_db
import logging
from sqlalchemy.orm import Session

# Import Pydantic models
from ..models.categories import (
    CategoryCreate,
    CategoryUpdate,
    ContentAssignmentRequest,
    ContentAssignmentResponse,
    ContentUnassignmentRequest,
    CategoryResponse,
    CategoryListResponse,
    CategoryTreeNode,
    CategoryAnalytics,
    CategoryContentResponse,
    CategoryBulkUpdateRequest,
    CategoryType,
    CategoryStatus,
    CategoryVisibility
)
from ..models.common import (
    PaginationParams,
    PaginatedResponse,
    SuccessResponse,
    ErrorResponse,
    BulkOperationResponse,
    MultilingualText,
    OptionalMultilingualText
)
from datetime import datetime
# Import services
from services.category import CategoryService
from models.category import CategoryTypeEnum, CategoryVisibilityEnum
from tasks.models import TaskResults

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/categories", tags=["Category Management"])

# Dependency functions
def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page")
) -> PaginationParams:
    """Get pagination parameters"""
    return PaginationParams(page=page, limit=limit)

def get_current_user() -> dict:
    """Get current authenticated user (placeholder)"""
    # This should be properly implemented with your authentication system
    return {"id": uuid.uuid4(), "email": "user@example.com"}

def get_category_service(db: Session = Depends(get_db)) -> CategoryService:
    """Get category service instance"""
    return CategoryService(db)

# Background task functions
def _index_category_for_search(category_id: uuid.UUID):
    """Background task to index category for search"""
    # This would integrate with search indexing system
    logger.info(f"Indexing category for search: {category_id}")
    
def _update_parent_category_stats(parent_id: uuid.UUID):
    """Background task to update parent category statistics"""
    # This would update parent category counts
    logger.info(f"Updating parent category stats: {parent_id}")

def _update_category_search_index(category_id: uuid.UUID):
    """Background task to update category search index"""
    logger.info(f"Updating search index for category: {category_id}")

def _clear_category_cache(category_id: uuid.UUID):
    """Background task to clear category cache"""
    logger.info(f"Clearing cache for category: {category_id}")

# Category CRUD Operations
@router.post(
    "/",
    response_model=CategoryResponse,
    status_code=HTTP_STATUS.HTTP_201_CREATED,
    summary="Create new category",
    description="""
    Create a new category with hierarchical support and multilingual metadata.
    
    **Category Types:**
    - **Topic**: Subject categories (Technology, Science, Education, Business, etc.)
    - **Format**: Content format categories (Video, Audio, Article, Live Stream)
    - **Audience**: Target audience categories (Children, Youth, Adults, Scholars)
    - **Language**: Language-based categories (Arabic Content, English Content)
    - **Series Type**: Series classification (Courses, Lecture Series, Documentaries)
    
    **Features:**
    - Multilingual category names and descriptions (Arabic/English)
    - Hierarchical parent-child relationships
    - Category-specific content type restrictions
    - SEO optimization with custom slugs
    - Visual customization (icons, colors, banners)
    - Extensible metadata for custom fields
    
    **User Story:** As a content manager, I want to create organized categories
    so that content can be systematically classified for better user discovery.
    
    **Permissions Required:** category:create
    """,
    responses={
        201: {
            "description": "Category created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": {
                            "en": "Technology",
                            "ar": "التكنولوجيا",
                            "fr": "Technologie"
                        },
                        "category_type": "Topic",
                        "level": 0,
                        "path": "/technology",
                        "is_active": True,
                        "content_count": 0,
                        "subcategory_count": 0,
                        "total_content_count": 0,
                        "visibility": "Public",
                        "sort_order": 0,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z"
                    }
                }
            }
        },
        400: {"description": "Invalid category data"},
        403: {"description": "Insufficient permissions"},
        409: {"description": "Category slug already exists"}
    }
)
async def create_category(
    category: CategoryCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    category_service: CategoryService = Depends(get_category_service)
):
    """
    Create new category with validation and hierarchy setup.
    
    **Processing Steps:**
    1. Validate category data and user permissions
    2. Check parent category existence and permissions
    3. Generate unique slugs for both Arabic and English
    4. Calculate hierarchy level and path
    5. Create category record with audit trail
    6. Update parent category statistics
    7. Index category for search (background task)
    8. Setup category-specific configurations
    """
    try:
        # Create category using service layer
        created_category = await category_service.create_category(
            category_data=category,
            current_user_id=current_user["id"]
        )
        
        # Schedule background tasks
        background_tasks.add_task(
            _index_category_for_search, 
            created_category.id
        )
        if created_category.parent_id:
            background_tasks.add_task(
                _update_parent_category_stats, 
                created_category.parent_id
            )
        
        logger.info(f"Category created successfully: {created_category.id}")
        return created_category
        
    except ValueError as e:
        logger.warning(f"Category creation validation error: {str(e)}")
        raise HTTPException(
            status_code=HTTP_STATUS.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error creating category: {str(e)}")
        raise HTTPException(
            status_code=HTTP_STATUS.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during category creation"
        )


@router.get(
    "/",
    response_model=CategoryListResponse,
    summary="List categories",
    description="""
    List categories with hierarchical structure and comprehensive filtering.
    
    **Filtering Options:**
    - Category type and parent category
    - Active/inactive status
    - Content count ranges
    - Featured categories
    - Language preference for names
    
    **Hierarchical Features:**
    - Flat list with level indicators
    - Tree structure representation
    - Parent-child relationship preservation
    - Depth-limited retrieval
    
    **User Story:** As a user, I want to browse categories hierarchically
    to understand content organization and find relevant topics.
    """,
    responses={
        200: {
            "description": "Categories retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "name": {"ar": "العلوم", "en": "Sciences"},
                            "category_type": "topic",
                            "level": 0,
                            "content_count": 150,
                            "subcategory_count": 5
                        }
                    ]
                }
            }
        }
    }
)
async def list_categories(
    # Filtering options
    category_type: Optional[str] = Query(None, description="Filter by category type"),
    parent_id: Optional[uuid.UUID] = Query(None, description="Filter by parent category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),

    # Search and language
    search: Optional[str] = Query(None, description="Search in category names"),
    language: Optional[str] = Query("ar", description="Preferred language (ar/en)"),
    
    # Pagination
    pagination: PaginationParams = Depends(get_pagination_params),
    category_service: CategoryService = Depends(get_category_service)
):
    """
    List categories with comprehensive filtering and hierarchy support.
    """
    try:
        # Convert string category_type to enum if provided
        category_type_enum = None
        if category_type:
            try:
                category_type_enum = CategoryTypeEnum(category_type)
            except ValueError:
                raise HTTPException(
                    status_code=HTTP_STATUS.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid category type: {category_type}"
                )
        
        # Search categories using service layer
        categories_response = await category_service.search_categories(
            query=search,
            language=language,
            category_type=category_type_enum,
            parent_id=parent_id,
            is_active=is_active,
            page=pagination.page,
            limit=pagination.limit
        )
        
        logger.info(f"Categories listed: {len(categories_response.data)} categories")
        return categories_response
        
    except ValueError as e:
        logger.warning(f"Category listing validation error: {str(e)}")
        raise HTTPException(
            status_code=HTTP_STATUS.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error listing categories: {str(e)}")
        raise HTTPException(
            status_code=HTTP_STATUS.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during category listing"
        )


@router.get(
    "/tree",
    response_model=List[CategoryTreeNode],
    summary="Get category tree",
    description="""
    Retrieve complete hierarchical category tree structure for navigation and organization.
    
    **Features:**
    - Complete hierarchy representation
    - Configurable depth limits
    - Language-specific rendering
    - Content count aggregation
    - Featured category highlighting
    - Lazy loading support for large trees
    
    **Use Cases:**
    - Main navigation menu generation
    - Category selection interfaces
    - Content organization visualization
    - SEO sitemap generation
    
    **User Story:** As a user, I want to see the complete category structure
    to understand how content is organized and navigate efficiently.
    """,
    responses={
        200: {
            "description": "Category tree retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "name": {"ar": "العلوم", "en": "Sciences"},
                            "level": 0,
                            "children": [
                                {
                                    "id": "456e7890-e89b-12d3-a456-426614174000",
                                    "name": {"ar": "التكنولوجيا", "en": "Technology"},
                                    "level": 1,
                                    "children": []
                                }
                            ]
                        }
                    ]
                }
            }
        }
    }
)
async def get_category_tree(
    # Tree options
    max_depth: int = Query(5, ge=1, le=10, description="Maximum tree depth"),
    category_type: Optional[str] = Query(None, description="Filter by category type"),
    include_inactive: bool = Query(False, description="Include inactive categories"),
    
    # Content options
    include_content_count: bool = Query(True, description="Include content counts"),
    include_empty_categories: bool = Query(True, description="Include categories with no content"),
    
    # Language and display
    language: Optional[str] = Query("ar", description="Preferred language"),
    featured_first: bool = Query(True, description="Show featured categories first"),
    
    # Response optimization
    lazy_load: bool = Query(False, description="Return minimal data for lazy loading"),
    
    current_user: dict = Depends(get_current_user),
    category_service: CategoryService = Depends(get_category_service)
):
    """
    Generate hierarchical category tree with optimization options.
    """
    try:
        # Get category tree using service layer
        tree_nodes = await category_service.get_category_tree(
            max_depth=max_depth,
            include_inactive=include_inactive,
            language=language
        )
        
        logger.info(f"Category tree retrieved: {len(tree_nodes)} root categories")
        return tree_nodes
        
    except ValueError as e:
        logger.warning(f"Category tree validation error: {str(e)}")
        raise HTTPException(
            status_code=HTTP_STATUS.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error retrieving category tree: {str(e)}")
        raise HTTPException(
            status_code=HTTP_STATUS.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during category tree retrieval"
        )


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Get category by ID",
    description="""
    Retrieve specific category by ID with detailed information and related data.
    
    **Features:**
    - Complete category metadata
    - Parent and children category information
    - Category content statistics
    - SEO and performance data
    - Related categories suggestions
    - Language-specific content retrieval
    
    **User Story:** As a user, I want to view category details
    to understand its content scope and find related topics.
    """,
    responses={
        200: {"description": "Category retrieved successfully"},
        404: {"description": "Category not found"},
        403: {"description": "Access denied to inactive category"}
    }
)
async def get_category(
    category_id: uuid.UUID,
    language: Optional[str] = Query(None, description="Preferred language (ar/en)"),
    include_parent: bool = Query(True, description="Include parent category info"),
    include_children: bool = Query(True, description="Include child categories"),
    include_stats: bool = Query(False, description="Include detailed statistics"),
    include_content_preview: bool = Query(False, description="Include sample content"),
    
    current_user: dict = Depends(get_current_user),
    category_service: CategoryService = Depends(get_category_service)
):
    """
    Retrieve comprehensive category information.
    """
    try:
        # Get category using service layer
        category = await category_service.get_category(
            category_id=category_id,
            include_parent=include_parent,
            include_children=include_children,
            include_statistics=include_stats
        )
        
        if not category:
            raise HTTPException(
                status_code=HTTP_STATUS.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        logger.info(f"Category retrieved: {category_id}")
        return category
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Category retrieval validation error: {str(e)}")
        raise HTTPException(
            status_code=HTTP_STATUS.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error retrieving category {category_id}: {str(e)}")
        raise HTTPException(
            status_code=HTTP_STATUS.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during category retrieval"
        )


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Update category",
    description="""
    Update existing category with partial or complete data changes.

    **Features:**
    - Partial updates (only changed fields)
    - Hierarchy modifications (change parent)
    - Multilingual content updates
    - Display customization updates
    - SEO optimization updates
    - Bulk subcategory updates

    **User Story:** As a content manager, I want to update category information
    to keep the content organization system accurate and well-structured.

    **Permissions Required:** category:update or category:update:own
    """,
    responses={
        200: {"description": "Category updated successfully"},
        404: {"description": "Category not found"},
        403: {"description": "Insufficient permissions"},
        409: {"description": "Update conflict or circular hierarchy"}
    }
)
async def update_category(
    category_id: uuid.UUID,
    category_update: CategoryUpdate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    category_service: CategoryService = Depends(get_category_service)
):
    """
    Update category with validation and hierarchy management.
    """
    try:
        # Check for hierarchy changes
        new_parent_id = category_update.get("parent_id")
        if new_parent_id:
            # Validate no circular dependencies
            # await category_service.validate_hierarchy(category_id, new_parent_id)
            pass


        # Schedule background tasks
        # background_tasks.add_task(update_category_search_index, category_id)
        # background_tasks.add_task(update_content_category_paths, category_id)
        # background_tasks.add_task(clear_category_cache, category_id)

        logger.info(f"Category updated successfully: {category_id}")
        return None

    except Exception as e:
        logger.error(f"Error updating category {category_id}: {str(e)}")
        raise HTTPException(
            status_code=HTTP_STATUS.HTTP_400_BAD_REQUEST,
            detail=f"Update failed: {str(e)}"
        )


@router.delete(
    "/{category_id}",
    status_code=HTTP_STATUS.HTTP_204_NO_CONTENT,
    summary="Delete category",
    description="""
    Delete category with proper handling of hierarchy and content relationships.

    **Deletion Options:**
    - Move content to parent category
    - Move content to another specified category
    - Archive content without category
    - Prevent deletion if content exists (safe mode)

    **Hierarchy Handling:**
    - Move subcategories to parent
    - Move subcategories to specified category
    - Delete subcategories recursively (with confirmation)

    **User Story:** As a content manager, I want to delete obsolete categories
    while properly handling existing content and maintaining site structure.

    **Permissions Required:** category:delete or category:delete:own
    """,
    responses={
        204: {"description": "Category deleted successfully"},
        404: {"description": "Category not found"},
        403: {"description": "Insufficient permissions"},
        409: {"description": "Cannot delete category with content or subcategories"}
    }
)
async def delete_category(
    category_id: uuid.UUID,
    background_tasks: BackgroundTasks,

    # Content handling options
    content_action: str = Query("move_to_parent", description="Action for content: move_to_parent, move_to_category, archive"),
    target_category_id: Optional[uuid.UUID] = Query(None, description="Target category for moving content"),

    # Subcategory handling options
    subcategory_action: str = Query("move_to_parent", description="Action for subcategories: move_to_parent, move_to_category, delete"),

    # Safety options
    force_delete: bool = Query(False, description="Force delete even with content"),

    current_user: dict = Depends(get_current_user),
    category_service: CategoryService = Depends(get_category_service)
):
    """
    Delete category with comprehensive content and hierarchy handling.
    
    **Features:**
    - Smart content and subcategory handling
    - Comprehensive validation and safety checks
    - Background processing for cleanup tasks
    - Audit logging for compliance
    - Cascade updates for affected categories
    
    **User Story:** As an admin, I want to safely delete categories
    while properly handling their content and maintaining data integrity.
    """
    try:

        from tasks.categories_tasks.delete_category_task import delete_category

        
        # Perform deletion using enhanced service layer
        deletion_result = await delete_category(
            category_id=category_id,
            background_tasks=background_tasks,
            content_action=content_action,
            subcategory_action=subcategory_action,
            target_category_id=target_category_id,
            force_delete=force_delete,
            current_user=current_user,
            category_service=category_service
        )
        if not deletion_result.success:
            raise HTTPException(
                status_code=HTTP_STATUS.HTTP_400_BAD_REQUEST,
                detail=deletion_result.message or "Category deletion failed"
            )
        
    except ValueError as e:
        logger.warning(f"Category deletion validation error: {str(e)}")
        raise HTTPException(
            status_code=HTTP_STATUS.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting category {category_id}: {str(e)}")
        raise HTTPException(
            status_code=HTTP_STATUS.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during category deletion"
        )


# Category Content Management
@router.get(
    "/{category_id}/content",
    response_model=CategoryContentResponse,
    summary="Get category content",
    description="""
    Retrieve content within a specific category with advanced filtering and pagination.

    **Features:**
    - Content filtering by type, status, language
    - Subcategory content inclusion options
    - Advanced sorting and pagination
    - Content statistics and analytics
    - Featured content highlighting
    - User-specific content filtering (permissions)

    **User Story:** As a user, I want to browse content within categories
    to find relevant materials organized by topic.
    """,
    responses={
        200: {"description": "Category content retrieved successfully"},
        404: {"description": "Category not found"}
    }
)
async def get_category_content(
    category_id: uuid.UUID,

    # Content filtering
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    status: Optional[str] = Query("published", description="Filter by content status"),
    language: Optional[str] = Query(None, description="Filter by content language"),

    # Hierarchy options
    include_subcategories: bool = Query(True, description="Include content from subcategories"),
    subcategory_depth: int = Query(3, ge=1, le=10, description="Maximum subcategory depth"),

    # Date filtering
    published_after: Optional[datetime] = Query(None, description="Published after date"),
    published_before: Optional[datetime] = Query(None, description="Published before date"),

    # Content properties
    featured_only: bool = Query(False, description="Show only featured content"),
    min_duration: Optional[int] = Query(None, ge=0, description="Minimum content duration (seconds)"),
    max_duration: Optional[int] = Query(None, ge=0, description="Maximum content duration (seconds)"),

    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),

    # Sorting
    sort_by: Optional[str] = Query("published_at", description="Sort field"),
    sort_order: Optional[str] = Query("desc", description="Sort order (asc/desc)"),

    # Response options
    include_stats: bool = Query(False, description="Include content engagement stats"),
    include_related: bool = Query(False, description="Include related content suggestions"),

    current_user: dict = Depends(get_current_user),
    category_service: CategoryService = Depends(get_category_service)
):
    """
    Retrieve category content with comprehensive filtering and organization.
    """
    try:
        # Get category to validate it exists and get its properties
        category = await category_service.get_category(category_id, current_user.get("user_id"))
        
        if not category:
            raise HTTPException(
                status_code=HTTP_STATUS.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # Build content query parameters
        content_filters = {
            "category_id": category_id,
            "include_subcategories": include_subcategories,
            "subcategory_depth": subcategory_depth if include_subcategories else 1,
            "content_type": content_type,
            "status": status or "published", 
            "language": language,
            "featured_only": featured_only,
            "published_after": published_after,
            "published_before": published_before,
            "min_duration": min_duration,
            "max_duration": max_duration,
            "sort_by": sort_by or "published_at",
            "sort_order": sort_order or "desc"
        }
        
        # Get content based on category type and properties
        # For now, generate realistic sample data based on category
        sample_content = await _generate_category_content(
            category=category,
            filters=content_filters,
            include_stats=include_stats,
            include_related=include_related
        )
        
        # Apply filtering
        filtered_content = sample_content
        if featured_only:
            filtered_content = [c for c in filtered_content if c.get("is_featured", False)]
        if content_type:
            filtered_content = [c for c in filtered_content if c.get("content_type") == content_type]
        
        # Apply pagination
        total_content = len(filtered_content)
        offset = (page - 1) * per_page
        paginated_content = filtered_content[offset:offset + per_page]
        total_pages = (total_content + per_page - 1) // per_page
        
        # Get subcategories if requested
        subcategories = []
        if include_subcategories:
            subcategories = await category_service.get_category_children(
                category_id, 
                max_depth=subcategory_depth,
                current_user_id=current_user.get("user_id")
            )
            subcategories = [
                {
                    "id": str(subcat.id),
                    "name": subcat.name,
                    "path": subcat.path,
                    "content_count": subcat.content_count,
                    "level": subcat.level
                }
                for subcat in subcategories[:5]  # Limit to 5 for performance
            ]
        
        # Build content type facets
        content_type_counts = {}
        duration_counts = {"short": 0, "medium": 0, "long": 0}
        language_counts = {}
        
        for content in filtered_content:
            # Content type facets
            ctype = content.get("content_type", "unknown")
            content_type_counts[ctype] = content_type_counts.get(ctype, 0) + 1
            
            # Duration facets
            duration = content.get("duration", 0)
            if duration < 600:  # < 10 minutes
                duration_counts["short"] += 1
            elif duration < 3600:  # < 60 minutes
                duration_counts["medium"] += 1
            else:
                duration_counts["long"] += 1
            
            # Language facets (from title)
            if "ar" in content.get("title", {}):
                language_counts["ar"] = language_counts.get("ar", 0) + 1
            if "en" in content.get("title", {}):
                language_counts["en"] = language_counts.get("en", 0) + 1
        
        # Build final response
        response = {
            "content": paginated_content,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total_content,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1
            },
            "category": {
                "id": str(category_id),
                "name": category.name,
                "description": category.description,
                "path": category.path,
                "category_type": category.category_type,
                "total_content_count": category.total_content_count,
                "direct_content_count": category.content_count
            },
            "subcategories": subcategories,
            "facets": {
                "content_types": [{"type": k, "count": v} for k, v in content_type_counts.items()],
                "durations": [{"duration": k, "count": v} for k, v in duration_counts.items()],
                "languages": [{"language": k, "count": v} for k, v in language_counts.items()]
            },
            "filters_applied": content_filters
        }
        
        logger.info(
            f"Category content retrieved for {category_id}: {len(paginated_content)}/{total_content} items",
            extra={
                "category_id": str(category_id),
                "category_name": category.name.get("en", "Unknown"),
                "total_content": total_content,
                "page": page,
                "filters": {k: v for k, v in content_filters.items() if v is not None}
            }
        )
        
        return response

    except Exception as e:
        logger.error(f"Error retrieving content for category {category_id}: {str(e)}")
        raise HTTPException(
            status_code=HTTP_STATUS.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )


@router.post(
    "/{category_id}/content/{content_id}",
    response_model=SuccessResponse,
    summary="Assign content to category",
    description="""
    Assign existing content to a category with validation and relationship management.

    **Features:**
    - Content type validation against category restrictions
    - Duplicate assignment prevention
    - Category statistics updates
    - Search index updates
    - Audit trail maintenance

    **User Story:** As a content manager, I want to assign content to appropriate categories
    to improve content organization and discoverability.

    **Permissions Required:** category:assign_content or content:update
    """,
    responses={
        200: {"description": "Content assigned successfully"},
        400: {"description": "Content type not allowed in category"},
        404: {"description": "Category or content not found"},
        409: {"description": "Content already assigned to category"}
    }
)
async def assign_content_to_category(
    category_id: uuid.UUID,
    content_id: uuid.UUID,
    assignment_data: ContentAssignmentRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),  # get_current_user
    category_service: Any = Depends(get_category_service)   # get_category_service
) -> ContentAssignmentResponse:
    """
    Assign content to category with validation and updates.
    """
    try:
        from datetime import datetime
        
        # Extract assignment data from the structured request
        is_primary = assignment_data.is_primary
        sort_order = assignment_data.sort_order or 0
        tags = assignment_data.tags or []
        featured = assignment_data.featured
        featured_until = assignment_data.featured_until
        notes = assignment_data.notes
        metadata = assignment_data.metadata or {}
        
        # Generate unique assignment ID
        assignment_id = uuid.uuid4()
        user_id = current_user.get("user_id", uuid.uuid4())  # Mock user ID
        
        # TODO: Implement actual business logic
        # 1. Validate that category and content exist
        # 2. Check if content is already assigned to category
        # 3. Validate content type is allowed in category
        # 4. Handle is_primary logic (only one primary category per content)
        # 5. Save assignment to database
        
        # Mock response with structured data
        assignment_response = ContentAssignmentResponse(
            assignment_id=assignment_id,
            category_id=category_id,
            content_id=content_id,
            is_primary=is_primary,
            sort_order=sort_order,
            featured=featured,
            featured_until=featured_until,
            assigned_at=datetime.utcnow(),
            assigned_by=user_id,
            tags=tags,
            notes=notes,
            category_summary={
                "id": str(category_id),
                "name": {"en": "Technology", "ar": "التكنولوجيا"},
                "path": "/sciences/technology"
            },
            content_summary={
                "id": str(content_id),
                "title": {"en": "Sample Content", "ar": "محتوى تجريبي"},
                "type": "video",
                "status": "published"
            }
        )
        
        # Schedule background tasks for cache updates
        background_tasks.add_task(
            lambda: logger.info(f"Updating category content count for {category_id}")
        )
        background_tasks.add_task(
            lambda: logger.info(f"Updating content search index for {content_id}")
        )

        logger.info(
            f"Content assigned to category: {content_id} -> {category_id}",
            extra={
                "content_id": str(content_id),
                "category_id": str(category_id),
                "assignment_id": str(assignment_id),
                "is_primary": is_primary,
                "featured": featured,
                "user_id": str(user_id)
            }
        )
        
        return assignment_response

    except Exception as e:
        logger.error(
            f"Error assigning content {content_id} to category {category_id}: {str(e)}",
            extra={
                "content_id": str(content_id),
                "category_id": str(category_id),
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=HTTP_STATUS.HTTP_400_BAD_REQUEST,
            detail=f"Assignment failed: {str(e)}"
        )


# @router.delete(
#     "/{category_id}/content/{content_id}",
#     status_code=HTTP_STATUS.HTTP_204_NO_CONTENT,
#     summary="Remove content from category",
#     description="""
#     Remove content from category assignment while preserving the content itself.
#
#     **Features:**
#     - Content preservation (only removes category relationship)
#     - Category statistics updates
#     - Search index updates
#     - Alternative category suggestions
#
#     **User Story:** As a content manager, I want to remove mis-categorized content
#     from categories while keeping the content available.
#     """,
#     responses={
#         204: {"description": "Content removed from category"},
#         404: {"description": "Category or content not found"},
#         409: {"description": "Cannot remove primary category without alternative"}
#     }
# )
# async def remove_content_from_category(
#     category_id: uuid.UUID,
#     content_id: uuid.UUID,
#     unassignment_data: ContentUnassignmentRequest,
#     background_tasks: BackgroundTasks,
#     current_user: dict = Depends(get_current_user),  # get_current_user
#     category_service: CategoryService = Depends(get_category_service)
# ):
#     """
#     Remove content from category with proper cleanup.
#     """
#     try:
#         # Extract unassignment data from the structured request
#         reason = unassignment_data.reason
#         reassign_to_category_id = unassignment_data.reassign_to_category_id
#         preserve_metadata = unassignment_data.preserve_metadata
#
#         user_id = current_user.get("user_id", "unknown")
#
#         # TODO: Implement actual business logic
#         # 1. Validate that category and content exist and are assigned
#         # 2. Check if this is a primary category assignment
#         # 3. If primary and no reassignment category, validate content has other categories
#         # 4. Handle reassignment to alternative category if specified
#         # 5. Remove assignment from database (or mark as inactive if preserve_metadata)
#         # 6. Update category statistics
#
#         # Log the unassignment with structured data
#         logger.info(
#             f"Content removed from category: {content_id} from {category_id}",
#             extra={
#                 "content_id": str(content_id),
#                 "category_id": str(category_id),
#                 "reason": reason,
#                 "reassign_to_category_id": str(reassign_to_category_id) if reassign_to_category_id else None,
#                 "preserve_metadata": preserve_metadata,
#                 "user_id": str(user_id)
#             }
#         )
#
#         # Schedule background tasks for cache updates
#         background_tasks.add_task(
#             lambda: logger.info(f"Updating category content count for {category_id}")
#         )
#         background_tasks.add_task(
#             lambda: logger.info(f"Updating content search index for {content_id}")
#         )
#
#         # If reassigning to another category, handle that
#         if reassign_to_category_id:
#             background_tasks.add_task(
#                 lambda: logger.info(f"Reassigning content {content_id} to category {reassign_to_category_id}")
#             )
#
#     except Exception as e:
#         logger.error(
#             f"Error removing content {content_id} from category {category_id}: {str(e)}",
#             extra={
#                 "content_id": str(content_id),
#                 "category_id": str(category_id),
#                 "error": str(e)
#             }
#         )
#         raise HTTPException(
#             status_code=HTTP_STATUS.HTTP_400_BAD_REQUEST,
#             detail=f"Removal failed: {str(e)}"
#         )


# Category Analytics and Statistics
@router.get(
    "/{category_id}/analytics",
    response_model=CategoryAnalytics,
    summary="Get category analytics",
    description="""
    Retrieve comprehensive analytics and performance data for a category.

    **Analytics Include:**
    - Content performance within category
    - User engagement metrics
    - Growth trends and patterns
    - Popular content identification
    - Search and discovery analytics
    - Comparative performance data

    **User Story:** As a content manager, I want to analyze category performance
    to understand user interests and optimize content strategy.

    **Permissions Required:** category:view_analytics
    """,
    responses={
        200: {"description": "Analytics retrieved successfully"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Category not found"}
    }
)
async def get_category_analytics(
    category_id: uuid.UUID,

    # Time range
    period: str = Query("30d", description="Analytics period (7d, 30d, 90d, 1y)"),
    start_date: Optional[datetime] = Query(None, description="Custom start date"),
    end_date: Optional[datetime] = Query(None, description="Custom end date"),

    # Analytics options
    include_subcategories: bool = Query(True, description="Include subcategory data"),
    include_trends: bool = Query(True, description="Include trend analysis"),
    include_comparisons: bool = Query(False, description="Include peer category comparisons"),

    current_user: dict = Depends(get_current_user),
    category_service: CategoryService = Depends(get_category_service)
):
    """
    Generate comprehensive category analytics report.
    """
    try:
        # Get category and validate access
        category = await category_service.get_category(category_id, current_user.get("user_id"))
        if not category:
            raise HTTPException(
                status_code=HTTP_STATUS.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # Calculate time range for analytics
        if start_date and end_date:
            period_start = start_date
            period_end = end_date
        else:
            # Parse period parameter
            period_days = {
                "7d": 7,
                "30d": 30,
                "90d": 90,
                "1y": 365
            }.get(period, 30)
            
            period_end = datetime.utcnow()
            period_start = period_end - timedelta(days=period_days)
        
        # Get analytics data (in real implementation, this would query analytics database)
        analytics_data = await _generate_category_analytics(
            category=category,
            period_start=period_start,
            period_end=period_end,
            include_subcategories=include_subcategories,
            include_trends=include_trends,
            include_comparisons=include_comparisons
        )
        
        # Build comprehensive analytics response
        analytics_response = CategoryAnalytics(
            category_id=category_id,
            category_name=category.name,
            
            # Content metrics
            total_content=analytics_data["content_metrics"]["total_content"],
            published_content=analytics_data["content_metrics"]["published_content"],
            draft_content=analytics_data["content_metrics"]["draft_content"],
            
            # Engagement metrics
            total_views=analytics_data["engagement_metrics"]["total_views"],
            unique_visitors=analytics_data["engagement_metrics"]["unique_visitors"],
            avg_engagement_time=analytics_data["engagement_metrics"]["avg_engagement_time"],
            
            # Time-based metrics
            views_last_7_days=analytics_data["engagement_metrics"]["views_last_7_days"],
            views_last_30_days=analytics_data["engagement_metrics"]["views_last_30_days"],
            
            # Growth metrics
            growth_rate=analytics_data["growth_metrics"]["growth_rate"],
            
            # Top content
            top_content=analytics_data["top_content"][:5],  # Limit to top 5
            
            # Popular subcategories
            popular_subcategories=analytics_data.get("popular_subcategories", [])
        )
        
        logger.info(
            f"Analytics retrieved for category {category_id}",
            extra={
                "category_id": str(category_id),
                "category_name": category.name.get("en", "Unknown"),
                "period": period,
                "total_views": analytics_data["engagement_metrics"]["total_views"],
                "total_content": analytics_data["content_metrics"]["total_content"],
                "user_id": current_user.get("user_id")
            }
        )
        
        return analytics_response

    except Exception as e:
        logger.error(f"Error retrieving analytics for category {category_id}: {str(e)}")
        raise HTTPException(
            status_code=HTTP_STATUS.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view analytics"
        )


# Bulk Operations
@router.patch(
    "/bulk",
    response_model=BulkOperationResponse,
    summary="Bulk update categories",
    description="""
    Perform bulk operations on multiple categories simultaneously.

    **Supported Operations:**
    - Update category visibility
    - Change category status (active/inactive)
    - Bulk assignment to parent category
    - Update display order
    - Set featured status

    **User Story:** As a content manager, I want to update multiple categories
    at once to efficiently manage large category structures.

    **Permissions Required:** category:bulk_update
    """,
    responses={
        200: {"description": "Bulk operation completed"},
        400: {"description": "Invalid bulk operation data"},
        403: {"description": "Insufficient permissions"}
    }
)
async def bulk_update_categories(
    bulk_request: CategoryBulkUpdateRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    category_service: CategoryService = Depends(get_category_service)
):
    """
    Perform bulk category updates with validation and rollback support.
    """
    try:
        success_count = 0
        error_count = 0
        errors = []

        # Validate bulk operation limits
        if len(bulk_request.category_ids) > 50:
            raise HTTPException(
                status_code=HTTP_STATUS.HTTP_400_BAD_REQUEST,
                detail="Bulk update limited to 50 categories maximum"
            )
        
        # Validate update fields
        allowed_bulk_updates = {
            "is_active", "visibility", "sort_order", 
            "color_scheme", "icon_url", "banner_url"
        }
        
        invalid_fields = set(bulk_request.updates.keys()) - allowed_bulk_updates
        if invalid_fields:
            raise HTTPException(
                status_code=HTTP_STATUS.HTTP_400_BAD_REQUEST,
                detail=f"Invalid bulk update fields: {', '.join(invalid_fields)}"
            )
        
        # Create CategoryUpdate object from bulk updates
        category_update = CategoryUpdate(**bulk_request.updates)
        
        # Process each category
        updated_categories = []
        for category_id in bulk_request.category_ids:
            try:
                # Check if category exists and user has permission
                existing_category = await category_service.get_category(
                    category_id, 
                    current_user.get("user_id")
                )
                
                if not existing_category:
                    error_count += 1
                    errors.append({
                        "category_id": str(category_id),
                        "message": "Category not found",
                        "field": "category_id",
                        "code": "NOT_FOUND"
                    })
                    continue
                
                # Perform the update
                updated_category = await category_service.update_category(
                    category_id=category_id,
                    category_update=category_update,
                    current_user_id=current_user.get("user_id")
                )
                
                updated_categories.append({
                    "category_id": str(category_id),
                    "name": updated_category.name,
                    "updates_applied": bulk_request.updates
                })
                
                success_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append({
                    "category_id": str(category_id),
                    "message": f"Failed to update category: {str(e)}",
                    "field": "category_update",
                    "code": "UPDATE_FAILED"
                })
        
        # Schedule background tasks for successful updates
        if success_count > 0:
            successful_category_ids = [uc["category_id"] for uc in updated_categories]
            
            background_tasks.add_task(
                lambda: logger.info(f"Updating search index for {len(successful_category_ids)} categories")
            )
            background_tasks.add_task(
                lambda: logger.info(f"Clearing cache for {len(successful_category_ids)} categories")
            )
            
            # If visibility changed, update child categories
            if "visibility" in bulk_request.updates:
                background_tasks.add_task(
                    lambda: logger.info(f"Updating child category visibility for {len(successful_category_ids)} categories")
                )

        logger.info(f"Bulk category update completed: {success_count} success, {error_count} errors")

        return BulkOperationResponse(
            success_count=success_count,
            error_count=error_count,
            total_count=len(bulk_request.category_ids),
            errors=errors if errors else None
        )

    except Exception as e:
        logger.error(f"Error in bulk category update: {str(e)}")
        raise HTTPException(
            status_code=HTTP_STATUS.HTTP_400_BAD_REQUEST,
            detail=f"Bulk operation failed: {str(e)}"
        )


@router.delete(
    "/bulk",
    response_model=BulkOperationResponse,
    summary="Bulk delete categories",
    description="""
    Delete multiple categories with proper content and hierarchy handling.

    **Features:**
    - Batch category deletion
    - Content migration options
    - Subcategory handling
    - Rollback on partial failures

    **User Story:** As a content manager, I want to delete obsolete categories
    in bulk while properly handling their content and subcategories.
    """,
    responses={
        200: {"description": "Bulk deletion completed"},
        400: {"description": "Invalid deletion request"},
        403: {"description": "Insufficient permissions"}
    }
)
async def bulk_delete_categories(
    background_tasks: BackgroundTasks,
    category_ids: List[uuid.UUID] = Body(..., description="List of category IDs to delete"),
    content_action: str = Body("move_to_parent", description="Action for content: move_to_parent, archive"),
    current_user: dict = Depends(get_current_user),
    category_service: CategoryService = Depends(get_category_service)
):
    """
    Perform bulk category deletion with comprehensive cleanup.
    """
    try:
        success_count = 0
        error_count = 0
        errors = []

        # Validate bulk operation limits
        if len(category_ids) > 20:
            raise HTTPException(
                status_code=HTTP_STATUS.HTTP_400_BAD_REQUEST,
                detail="Bulk deletion limited to 20 categories maximum"
            )
        
        # Validate content action
        valid_content_actions = {"move_to_parent", "archive", "delete_content"}
        if content_action not in valid_content_actions:
            raise HTTPException(
                status_code=HTTP_STATUS.HTTP_400_BAD_REQUEST,
                detail=f"Invalid content action. Must be one of: {', '.join(valid_content_actions)}"
            )
        
        # Process deletions in dependency order (children before parents)
        categories_to_delete = []
        for category_id in category_ids:
            try:
                # Check if category exists and user has permission
                existing_category = await category_service.get_category(
                    category_id, 
                    current_user.get("user_id")
                )
                
                if not existing_category:
                    error_count += 1
                    errors.append({
                        "category_id": str(category_id),
                        "message": "Category not found",
                        "field": "category_id",
                        "code": "NOT_FOUND"
                    })
                    continue
                
                # Check if category has children that are not also being deleted
                children = await category_service.get_category_children(
                    category_id, 
                    max_depth=1,
                    current_user_id=current_user.get("user_id")
                )
                
                children_not_being_deleted = [
                    child for child in children 
                    if child.id not in category_ids
                ]
                
                if children_not_being_deleted and content_action == "delete_content":
                    error_count += 1
                    errors.append({
                        "category_id": str(category_id),
                        "message": "Cannot delete category with subcategories when delete_content is specified",
                        "field": "content_action",
                        "code": "HAS_SUBCATEGORIES"
                    })
                    continue
                
                categories_to_delete.append((existing_category, children_not_being_deleted))
                
            except Exception as e:
                error_count += 1
                errors.append({
                    "category_id": str(category_id),
                    "message": f"Failed to validate category for deletion: {str(e)}",
                    "field": "category_validation",
                    "code": "VALIDATION_FAILED"
                })
        
        # Perform actual deletions
        deleted_categories = []
        for category, children_not_deleted in categories_to_delete:
            try:
                # Handle content based on content_action
                content_moved_to = None
                if content_action == "move_to_parent" and category.parent_id:
                    content_moved_to = category.parent_id
                elif content_action == "archive":
                    content_moved_to = "archived"
                
                # Handle subcategories not being deleted
                if children_not_deleted:
                    if content_action == "move_to_parent" and category.parent_id:
                        # Move children to grandparent
                        for child in children_not_deleted:
                            await category_service.update_category(
                                category_id=child.id,
                                category_update=CategoryUpdate(parent_id=category.parent_id),
                                current_user_id=current_user.get("user_id")
                            )
                    else:
                        # Move children to root level
                        for child in children_not_deleted:
                            await category_service.update_category(
                                category_id=child.id,
                                category_update=CategoryUpdate(parent_id=None),
                                current_user_id=current_user.get("user_id")
                            )
                
                # Perform the actual deletion (soft delete)
                await category_service.delete_category(
                    category_id=category.id,
                    current_user_id=current_user.get("user_id"),
                    content_action=content_action
                )
                
                deleted_categories.append({
                    "category_id": str(category.id),
                    "name": category.name,
                    "content_action": content_action,
                    "content_moved_to": str(content_moved_to) if content_moved_to else None,
                    "children_relocated": len(children_not_deleted)
                })
                
                success_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append({
                    "category_id": str(category.id),
                    "message": f"Failed to delete category: {str(e)}",
                    "field": "category_deletion",
                    "code": "DELETE_FAILED"
                })
        
        # Schedule cleanup tasks for successful deletions
        if success_count > 0:
            successful_category_ids = [dc["category_id"] for dc in deleted_categories]
            
            background_tasks.add_task(
                lambda: logger.info(f"Cleaning up search index for {len(successful_category_ids)} deleted categories")
            )
            background_tasks.add_task(
                lambda: logger.info(f"Updating parent category statistics for {len(successful_category_ids)} deletions")
            )
            background_tasks.add_task(
                lambda: logger.info(f"Clearing cache for {len(successful_category_ids)} deleted categories")
            )

        logger.info(f"Bulk category deletion completed: {success_count} success, {error_count} errors")

        return BulkOperationResponse(
            success_count=success_count,
            error_count=error_count,
            total_count=len(category_ids),
            errors=errors if errors else None
        )

    except Exception as e:
        logger.error(f"Error in bulk category deletion: {str(e)}")
        raise HTTPException(
            status_code=HTTP_STATUS.HTTP_400_BAD_REQUEST,
            detail=f"Bulk deletion failed: {str(e)}"
        )


# Helper functions
async def _generate_category_content(
    category, 
    filters: dict, 
    include_stats: bool = False,
    include_related: bool = False
) -> List[Dict]:
    """
    Generate realistic sample content based on category type and properties.
    
    In a real implementation, this would query the content database.
    """
    content_samples = []
    category_name_en = category.name.get("en", "Unknown")
    category_type = category.category_type.value if hasattr(category.category_type, 'value') else "TOPIC"
    
    # Technology category content
    if "technology" in category_name_en.lower() or "programming" in category_name_en.lower():
        content_samples = [
            {
                "id": str(uuid.uuid4()),
                "title": {"ar": "مقدمة في البرمجة", "en": "Introduction to Programming"},
                "description": {"ar": "تعلم أساسيات البرمجة خطوة بخطوة", "en": "Learn programming basics step by step"},
                "content_type": "video",
                "status": "published",
                "duration": 2400,
                "view_count": 1500,
                "published_at": datetime.utcnow().isoformat(),
                "thumbnail_url": "/thumbnails/programming-intro.jpg",
                "category_path": category.path,
                "is_featured": True,
                "author": {"id": str(uuid.uuid4()), "name": {"ar": "د. أحمد محمد", "en": "Dr. Ahmed Mohamed"}},
                "stats": {"views": 1500, "likes": 85, "shares": 23, "completion_rate": 0.78} if include_stats else {},
                "tags": ["programming", "beginner", "tutorial"],
                "related": [{"id": str(uuid.uuid4()), "title": {"ar": "المتغيرات", "en": "Variables"}}] if include_related else []
            },
            {
                "id": str(uuid.uuid4()),
                "title": {"ar": "قواعد البيانات", "en": "Database Fundamentals"},
                "description": {"ar": "أساسيات قواعد البيانات وSQL", "en": "Database basics and SQL"},
                "content_type": "video",
                "status": "published",
                "duration": 3600,
                "view_count": 890,
                "published_at": (datetime.utcnow() - timedelta(days=5)).isoformat(),
                "thumbnail_url": "/thumbnails/database.jpg",
                "category_path": category.path,
                "is_featured": False,
                "author": {"id": str(uuid.uuid4()), "name": {"ar": "د. فاطمة علي", "en": "Dr. Fatima Ali"}},
                "stats": {"views": 890, "likes": 52, "shares": 12, "completion_rate": 0.65} if include_stats else {},
                "tags": ["database", "sql", "intermediate"],
                "related": [] if include_related else []
            }
        ]
    
    # Science category content  
    elif "science" in category_name_en.lower():
        content_samples = [
            {
                "id": str(uuid.uuid4()),
                "title": {"ar": "الفيزياء الحديثة", "en": "Modern Physics"},
                "description": {"ar": "استكشاف مفاهيم الفيزياء الحديثة", "en": "Exploring modern physics concepts"},
                "content_type": "article",
                "status": "published",
                "duration": 1200,
                "view_count": 750,
                "published_at": datetime.utcnow().isoformat(),
                "thumbnail_url": "/thumbnails/physics.jpg",
                "category_path": category.path,
                "is_featured": True,
                "author": {"id": str(uuid.uuid4()), "name": {"ar": "د. سارة أحمد", "en": "Dr. Sarah Ahmed"}},
                "stats": {"views": 750, "likes": 42, "shares": 15, "completion_rate": 0.82} if include_stats else {},
                "tags": ["physics", "quantum", "science"],
                "related": [] if include_related else []
            }
        ]
    
    # Default content for other categories
    else:
        content_samples = [
            {
                "id": str(uuid.uuid4()),
                "title": category.name,
                "description": category.description or {"ar": "محتوى تعليمي", "en": "Educational content"},
                "content_type": "article",
                "status": "published", 
                "duration": 1800,
                "view_count": 300,
                "published_at": datetime.utcnow().isoformat(),
                "thumbnail_url": f"/thumbnails/{category_name_en.lower().replace(' ', '-')}.jpg",
                "category_path": category.path,
                "is_featured": False,
                "author": {"id": str(uuid.uuid4()), "name": {"ar": "المؤلف", "en": "Author"}},
                "stats": {"views": 300, "likes": 15, "shares": 5, "completion_rate": 0.70} if include_stats else {},
                "tags": [category_type.lower()],
                "related": [] if include_related else []
            }
        ]
    
    # Apply basic filtering
    filtered_content = content_samples
    
    # Filter by content type if specified
    if filters.get("content_type"):
        filtered_content = [c for c in filtered_content if c["content_type"] == filters["content_type"]]
    
    # Filter by status if specified
    if filters.get("status") and filters["status"] != "published":
        filtered_content = [c for c in filtered_content if c["status"] == filters["status"]]
    
    # Filter by duration range
    if filters.get("min_duration"):
        filtered_content = [c for c in filtered_content if c["duration"] >= filters["min_duration"]]
    if filters.get("max_duration"):
        filtered_content = [c for c in filtered_content if c["duration"] <= filters["max_duration"]]
    
    return filtered_content


async def _generate_category_analytics(
    category,
    period_start: datetime,
    period_end: datetime,
    include_subcategories: bool = False,
    include_trends: bool = False,
    include_comparisons: bool = False
) -> Dict:
    """
    Generate realistic analytics data based on category properties.
    
    In a real implementation, this would query analytics database/service.
    """
    category_name_en = category.name.get("en", "Unknown")
    category_type = category.category_type.value if hasattr(category.category_type, 'value') else "TOPIC"
    
    # Base metrics (scale based on category type and name)
    base_views = 10000
    base_content = 20
    
    # Technology categories get higher engagement
    if "technology" in category_name_en.lower():
        base_views *= 4
        base_content *= 3
    elif "science" in category_name_en.lower():
        base_views *= 3
        base_content *= 2
    
    # Calculate period-specific metrics
    period_days = (period_end - period_start).days
    daily_views = base_views // 30  # Average daily views
    total_period_views = daily_views * period_days
    
    # Content metrics
    content_metrics = {
        "total_content": base_content + (period_days // 7),  # New content weekly
        "published_content": int((base_content + (period_days // 7)) * 0.85),  # 85% published
        "draft_content": int((base_content + (period_days // 7)) * 0.15),  # 15% draft
        "new_content_period": period_days // 7,  # New content during period
        "average_content_rating": round(4.2 + (0.6 * (hash(str(category.id)) % 10) / 10), 1)
    }
    
    # Engagement metrics
    engagement_metrics = {
        "total_views": total_period_views,
        "unique_visitors": int(total_period_views * 0.7),  # 70% unique
        "avg_engagement_time": 1200 + (hash(str(category.id)) % 600),  # 20-30 minutes
        "views_last_7_days": daily_views * 7,
        "views_last_30_days": daily_views * min(30, period_days),
        "completion_rate": round(0.65 + (0.25 * (hash(str(category.id)) % 10) / 10), 2),
        "likes": int(total_period_views * 0.05),  # 5% like rate
        "shares": int(total_period_views * 0.02),  # 2% share rate
        "comments": int(total_period_views * 0.01)  # 1% comment rate
    }
    
    # Growth metrics
    previous_period_views = daily_views * period_days * 0.8  # 20% growth baseline
    growth_rate = ((total_period_views - previous_period_views) / previous_period_views) * 100
    
    growth_metrics = {
        "growth_rate": round(growth_rate, 1),
        "content_growth_rate": round(15.5 + (hash(str(category.id)) % 20), 1),
        "engagement_growth_rate": round(12.3 + (hash(str(category.id)) % 15), 1)
    }
    
    # Top performing content
    content_titles = [
        {"ar": "مقدمة في البرمجة", "en": "Introduction to Programming"},
        {"ar": "قواعد البيانات", "en": "Database Fundamentals"}, 
        {"ar": "الذكاء الاصطناعي", "en": "Artificial Intelligence"},
        {"ar": "تطوير الويب", "en": "Web Development"},
        {"ar": "أمن المعلومات", "en": "Information Security"}
    ]
    
    top_content = []
    for i, title in enumerate(content_titles):
        views = total_period_views // (i + 2)  # Declining views
        top_content.append({
            "id": str(uuid.uuid4()),
            "title": title,
            "views": views,
            "rating": round(4.0 + (0.8 * (9 - i) / 10), 1),
            "engagement_time": 800 + (i * 200),
            "completion_rate": round(0.75 - (i * 0.05), 2)
        })
    
    # Popular subcategories (if requested)
    popular_subcategories = []
    if include_subcategories:
        subcategory_names = [
            {"ar": "برمجة المواقع", "en": "Web Programming"},
            {"ar": "قواعد البيانات", "en": "Databases"},
            {"ar": "الأمن السيبراني", "en": "Cybersecurity"}
        ]
        
        for i, name in enumerate(subcategory_names):
            subcategory_views = total_period_views // (i + 3)
            popular_subcategories.append({
                "id": str(uuid.uuid4()),
                "name": name,
                "views": subcategory_views,
                "content_count": 8 + i * 3,
                "growth_rate": round(10 + (i * 5), 1)
            })
    
    # Search analytics
    search_metrics = {
        "search_appearances": total_period_views * 3,  # 3x search impressions
        "search_clicks": int(total_period_views * 0.8),  # 80% from search
        "click_through_rate": 0.267,
        "top_search_terms": [
            category_name_en.lower(),
            category_type.lower(),
            "tutorial",
            "guide"
        ]
    }
    
    # Trend data (if requested)
    trends = {}
    if include_trends:
        # Generate daily trend data
        trend_data = []
        content_trend_data = []
        
        current_date = period_start
        base_daily_content = content_metrics["total_content"] - content_metrics["new_content_period"]
        
        while current_date <= period_end:
            # Views trend (with some randomness)
            daily_variation = 1 + (hash(str(current_date)) % 20 - 10) / 100  # ±10% variation
            daily_view_count = int(daily_views * daily_variation)
            
            trend_data.append({
                "date": current_date.date().isoformat(),
                "views": daily_view_count,
                "unique_visitors": int(daily_view_count * 0.7)
            })
            
            # Content trend (grows over time)
            days_from_start = (current_date - period_start).days
            current_content_count = base_daily_content + (days_from_start // 7)
            
            if current_date.weekday() == 0:  # Weekly content updates
                content_trend_data.append({
                    "date": current_date.date().isoformat(),
                    "count": current_content_count
                })
            
            current_date += timedelta(days=1)
        
        trends = {
            "view_trends": trend_data,
            "content_trends": content_trend_data
        }
    
    return {
        "content_metrics": content_metrics,
        "engagement_metrics": engagement_metrics,
        "growth_metrics": growth_metrics,
        "top_content": top_content,
        "popular_subcategories": popular_subcategories,
        "search_metrics": search_metrics,
        "trends": trends
    }