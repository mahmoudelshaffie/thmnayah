"""
Series Business Service

Core business logic for series management following clean architecture principles.
This service contains all series-related business rules, validation, and domain event publishing.
"""

import uuid
import enum
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from models.series import Series, SeriesStatusEnum, SeriesVisibilityEnum, SeriesTypeEnum
from api.v1.models.series import SeriesCreate, SeriesUpdate, SeriesResponse
from repositories.interfaces import ISeriesRepository, ICategoryRepository, IUserRepository
from business.domain_events import (
    SeriesCreatedEvent, SeriesUpdatedEvent, SeriesPublishedEvent,
    SeriesCompletedEvent, SeriesPausedEvent, SeriesResumedEvent,
    SeriesCancelledEvent, SeriesDeletedEvent, SeriesFeaturedEvent,
    EventType
)


class SeriesBusinessService:
    """
    Business service for series domain operations.
    
    Encapsulates business logic, rules, and domain event publishing
    for series management operations.
    """
    
    def __init__(
        self,
        series_repository: ISeriesRepository,
        category_repository: ICategoryRepository,
        user_repository: IUserRepository,
        db: Session
    ):
        self.repository = series_repository
        self.category_repository = category_repository
        self.user_repository = user_repository
        self.db = db
        self._domain_events: List = []
    
    # Core Business Operations
    
    def create_series_with_business_rules(
        self,
        series_data: Dict[str, Any],
        creator_id: uuid.UUID
    ) -> Series:
        """
        Create series with business rule enforcement.
        
        Business Rules:
        - Series title must be unique within creator's series
        - Creator must have permission to create series
        - Category must exist and be active
        - Slug must be unique if provided
        """
        
        # Enforce business rules
        self._enforce_series_creation_rules(series_data, creator_id)
        
        # Apply business defaults
        series_data = self._apply_series_defaults(series_data, creator_id)
        
        # Create series
        series = self.repository.create_series(self.db, series_data=SeriesCreate(**series_data))
        
        # Publish domain event
        self._publish_event(SeriesCreatedEvent(
            aggregate_id=series.id,
            series_title=series.title,
            series_type=series.series_type.value,
            creator_id=creator_id,
            category_id=series.primary_category_id,
            expected_episode_count=series.expected_episode_count,
            user_id=creator_id
        ))
        
        return series
    
    def update_series_with_business_rules(
        self,
        series_id: uuid.UUID,
        updates: Dict[str, Any],
        updated_by_user_id: uuid.UUID
    ) -> Series:
        """
        Update series with business rule enforcement.
        
        Business Rules:
        - Only creator or admin can update series
        - Cannot change certain fields after publication
        - Status transitions must follow valid flow
        - Category changes require validation
        """
        
        # Get current series
        current_series = self.repository.get_by_id(self.db, series_id)
        if not current_series:
            raise ValueError("Series not found")
        
        # Enforce update rules
        self._enforce_series_update_rules(current_series, updates, updated_by_user_id)
        
        # Track changes for events
        previous_values = self._extract_previous_values(current_series, updates.keys())
        
        # Apply updates
        updated_series = self.repository.update_series(
            self.db, 
            series_id=series_id, 
            updates=SeriesUpdate(**updates)
        )
        
        # Publish domain event
        self._publish_event(SeriesUpdatedEvent(
            aggregate_id=series_id,
            updated_fields=list(updates.keys()),
            previous_status=previous_values.get('status'),
            new_status=updates.get('status'),
            user_id=updated_by_user_id
        ))
        
        # Handle special status changes
        self._handle_status_change_events(
            updated_series, 
            previous_values.get('status'), 
            updates.get('status'),
            updated_by_user_id
        )
        
        return updated_series
    
    def publish_series_with_business_rules(
        self,
        series_id: uuid.UUID,
        published_by_user_id: uuid.UUID,
        publish_immediately: bool = True,
        scheduled_start_date: Optional[datetime] = None
    ) -> Series:
        """
        Publish series with business rule enforcement.
        
        Business Rules:
        - Series must be in DRAFT or PENDING_REVIEW status
        - Series must have at least one episode (optional rule)
        - Creator must have publishing permissions
        - Category must be active
        """
        
        series = self.repository.get_by_id(self.db, series_id)
        if not series:
            raise ValueError("Series not found")
        
        # Enforce publishing rules
        self._enforce_series_publishing_rules(series, published_by_user_id)
        
        # Determine publication details
        now = datetime.utcnow()
        if publish_immediately:
            published_at = now
            actual_start_date = now
            new_status = SeriesStatusEnum.PUBLISHED
        else:
            published_at = scheduled_start_date or now
            actual_start_date = scheduled_start_date
            new_status = SeriesStatusEnum.DRAFT  # Keep as draft until scheduled time
        
        # Update series
        updates = {
            'status': new_status,
            'published_at': published_at if publish_immediately else None,
            'actual_start_date': actual_start_date
        }
        
        updated_series = self.repository.update_series(
            self.db,
            series_id=series_id,
            updates=SeriesUpdate(**updates)
        )
        
        # Publish domain event
        if publish_immediately:
            self._publish_event(SeriesPublishedEvent(
                aggregate_id=series_id,
                series_title=series.title,
                series_type=series.series_type.value,
                creator_id=series.creator_id,
                published_at=published_at,
                category_id=series.primary_category_id,
                episode_count=series.episode_count,
                user_id=published_by_user_id
            ))
        
        return updated_series
    
    def complete_series_with_business_rules(
        self,
        series_id: uuid.UUID,
        completed_by_user_id: uuid.UUID
    ) -> Series:
        """
        Mark series as completed with business rule enforcement.
        
        Business Rules:
        - Series must be published
        - Only creator or admin can complete series
        - Series must have episodes
        """
        
        series = self.repository.get_by_id(self.db, series_id)
        if not series:
            raise ValueError("Series not found")
        
        # Enforce completion rules
        self._enforce_series_completion_rules(series, completed_by_user_id)
        
        # Calculate completion metrics
        start_date = series.actual_start_date or series.published_at
        duration_days = (datetime.utcnow() - start_date).days if start_date else 0
        
        # Update series
        updates = {
            'status': SeriesStatusEnum.COMPLETED,
            'actual_end_date': datetime.utcnow()
        }
        
        updated_series = self.repository.update_series(
            self.db,
            series_id=series_id,
            updates=SeriesUpdate(**updates)
        )
        
        # Publish domain event
        self._publish_event(SeriesCompletedEvent(
            aggregate_id=series_id,
            series_title=series.title,
            creator_id=series.creator_id,
            total_episodes=series.episode_count,
            completion_date=datetime.utcnow(),
            duration_days=duration_days,
            user_id=completed_by_user_id
        ))
        
        return updated_series
    
    def delete_series_with_business_rules(
        self,
        series_id: uuid.UUID,
        deleted_by_user_id: uuid.UUID,
        soft_delete: bool = True,
        deletion_reason: Optional[str] = None
    ) -> bool:
        """
        Delete series with business rule enforcement.
        
        Business Rules:
        - Only creator or admin can delete series
        - Published series with subscribers require confirmation
        - Episode cleanup handled automatically
        """
        
        series = self.repository.get_by_id(self.db, series_id)
        if not series:
            raise ValueError("Series not found")
        
        # Enforce deletion rules
        self._enforce_series_deletion_rules(series, deleted_by_user_id)
        
        # Perform deletion
        success = self.repository.delete_series(self.db, series_id, soft_delete)
        
        if success:
            # Publish domain event
            self._publish_event(SeriesDeletedEvent(
                aggregate_id=series_id,
                series_title=series.title,
                deleted_at=datetime.utcnow(),
                soft_delete=soft_delete,
                episode_count=series.episode_count,
                user_id=deleted_by_user_id,
                metadata={'deletion_reason': deletion_reason}
            ))
        
        return success
    
    # Business Rule Enforcement Methods
    
    def _enforce_series_creation_rules(
        self,
        series_data: Dict[str, Any],
        creator_id: uuid.UUID
    ) -> None:
        """Enforce business rules for series creation"""
        
        # Check creator permissions
        creator = self.user_repository.get_by_id(self.db, creator_id)
        if not creator:
            raise ValueError("Creator not found")
        
        if not self.user_repository.has_permission(self.db, creator_id, 'create_series'):
            raise ValueError("User does not have permission to create series")
        
        # Validate category if provided
        if 'primary_category_id' in series_data and series_data['primary_category_id']:
            category = self.category_repository.get_by_id(self.db, series_data['primary_category_id'])
            if not category or not category.is_active:
                raise ValueError("Invalid or inactive category")
        
        # Check title uniqueness within creator's series
        if self._is_series_title_duplicate(series_data.get('title', {}), creator_id):
            raise ValueError("Series title already exists for this creator")
        
        # Validate slug uniqueness if provided
        if 'slug' in series_data and series_data['slug']:
            for lang, slug in series_data['slug'].items():
                if self.repository.find_series_by_slug(self.db, slug, lang):
                    raise ValueError(f"Slug '{slug}' already exists for language '{lang}'")
    
    def _enforce_series_update_rules(
        self,
        current_series: Series,
        updates: Dict[str, Any],
        updated_by_user_id: uuid.UUID
    ) -> None:
        """Enforce business rules for series updates"""
        
        # Check update permissions
        if (current_series.creator_id != updated_by_user_id and 
            not self.user_repository.has_permission(self.db, updated_by_user_id, 'edit_any_series')):
            raise ValueError("User does not have permission to update this series")
        
        # Prevent certain changes after publication
        if current_series.status in [SeriesStatusEnum.PUBLISHED, SeriesStatusEnum.COMPLETED]:
            restricted_fields = ['series_type', 'primary_category_id']
            for field in restricted_fields:
                if field in updates:
                    raise ValueError(f"Cannot change '{field}' after series is published")
        
        # Validate status transitions
        if 'status' in updates:
            self._validate_series_status_transition(current_series.status, updates['status'])
        
        # Validate category change if provided
        if 'primary_category_id' in updates and updates['primary_category_id']:
            category = self.category_repository.get_by_id(self.db, updates['primary_category_id'])
            if not category or not category.is_active:
                raise ValueError("Invalid or inactive category")
    
    def _enforce_series_publishing_rules(
        self,
        series: Series,
        published_by_user_id: uuid.UUID
    ) -> None:
        """Enforce business rules for series publishing"""
        
        # Check publishing permissions
        if (series.creator_id != published_by_user_id and 
            not self.user_repository.has_permission(self.db, published_by_user_id, 'publish_any_series')):
            raise ValueError("User does not have permission to publish this series")
        
        # Validate current status
        if series.status not in [SeriesStatusEnum.DRAFT, SeriesStatusEnum.PENDING_REVIEW]:
            raise ValueError("Series must be in DRAFT or PENDING_REVIEW status to publish")
        
        # Validate category is active
        if series.primary_category_id:
            category = self.category_repository.get_by_id(self.db, series.primary_category_id)
            if not category or not category.is_active:
                raise ValueError("Series category is not active")
        
        # Optional: Require at least one episode
        # if series.episode_count == 0:
        #     raise ValueError("Series must have at least one episode to publish")
    
    def _enforce_series_completion_rules(
        self,
        series: Series,
        completed_by_user_id: uuid.UUID
    ) -> None:
        """Enforce business rules for series completion"""
        
        # Check completion permissions
        if (series.creator_id != completed_by_user_id and 
            not self.user_repository.has_permission(self.db, completed_by_user_id, 'manage_any_series')):
            raise ValueError("User does not have permission to complete this series")
        
        # Validate current status
        if series.status != SeriesStatusEnum.PUBLISHED:
            raise ValueError("Only published series can be completed")
        
        # Validate has episodes
        if series.episode_count == 0:
            raise ValueError("Cannot complete series with no episodes")
    
    def _enforce_series_deletion_rules(
        self,
        series: Series,
        deleted_by_user_id: uuid.UUID
    ) -> None:
        """Enforce business rules for series deletion"""
        
        # Check deletion permissions
        if (series.creator_id != deleted_by_user_id and 
            not self.user_repository.has_permission(self.db, deleted_by_user_id, 'delete_any_series')):
            raise ValueError("User does not have permission to delete this series")
        
        # Warning for published series with subscribers
        if (series.status == SeriesStatusEnum.PUBLISHED and 
            series.subscription_count > 0):
            # In production, this might require additional confirmation
            pass
    
    # Helper Methods
    
    def _apply_series_defaults(
        self,
        series_data: Dict[str, Any],
        creator_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Apply business defaults to series data"""
        
        # Set creator
        series_data['creator_id'] = creator_id
        
        # Generate slug if not provided
        if 'slug' not in series_data or not series_data['slug']:
            series_data['slug'] = self._generate_series_slug(series_data.get('title', {}))
        
        # Set default visibility
        if 'visibility' not in series_data:
            series_data['visibility'] = SeriesVisibilityEnum.PUBLIC
        
        # Set default status
        if 'status' not in series_data:
            series_data['status'] = SeriesStatusEnum.DRAFT
        
        return series_data
    
    def _validate_series_status_transition(
        self,
        current_status: SeriesStatusEnum,
        new_status: SeriesStatusEnum
    ) -> None:
        """Validate series status transition"""
        
        valid_transitions = {
            SeriesStatusEnum.DRAFT: [
                SeriesStatusEnum.PENDING_REVIEW,
                SeriesStatusEnum.PUBLISHED,
                SeriesStatusEnum.CANCELLED,
                SeriesStatusEnum.ARCHIVED
            ],
            SeriesStatusEnum.PENDING_REVIEW: [
                SeriesStatusEnum.DRAFT,
                SeriesStatusEnum.PUBLISHED,
                SeriesStatusEnum.CANCELLED
            ],
            SeriesStatusEnum.PUBLISHED: [
                SeriesStatusEnum.COMPLETED,
                SeriesStatusEnum.PAUSED,
                SeriesStatusEnum.CANCELLED,
                SeriesStatusEnum.ARCHIVED
            ],
            SeriesStatusEnum.PAUSED: [
                SeriesStatusEnum.PUBLISHED,
                SeriesStatusEnum.CANCELLED,
                SeriesStatusEnum.COMPLETED
            ],
            SeriesStatusEnum.COMPLETED: [
                SeriesStatusEnum.ARCHIVED
            ],
            SeriesStatusEnum.CANCELLED: [
                SeriesStatusEnum.ARCHIVED,
                SeriesStatusEnum.DRAFT  # Allow reactivation
            ],
            SeriesStatusEnum.ARCHIVED: []  # Terminal state
        }
        
        if new_status not in valid_transitions.get(current_status, []):
            raise ValueError(
                f"Invalid status transition from {current_status.value} to {new_status.value}"
            )
    
    def _is_series_title_duplicate(
        self,
        title: Dict[str, str],
        creator_id: uuid.UUID,
        exclude_id: Optional[uuid.UUID] = None
    ) -> bool:
        """Check if series title is duplicate for creator"""
        
        for lang, title_text in title.items():
            existing_series = self.repository.find_series_by_creator_and_title(
                self.db, creator_id, title_text, lang, exclude_id
            )
            if existing_series:
                return True
        return False
    
    def _generate_series_slug(self, title: Dict[str, str]) -> Dict[str, str]:
        """Generate URL-friendly slugs from title"""
        
        import re
        slugs = {}
        
        for lang, title_text in title.items():
            # Simple slug generation (in production, use more sophisticated method)
            slug = re.sub(r'[^a-zA-Z0-9\u0600-\u06FF\s-]', '', title_text.lower())
            slug = re.sub(r'\s+', '-', slug.strip())
            slug = f"{slug}-{uuid.uuid4().hex[:8]}"  # Add uniqueness
            slugs[lang] = slug
        
        return slugs
    
    def _extract_previous_values(
        self,
        series: Series,
        field_names: List[str]
    ) -> Dict[str, Any]:
        """Extract previous values for change tracking"""
        
        previous_values = {}
        for field_name in field_names:
            if hasattr(series, field_name):
                value = getattr(series, field_name)
                if isinstance(value, enum.Enum):
                    previous_values[field_name] = value.value
                else:
                    previous_values[field_name] = value
        
        return previous_values
    
    def _handle_status_change_events(
        self,
        series: Series,
        previous_status: Optional[str],
        new_status: Optional[str],
        user_id: uuid.UUID
    ) -> None:
        """Handle special events for status changes"""
        
        if not new_status or previous_status == new_status:
            return
        
        # Handle specific status change events
        if new_status == SeriesStatusEnum.PAUSED.value:
            self._publish_event(SeriesPausedEvent(
                aggregate_id=series.id,
                series_title=series.title,
                paused_at=datetime.utcnow(),
                episodes_completed=series.episode_count,
                user_id=user_id
            ))
        
        elif (previous_status == SeriesStatusEnum.PAUSED.value and 
              new_status == SeriesStatusEnum.PUBLISHED.value):
            self._publish_event(SeriesResumedEvent(
                aggregate_id=series.id,
                series_title=series.title,
                resumed_at=datetime.utcnow(),
                paused_duration_days=0,  # Calculate from pause history
                user_id=user_id
            ))
        
        elif new_status == SeriesStatusEnum.CANCELLED.value:
            self._publish_event(SeriesCancelledEvent(
                aggregate_id=series.id,
                series_title=series.title,
                cancelled_at=datetime.utcnow(),
                episodes_completed=series.episode_count,
                total_planned_episodes=series.expected_episode_count,
                user_id=user_id
            ))
    
    def _publish_event(self, event) -> None:
        """Publish domain event (placeholder implementation)"""
        self._domain_events.append(event)
        # In production, integrate with actual event publisher
    
    def get_domain_events(self) -> List:
        """Get unpublished domain events"""
        return self._domain_events.copy()
    
    def clear_domain_events(self) -> None:
        """Clear domain events after publishing"""
        self._domain_events.clear()
    
    # Advanced Business Logic Methods
    
    def calculate_series_completion_rate(
        self,
        series_id: uuid.UUID
    ) -> float:
        """Calculate series completion rate based on subscriber behavior"""
        
        # This would integrate with analytics to calculate
        # what percentage of subscribers complete the series
        # Placeholder implementation
        return 0.0
    
    def recommend_similar_series(
        self,
        series_id: uuid.UUID,
        limit: int = 5
    ) -> List[uuid.UUID]:
        """Recommend similar series based on content analysis"""
        
        # This would implement sophisticated recommendation logic
        # based on series metadata, tags, categories, etc.
        # Placeholder implementation
        return []
    
    def validate_series_business_constraints(
        self,
        series_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Validate all business constraints for a series"""
        
        series = self.repository.get_by_id(self.db, series_id)
        if not series:
            return {'valid': False, 'errors': ['Series not found']}
        
        errors = []
        warnings = []
        
        # Check business constraints
        if series.status == SeriesStatusEnum.PUBLISHED and series.episode_count == 0:
            warnings.append("Published series has no episodes")
        
        if series.expected_episode_count and series.episode_count > series.expected_episode_count:
            warnings.append("Episode count exceeds expected count")
        
        if series.visibility == SeriesVisibilityEnum.PUBLIC and not series.primary_category_id:
            errors.append("Public series must have a category")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }