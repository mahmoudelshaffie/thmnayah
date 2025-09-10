"""
Repository Interfaces

Defines contracts for repository implementations following clean architecture principles.
"""

import uuid
from typing import List, Optional, Dict, Any, Tuple
from abc import ABC, abstractmethod
from datetime import datetime
from sqlalchemy.orm import Session

from models.content import Content, ContentStatusEnum, ContentTypeEnum


class IContentRepository(ABC):
    """
    Interface for content repository defining the contract for content data access.
    
    This interface ensures loose coupling between business logic and data access,
    making the system more testable and maintainable.
    """
    
    @abstractmethod
    def get_by_id(self, db: Session, content_id: uuid.UUID) -> Optional[Content]:
        """Get content by ID"""
        pass
    
    @abstractmethod
    def search_content_advanced(
        self,
        db: Session,
        search_params: Dict[str, Any],
        pagination: Dict[str, int]
    ) -> Tuple[List[Content], int]:
        """Advanced content search with filtering and pagination"""
        pass
    
    @abstractmethod
    def get_published_content_by_category(
        self,
        db: Session,
        category_id: uuid.UUID,
        limit: int = 10,
        language: Optional[str] = None
    ) -> List[Content]:
        """Get published content in specific category"""
        pass
    
    @abstractmethod
    def get_trending_content(
        self,
        db: Session,
        hours: int = 24,
        limit: int = 10,
        category_id: Optional[uuid.UUID] = None
    ) -> List[Content]:
        """Get trending content based on engagement"""
        pass
    
    @abstractmethod
    def get_popular_content(
        self,
        db: Session,
        period_days: int = 30,
        limit: int = 10,
        content_type: Optional[ContentTypeEnum] = None
    ) -> List[Content]:
        """Get popular content by view count"""
        pass
    
    @abstractmethod
    def get_related_content(
        self,
        db: Session,
        content_id: uuid.UUID,
        limit: int = 5
    ) -> List[Content]:
        """Get content related to specified content"""
        pass
    
    @abstractmethod
    def get_content_stats(
        self,
        db: Session,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get comprehensive content statistics"""
        pass
    
    @abstractmethod
    def bulk_update_status(
        self,
        db: Session,
        content_ids: List[uuid.UUID],
        new_status: ContentStatusEnum
    ) -> int:
        """Bulk update content status"""
        pass
    
    @abstractmethod
    def increment_engagement_counters(
        self,
        db: Session,
        content_id: uuid.UUID,
        view_increment: int = 0,
        like_increment: int = 0,
        share_increment: int = 0,
        comment_increment: int = 0
    ) -> bool:
        """Increment engagement counters"""
        pass
    
    @abstractmethod
    def find_content_by_slug(
        self,
        db: Session,
        slug: str,
        language: str = 'ar'
    ) -> Optional[Content]:
        """Find content by slug in specific language"""
        pass
    
    @abstractmethod
    def get_scheduled_content(
        self,
        db: Session,
        before_time: Optional[datetime] = None
    ) -> List[Content]:
        """Get content scheduled for publication"""
        pass


class ICategoryRepository(ABC):
    """Interface for category repository"""
    
    @abstractmethod
    def get_by_id(self, db: Session, category_id: uuid.UUID):
        """Get category by ID"""
        pass
    
    @abstractmethod
    def get_active_categories(self, db: Session) -> List:
        """Get all active categories"""
        pass
    
    @abstractmethod
    def get_category_hierarchy(self, db: Session, parent_id: Optional[uuid.UUID] = None) -> List:
        """Get category hierarchy"""
        pass


class IUserRepository(ABC):
    """Interface for user repository"""
    
    @abstractmethod
    def get_by_id(self, db: Session, user_id: uuid.UUID):
        """Get user by ID"""
        pass
    
    @abstractmethod
    def get_by_email(self, db: Session, email: str):
        """Get user by email"""
        pass
    
    @abstractmethod
    def has_permission(self, db: Session, user_id: uuid.UUID, permission: str) -> bool:
        """Check if user has specific permission"""
        pass


class IAnalyticsRepository(ABC):
    """Interface for analytics repository"""
    
    @abstractmethod
    def record_view(
        self,
        db: Session,
        content_id: uuid.UUID,
        user_id: Optional[uuid.UUID],
        session_data: Dict[str, Any]
    ) -> bool:
        """Record content view event"""
        pass
    
    @abstractmethod
    def record_engagement(
        self,
        db: Session,
        content_id: uuid.UUID,
        user_id: Optional[uuid.UUID],
        engagement_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Record engagement event"""
        pass
    
    @abstractmethod
    def get_content_analytics(
        self,
        db: Session,
        content_id: uuid.UUID,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get content analytics data"""
        pass


class ISeriesRepository(ABC):
    """
    Interface for series repository defining the contract for series data access.
    
    This interface ensures loose coupling between business logic and data access,
    making the system more testable and maintainable.
    """
    
    @abstractmethod
    def get_by_id(self, db: Session, series_id: uuid.UUID) -> Optional:
        """Get series by ID"""
        pass
    
    @abstractmethod
    def search_series_advanced(
        self,
        db: Session,
        search_params: Dict[str, Any],
        pagination: Dict[str, int]
    ) -> Tuple[List, int]:
        """Advanced series search with filtering and pagination"""
        pass
    
    @abstractmethod
    def get_published_series_by_category(
        self,
        db: Session,
        category_id: uuid.UUID,
        limit: int = 10,
        language: Optional[str] = None
    ) -> List:
        """Get published series in specific category"""
        pass
    
    @abstractmethod
    def get_trending_series(
        self,
        db: Session,
        hours: int = 24,
        limit: int = 10,
        category_id: Optional[uuid.UUID] = None
    ) -> List:
        """Get trending series based on engagement"""
        pass
    
    @abstractmethod
    def get_popular_series(
        self,
        db: Session,
        period_days: int = 30,
        limit: int = 10,
        series_type: Optional[str] = None
    ) -> List:
        """Get popular series by subscription count"""
        pass
    
    @abstractmethod
    def get_series_by_creator(
        self,
        db: Session,
        creator_id: uuid.UUID,
        status: Optional[str] = None,
        limit: int = 10
    ) -> List:
        """Get series by creator"""
        pass
    
    @abstractmethod
    def get_series_stats(
        self,
        db: Session,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get comprehensive series statistics"""
        pass
    
    @abstractmethod
    def bulk_update_status(
        self,
        db: Session,
        series_ids: List[uuid.UUID],
        new_status: str
    ) -> int:
        """Bulk update series status"""
        pass
    
    @abstractmethod
    def increment_engagement_counters(
        self,
        db: Session,
        series_id: uuid.UUID,
        subscription_increment: int = 0,
        view_increment: int = 0,
        like_increment: int = 0,
        share_increment: int = 0,
        comment_increment: int = 0
    ) -> bool:
        """Increment engagement counters"""
        pass
    
    @abstractmethod
    def find_series_by_slug(
        self,
        db: Session,
        slug: str,
        language: str = 'ar'
    ) -> Optional:
        """Find series by slug in specific language"""
        pass
    
    @abstractmethod
    def get_scheduled_series(
        self,
        db: Session,
        before_time: Optional[datetime] = None
    ) -> List:
        """Get series scheduled for publication"""
        pass
    
    @abstractmethod
    def get_completed_series(
        self,
        db: Session,
        limit: int = 10
    ) -> List:
        """Get recently completed series"""
        pass
    
    @abstractmethod
    def get_series_with_episodes(
        self,
        db: Session,
        series_id: uuid.UUID,
        include_unpublished: bool = False
    ) -> Optional:
        """Get series with its episodes"""
        pass


class ISeriesSubscriptionRepository(ABC):
    """Interface for series subscription repository"""
    
    @abstractmethod
    def get_by_id(self, db: Session, subscription_id: uuid.UUID) -> Optional:
        """Get subscription by ID"""
        pass
    
    @abstractmethod
    def get_user_subscriptions(
        self,
        db: Session,
        user_id: uuid.UUID,
        status: Optional[str] = None,
        pagination: Optional[Dict[str, int]] = None
    ) -> Tuple[List, int]:
        """Get user's series subscriptions"""
        pass
    
    @abstractmethod
    def get_series_subscriptions(
        self,
        db: Session,
        series_id: uuid.UUID,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List:
        """Get subscriptions for a series"""
        pass
    
    @abstractmethod
    def create_subscription(
        self,
        db: Session,
        user_id: uuid.UUID,
        series_id: uuid.UUID,
        notification_enabled: bool = True,
        auto_download: bool = False
    ) -> Optional:
        """Create new subscription"""
        pass
    
    @abstractmethod
    def update_subscription(
        self,
        db: Session,
        subscription_id: uuid.UUID,
        updates: Dict[str, Any]
    ) -> Optional:
        """Update subscription"""
        pass
    
    @abstractmethod
    def delete_subscription(
        self,
        db: Session,
        subscription_id: uuid.UUID
    ) -> bool:
        """Delete subscription"""
        pass
    
    @abstractmethod
    def is_user_subscribed(
        self,
        db: Session,
        user_id: uuid.UUID,
        series_id: uuid.UUID
    ) -> bool:
        """Check if user is subscribed to series"""
        pass
    
    @abstractmethod
    def get_subscription_stats(
        self,
        db: Session,
        series_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """Get subscription statistics"""
        pass
    
    @abstractmethod
    def bulk_update_subscriptions(
        self,
        db: Session,
        subscription_ids: List[uuid.UUID],
        updates: Dict[str, Any]
    ) -> int:
        """Bulk update subscriptions"""
        pass
    
    @abstractmethod
    def get_users_to_notify(
        self,
        db: Session,
        series_id: uuid.UUID
    ) -> List[uuid.UUID]:
        """Get users who should be notified about series updates"""
        pass