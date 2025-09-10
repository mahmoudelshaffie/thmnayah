"""
Content Controller

Clean architecture controller that handles business logic coordination
for content management operations. Acts as the application layer between
endpoints and business services.
"""

import uuid
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session

from api.v1.models.content import (
    ContentCreate, ContentUpdate, ContentResponse,
    ContentListResponse, ContentAnalytics,
    ContentBulkUpdateRequest, ContentScheduleRequest
)
from api.v1.models.common import PaginatedResponse, PaginationMeta
from services.content import ContentService
from models.content import ContentStatusEnum, ContentTypeEnum, ContentVisibilityEnum

logger = logging.getLogger(__name__)


class ContentController:
    """
    Application controller for content management.
    
    Coordinates between the presentation layer (endpoints) and business layer (services).
    Handles request validation, business rule enforcement, and response formatting.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.content_service = ContentService(db)
    
    async def create_content(
        self,
        content_data: ContentCreate,
        current_user_id: uuid.UUID
    ) -> ContentResponse:
        """
        Create new content with business validation.
        
        Args:
            content_data: Content creation data
            current_user_id: ID of user creating content
            
        Returns:
            Created content response
            
        Raises:
            ValueError: For business rule violations
        """
        try:
            # Business validation
            self._validate_create_permissions(current_user_id)
            self._validate_content_data(content_data)
            
            # Create through service layer
            content_response = await self.content_service.create_content(
                content_data, current_user_id
            )
            
            logger.info(
                f"Content created successfully: {content_response.id}",
                extra={
                    "content_id": str(content_response.id),
                    "user_id": str(current_user_id),
                    "content_type": content_response.content_type
                }
            )
            
            return content_response
            
        except ValueError as e:
            logger.warning(f"Content creation failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in content creation: {str(e)}")
            raise ValueError("Content creation failed due to system error")
    
    async def get_content(
        self,
        content_id: uuid.UUID,
        current_user_id: Optional[uuid.UUID] = None,
        include_analytics: bool = False
    ) -> Optional[ContentResponse]:
        """
        Retrieve content with access control.
        
        Args:
            content_id: Content ID to retrieve
            current_user_id: Optional user ID for access control
            include_analytics: Whether to include analytics data
            
        Returns:
            Content response or None if not found/unauthorized
        """
        try:
            # Get content through service
            content = await self.content_service.get_content(
                content_id,
                include_analytics=include_analytics
            )
            
            if not content:
                return None
            
            # Apply access control
            if not self._has_content_access(content, current_user_id):
                logger.warning(
                    f"Access denied to content {content_id} for user {current_user_id}"
                )
                return None
            
            # Track view if user is provided and content is public
            if current_user_id and content.visibility == ContentVisibilityEnum.PUBLIC:
                await self.content_service.increment_view_count(content_id)
            
            return content
            
        except Exception as e:
            logger.error(f"Error retrieving content {content_id}: {str(e)}")
            raise ValueError("Failed to retrieve content")
    
    async def update_content(
        self,
        content_id: uuid.UUID,
        content_update: ContentUpdate,
        current_user_id: uuid.UUID
    ) -> ContentResponse:
        """
        Update content with business validation.
        
        Args:
            content_id: Content to update
            content_update: Update data
            current_user_id: User performing update
            
        Returns:
            Updated content response
        """
        try:
            # Validate update permissions
            existing_content = await self.content_service.get_content(content_id)
            if not existing_content:
                raise ValueError("Content not found")
            
            self._validate_update_permissions(existing_content, current_user_id)
            self._validate_update_data(content_update, existing_content)
            
            # Update through service layer
            updated_content = await self.content_service.update_content(
                content_id, content_update, current_user_id
            )
            
            logger.info(
                f"Content updated successfully: {content_id}",
                extra={
                    "content_id": str(content_id),
                    "user_id": str(current_user_id),
                    "update_fields": content_update.model_dump(exclude_unset=True).keys()
                }
            )
            
            return updated_content
            
        except ValueError as e:
            logger.warning(f"Content update failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in content update: {str(e)}")
            raise ValueError("Content update failed due to system error")
    
    async def delete_content(
        self,
        content_id: uuid.UUID,
        current_user_id: uuid.UUID,
        soft_delete: bool = True
    ) -> Dict[str, Any]:
        """
        Delete content with proper authorization.
        
        Args:
            content_id: Content to delete
            current_user_id: User performing deletion
            soft_delete: Whether to soft delete
            
        Returns:
            Deletion result
        """
        try:
            # Validate delete permissions
            existing_content = await self.content_service.get_content(content_id)
            if not existing_content:
                raise ValueError("Content not found")
            
            self._validate_delete_permissions(existing_content, current_user_id)
            
            # Delete through service layer
            result = await self.content_service.delete_content(
                content_id, current_user_id, soft_delete
            )
            
            logger.info(
                f"Content deleted successfully: {content_id}",
                extra={
                    "content_id": str(content_id),
                    "user_id": str(current_user_id),
                    "soft_delete": soft_delete
                }
            )
            
            return result
            
        except ValueError as e:
            logger.warning(f"Content deletion failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in content deletion: {str(e)}")
            raise ValueError("Content deletion failed due to system error")
    
    async def search_content(
        self,
        filters: Dict[str, Any],
        pagination: Dict[str, int],
        current_user_id: Optional[uuid.UUID] = None
    ) -> PaginatedResponse[ContentResponse]:
        """
        Search content with filtering and pagination.
        
        Args:
            filters: Search filters
            pagination: Pagination parameters
            current_user_id: Optional user ID for access control
            
        Returns:
            Paginated content results
        """
        try:
            # Apply access control filters
            self._apply_access_filters(filters, current_user_id)
            
            # Search through service layer
            results = await self.content_service.search_content(
                **filters,
                page=pagination.get("page", 1),
                limit=pagination.get("limit", 20)
            )
            
            logger.debug(
                f"Content search completed: {len(results.data)} results",
                extra={
                    "user_id": str(current_user_id) if current_user_id else None,
                    "filters": {k: v for k, v in filters.items() if v is not None},
                    "results_count": len(results.data)
                }
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error in content search: {str(e)}")
            raise ValueError("Content search failed")
    
    async def publish_content(
        self,
        content_id: uuid.UUID,
        current_user_id: uuid.UUID
    ) -> ContentResponse:
        """
        Publish content after validation.
        
        Args:
            content_id: Content to publish
            current_user_id: User performing action
            
        Returns:
            Published content
        """
        try:
            # Validate publish permissions
            existing_content = await self.content_service.get_content(content_id)
            if not existing_content:
                raise ValueError("Content not found")
            
            self._validate_publish_permissions(existing_content, current_user_id)
            self._validate_content_ready_for_publication(existing_content)
            
            # Publish through service layer
            published_content = await self.content_service.publish_content(
                content_id, current_user_id
            )
            
            logger.info(
                f"Content published successfully: {content_id}",
                extra={
                    "content_id": str(content_id),
                    "user_id": str(current_user_id)
                }
            )
            
            return published_content
            
        except ValueError as e:
            logger.warning(f"Content publication failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in content publication: {str(e)}")
            raise ValueError("Content publication failed due to system error")
    
    async def schedule_content(
        self,
        content_id: uuid.UUID,
        schedule_request: ContentScheduleRequest,
        current_user_id: uuid.UUID
    ) -> ContentResponse:
        """
        Schedule content for future publication.
        
        Args:
            content_id: Content to schedule
            schedule_request: Scheduling parameters
            current_user_id: User performing action
            
        Returns:
            Scheduled content
        """
        try:
            # Validate scheduling permissions
            existing_content = await self.content_service.get_content(content_id)
            if not existing_content:
                raise ValueError("Content not found")
            
            self._validate_publish_permissions(existing_content, current_user_id)
            self._validate_schedule_request(schedule_request)
            
            # Schedule through service layer
            scheduled_content = await self.content_service.schedule_content(
                content_id, schedule_request.scheduled_at, current_user_id
            )
            
            logger.info(
                f"Content scheduled successfully: {content_id} for {schedule_request.scheduled_at}",
                extra={
                    "content_id": str(content_id),
                    "scheduled_at": schedule_request.scheduled_at.isoformat(),
                    "user_id": str(current_user_id)
                }
            )
            
            return scheduled_content
            
        except ValueError as e:
            logger.warning(f"Content scheduling failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in content scheduling: {str(e)}")
            raise ValueError("Content scheduling failed due to system error")
    
    async def bulk_update_content(
        self,
        bulk_request: ContentBulkUpdateRequest,
        current_user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Perform bulk content updates.
        
        Args:
            bulk_request: Bulk update request
            current_user_id: User performing updates
            
        Returns:
            Bulk operation results
        """
        try:
            self._validate_bulk_request(bulk_request)
            
            results = {
                "successful_updates": [],
                "failed_updates": [],
                "total_requested": len(bulk_request.content_ids)
            }
            
            # Process each content item
            for content_id in bulk_request.content_ids:
                try:
                    # Create update model from bulk updates
                    update_data = ContentUpdate(**bulk_request.updates)
                    
                    # Update content
                    updated_content = await self.update_content(
                        content_id, update_data, current_user_id
                    )
                    
                    results["successful_updates"].append({
                        "content_id": str(content_id),
                        "title": updated_content.title,
                        "updated_at": updated_content.updated_at.isoformat()
                    })
                    
                except Exception as e:
                    results["failed_updates"].append({
                        "content_id": str(content_id),
                        "error": str(e)
                    })
            
            results["success_count"] = len(results["successful_updates"])
            results["error_count"] = len(results["failed_updates"])
            
            logger.info(
                f"Bulk update completed: {results['success_count']}/{results['total_requested']} successful",
                extra={
                    "user_id": str(current_user_id),
                    "success_count": results["success_count"],
                    "error_count": results["error_count"]
                }
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error in bulk content update: {str(e)}")
            raise ValueError("Bulk content update failed")
    
    async def get_content_analytics(
        self,
        content_id: uuid.UUID,
        current_user_id: uuid.UUID
    ) -> ContentAnalytics:
        """
        Get content analytics with authorization.
        
        Args:
            content_id: Content to analyze
            current_user_id: User requesting analytics
            
        Returns:
            Content analytics data
        """
        try:
            # Validate analytics permissions
            existing_content = await self.content_service.get_content(content_id)
            if not existing_content:
                raise ValueError("Content not found")
            
            self._validate_analytics_permissions(existing_content, current_user_id)
            
            # Get analytics through service layer
            analytics = await self.content_service.get_content_analytics(
                content_id, current_user_id
            )
            
            return analytics
            
        except ValueError as e:
            logger.warning(f"Content analytics access failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error getting content analytics: {str(e)}")
            raise ValueError("Failed to retrieve content analytics")
    
    # Engagement actions
    
    async def add_like(
        self,
        content_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Add a like to content"""
        try:
            result = await self.content_service.add_like(content_id, user_id)
            
            if result:
                # Get updated content for new count
                content = await self.content_service.get_content(content_id)
                return {
                    "success": True,
                    "content_id": str(content_id),
                    "new_like_count": content.like_count if content else 0,
                    "action": "like"
                }
            else:
                return {
                    "success": False,
                    "content_id": str(content_id),
                    "error": "Failed to add like"
                }
                
        except Exception as e:
            logger.error(f"Error adding like to content {content_id}: {str(e)}")
            raise ValueError("Failed to add like")
    
    async def add_share(
        self,
        content_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Add a share to content"""
        try:
            result = await self.content_service.add_share(content_id, user_id)
            
            if result:
                # Get updated content for new count
                content = await self.content_service.get_content(content_id)
                return {
                    "success": True,
                    "content_id": str(content_id),
                    "new_share_count": content.share_count if content else 0,
                    "action": "share"
                }
            else:
                return {
                    "success": False,
                    "content_id": str(content_id),
                    "error": "Failed to add share"
                }
                
        except Exception as e:
            logger.error(f"Error adding share to content {content_id}: {str(e)}")
            raise ValueError("Failed to add share")
    
    # Validation methods
    
    def _validate_create_permissions(self, user_id: uuid.UUID) -> None:
        """Validate user can create content"""
        # In a real implementation, check user roles/permissions
        if not user_id:
            raise ValueError("Authentication required to create content")
    
    def _validate_content_data(self, content_data: ContentCreate) -> None:
        """Validate content creation data"""
        if not content_data.title or not any(content_data.title.values()):
            raise ValueError("Content title is required in at least one language")
        
        # Validate content type specific requirements
        if content_data.content_type in [ContentTypeEnum.VIDEO, ContentTypeEnum.AUDIO]:
            if not content_data.file_url:
                raise ValueError(f"{content_data.content_type.value} content requires a file URL")
            if not content_data.duration:
                raise ValueError(f"{content_data.content_type.value} content requires duration")
    
    def _has_content_access(
        self,
        content: ContentResponse,
        user_id: Optional[uuid.UUID]
    ) -> bool:
        """Check if user has access to content"""
        # Public content is always accessible
        if content.visibility == ContentVisibilityEnum.PUBLIC:
            return True
        
        # Private/restricted content requires authentication
        if not user_id:
            return False
        
        # Owner always has access
        if content.author_id == user_id:
            return True
        
        # In a real implementation, check additional permissions
        return False
    
    def _validate_update_permissions(
        self,
        content: ContentResponse,
        user_id: uuid.UUID
    ) -> None:
        """Validate user can update content"""
        if content.author_id != user_id:
            # In a real implementation, check editor/admin roles
            raise ValueError("Insufficient permissions to update this content")
    
    def _validate_update_data(
        self,
        update_data: ContentUpdate,
        existing_content: ContentResponse
    ) -> None:
        """Validate content update data"""
        # Prevent certain status transitions
        if hasattr(update_data, 'status') and update_data.status:
            if (existing_content.status == ContentStatusEnum.PUBLISHED and
                update_data.status == ContentStatusEnum.DRAFT):
                raise ValueError("Cannot unpublish content by changing to draft status")
    
    def _validate_delete_permissions(
        self,
        content: ContentResponse,
        user_id: uuid.UUID
    ) -> None:
        """Validate user can delete content"""
        if content.author_id != user_id:
            # In a real implementation, check admin roles
            raise ValueError("Insufficient permissions to delete this content")
        
        if content.status == ContentStatusEnum.PUBLISHED:
            raise ValueError("Cannot delete published content. Archive it first.")
    
    def _validate_publish_permissions(
        self,
        content: ContentResponse,
        user_id: uuid.UUID
    ) -> None:
        """Validate user can publish content"""
        if content.author_id != user_id:
            # In a real implementation, check publisher role
            raise ValueError("Insufficient permissions to publish this content")
    
    def _validate_content_ready_for_publication(self, content: ContentResponse) -> None:
        """Validate content is ready for publication"""
        if not content.title or not any(content.title.values()):
            raise ValueError("Content title is required for publication")
        
        if not content.description:
            raise ValueError("Content description is required for publication")
        
        # Content type specific validations
        if content.content_type in [ContentTypeEnum.VIDEO, ContentTypeEnum.AUDIO]:
            if not content.file_url:
                raise ValueError(f"{content.content_type.value} content requires a file for publication")
    
    def _validate_schedule_request(self, schedule_request: ContentScheduleRequest) -> None:
        """Validate scheduling request"""
        if schedule_request.scheduled_at <= datetime.utcnow():
            raise ValueError("Scheduled time must be in the future")
    
    def _validate_analytics_permissions(
        self,
        content: ContentResponse,
        user_id: uuid.UUID
    ) -> None:
        """Validate user can view analytics"""
        if content.author_id != user_id:
            # In a real implementation, check analytics viewer role
            raise ValueError("Insufficient permissions to view content analytics")
    
    def _validate_bulk_request(self, bulk_request: ContentBulkUpdateRequest) -> None:
        """Validate bulk update request"""
        if len(bulk_request.content_ids) > 50:
            raise ValueError("Bulk updates limited to 50 items maximum")
        
        if not bulk_request.updates:
            raise ValueError("No updates specified for bulk operation")
        
        # Validate update fields
        restricted_fields = {"id", "created_at", "created_by", "author_id"}
        invalid_fields = set(bulk_request.updates.keys()) & restricted_fields
        if invalid_fields:
            raise ValueError(f"Cannot bulk update restricted fields: {', '.join(invalid_fields)}")
    
    def _apply_access_filters(
        self,
        filters: Dict[str, Any],
        user_id: Optional[uuid.UUID]
    ) -> None:
        """Apply access control filters to search"""
        if not user_id:
            # Anonymous users only see public published content
            filters["visibility"] = ContentVisibilityEnum.PUBLIC
            filters["status"] = ContentStatusEnum.PUBLISHED
        else:
            # Authenticated users can see their own content plus public content
            # In a real implementation, this would be more sophisticated
            if "author_id" not in filters:
                filters["visibility"] = ContentVisibilityEnum.PUBLIC