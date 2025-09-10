"""
Clean Content REST API Endpoints

This module provides clean architecture REST endpoints for content management
using controllers and business services to encapsulate logic.
"""

import uuid
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, BackgroundTasks

from api.v1.models.content import (
    ContentCreate, ContentUpdate, ContentResponse,
    ContentListResponse, ContentAnalytics,
    ContentBulkUpdateRequest, ContentScheduleRequest,
    ContentEngagementRequest, ContentEngagementResponse
)
from api.v1.models.common import PaginatedResponse, PaginationParams, SuccessResponse
from controllers.content_controller import ContentController
from db.session import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content", tags=["Content Management"])


# Dependency functions
def get_content_controller(db: Session = Depends(get_db)) -> ContentController:
    """Get content controller instance"""
    return ContentController(db)


def get_current_user() -> dict:
    """Get current authenticated user (placeholder)"""
    # This should be properly implemented with your authentication system
    return {"id": uuid.uuid4(), "email": "user@example.com"}


# Content CRUD Operations
@router.post(
    "/",
    response_model=ContentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new content",
    description="Create new multilingual content with comprehensive metadata support."
)
async def create_content(
    content: ContentCreate,
    background_tasks: BackgroundTasks,
    controller: ContentController = Depends(get_content_controller),
    current_user: dict = Depends(get_current_user)
) -> ContentResponse:
    """Create new content with comprehensive validation and processing."""
    try:
        current_user_id = current_user.get("id")
        if not current_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Create content through controller
        created_content = await controller.create_content(
            content, current_user_id
        )
        
        # Schedule background tasks
        background_tasks.add_task(
            _schedule_post_creation_tasks,
            created_content.id
        )
        
        return created_content
        
    except ValueError as e:
        logger.warning(f"Content creation validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Content creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Content creation failed"
        )


@router.get(
    "/",
    response_model=PaginatedResponse[ContentResponse],
    summary="Search and filter content",
    description="Advanced content search with multilingual support and comprehensive filtering."
)
async def search_content(
    # Search parameters
    query: Optional[str] = Query(None, description="Search query text"),
    language: str = Query("ar", description="Search in specific language"),
    
    # Content filters
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    category: Optional[uuid.UUID] = Query(None, description="Filter by category ID"),
    status: Optional[str] = Query(None, description="Filter by content status"),
    visibility: Optional[str] = Query(None, description="Filter by visibility"),
    
    # Date filters
    created_after: Optional[datetime] = Query(None, description="Created after date"),
    created_before: Optional[datetime] = Query(None, description="Created before date"),
    published_after: Optional[datetime] = Query(None, description="Published after date"),
    published_before: Optional[datetime] = Query(None, description="Published before date"),
    
    # Content properties
    has_media: Optional[bool] = Query(None, description="Filter content with/without media"),
    is_featured: Optional[bool] = Query(None, description="Filter featured content"),
    
    # Tags and custom filters
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    
    # Sorting
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    
    controller: ContentController = Depends(get_content_controller),
    current_user: dict = Depends(get_current_user)
) -> PaginatedResponse[ContentResponse]:
    """Execute advanced content search with comprehensive filtering and optimization."""
    try:
        current_user_id = current_user.get("id")
        
        # Build search filters
        filters = {
            "query": query,
            "language": language,
            "content_type": content_type,
            "category_id": category,
            "status": status,
            "visibility": visibility,
            "created_after": created_after,
            "created_before": created_before,
            "published_after": published_after,
            "published_before": published_before,
            "has_media": has_media,
            "is_featured": is_featured,
            "tags": tags,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        # Pagination parameters
        pagination = {"page": page, "limit": limit}
        
        # Search through controller
        results = await controller.search_content(
            filters, pagination, current_user_id
        )
        
        return results
        
    except ValueError as e:
        logger.warning(f"Content search validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Content search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Content search failed"
        )


@router.get(
    "/{content_id}",
    response_model=ContentResponse,
    summary="Get content by ID",
    description="Retrieve specific content by ID with optional language preference and additional data."
)
async def get_content(
    content_id: uuid.UUID,
    language: Optional[str] = Query(None, description="Preferred language (ar/en)"),
    include_analytics: bool = Query(False, description="Include engagement statistics"),
    track_view: bool = Query(True, description="Track this view in analytics"),
    controller: ContentController = Depends(get_content_controller),
    current_user: dict = Depends(get_current_user)
) -> ContentResponse:
    """Retrieve content with comprehensive data and access control."""
    try:
        current_user_id = current_user.get("id")
        
        # Get content through controller
        content = await controller.get_content(
            content_id, current_user_id, include_analytics
        )
        
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        
        return content
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Content retrieval validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Content retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve content"
        )


