"""
Enhanced Series Repository

Improved series repository using clean architecture principles
and advanced query building capabilities.
"""

import uuid
from typing import List, Optional, Dict, Any, Union, Tuple
from sqlalchemy import func, and_, or_, text, desc, asc, cast
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.dialects.postgresql import TSVECTOR
from datetime import datetime, timedelta

from models.series import (
    Series, SeriesSubscription, SeriesStatusEnum, SeriesVisibilityEnum, 
    SeriesTypeEnum, SubscriptionStatusEnum
)
from api.v1.models.series import SeriesCreate, SeriesUpdate
from repositories.base import BaseRepository, QueryBuilder
from repositories.interfaces import ISeriesRepository, ISeriesSubscriptionRepository


class SeriesRepository(BaseRepository[Series, SeriesCreate, SeriesUpdate], ISeriesRepository):
    """
    Enhanced repository for series data access with advanced querying capabilities.
    
    Provides:
    - Advanced search with full-text capabilities
    - Multilingual series support
    - Complex filtering and aggregation
    - Performance-optimized queries
    - Cache-aware operations
    - Subscription management
    """
    
    def __init__(self):
        super().__init__(Series)
    
    # Advanced Query Methods
    
    def search_series_advanced(
        self,
        db: Session,
        search_params: Dict[str, Any],
        pagination: Dict[str, int]
    ) -> Tuple[List[Series], int]:
        """
        Advanced series search with full-text search and complex filtering.
        
        Args:
            db: Database session
            search_params: Search parameters and filters
            pagination: Pagination parameters
            
        Returns:
            Tuple of (series_list, total_count)
        """
        builder = self.query_builder(db)
        
        # Apply search query
        query_text = search_params.get('query')
        language = search_params.get('language', 'ar')
        
        if query_text:
            builder = self._apply_multilingual_search(builder, query_text, language)
        
        # Apply filters
        builder = self._apply_series_filters(builder, search_params)
        
        # Get total count before pagination
        total_count = builder.count()
        
        # Apply pagination and ordering
        page = pagination.get('page', 1)
        limit = pagination.get('limit', 20)
        sort_by = search_params.get('sort_by', 'created_at')
        sort_order = search_params.get('sort_order', 'desc')
        
        builder = builder.order_by(sort_by, sort_order).paginate(page, limit)
        
        # Include relationships
        builder = builder.include('primary_category')
        
        series_list = builder.all()
        
        return series_list, total_count
    
    def get_series_with_relationships(
        self,
        db: Session,
        series_id: uuid.UUID
    ) -> Optional[Series]:
        """Get series with all relationships loaded"""
        return (
            self.query_builder(db)
            .filter_by(id=series_id)
            .include('primary_category')
            .include('creator')
            .include('episodes')
            .first()
        )
    
    def get_published_series_by_category(
        self,
        db: Session,
        category_id: uuid.UUID,
        limit: int = 10,
        language: Optional[str] = None
    ) -> List[Series]:
        """Get published series in specific category"""
        builder = (
            self.query_builder(db)
            .filter_by(
                primary_category_id=category_id,
                status=SeriesStatusEnum.PUBLISHED,
                visibility=SeriesVisibilityEnum.PUBLIC
            )
            .order_by('published_at', 'desc')
            .include('primary_category')
        )
        
        if limit > 0:
            builder = builder.paginate(1, limit)
        
        return builder.all()
    
    def get_trending_series(
        self,
        db: Session,
        hours: int = 24,
        limit: int = 10,
        category_id: Optional[uuid.UUID] = None
    ) -> List[Series]:
        """Get trending series based on engagement metrics"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        builder = (
            self.query_builder(db)
            .filter(
                Series.status == SeriesStatusEnum.PUBLISHED,
                Series.visibility == SeriesVisibilityEnum.PUBLIC,
                Series.published_at >= cutoff_time
            )
            .include('primary_category')
        )
        
        if category_id:
            builder = builder.filter_by(primary_category_id=category_id)
        
        # Order by engagement score (subscriptions + views + likes*2 + shares*3)
        results = builder.all()
        
        # Sort by calculated engagement score
        def engagement_score(series):
            return (series.subscription_count * 5 + series.view_count + 
                   (series.like_count * 2) + (series.share_count * 3))
        
        return sorted(results, key=engagement_score, reverse=True)[:limit]
    
    def get_popular_series(
        self,
        db: Session,
        period_days: int = 30,
        limit: int = 10,
        series_type: Optional[str] = None
    ) -> List[Series]:
        """Get popular series by subscription count in specified period"""
        cutoff_date = datetime.utcnow() - timedelta(days=period_days)
        
        builder = (
            self.query_builder(db)
            .filter(
                Series.status == SeriesStatusEnum.PUBLISHED,
                Series.visibility == SeriesVisibilityEnum.PUBLIC,
                Series.published_at >= cutoff_date
            )
            .order_by('subscription_count', 'desc')
            .include('primary_category')
        )
        
        if series_type:
            builder = builder.filter_by(series_type=SeriesTypeEnum(series_type))
        
        if limit > 0:
            builder = builder.paginate(1, limit)
        
        return builder.all()
    
    def get_series_by_creator(
        self,
        db: Session,
        creator_id: uuid.UUID,
        status: Optional[str] = None,
        limit: int = 10
    ) -> List[Series]:
        """Get series by creator"""
        builder = (
            self.query_builder(db)
            .filter_by(creator_id=creator_id)
            .order_by('created_at', 'desc')
            .include('primary_category')
        )
        
        if status:
            builder = builder.filter_by(status=SeriesStatusEnum(status))
        
        if limit > 0:
            builder = builder.paginate(1, limit)
        
        return builder.all()
    
    def get_completed_series(
        self,
        db: Session,
        limit: int = 10
    ) -> List[Series]:
        """Get recently completed series"""
        return (
            self.query_builder(db)
            .filter_by(status=SeriesStatusEnum.COMPLETED)
            .order_by('actual_end_date', 'desc')
            .include('primary_category')
            .paginate(1, limit)
            .all()
        )
    
    def get_series_with_episodes(
        self,
        db: Session,
        series_id: uuid.UUID,
        include_unpublished: bool = False
    ) -> Optional[Series]:
        """Get series with its episodes"""
        series = self.get_series_with_relationships(db, series_id)
        
        if series and not include_unpublished:
            # Filter out unpublished episodes
            published_episodes = [
                ep for ep in series.episodes 
                if ep.status == 'PUBLISHED'  # Assuming content has status
            ]
            series.episodes = published_episodes
        
        return series
    
    # Series Analytics and Aggregation
    
    def get_series_stats(
        self,
        db: Session,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get comprehensive series statistics"""
        base_query = self._build_base_query(db, filters)
        
        # Basic counts
        total_count = base_query.count()
        published_count = base_query.filter(Series.status == SeriesStatusEnum.PUBLISHED).count()
        draft_count = base_query.filter(Series.status == SeriesStatusEnum.DRAFT).count()
        completed_count = base_query.filter(Series.status == SeriesStatusEnum.COMPLETED).count()
        active_count = base_query.filter(
            Series.status.in_([SeriesStatusEnum.PUBLISHED, SeriesStatusEnum.PAUSED])
        ).count()
        
        # Series type breakdown
        type_stats = (
            db.query(Series.series_type, func.count(Series.id))
            .group_by(Series.series_type)
            .all()
        )
        
        # Engagement totals
        engagement_stats = (
            base_query
            .with_entities(
                func.sum(Series.subscription_count).label('total_subscriptions'),
                func.sum(Series.view_count).label('total_views'),
                func.sum(Series.like_count).label('total_likes'),
                func.sum(Series.share_count).label('total_shares'),
                func.sum(Series.comment_count).label('total_comments'),
                func.sum(Series.episode_count).label('total_episodes'),
                func.avg(Series.episode_count).label('avg_episodes_per_series')
            )
            .first()
        )
        
        return {
            "total_series": total_count,
            "published_series": published_count,
            "draft_series": draft_count,
            "completed_series": completed_count,
            "active_series": active_count,
            "by_type": {str(st): count for st, count in type_stats},
            "engagement": {
                "total_subscriptions": engagement_stats.total_subscriptions or 0,
                "total_views": engagement_stats.total_views or 0,
                "total_likes": engagement_stats.total_likes or 0,
                "total_shares": engagement_stats.total_shares or 0,
                "total_comments": engagement_stats.total_comments or 0
            },
            "episodes": {
                "total_episodes": engagement_stats.total_episodes or 0,
                "average_episodes_per_series": float(engagement_stats.avg_episodes_per_series or 0)
            }
        }
    
    def get_creator_series_stats(
        self,
        db: Session,
        creator_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get series statistics for specific creator"""
        filters = {"creator_id": creator_id}
        return self.get_series_stats(db, filters)
    
    def get_category_series_count(
        self,
        db: Session,
        category_id: uuid.UUID,
        status: Optional[SeriesStatusEnum] = None
    ) -> int:
        """Get series count for a specific category"""
        filters = {"primary_category_id": category_id}
        if status:
            filters["status"] = status
        
        return self.count(db, filters)
    
    # Series Management Operations
    
    def bulk_update_status(
        self,
        db: Session,
        series_ids: List[uuid.UUID],
        new_status: str
    ) -> int:
        """Bulk update series status"""
        updated_count = (
            db.query(Series)
            .filter(Series.id.in_(series_ids))
            .update(
                {
                    Series.status: SeriesStatusEnum(new_status),
                    Series.updated_at: datetime.utcnow()
                },
                synchronize_session=False
            )
        )
        db.commit()
        return updated_count
    
    def bulk_update_category(
        self,
        db: Session,
        series_ids: List[uuid.UUID],
        new_category_id: uuid.UUID
    ) -> int:
        """Bulk update series category"""
        updated_count = (
            db.query(Series)
            .filter(Series.id.in_(series_ids))
            .update(
                {
                    Series.primary_category_id: new_category_id,
                    Series.updated_at: datetime.utcnow()
                },
                synchronize_session=False
            )
        )
        db.commit()
        return updated_count
    
    def archive_old_series(
        self,
        db: Session,
        days_old: int,
        status: SeriesStatusEnum = SeriesStatusEnum.DRAFT
    ) -> int:
        """Archive series older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        updated_count = (
            db.query(Series)
            .filter(
                Series.status == status,
                Series.created_at < cutoff_date
            )
            .update(
                {
                    Series.status: SeriesStatusEnum.ARCHIVED,
                    Series.updated_at: datetime.utcnow()
                },
                synchronize_session=False
            )
        )
        db.commit()
        return updated_count
    
    # Engagement Operations
    
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
        """Increment engagement counters efficiently"""
        try:
            updates = {}
            if subscription_increment != 0:
                updates[Series.subscription_count] = Series.subscription_count + subscription_increment
            if view_increment > 0:
                updates[Series.view_count] = Series.view_count + view_increment
            if like_increment > 0:
                updates[Series.like_count] = Series.like_count + like_increment
            if share_increment > 0:
                updates[Series.share_count] = Series.share_count + share_increment
            if comment_increment > 0:
                updates[Series.comment_count] = Series.comment_count + comment_increment
            
            if updates:
                updates[Series.updated_at] = datetime.utcnow()
                
                db.query(Series).filter(Series.id == series_id).update(
                    updates, synchronize_session=False
                )
                db.commit()
                return True
            
            return False
            
        except Exception as e:
            db.rollback()
            return False
    
    # Specialized Query Methods
    
    def find_series_by_slug(
        self,
        db: Session,
        slug: str,
        language: str = 'ar'
    ) -> Optional[Series]:
        """Find series by slug in specific language"""
        return (
            db.query(Series)
            .filter(Series.slug[language].astext == slug)
            .first()
        )
    
    def find_series_by_creator_and_title(
        self,
        db: Session,
        creator_id: uuid.UUID,
        title_text: str,
        language: str = 'ar',
        exclude_id: Optional[uuid.UUID] = None
    ) -> Optional[Series]:
        """Find series by creator and title (for duplicate checking)"""
        query = (
            db.query(Series)
            .filter(
                Series.creator_id == creator_id,
                Series.title[language].astext.ilike(f"%{title_text}%")
            )
        )
        
        if exclude_id:
            query = query.filter(Series.id != exclude_id)
        
        return query.first()
    
    def find_duplicate_titles(
        self,
        db: Session,
        title_text: str,
        language: str = 'ar',
        exclude_id: Optional[uuid.UUID] = None
    ) -> List[Series]:
        """Find series with duplicate titles"""
        query = (
            db.query(Series)
            .filter(Series.title[language].astext.ilike(f"%{title_text}%"))
        )
        
        if exclude_id:
            query = query.filter(Series.id != exclude_id)
        
        return query.all()
    
    def get_scheduled_series(
        self,
        db: Session,
        before_time: Optional[datetime] = None
    ) -> List[Series]:
        """Get series scheduled for publication"""
        if not before_time:
            before_time = datetime.utcnow()
        
        return (
            self.query_builder(db)
            .filter(
                Series.scheduled_start_date <= before_time,
                Series.status == SeriesStatusEnum.DRAFT
            )
            .order_by('scheduled_start_date', 'asc')
            .all()
        )
    
    def get_expiring_series(
        self,
        db: Session,
        days_ahead: int = 7
    ) -> List[Series]:
        """Get series that will reach expected end date soon"""
        future_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        return (
            self.query_builder(db)
            .filter(
                Series.expected_end_date.isnot(None),
                Series.expected_end_date <= future_date,
                Series.status == SeriesStatusEnum.PUBLISHED
            )
            .order_by('expected_end_date', 'asc')
            .include('primary_category')
            .all()
        )
    
    # Private Helper Methods
    
    def _apply_multilingual_search(
        self,
        builder: QueryBuilder[Series],
        query_text: str,
        language: str
    ) -> QueryBuilder[Series]:
        """Apply multilingual full-text search"""
        search_term = f"%{query_text.lower()}%"
        
        return builder.filter(
            or_(
                # Primary language search
                Series.title[language].astext.ilike(search_term),
                Series.description[language].astext.ilike(search_term),
                # Fallback to full JSON search
                func.lower(func.cast(Series.title, text('text'))).contains(query_text.lower()),
                func.lower(func.cast(Series.description, text('text'))).contains(query_text.lower()),
                # Tags search
                Series.tags.op('@>')([query_text.lower()])
            )
        )
    
    def _apply_series_filters(
        self,
        builder: QueryBuilder[Series],
        filters: Dict[str, Any]
    ) -> QueryBuilder[Series]:
        """Apply series-specific filters"""
        
        # Status filter
        if 'status' in filters and filters['status']:
            if isinstance(filters['status'], str):
                builder = builder.filter_by(status=SeriesStatusEnum(filters['status']))
            else:
                builder = builder.filter_by(status=filters['status'])
        
        # Series type filter
        if 'series_type' in filters and filters['series_type']:
            if isinstance(filters['series_type'], str):
                builder = builder.filter_by(series_type=SeriesTypeEnum(filters['series_type']))
            else:
                builder = builder.filter_by(series_type=filters['series_type'])
        
        # Visibility filter
        if 'visibility' in filters and filters['visibility']:
            if isinstance(filters['visibility'], str):
                builder = builder.filter_by(visibility=SeriesVisibilityEnum(filters['visibility']))
            else:
                builder = builder.filter_by(visibility=filters['visibility'])
        
        # Category filter
        if 'category_id' in filters and filters['category_id']:
            builder = builder.filter_by(primary_category_id=filters['category_id'])
        
        # Creator filter
        if 'creator_id' in filters and filters['creator_id']:
            builder = builder.filter_by(creator_id=filters['creator_id'])
        
        # Featured filter
        if 'is_featured' in filters and filters['is_featured'] is not None:
            builder = builder.filter_by(is_featured=filters['is_featured'])
        
        # Date range filters
        if 'created_after' in filters and filters['created_after']:
            builder = builder.filter(Series.created_at >= filters['created_after'])
        
        if 'created_before' in filters and filters['created_before']:
            builder = builder.filter(Series.created_at <= filters['created_before'])
        
        if 'published_after' in filters and filters['published_after']:
            builder = builder.filter(Series.published_at >= filters['published_after'])
        
        if 'published_before' in filters and filters['published_before']:
            builder = builder.filter(Series.published_at <= filters['published_before'])
        
        # Episode count range
        if 'min_episodes' in filters and filters['min_episodes'] is not None:
            builder = builder.filter(Series.episode_count >= filters['min_episodes'])
        
        if 'max_episodes' in filters and filters['max_episodes'] is not None:
            builder = builder.filter(Series.episode_count <= filters['max_episodes'])
        
        # Subscription count range
        if 'min_subscriptions' in filters and filters['min_subscriptions'] is not None:
            builder = builder.filter(Series.subscription_count >= filters['min_subscriptions'])
        
        if 'has_episodes' in filters and filters['has_episodes'] is not None:
            if filters['has_episodes']:
                builder = builder.filter(Series.episode_count > 0)
            else:
                builder = builder.filter(Series.episode_count == 0)
        
        # Completion status
        if 'is_complete' in filters and filters['is_complete'] is not None:
            if filters['is_complete']:
                builder = builder.filter(Series.status == SeriesStatusEnum.COMPLETED)
            else:
                builder = builder.filter(Series.status != SeriesStatusEnum.COMPLETED)
        
        # Rating filter
        if 'min_rating' in filters and filters['min_rating'] is not None:
            builder = builder.filter(Series.rating >= filters['min_rating'])
        
        # Tags filter
        if 'tags' in filters and filters['tags']:
            for tag in filters['tags']:
                builder = builder.filter(Series.tags.op('@>')([tag]))
        
        return builder


class SeriesSubscriptionRepository(BaseRepository[SeriesSubscription, dict, dict], ISeriesSubscriptionRepository):
    """
    Enhanced repository for series subscription data access.
    """
    
    def __init__(self):
        super().__init__(SeriesSubscription)
    
    def get_user_subscriptions(
        self,
        db: Session,
        user_id: uuid.UUID,
        status: Optional[str] = None,
        pagination: Optional[Dict[str, int]] = None
    ) -> Tuple[List[SeriesSubscription], int]:
        """Get user's series subscriptions"""
        builder = (
            self.query_builder(db)
            .filter_by(user_id=user_id)
            .include('series')
            .order_by('created_at', 'desc')
        )
        
        if status:
            builder = builder.filter_by(status=SubscriptionStatusEnum(status))
        
        total_count = builder.count()
        
        if pagination:
            page = pagination.get('page', 1)
            limit = pagination.get('limit', 20)
            builder = builder.paginate(page, limit)
        
        subscriptions = builder.all()
        return subscriptions, total_count
    
    def get_series_subscriptions(
        self,
        db: Session,
        series_id: uuid.UUID,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[SeriesSubscription]:
        """Get subscriptions for a series"""
        builder = (
            self.query_builder(db)
            .filter_by(series_id=series_id)
            .include('user')
            .order_by('created_at', 'desc')
        )
        
        if status:
            builder = builder.filter_by(status=SubscriptionStatusEnum(status))
        
        if limit > 0:
            builder = builder.paginate(1, limit)
        
        return builder.all()
    
    def create_subscription(
        self,
        db: Session,
        user_id: uuid.UUID,
        series_id: uuid.UUID,
        notification_enabled: bool = True,
        auto_download: bool = False
    ) -> Optional[SeriesSubscription]:
        """Create new subscription"""
        try:
            # Check if subscription already exists
            existing = (
                db.query(SeriesSubscription)
                .filter_by(user_id=user_id, series_id=series_id)
                .first()
            )
            
            if existing:
                if existing.status == SubscriptionStatusEnum.CANCELLED:
                    # Reactivate cancelled subscription
                    existing.status = SubscriptionStatusEnum.ACTIVE
                    existing.notification_enabled = notification_enabled
                    existing.auto_download = auto_download
                    existing.updated_at = datetime.utcnow()
                    db.commit()
                    return existing
                else:
                    # Already subscribed
                    return existing
            
            # Create new subscription
            subscription = SeriesSubscription(
                user_id=user_id,
                series_id=series_id,
                status=SubscriptionStatusEnum.ACTIVE,
                notification_enabled=notification_enabled,
                auto_download=auto_download
            )
            
            db.add(subscription)
            db.commit()
            db.refresh(subscription)
            
            return subscription
            
        except Exception as e:
            db.rollback()
            return None
    
    def update_subscription(
        self,
        db: Session,
        subscription_id: uuid.UUID,
        updates: Dict[str, Any]
    ) -> Optional[SeriesSubscription]:
        """Update subscription"""
        try:
            subscription = db.query(SeriesSubscription).filter_by(id=subscription_id).first()
            if not subscription:
                return None
            
            for field, value in updates.items():
                if hasattr(subscription, field):
                    setattr(subscription, field, value)
            
            subscription.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(subscription)
            
            return subscription
            
        except Exception as e:
            db.rollback()
            return None
    
    def delete_subscription(
        self,
        db: Session,
        subscription_id: uuid.UUID
    ) -> bool:
        """Delete subscription"""
        try:
            result = (
                db.query(SeriesSubscription)
                .filter_by(id=subscription_id)
                .delete()
            )
            db.commit()
            return result > 0
            
        except Exception as e:
            db.rollback()
            return False
    
    def is_user_subscribed(
        self,
        db: Session,
        user_id: uuid.UUID,
        series_id: uuid.UUID
    ) -> bool:
        """Check if user is subscribed to series"""
        subscription = (
            db.query(SeriesSubscription)
            .filter_by(
                user_id=user_id,
                series_id=series_id,
                status=SubscriptionStatusEnum.ACTIVE
            )
            .first()
        )
        return subscription is not None
    
    def get_subscription_stats(
        self,
        db: Session,
        series_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """Get subscription statistics"""
        query = db.query(SeriesSubscription)
        
        if series_id:
            query = query.filter_by(series_id=series_id)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        total_count = query.count()
        active_count = query.filter_by(status=SubscriptionStatusEnum.ACTIVE).count()
        cancelled_count = query.filter_by(status=SubscriptionStatusEnum.CANCELLED).count()
        
        return {
            "total_subscriptions": total_count,
            "active_subscriptions": active_count,
            "cancelled_subscriptions": cancelled_count,
            "retention_rate": (active_count / total_count * 100) if total_count > 0 else 0
        }
    
    def bulk_update_subscriptions(
        self,
        db: Session,
        subscription_ids: List[uuid.UUID],
        updates: Dict[str, Any]
    ) -> int:
        """Bulk update subscriptions"""
        try:
            updates['updated_at'] = datetime.utcnow()
            
            updated_count = (
                db.query(SeriesSubscription)
                .filter(SeriesSubscription.id.in_(subscription_ids))
                .update(updates, synchronize_session=False)
            )
            db.commit()
            return updated_count
            
        except Exception as e:
            db.rollback()
            return 0
    
    def get_users_to_notify(
        self,
        db: Session,
        series_id: uuid.UUID
    ) -> List[uuid.UUID]:
        """Get users who should be notified about series updates"""
        subscriptions = (
            db.query(SeriesSubscription)
            .filter_by(
                series_id=series_id,
                status=SubscriptionStatusEnum.ACTIVE,
                notification_enabled=True
            )
            .all()
        )
        
        return [sub.user_id for sub in subscriptions]