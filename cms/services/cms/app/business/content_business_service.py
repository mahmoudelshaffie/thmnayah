"""
Content Business Service

Contains core business logic and domain rules for content management.
This layer is independent of infrastructure and handles business rule enforcement.
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Set
from sqlalchemy.orm import Session

from models.content import Content, ContentStatusEnum, ContentTypeEnum, ContentVisibilityEnum
from repositories.content import ContentRepository
from .domain_events import (
    ContentCreatedEvent, ContentUpdatedEvent, ContentPublishedEvent,
    ContentArchivedEvent, ContentDeletedEvent, ContentLikedEvent,
    ContentSharedEvent, ContentViewedEvent
)

logger = logging.getLogger(__name__)


class ContentBusinessService:
    """
    Core business service for content domain logic.
    
    Handles:
    - Business rule enforcement
    - Domain event publishing
    - Cross-cutting business concerns
    - Content lifecycle management
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = ContentRepository()
        self.domain_events: List = []  # In-memory event store for this transaction
    
    def create_content_with_business_rules(
        self,
        content_data: Dict[str, Any],
        author_id: uuid.UUID
    ) -> Content:
        """
        Create content with full business rule enforcement.
        
        Args:
            content_data: Content creation data
            author_id: Author user ID
            
        Returns:
            Created content entity
            
        Raises:
            ValueError: For business rule violations
        """
        # Apply business rules
        self._enforce_content_creation_rules(content_data, author_id)
        
        # Apply content defaults
        content_data = self._apply_content_defaults(content_data, author_id)
        
        # Create content through repository
        from api.v1.models.content import ContentCreate
        content_create = ContentCreate(**content_data)
        content = self.repository.create_content(self.db, content_data=content_create)
        
        # Publish domain event
        self._publish_event(ContentCreatedEvent(
            aggregate_id=content.id,
            content_title=content.title,
            content_type=content.content_type.value,
            author_id=author_id,
            category_id=content.primary_category_id,
            user_id=author_id
        ))
        
        logger.info(f"Content created with business rules: {content.id}")
        return content
    
    def update_content_with_business_rules(
        self,
        content_id: uuid.UUID,
        update_data: Dict[str, Any],
        user_id: uuid.UUID
    ) -> Content:
        """
        Update content with business rule enforcement.
        
        Args:
            content_id: Content to update
            update_data: Update data
            user_id: User performing update
            
        Returns:
            Updated content entity
        """
        # Get existing content
        existing_content = self.repository.get_by_id(self.db, content_id)
        if not existing_content:
            raise ValueError("Content not found")
        
        # Apply business rules
        self._enforce_content_update_rules(existing_content, update_data, user_id)
        
        # Track status changes
        previous_status = existing_content.status.value
        new_status = update_data.get('status')
        
        # Update through repository
        from api.v1.models.content import ContentUpdate
        content_update = ContentUpdate(**update_data)
        updated_content = self.repository.update_content(
            self.db, content_id=content_id, content_update=content_update
        )
        
        # Publish domain event
        self._publish_event(ContentUpdatedEvent(
            aggregate_id=content_id,
            updated_fields=update_data,
            previous_status=previous_status,
            new_status=new_status,
            user_id=user_id
        ))
        
        logger.info(f"Content updated with business rules: {content_id}")
        return updated_content
    
    def publish_content_with_business_rules(
        self,
        content_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Content:
        """
        Publish content with full business validation.
        
        Args:
            content_id: Content to publish
            user_id: User performing action
            
        Returns:
            Published content
        """
        # Get content
        content = self.repository.get_by_id(self.db, content_id)
        if not content:
            raise ValueError("Content not found")
        
        # Apply publication business rules
        self._enforce_content_publication_rules(content, user_id)
        
        # Publish through repository
        published_content = self.repository.publish_content(self.db, content_id)
        
        # Publish domain event
        self._publish_event(ContentPublishedEvent(
            aggregate_id=content_id,
            content_title=published_content.title,
            content_type=published_content.content_type.value,
            published_at=published_content.published_at or datetime.utcnow(),
            category_id=published_content.primary_category_id,
            user_id=user_id
        ))
        
        logger.info(f"Content published with business rules: {content_id}")
        return published_content
    
    def archive_content_with_business_rules(
        self,
        content_id: uuid.UUID,
        user_id: uuid.UUID,
        reason: Optional[str] = None
    ) -> Content:
        """
        Archive content with business validation.
        
        Args:
            content_id: Content to archive
            user_id: User performing action
            reason: Optional reason for archival
            
        Returns:
            Archived content
        """
        # Get content
        content = self.repository.get_by_id(self.db, content_id)
        if not content:
            raise ValueError("Content not found")
        
        # Apply archival business rules
        self._enforce_content_archival_rules(content, user_id)
        
        # Archive through repository
        archived_content = self.repository.archive_content(self.db, content_id)
        
        # Publish domain event
        self._publish_event(ContentArchivedEvent(
            aggregate_id=content_id,
            content_title=archived_content.title,
            archived_at=datetime.utcnow(),
            reason=reason,
            user_id=user_id
        ))
        
        logger.info(f"Content archived with business rules: {content_id}")
        return archived_content
    
    def delete_content_with_business_rules(
        self,
        content_id: uuid.UUID,
        user_id: uuid.UUID,
        soft_delete: bool = True
    ) -> bool:
        """
        Delete content with business validation.
        
        Args:
            content_id: Content to delete
            user_id: User performing action
            soft_delete: Whether to soft delete
            
        Returns:
            Success status
        """
        # Get content
        content = self.repository.get_by_id(self.db, content_id)
        if not content:
            raise ValueError("Content not found")
        
        # Apply deletion business rules
        self._enforce_content_deletion_rules(content, user_id)
        
        # Delete through repository
        result = self.repository.delete_content(
            self.db, content_id=content_id, soft_delete=soft_delete
        )
        
        if result:
            # Publish domain event
            self._publish_event(ContentDeletedEvent(
                aggregate_id=content_id,
                content_title=content.title,
                deleted_at=datetime.utcnow(),
                soft_delete=soft_delete,
                user_id=user_id
            ))
            
            logger.info(f"Content deleted with business rules: {content_id}")
        
        return result
    
    def add_like_with_business_rules(
        self,
        content_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> bool:
        """
        Add like with business validation.
        
        Args:
            content_id: Content to like
            user_id: User adding like
            
        Returns:
            Success status
        """
        # Get current like count
        content = self.repository.get_by_id(self.db, content_id)
        if not content:
            raise ValueError("Content not found")
        
        previous_count = content.like_count
        
        # Apply like business rules
        self._enforce_like_business_rules(content, user_id)
        
        # Add like through repository
        result = self.repository.add_like(self.db, content_id)
        
        if result:
            # Publish domain event
            self._publish_event(ContentLikedEvent(
                aggregate_id=content_id,
                previous_count=previous_count,
                new_count=previous_count + 1,
                user_id=user_id
            ))
        
        return result
    
    def add_share_with_business_rules(
        self,
        content_id: uuid.UUID,
        user_id: uuid.UUID,
        platform: Optional[str] = None
    ) -> bool:
        """
        Add share with business validation.
        
        Args:
            content_id: Content to share
            user_id: User sharing content
            platform: Platform where shared
            
        Returns:
            Success status
        """
        # Get current share count
        content = self.repository.get_by_id(self.db, content_id)
        if not content:
            raise ValueError("Content not found")
        
        previous_count = content.share_count
        
        # Apply share business rules
        self._enforce_share_business_rules(content, user_id)
        
        # Add share through repository
        result = self.repository.add_share(self.db, content_id)
        
        if result:
            # Publish domain event
            self._publish_event(ContentSharedEvent(
                aggregate_id=content_id,
                previous_count=previous_count,
                new_count=previous_count + 1,
                platform=platform,
                user_id=user_id
            ))
        
        return result
    
    def record_view_with_business_rules(
        self,
        content_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        view_duration: Optional[int] = None,
        view_source: Optional[str] = None
    ) -> bool:
        """
        Record content view with business validation.
        
        Args:
            content_id: Content viewed
            user_id: Optional user who viewed
            view_duration: Optional view duration in seconds
            view_source: Optional source of view
            
        Returns:
            Success status
        """
        # Get content
        content = self.repository.get_by_id(self.db, content_id)
        if not content:
            raise ValueError("Content not found")
        
        # Apply view business rules
        self._enforce_view_business_rules(content, user_id)
        
        # Record view through repository
        result = self.repository.increment_view_count(self.db, content_id)
        
        if result:
            # Publish domain event
            self._publish_event(ContentViewedEvent(
                aggregate_id=content_id,
                view_duration=view_duration,
                view_source=view_source,
                user_id=user_id
            ))
        
        return result
    
    def get_content_with_business_context(
        self,
        content_id: uuid.UUID,
        requesting_user_id: Optional[uuid.UUID] = None
    ) -> Optional[Content]:
        """
        Get content with business context and access control.
        
        Args:
            content_id: Content to retrieve
            requesting_user_id: User requesting content
            
        Returns:
            Content if accessible, None otherwise
        """
        content = self.repository.get_by_id(self.db, content_id)
        if not content:
            return None
        
        # Apply access business rules
        if not self._has_content_access(content, requesting_user_id):
            return None
        
        return content
    
    # Business rule enforcement methods
    
    def _enforce_content_creation_rules(
        self,
        content_data: Dict[str, Any],
        author_id: uuid.UUID
    ) -> None:
        """Enforce business rules for content creation"""
        
        # Rule: Content must have title in at least one language
        title = content_data.get('title', {})
        if not title or not any(v.strip() for v in title.values() if isinstance(v, str)):
            raise ValueError("Content must have a title in at least one language")
        
        # Rule: Video/Audio content must have file and duration
        content_type = content_data.get('content_type')
        if content_type in [ContentTypeEnum.VIDEO.value, ContentTypeEnum.AUDIO.value]:
            if not content_data.get('file_url'):
                raise ValueError(f"{content_type} content requires a file URL")
            if not content_data.get('duration'):
                raise ValueError(f"{content_type} content requires duration specification")
        
        # Rule: Check content creation quota
        self._enforce_creation_quota(author_id)
        
        # Rule: Validate category assignment
        category_id = content_data.get('primary_category_id')
        if category_id:
            self._validate_category_assignment(category_id, author_id)
    
    def _enforce_content_update_rules(
        self,
        existing_content: Content,
        update_data: Dict[str, Any],
        user_id: uuid.UUID
    ) -> None:
        """Enforce business rules for content updates"""
        
        # Rule: Only author or authorized users can update
        if existing_content.author_id != user_id:
            if not self._has_content_edit_permission(user_id):
                raise ValueError("Insufficient permissions to update this content")
        
        # Rule: Published content has limited update options
        if existing_content.status == ContentStatusEnum.PUBLISHED:
            restricted_fields = {'content_type', 'file_url', 'primary_category_id'}
            updating_restricted = any(field in update_data for field in restricted_fields)
            if updating_restricted and not self._has_admin_permission(user_id):
                raise ValueError("Cannot modify core fields of published content")
        
        # Rule: Status transitions must be valid
        new_status = update_data.get('status')
        if new_status:
            self._validate_status_transition(existing_content.status, new_status)
    
    def _enforce_content_publication_rules(
        self,
        content: Content,
        user_id: uuid.UUID
    ) -> None:
        """Enforce business rules for content publication"""
        
        # Rule: Only author or publishers can publish
        if content.author_id != user_id:
            if not self._has_publish_permission(user_id):
                raise ValueError("Insufficient permissions to publish this content")
        
        # Rule: Content must be ready for publication
        if not content.title or not any(v.strip() for v in content.title.values()):
            raise ValueError("Content must have a title for publication")
        
        if not content.description or not any(v.strip() for v in content.description.values()):
            raise ValueError("Content must have a description for publication")
        
        # Rule: Media content must have files
        if content.content_type in [ContentTypeEnum.VIDEO, ContentTypeEnum.AUDIO]:
            if not content.file_url:
                raise ValueError(f"{content.content_type.value} content must have a file for publication")
        
        # Rule: Check publication quota
        self._enforce_publication_quota(user_id)
    
    def _enforce_content_archival_rules(
        self,
        content: Content,
        user_id: uuid.UUID
    ) -> None:
        """Enforce business rules for content archival"""
        
        # Rule: Only author or authorized users can archive
        if content.author_id != user_id:
            if not self._has_archive_permission(user_id):
                raise ValueError("Insufficient permissions to archive this content")
        
        # Rule: Cannot archive draft content (should delete instead)
        if content.status == ContentStatusEnum.DRAFT:
            raise ValueError("Draft content should be deleted, not archived")
    
    def _enforce_content_deletion_rules(
        self,
        content: Content,
        user_id: uuid.UUID
    ) -> None:
        """Enforce business rules for content deletion"""
        
        # Rule: Only author or authorized users can delete
        if content.author_id != user_id:
            if not self._has_delete_permission(user_id):
                raise ValueError("Insufficient permissions to delete this content")
        
        # Rule: Published content should be archived first
        if content.status == ContentStatusEnum.PUBLISHED:
            if not self._has_admin_permission(user_id):
                raise ValueError("Published content must be archived before deletion")
    
    def _enforce_like_business_rules(
        self,
        content: Content,
        user_id: uuid.UUID
    ) -> None:
        """Enforce business rules for liking content"""
        
        # Rule: Cannot like private content you don't have access to
        if not self._has_content_access(content, user_id):
            raise ValueError("Cannot like content you don't have access to")
        
        # Rule: Cannot like unpublished content
        if content.status != ContentStatusEnum.PUBLISHED:
            raise ValueError("Cannot like unpublished content")
        
        # In a real implementation: Check if user already liked this content
        # to prevent duplicate likes
    
    def _enforce_share_business_rules(
        self,
        content: Content,
        user_id: uuid.UUID
    ) -> None:
        """Enforce business rules for sharing content"""
        
        # Rule: Cannot share private content
        if content.visibility != ContentVisibilityEnum.PUBLIC:
            raise ValueError("Cannot share private or restricted content")
        
        # Rule: Cannot share unpublished content
        if content.status != ContentStatusEnum.PUBLISHED:
            raise ValueError("Cannot share unpublished content")
    
    def _enforce_view_business_rules(
        self,
        content: Content,
        user_id: Optional[uuid.UUID]
    ) -> None:
        """Enforce business rules for viewing content"""
        
        # Rule: Must have access to view content
        if not self._has_content_access(content, user_id):
            raise ValueError("Access denied to this content")
    
    # Business logic helper methods
    
    def _apply_content_defaults(
        self,
        content_data: Dict[str, Any],
        author_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Apply default values based on business rules"""
        
        # Set author ID
        content_data['author_id'] = author_id
        
        # Generate slugs if not provided
        if not content_data.get('slug') and content_data.get('title'):
            content_data['slug'] = self._generate_slugs(content_data['title'])
        
        # Set default SEO fields
        if not content_data.get('seo_title'):
            content_data['seo_title'] = content_data.get('title')
        
        if not content_data.get('seo_description'):
            content_data['seo_description'] = content_data.get('description')
        
        return content_data
    
    def _generate_slugs(self, title_dict: Dict[str, str]) -> Dict[str, str]:
        """Generate URL-friendly slugs from titles"""
        import re
        
        slugs = {}
        for lang, title in title_dict.items():
            if title:
                # Convert to lowercase and replace spaces with hyphens
                slug = title.lower().strip()
                slug = re.sub(r'[^\w\s-]', '', slug)  # Remove special characters
                slug = re.sub(r'[-\s]+', '-', slug)   # Replace spaces/multiple hyphens
                slug = slug.strip('-')                # Remove leading/trailing hyphens
                slugs[lang] = slug
        
        return slugs
    
    def _has_content_access(
        self,
        content: Content,
        user_id: Optional[uuid.UUID]
    ) -> bool:
        """Check if user has access to content"""
        
        # Public published content is accessible to all
        if (content.visibility == ContentVisibilityEnum.PUBLIC and
            content.status == ContentStatusEnum.PUBLISHED):
            return True
        
        # Owner always has access
        if user_id and content.author_id == user_id:
            return True
        
        # Private content requires authentication
        if content.visibility == ContentVisibilityEnum.PRIVATE:
            return user_id is not None and user_id == content.author_id
        
        # Restricted content needs special permission
        if content.visibility == ContentVisibilityEnum.RESTRICTED:
            return user_id is not None and self._has_restricted_content_access(user_id)
        
        return False
    
    def _validate_status_transition(
        self,
        current_status: ContentStatusEnum,
        new_status: str
    ) -> None:
        """Validate status transition is allowed"""
        
        # Convert string to enum if needed
        if isinstance(new_status, str):
            try:
                new_status = ContentStatusEnum(new_status)
            except ValueError:
                raise ValueError(f"Invalid status: {new_status}")
        
        # Define valid transitions
        valid_transitions = {
            ContentStatusEnum.DRAFT: [
                ContentStatusEnum.PENDING_REVIEW,
                ContentStatusEnum.PUBLISHED,
                ContentStatusEnum.ARCHIVED
            ],
            ContentStatusEnum.PENDING_REVIEW: [
                ContentStatusEnum.PUBLISHED,
                ContentStatusEnum.DRAFT
            ],
            ContentStatusEnum.PUBLISHED: [
                ContentStatusEnum.ARCHIVED
            ],
            ContentStatusEnum.ARCHIVED: [
                ContentStatusEnum.DRAFT,
                ContentStatusEnum.DELETED
            ],
            ContentStatusEnum.DELETED: []  # No transitions from deleted
        }
        
        allowed = valid_transitions.get(current_status, [])
        if new_status not in allowed:
            raise ValueError(
                f"Invalid status transition from {current_status.value} to {new_status.value}"
            )
    
    # Permission and quota check methods (stubbed for now)
    
    def _enforce_creation_quota(self, user_id: uuid.UUID) -> None:
        """Check if user has exceeded content creation quota"""
        # In a real implementation, check user's content creation limits
        pass
    
    def _enforce_publication_quota(self, user_id: uuid.UUID) -> None:
        """Check if user has exceeded publication quota"""
        # In a real implementation, check user's publication limits
        pass
    
    def _validate_category_assignment(
        self,
        category_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> None:
        """Validate user can assign content to category"""
        # In a real implementation, check category permissions
        pass
    
    def _has_content_edit_permission(self, user_id: uuid.UUID) -> bool:
        """Check if user has content edit permissions"""
        # In a real implementation, check user roles
        return False
    
    def _has_admin_permission(self, user_id: uuid.UUID) -> bool:
        """Check if user has admin permissions"""
        # In a real implementation, check user roles
        return False
    
    def _has_publish_permission(self, user_id: uuid.UUID) -> bool:
        """Check if user has publish permissions"""
        # In a real implementation, check user roles
        return False
    
    def _has_archive_permission(self, user_id: uuid.UUID) -> bool:
        """Check if user has archive permissions"""
        # In a real implementation, check user roles
        return False
    
    def _has_delete_permission(self, user_id: uuid.UUID) -> bool:
        """Check if user has delete permissions"""
        # In a real implementation, check user roles
        return False
    
    def _has_restricted_content_access(self, user_id: uuid.UUID) -> bool:
        """Check if user has access to restricted content"""
        # In a real implementation, check user permissions
        return False
    
    # Event handling
    
    def _publish_event(self, event) -> None:
        """Publish domain event"""
        self.domain_events.append(event)
        logger.debug(f"Published domain event: {event.event_type}")
    
    def get_domain_events(self) -> List:
        """Get all domain events from this transaction"""
        return self.domain_events.copy()
    
    def clear_domain_events(self) -> None:
        """Clear domain events (typically after processing)"""
        self.domain_events.clear()