@router.put(
    "/{content_id}",
    response_model=ContentResponse,
    summary="Update existing content",
    description="Update existing content with partial or complete data changes."
)
async def update_content(
    content_id: uuid.UUID,
    content_update: ContentUpdate,
    background_tasks: BackgroundTasks,
    controller: ContentController = Depends(get_content_controller),
    current_user: dict = Depends(get_current_user)
) -> ContentResponse:
    """Update content with validation, version control, and background processing."""
    try:
        current_user_id = current_user.get("id")
        if not current_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Update content through controller
        updated_content = await controller.update_content(
            content_id, content_update, current_user_id
        )
        
        # Schedule background tasks
        background_tasks.add_task(
            _schedule_post_update_tasks,
            content_id,
            content_update.model_dump(exclude_unset=True)
        )
        
        return updated_content
        
    except ValueError as e:
        logger.warning(f"Content update validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Content update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Content update failed"
        )


@router.delete(
    "/{content_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete content",
    description="Soft delete content (changes status to deleted) with cleanup tasks."
)
async def delete_content(
    content_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    soft_delete: bool = Query(True, description="Soft delete vs hard delete"),
    controller: ContentController = Depends(get_content_controller),
    current_user: dict = Depends(get_current_user)
):
    """Soft delete content with comprehensive cleanup."""
    try:
        current_user_id = current_user.get("id")
        if not current_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Delete content through controller
        result = await controller.delete_content(
            content_id, current_user_id, soft_delete
        )
        
        # Schedule background cleanup tasks
        background_tasks.add_task(
            _schedule_post_deletion_tasks,
            content_id,
            soft_delete
        )
        
        return None
        
    except ValueError as e:
        logger.warning(f"Content deletion validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Content deletion failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Content deletion failed"
        )


# Content Workflow Operations
@router.post(
    "/{content_id}/publish",
    response_model=ContentResponse,
    summary="Publish content",
    description="Publish content immediately with validation and background processing."
)
async def publish_content(
    content_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    controller: ContentController = Depends(get_content_controller),
    current_user: dict = Depends(get_current_user)
) -> ContentResponse:
    """Publish content with comprehensive processing and distribution."""
    try:
        current_user_id = current_user.get("id")
        if not current_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Publish content through controller
        published_content = await controller.publish_content(
            content_id, current_user_id
        )
        
        # Schedule background tasks for publication
        background_tasks.add_task(
            _schedule_post_publication_tasks,
            content_id
        )
        
        return published_content
        
    except ValueError as e:
        logger.warning(f"Content publication validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Content publication failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Content publication failed"
        )


@router.post(
    "/{content_id}/schedule",
    response_model=ContentResponse,
    summary="Schedule content publication",
    description="Schedule content for future publication with validation."
)
async def schedule_content(
    content_id: uuid.UUID,
    schedule_request: ContentScheduleRequest,
    background_tasks: BackgroundTasks,
    controller: ContentController = Depends(get_content_controller),
    current_user: dict = Depends(get_current_user)
) -> ContentResponse:
    """Schedule content for future publication."""
    try:
        current_user_id = current_user.get("id")
        if not current_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Schedule content through controller
        scheduled_content = await controller.schedule_content(
            content_id, schedule_request, current_user_id
        )
        
        # Schedule background tasks
        background_tasks.add_task(
            _schedule_post_scheduling_tasks,
            content_id,
            schedule_request.scheduled_at
        )
        
        return scheduled_content
        
    except ValueError as e:
        logger.warning(f"Content scheduling validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Content scheduling failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Content scheduling failed"
        )


