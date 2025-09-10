"""
Domain Events

Events that represent business-significant occurrences in the content domain.
Used for decoupling business logic and enabling event-driven architecture.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from enum import Enum

from api.v1.models.common import BaseModel


class EventType(str, Enum):
    """Domain event types"""
    # Content events
    CONTENT_CREATED = "content.created"
    CONTENT_UPDATED = "content.updated"
    CONTENT_PUBLISHED = "content.published"
    CONTENT_ARCHIVED = "content.archived"
    CONTENT_DELETED = "content.deleted"
    CONTENT_LIKED = "content.liked"
    CONTENT_SHARED = "content.shared"
    CONTENT_VIEWED = "content.viewed"
    
    # Series events
    SERIES_CREATED = "series.created"
    SERIES_UPDATED = "series.updated"
    SERIES_PUBLISHED = "series.published"
    SERIES_COMPLETED = "series.completed"
    SERIES_PAUSED = "series.paused"
    SERIES_RESUMED = "series.resumed"
    SERIES_CANCELLED = "series.cancelled"
    SERIES_DELETED = "series.deleted"
    SERIES_SUBSCRIBED = "series.subscribed"
    SERIES_UNSUBSCRIBED = "series.unsubscribed"
    SERIES_EPISODE_ADDED = "series.episode.added"
    SERIES_FEATURED = "series.featured"
    SERIES_LIKED = "series.liked"
    SERIES_SHARED = "series.shared"
    SERIES_VIEWED = "series.viewed"


class DomainEvent(BaseModel, ABC):
    """Base class for all domain events"""
    
    event_id: uuid.UUID
    event_type: EventType
    aggregate_id: uuid.UUID  # ID of the content entity
    occurred_at: datetime
    user_id: Optional[uuid.UUID] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __init__(self, **data):
        if 'event_id' not in data:
            data['event_id'] = uuid.uuid4()
        if 'occurred_at' not in data:
            data['occurred_at'] = datetime.utcnow()
        super().__init__(**data)


class ContentCreatedEvent(DomainEvent):
    """Event fired when content is created"""
    
    content_title: Dict[str, str]
    content_type: str
    author_id: uuid.UUID
    category_id: Optional[uuid.UUID] = None
    
    def __init__(self, **data):
        data['event_type'] = EventType.CONTENT_CREATED
        super().__init__(**data)


class ContentUpdatedEvent(DomainEvent):
    """Event fired when content is updated"""
    
    updated_fields: Dict[str, Any]
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    
    def __init__(self, **data):
        data['event_type'] = EventType.CONTENT_UPDATED
        super().__init__(**data)


class ContentPublishedEvent(DomainEvent):
    """Event fired when content is published"""
    
    content_title: Dict[str, str]
    content_type: str
    published_at: datetime
    category_id: Optional[uuid.UUID] = None
    
    def __init__(self, **data):
        data['event_type'] = EventType.CONTENT_PUBLISHED
        super().__init__(**data)


class ContentArchivedEvent(DomainEvent):
    """Event fired when content is archived"""
    
    content_title: Dict[str, str]
    archived_at: datetime
    reason: Optional[str] = None
    
    def __init__(self, **data):
        data['event_type'] = EventType.CONTENT_ARCHIVED
        super().__init__(**data)


class ContentDeletedEvent(DomainEvent):
    """Event fired when content is deleted"""
    
    content_title: Dict[str, str]
    deleted_at: datetime
    soft_delete: bool = True
    
    def __init__(self, **data):
        data['event_type'] = EventType.CONTENT_DELETED
        super().__init__(**data)


class ContentEngagementEvent(DomainEvent):
    """Base class for content engagement events"""
    
    engagement_type: str
    previous_count: int
    new_count: int


class ContentLikedEvent(ContentEngagementEvent):
    """Event fired when content is liked"""
    
    def __init__(self, **data):
        data['event_type'] = EventType.CONTENT_LIKED
        data['engagement_type'] = 'like'
        super().__init__(**data)


class ContentSharedEvent(ContentEngagementEvent):
    """Event fired when content is shared"""
    
    platform: Optional[str] = None  # Social platform where shared
    
    def __init__(self, **data):
        data['event_type'] = EventType.CONTENT_SHARED
        data['engagement_type'] = 'share'
        super().__init__(**data)


class ContentViewedEvent(DomainEvent):
    """Event fired when content is viewed"""
    
    view_duration: Optional[int] = None  # Seconds
    view_source: Optional[str] = None  # How user found content
    
    def __init__(self, **data):
        data['event_type'] = EventType.CONTENT_VIEWED
        super().__init__(**data)


# Series Domain Events

class SeriesCreatedEvent(DomainEvent):
    """Event fired when series is created"""
    
    series_title: Dict[str, str]
    series_type: str
    creator_id: uuid.UUID
    category_id: Optional[uuid.UUID] = None
    expected_episode_count: Optional[int] = None
    
    def __init__(self, **data):
        data['event_type'] = EventType.SERIES_CREATED
        super().__init__(**data)


class SeriesUpdatedEvent(DomainEvent):
    """Event fired when series is updated"""
    
    updated_fields: Dict[str, Any]
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    
    def __init__(self, **data):
        data['event_type'] = EventType.SERIES_UPDATED
        super().__init__(**data)


class SeriesPublishedEvent(DomainEvent):
    """Event fired when series is published"""
    
    series_title: Dict[str, str]
    series_type: str
    creator_id: uuid.UUID
    published_at: datetime
    category_id: Optional[uuid.UUID] = None
    episode_count: int = 0
    
    def __init__(self, **data):
        data['event_type'] = EventType.SERIES_PUBLISHED
        super().__init__(**data)


class SeriesCompletedEvent(DomainEvent):
    """Event fired when series is completed"""
    
    series_title: Dict[str, str]
    creator_id: uuid.UUID
    total_episodes: int
    completion_date: datetime
    duration_days: int
    
    def __init__(self, **data):
        data['event_type'] = EventType.SERIES_COMPLETED
        super().__init__(**data)


class SeriesPausedEvent(DomainEvent):
    """Event fired when series is paused"""
    
    series_title: Dict[str, str]
    paused_at: datetime
    reason: Optional[str] = None
    episodes_completed: int = 0
    
    def __init__(self, **data):
        data['event_type'] = EventType.SERIES_PAUSED
        super().__init__(**data)


class SeriesResumedEvent(DomainEvent):
    """Event fired when series is resumed"""
    
    series_title: Dict[str, str]
    resumed_at: datetime
    paused_duration_days: int
    
    def __init__(self, **data):
        data['event_type'] = EventType.SERIES_RESUMED
        super().__init__(**data)


class SeriesCancelledEvent(DomainEvent):
    """Event fired when series is cancelled"""
    
    series_title: Dict[str, str]
    cancelled_at: datetime
    reason: Optional[str] = None
    episodes_completed: int = 0
    total_planned_episodes: Optional[int] = None
    
    def __init__(self, **data):
        data['event_type'] = EventType.SERIES_CANCELLED
        super().__init__(**data)


class SeriesDeletedEvent(DomainEvent):
    """Event fired when series is deleted"""
    
    series_title: Dict[str, str]
    deleted_at: datetime
    soft_delete: bool = True
    episode_count: int = 0
    
    def __init__(self, **data):
        data['event_type'] = EventType.SERIES_DELETED
        super().__init__(**data)


class SeriesSubscribedEvent(DomainEvent):
    """Event fired when user subscribes to series"""
    
    series_title: Dict[str, str]
    subscriber_id: uuid.UUID
    notification_enabled: bool = True
    auto_download: bool = False
    subscription_source: Optional[str] = None
    
    def __init__(self, **data):
        data['event_type'] = EventType.SERIES_SUBSCRIBED
        super().__init__(**data)


class SeriesUnsubscribedEvent(DomainEvent):
    """Event fired when user unsubscribes from series"""
    
    series_title: Dict[str, str]
    subscriber_id: uuid.UUID
    subscription_duration_days: int
    episodes_watched: int = 0
    cancellation_reason: Optional[str] = None
    
    def __init__(self, **data):
        data['event_type'] = EventType.SERIES_UNSUBSCRIBED
        super().__init__(**data)


class SeriesEpisodeAddedEvent(DomainEvent):
    """Event fired when new episode is added to series"""
    
    series_title: Dict[str, str]
    episode_title: Dict[str, str]
    episode_number: int
    season_number: Optional[int] = None
    episode_id: uuid.UUID  # Content ID of the episode
    is_published: bool = False
    notify_subscribers: bool = True
    
    def __init__(self, **data):
        data['event_type'] = EventType.SERIES_EPISODE_ADDED
        super().__init__(**data)


class SeriesEngagementEvent(DomainEvent):
    """Base class for series engagement events"""
    
    engagement_type: str
    previous_count: int
    new_count: int


class SeriesFeaturedEvent(DomainEvent):
    """Event fired when series is featured or unfeatured"""
    
    series_title: Dict[str, str]
    is_featured: bool
    featured_at: Optional[datetime] = None
    
    def __init__(self, **data):
        data['event_type'] = EventType.SERIES_FEATURED
        super().__init__(**data)


class SeriesLikedEvent(SeriesEngagementEvent):
    """Event fired when series is liked"""
    
    def __init__(self, **data):
        data['event_type'] = EventType.SERIES_LIKED
        data['engagement_type'] = 'like'
        super().__init__(**data)


class SeriesSharedEvent(SeriesEngagementEvent):
    """Event fired when series is shared"""
    
    platform: Optional[str] = None  # Social platform where shared
    
    def __init__(self, **data):
        data['event_type'] = EventType.SERIES_SHARED
        data['engagement_type'] = 'share'
        super().__init__(**data)


class SeriesViewedEvent(DomainEvent):
    """Event fired when series is viewed"""
    
    view_duration: Optional[int] = None  # Seconds
    view_source: Optional[str] = None  # How user found series
    episode_context: Optional[uuid.UUID] = None  # If viewed from episode
    
    def __init__(self, **data):
        data['event_type'] = EventType.SERIES_VIEWED
        super().__init__(**data)