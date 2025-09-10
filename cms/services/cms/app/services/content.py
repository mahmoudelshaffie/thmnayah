"""
Content Service

This module provides business logic for content management including validation,
lifecycle management, multilingual support, and category integration.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

from models.content import Content, ContentTypeEnum, ContentStatusEnum, ContentVisibilityEnum
from repositories.content import ContentRepository
from business.content_business_service import ContentBusinessService
from api.v1.models.content import (
    ContentCreate, 
    ContentUpdate, 
    ContentResponse,
    ContentAnalytics,
    ContentSearchFilters
)
from api.v1.models.common import PaginatedResponse


logger = logging.getLogger(__name__)


class ContentService:
    """
    Business service for content management.
    
    Handles:
    - Content CRUD with validation
    - Content lifecycle management (draft, review, published)
    - Multilingual content support
    - Category relationships
    - Content analytics and engagement
    - Business rules enforcement
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = ContentRepository()
        self.business_service = ContentBusinessService(db)
    
    # Core CRUD Operations
    
    async def create_content(
        self, 
        content_data: ContentCreate,
        current_user_id: uuid.UUID
    ) -> ContentResponse:
        """
        Create new content with validation and business rules.
        
        Args:
            content_data: Content creation data
            current_user_id: ID of user creating the content
            
        Returns:
            Created content response
            
        Raises:
            ValueError: For validation errors
        """
        try:
            # Create content using business service with full business rules
            content_dict = content_data.model_dump()
            db_content = self.business_service.create_content_with_business_rules(
                content_dict, current_user_id
            )
            
            # Log creation
            logger.info(
                f"Content created: {db_content.id} by user {current_user_id}",
                extra={
                    "content_id": str(db_content.id),
                    "user_id": str(current_user_id),
                    "content_type": db_content.content_type.value,
                    "content_title": db_content.get_title()
                }
            )
            
            # Convert to response model
            return self._content_to_response(db_content)
            
        except ValueError as e:
            logger.warning(f"Content creation validation failed: {str(e)}")
            raise
        except IntegrityError as e:
            logger.error(f"Database integrity error during content creation: {str(e)}")
            raise ValueError("Content creation failed due to data conflicts")
        except Exception as e:
            logger.error(f"Unexpected error during content creation: {str(e)}")
            raise ValueError("Content creation failed")
    
    async def get_content(
        self, 
        content_id: uuid.UUID,
        include_category: bool = True,
        include_analytics: bool = False
    ) -> Optional[ContentResponse]:
        """
        Get content by ID with optional related data.
        
        Args:
            content_id: Content ID to retrieve
            include_category: Include category information
            include_analytics: Include analytics data
            
        Returns:
            Content response or None if not found
        """
        try:
            db_content = self.repository.get_by_id(self.db, content_id)
            if not db_content:
                return None
            
            response = self._content_to_response(
                db_content,
                include_category=include_category,
                include_analytics=include_analytics
            )
            
            return response
            
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
        Update existing content with validation.
        
        Args:
            content_id: Content to update
            content_update: Update data
            current_user_id: ID of user making update
            
        Returns:
            Updated content response
        """
        try:
            # Update content using business service with full business rules
            update_dict = content_update.model_dump(exclude_unset=True)
            db_content = self.business_service.update_content_with_business_rules(
                content_id, update_dict, current_user_id
            )
            
            # Log update
            logger.info(
                f"Content updated: {content_id} by user {current_user_id}",
                extra={
                    "content_id": str(content_id),
                    "user_id": str(current_user_id),
                    "updates": content_update.model_dump(exclude_unset=True)
                }
            )
            
            return self._content_to_response(db_content)
            
        except ValueError as e:
            logger.warning(f"Content update validation failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error updating content {content_id}: {str(e)}")
            raise ValueError("Content update failed")
    
    async def delete_content(
        self,
        content_id: uuid.UUID,
        current_user_id: uuid.UUID,
        soft_delete: bool = True
    ) -> Dict[str, Any]:
        """
        Delete content with proper cleanup.
        
        Args:
            content_id: Content to delete
            current_user_id: ID of user performing deletion
            soft_delete: Whether to soft delete (mark as deleted) or hard delete
            
        Returns:
            Dict with deletion results
        """
        try:
            # Get content details before deletion
            content = await self.get_content(content_id)
            if not content:
                raise ValueError(f"Content {content_id} not found")
            
            # Check permissions
            existing_content = self.repository.get_by_id(self.db, content_id)
            self._validate_content_delete_permissions(existing_content, current_user_id)
            
            # Delete via repository
            result = self.repository.delete_content(
                db=self.db,
                content_id=content_id,
                soft_delete=soft_delete
            )
            
            if result:
                deletion_result = {
                    "success": True,
                    "content_id": str(content_id),
                    "content_title": content.title,
                    "deletion_timestamp": datetime.utcnow().isoformat(),
                    "deleted_by": str(current_user_id),
                    "soft_delete": soft_delete
                }
                
                logger.info(
                    f"Content deleted successfully: {content_id}",
                    extra={
                        "content_id": str(content_id),
                        "user_id": str(current_user_id),
                        "soft_delete": soft_delete
                    }
                )
                
                return deletion_result
            
            raise ValueError("Content deletion failed in repository")
            
        except ValueError as e:
            logger.warning(f"Content deletion validation failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error deleting content {content_id}: {str(e)}")
            raise ValueError(f"Content deletion failed: {str(e)}")
    
    # Search and Listing
    
    async def search_content(
        self,
        *,
        query: Optional[str] = None,
        language: str = 'ar',
        content_type: Optional[ContentTypeEnum] = None,
        status: Optional[ContentStatusEnum] = None,
        visibility: Optional[ContentVisibilityEnum] = None,
        category_id: Optional[uuid.UUID] = None,
        author_id: Optional[uuid.UUID] = None,
        is_featured: Optional[bool] = None,
        published_after: Optional[datetime] = None,
        published_before: Optional[datetime] = None,
        min_rating: Optional[int] = None,
        tags: Optional[List[str]] = None,
        page: int = 1,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> PaginatedResponse[ContentResponse]:
        """
        Search content with filters and pagination.
        
        Args:
            query: Text search query
            language: Search language preference
            content_type: Filter by content type
            status: Filter by content status
            visibility: Filter by visibility
            category_id: Filter by category
            author_id: Filter by author
            is_featured: Filter featured content
            published_after: Filter by publication date
            published_before: Filter by publication date
            min_rating: Minimum rating filter
            tags: Filter by tags
            page: Page number (1-based)
            limit: Items per page
            sort_by: Sort field
            sort_order: Sort direction (asc/desc)
            
        Returns:
            Paginated content responses
        """
        try:
            skip = (page - 1) * limit
            
            # Get content from repository
            content_list = self.repository.search_content(
                db=self.db,
                query=query,
                language=language,
                content_type=content_type,
                status=status,
                visibility=visibility,
                category_id=category_id,
                author_id=author_id,
                is_featured=is_featured,
                published_after=published_after,
                published_before=published_before,
                min_rating=min_rating,
                tags=tags,
                skip=skip,
                limit=limit + 1,  # Get one extra to check for next page
                sort_by=sort_by,
                sort_order=sort_order
            )
            
            has_next = len(content_list) > limit
            if has_next:
                content_list = content_list[:limit]
            
            # Convert to response models
            content_responses = [
                self._content_to_response(content) for content in content_list
            ]
            
            # Create pagination info (simplified - in real implementation would get actual count)
            total = skip + len(content_responses) + (1 if has_next else 0)
            
            return PaginatedResponse(
                data=content_responses,
                pagination={
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "total_pages": (total + limit - 1) // limit,
                    "has_next": has_next,
                    "has_prev": page > 1
                }
            )
            
        except Exception as e:
            logger.error(f"Error searching content: {str(e)}")
            raise ValueError("Content search failed")
    
    async def get_published_content(
        self,
        *,
        category_id: Optional[uuid.UUID] = None,
        content_type: Optional[ContentTypeEnum] = None,
        is_featured: Optional[bool] = None,
        limit: int = 10
    ) -> List[ContentResponse]:
        """Get published content with optional filters"""
        try:
            content_list = self.repository.get_published_content(
                db=self.db,
                category_id=category_id,
                content_type=content_type,
                is_featured=is_featured,
                limit=limit
            )
            
            return [self._content_to_response(content) for content in content_list]
            
        except Exception as e:
            logger.error(f"Error getting published content: {str(e)}")
            raise ValueError("Failed to retrieve published content")
    
    async def get_featured_content(
        self,
        *,
        category_id: Optional[uuid.UUID] = None,
        limit: int = 5
    ) -> List[ContentResponse]:
        """Get featured content"""
        try:
            content_list = self.repository.get_featured_content(
                db=self.db,
                category_id=category_id,
                limit=limit
            )
            
            return [self._content_to_response(content) for content in content_list]
            
        except Exception as e:
            logger.error(f"Error getting featured content: {str(e)}")
            raise ValueError("Failed to retrieve featured content")
    
    # Content Lifecycle Management
    
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
            # Publish content using business service with full business rules
            published_content = self.business_service.publish_content_with_business_rules(
                content_id, current_user_id
            )
            
            logger.info(
                f"Content published: {content_id} by user {current_user_id}",
                extra={
                    "content_id": str(content_id),
                    "user_id": str(current_user_id)
                }
            )
            
            return self._content_to_response(published_content)
            
        except ValueError as e:
            logger.warning(f"Content publication failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error publishing content {content_id}: {str(e)}")
            raise ValueError("Content publication failed")
    
    async def archive_content(
        self,
        content_id: uuid.UUID,
        current_user_id: uuid.UUID
    ) -> ContentResponse:
        """
        Archive content.
        
        Args:
            content_id: Content to archive
            current_user_id: User performing action
            
        Returns:
            Archived content
        """
        try:
            # Get and validate content
            content = self.repository.get_by_id(self.db, content_id)
            if not content:
                raise ValueError("Content not found")
            
            # Check permissions
            self._validate_content_update_permissions(content, current_user_id)
            
            # Archive via repository
            archived_content = self.repository.archive_content(self.db, content_id)
            
            logger.info(
                f"Content archived: {content_id} by user {current_user_id}",
                extra={
                    "content_id": str(content_id),
                    "user_id": str(current_user_id)
                }
            )
            
            return self._content_to_response(archived_content)
            
        except ValueError as e:
            logger.warning(f"Content archival failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error archiving content {content_id}: {str(e)}")
            raise ValueError("Content archival failed")
    
    async def schedule_content(
        self,
        content_id: uuid.UUID,
        scheduled_at: datetime,
        current_user_id: uuid.UUID
    ) -> ContentResponse:
        """
        Schedule content for future publication.
        
        Args:
            content_id: Content to schedule
            scheduled_at: When to publish
            current_user_id: User performing action
            
        Returns:
            Scheduled content
        """
        try:
            # Get and validate content
            content = self.repository.get_by_id(self.db, content_id)
            if not content:
                raise ValueError("Content not found")
            
            # Check permissions
            self._validate_content_update_permissions(content, current_user_id)
            
            # Schedule via repository
            scheduled_content = self.repository.schedule_content(
                db=self.db,
                content_id=content_id,
                scheduled_at=scheduled_at
            )
            
            logger.info(
                f"Content scheduled: {content_id} for {scheduled_at} by user {current_user_id}",
                extra={
                    "content_id": str(content_id),
                    "scheduled_at": scheduled_at.isoformat(),
                    "user_id": str(current_user_id)
                }
            )
            
            return self._content_to_response(scheduled_content)
            
        except ValueError as e:
            logger.warning(f"Content scheduling failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error scheduling content {content_id}: {str(e)}")
            raise ValueError("Content scheduling failed")
    
    # Engagement Methods
    
    async def increment_view_count(self, content_id: uuid.UUID) -> bool:
        """Increment view count for content"""
        try:
            return self.repository.increment_view_count(self.db, content_id)
        except Exception as e:
            logger.error(f"Error incrementing view count for {content_id}: {str(e)}")
            return False
    
    async def add_like(self, content_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Add a like to content"""
        try:
            # In a real implementation, would check if user already liked
            result = self.repository.add_like(self.db, content_id)
            if result:
                logger.info(f"Content {content_id} liked by user {user_id}")
            return result
        except Exception as e:
            logger.error(f"Error adding like to content {content_id}: {str(e)}")
            return False
    
    async def add_share(self, content_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Add a share to content"""
        try:
            result = self.repository.add_share(self.db, content_id)
            if result:
                logger.info(f"Content {content_id} shared by user {user_id}")
            return result
        except Exception as e:
            logger.error(f"Error adding share to content {content_id}: {str(e)}")
            return False
    
    # Analytics
    
    async def get_content_analytics(
        self,
        content_id: uuid.UUID,
        current_user_id: uuid.UUID
    ) -> ContentAnalytics:
        """
        Get comprehensive content analytics.
        
        Args:
            content_id: Content to analyze
            current_user_id: User requesting analytics
            
        Returns:
            Content analytics data
        """
        try:
            # Get content and validate access
            content = self.repository.get_by_id(self.db, content_id)
            if not content:
                raise ValueError("Content not found")
            
            # Check permissions
            self._validate_content_analytics_permissions(content, current_user_id)
            
            # Get analytics from repository
            analytics_data = self.repository.get_content_analytics(self.db, content_id)
            
            # Create comprehensive analytics response
            analytics = ContentAnalytics(
                content_id=content_id,
                content_title=content.title,
                view_count=analytics_data.get("view_count", 0),
                like_count=analytics_data.get("like_count", 0),
                share_count=analytics_data.get("share_count", 0),
                comment_count=analytics_data.get("comment_count", 0),
                rating=analytics_data.get("rating"),
                rating_count=analytics_data.get("rating_count", 0),
                average_rating=analytics_data.get("average_rating"),
                published_at=analytics_data.get("published_at"),
                total_engagement=analytics_data.get("view_count", 0) + 
                               analytics_data.get("like_count", 0) + 
                               analytics_data.get("share_count", 0),
                engagement_rate=0.0,  # Would be calculated based on impressions
                category_name=analytics_data.get("primary_category")
            )
            
            return analytics
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error getting content analytics {content_id}: {str(e)}")
            raise ValueError("Failed to retrieve content analytics")
    
    # Validation Methods
    
    def _validate_content_creation(self, content_data: ContentCreate, user_id: uuid.UUID) -> None:
        """Validate content creation data"""
        # Check title is provided
        if not content_data.title or not any(content_data.title.values()):
            raise ValueError("Content title is required in at least one language")
        
        # Validate content type
        if content_data.content_type not in ContentTypeEnum:
            raise ValueError("Invalid content type")
        
        # Validate category if provided
        if content_data.primary_category_id:
            from repositories.category import CategoryRepository
            category_repo = CategoryRepository()
            category = category_repo.get_by_id(self.db, content_data.primary_category_id)
            if not category:
                raise ValueError("Primary category not found")
            if not category.is_active:
                raise ValueError("Cannot assign content to inactive category")
    
    def _validate_content_update(
        self, 
        content_id: uuid.UUID, 
        content_update: ContentUpdate
    ) -> None:
        """Validate content update data"""
        # Check content exists
        content = self.repository.get_by_id(self.db, content_id)
        if not content:
            raise ValueError("Content not found")
        
        # Validate category change if specified
        if hasattr(content_update, 'primary_category_id') and content_update.primary_category_id:
            from repositories.category import CategoryRepository
            category_repo = CategoryRepository()
            category = category_repo.get_by_id(self.db, content_update.primary_category_id)
            if not category:
                raise ValueError("New primary category not found")
            if not category.is_active:
                raise ValueError("Cannot assign content to inactive category")
    
    def _validate_content_update_permissions(self, content: Content, user_id: uuid.UUID) -> None:
        """Validate user has permission to update content"""
        # Simple permission check - in real implementation would be more sophisticated
        if content.author_id != user_id:
            # Check if user has admin permissions or editor role
            pass  # Would implement proper permission checking
    
    def _validate_content_delete_permissions(self, content: Content, user_id: uuid.UUID) -> None:
        """Validate user has permission to delete content"""
        # Simple permission check
        if content.author_id != user_id:
            # Check if user has admin permissions
            pass  # Would implement proper permission checking
    
    def _validate_content_publish_permissions(self, content: Content, user_id: uuid.UUID) -> None:
        """Validate user has permission to publish content"""
        # Check if user can publish (author or has publisher role)
        if content.author_id != user_id:
            # Check if user has publisher permissions
            pass  # Would implement proper permission checking
    
    def _validate_content_analytics_permissions(self, content: Content, user_id: uuid.UUID) -> None:
        """Validate user has permission to view analytics"""
        # Check if user can view analytics (author or has analytics role)
        if content.author_id != user_id:
            # Check if user has analytics permissions
            pass  # Would implement proper permission checking
    
    # Helper Methods
    
    def _content_to_response(
        self,
        content: Content,
        include_category: bool = True,
        include_analytics: bool = False
    ) -> ContentResponse:
        """Convert Content ORM to ContentResponse"""
        response_data = {
            "id": content.id,
            "title": content.title,
            "description": content.description,
            "body": content.body,
            "slug": content.slug,
            "content_type": content.content_type,
            "status": content.status,
            "visibility": content.visibility,
            "is_featured": content.is_featured,
            "published_at": content.published_at,
            "scheduled_at": content.scheduled_at,
            "expires_at": content.expires_at,
            "author_id": content.author_id,
            "author_name": content.author_name,
            "file_url": content.file_url,
            "thumbnail_url": content.thumbnail_url,
            "file_size": content.file_size,
            "file_type": content.file_type,
            "duration": content.duration,
            "view_count": content.view_count,
            "like_count": content.like_count,
            "share_count": content.share_count,
            "comment_count": content.comment_count,
            "rating": content.rating,
            "rating_count": content.rating_count,
            "seo_title": content.seo_title,
            "seo_description": content.seo_description,
            "seo_keywords": content.seo_keywords,
            "tags": content.tags,
            "metadata": content._metadata,
            "created_at": content.created_at,
            "updated_at": content.updated_at,
            "primary_category_id": content.primary_category_id
        }
        
        if include_category and content.primary_category:
            response_data["primary_category"] = {
                "id": content.primary_category.id,
                "name": content.primary_category.name,
                "path": content.primary_category.path
            }
        
        if include_analytics:
            response_data.update({
                "average_rating": content.average_rating,
                "total_engagement": content.view_count + content.like_count + content.share_count,
                "is_published": content.is_published,
                "is_scheduled": content.is_scheduled,
                "is_expired": content.is_expired
            })
        
        return ContentResponse(**response_data)