# Bulk Operations
@router.post(
    "/bulk/update",
    response_model=Dict[str, Any],
    summary="Bulk update content",
    description="Update multiple content items efficiently in a single operation."
)
async def bulk_update_content(
    bulk_request: ContentBulkUpdateRequest,
    background_tasks: BackgroundTasks,
    controller: ContentController = Depends(get_content_controller),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Execute bulk content updates with comprehensive error handling."""
    try:
        current_user_id = current_user.get("id")
        if not current_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Execute bulk update through controller
        results = await controller.bulk_update_content(
            bulk_request, current_user_id
        )
        
        # Schedule background tasks for successful updates
        if results.get("successful_updates"):
            background_tasks.add_task(
                _schedule_post_bulk_update_tasks,
                [u["content_id"] for u in results["successful_updates"]]
            )
        
        return results
        
    except ValueError as e:
        logger.warning(f"Bulk update validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Bulk update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bulk update failed"
        )


# Engagement Operations
@router.post(
    "/{content_id}/like",
    response_model=ContentEngagementResponse,
    summary="Like content",
    description="Add a like to content with validation."
)
async def like_content(
    content_id: uuid.UUID,
    controller: ContentController = Depends(get_content_controller),
    current_user: dict = Depends(get_current_user)
) -> ContentEngagementResponse:
    """Add a like to content."""
    try:
        current_user_id = current_user.get("id")
        if not current_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Add like through controller
        result = await controller.add_like(content_id, current_user_id)
        
        return ContentEngagementResponse(
            success=result.get("success", False),
            content_id=content_id,
            action="like",
            new_count=result.get("new_like_count", 0),
            timestamp=datetime.utcnow()
        )
        
    except ValueError as e:
        logger.warning(f"Like operation validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Like operation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Like operation failed"
        )


@router.post(
    "/{content_id}/share",
    response_model=ContentEngagementResponse,
    summary="Share content",
    description="Record a content share with validation."
)
async def share_content(
    content_id: uuid.UUID,
    controller: ContentController = Depends(get_content_controller),
    current_user: dict = Depends(get_current_user)
) -> ContentEngagementResponse:
    """Record a content share."""
    try:
        current_user_id = current_user.get("id")
        if not current_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Add share through controller
        result = await controller.add_share(content_id, current_user_id)
        
        return ContentEngagementResponse(
            success=result.get("success", False),
            content_id=content_id,
            action="share",
            new_count=result.get("new_share_count", 0),
            timestamp=datetime.utcnow()
        )
        
    except ValueError as e:
        logger.warning(f"Share operation validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Share operation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Share operation failed"
        )


# Analytics
@router.get(
    "/{content_id}/analytics",
    response_model=ContentAnalytics,
    summary="Get content analytics",
    description="Get comprehensive content analytics with authorization."
)
async def get_content_analytics(
    content_id: uuid.UUID,
    controller: ContentController = Depends(get_content_controller),
    current_user: dict = Depends(get_current_user)
) -> ContentAnalytics:
    """Get comprehensive content analytics."""
    try:
        current_user_id = current_user.get("id")
        if not current_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Get analytics through controller
        analytics = await controller.get_content_analytics(
            content_id, current_user_id
        )
        
        return analytics
        
    except ValueError as e:
        logger.warning(f"Analytics access validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Analytics retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics"
        )


# Background task functions
async def _schedule_post_creation_tasks(content_id: uuid.UUID) -> None:
    """Schedule tasks to run after content creation"""
    logger.info(f"Scheduling post-creation tasks for content: {content_id}")
    # In a real implementation, this would:
    # - Index content for search
    # - Generate thumbnails
    # - Send notifications
    # - Update caches


async def _schedule_post_update_tasks(
    content_id: uuid.UUID,
    updated_fields: Dict[str, Any]
) -> None:
    """Schedule tasks to run after content update"""
    logger.info(f"Scheduling post-update tasks for content: {content_id}")
    # In a real implementation, this would:
    # - Update search index
    # - Clear caches
    # - Sync to external systems
    # - Send notifications if published


async def _schedule_post_deletion_tasks(
    content_id: uuid.UUID,
    soft_delete: bool
) -> None:
    """Schedule tasks to run after content deletion"""
    logger.info(f"Scheduling post-deletion tasks for content: {content_id}")
    # In a real implementation, this would:
    # - Remove from search index
    # - Clean up files
    # - Clear caches
    # - Update category counts


async def _schedule_post_publication_tasks(content_id: uuid.UUID) -> None:
    """Schedule tasks to run after content publication"""
    logger.info(f"Scheduling post-publication tasks for content: {content_id}")
    # In a real implementation, this would:
    # - Index for search
    # - Generate SEO data
    # - Notify subscribers
    # - Sync to social platforms


async def _schedule_post_scheduling_tasks(
    content_id: uuid.UUID,
    scheduled_at: datetime
) -> None:
    """Schedule tasks to run after content scheduling"""
    logger.info(f"Scheduling post-scheduling tasks for content: {content_id}")
    # In a real implementation, this would:
    # - Add to publication queue
    # - Set up cron job
    # - Send confirmation notifications


async def _schedule_post_bulk_update_tasks(content_ids: List[str]) -> None:
    """Schedule tasks to run after bulk updates"""
    logger.info(f"Scheduling post-bulk-update tasks for {len(content_ids)} content items")
    # In a real implementation, this would:
    # - Bulk update search index
    # - Clear multiple caches
    # - Send bulk notifications