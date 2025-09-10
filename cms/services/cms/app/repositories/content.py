"""
Enhanced Content Repository

Improved content repository using clean architecture principles
and advanced query building capabilities.
"""

import uuid
from typing import List, Optional, Dict, Any, Union, Tuple
from sqlalchemy import func, and_, or_, text, desc, asc, cast
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.dialects.postgresql import TSVECTOR
from datetime import datetime, timedelta

from models.content import Content, ContentStatusEnum, ContentTypeEnum, ContentVisibilityEnum
from api.v1.models.content import ContentCreate, ContentUpdate
from repositories.base import BaseRepository, QueryBuilder
from repositories.interfaces import IContentRepository


class ContentRepository(BaseRepository[Content, ContentCreate, ContentUpdate], IContentRepository):
    """
    Enhanced repository for content data access with advanced querying capabilities.
    
    Provides:
    - Advanced search with full-text capabilities
    - Multilingual content support
    - Complex filtering and aggregation
    - Performance-optimized queries
    - Cache-aware operations
    """
    
    def __init__(self):
        super().__init__(Content)
    
    # Advanced Query Methods
    
    def search_content_advanced(
        self,
        db: Session,
        search_params: Dict[str, Any],
        pagination: Dict[str, int]
    ) -> Tuple[List[Content], int]:
        """
        Advanced content search with full-text search and complex filtering.
        
        Args:
            db: Database session
            search_params: Search parameters and filters
            pagination: Pagination parameters
            
        Returns:
            Tuple of (content_list, total_count)
        """
        builder = self.query_builder(db)
        
        # Apply search query
        query_text = search_params.get('query')
        language = search_params.get('language', 'ar')
        
        if query_text:
            builder = self._apply_multilingual_search(builder, query_text, language)
        
        # Apply filters
        builder = self._apply_content_filters(builder, search_params)
        
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
        
        content_list = builder.all()
        
        return content_list, total_count
    
    def get_content_with_relationships(
        self,
        db: Session,
        content_id: uuid.UUID
    ) -> Optional[Content]:
        """Get content with all relationships loaded"""
        return (
            self.query_builder(db)
            .filter_by(id=content_id)
            .include('primary_category')
            .first()
        )
    
    def get_published_content_by_category(
        self,
        db: Session,
        category_id: uuid.UUID,
        limit: int = 10,
        language: Optional[str] = None
    ) -> List[Content]:
        """Get published content in specific category"""
        builder = (
            self.query_builder(db)
            .filter_by(
                primary_category_id=category_id,
                status=ContentStatusEnum.PUBLISHED,
                visibility=ContentVisibilityEnum.PUBLIC
            )
            .order_by('published_at', 'desc')
            .include('primary_category')
        )
        
        if limit > 0:
            builder = builder.paginate(1, limit)
        
        return builder.all()
    
    def get_trending_content(
        self,
        db: Session,
        hours: int = 24,
        limit: int = 10,
        category_id: Optional[uuid.UUID] = None
    ) -> List[Content]:
        """Get trending content based on engagement metrics"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        builder = (
            self.query_builder(db)
            .filter(
                Content.status == ContentStatusEnum.PUBLISHED,
                Content.visibility == ContentVisibilityEnum.PUBLIC,
                Content.published_at >= cutoff_time
            )
            .include('primary_category')
        )
        
        if category_id:
            builder = builder.filter_by(primary_category_id=category_id)
        
        # Order by engagement score (views + likes*2 + shares*3)
        results = builder.all()
        
        # Sort by calculated engagement score
        def engagement_score(content):
            return content.view_count + (content.like_count * 2) + (content.share_count * 3)
        
        return sorted(results, key=engagement_score, reverse=True)[:limit]
    
    def get_popular_content(
        self,
        db: Session,
        period_days: int = 30,
        limit: int = 10,
        content_type: Optional[ContentTypeEnum] = None
    ) -> List[Content]:
        """Get popular content by view count in specified period"""
        cutoff_date = datetime.utcnow() - timedelta(days=period_days)
        
        builder = (
            self.query_builder(db)
            .filter(
                Content.status == ContentStatusEnum.PUBLISHED,
                Content.visibility == ContentVisibilityEnum.PUBLIC,
                Content.published_at >= cutoff_date
            )
            .order_by('view_count', 'desc')
            .include('primary_category')
        )
        
        if content_type:
            builder = builder.filter_by(content_type=content_type)
        
        if limit > 0:
            builder = builder.paginate(1, limit)
        
        return builder.all()
    
    def get_related_content(
        self,
        db: Session,
        content_id: uuid.UUID,
        limit: int = 5
    ) -> List[Content]:
        """Get content related to the specified content"""
        # Get the reference content
        reference_content = self.get_by_id(db, content_id)
        if not reference_content:
            return []
        
        builder = (
            self.query_builder(db)
            .filter(
                Content.id != content_id,
                Content.status == ContentStatusEnum.PUBLISHED,
                Content.visibility == ContentVisibilityEnum.PUBLIC
            )
            .include('primary_category')
        )
        
        # Prioritize by same category
        if reference_content.primary_category_id:
            builder = builder.filter_by(primary_category_id=reference_content.primary_category_id)
        
        # Then by content type
        builder = builder.filter_by(content_type=reference_content.content_type)
        
        # Order by popularity
        builder = builder.order_by('view_count', 'desc')
        
        if limit > 0:
            builder = builder.paginate(1, limit)
        
        return builder.all()
    
    # Content Analytics and Aggregation
    
    def get_content_stats(
        self,
        db: Session,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get comprehensive content statistics"""
        base_query = self._build_base_query(db, filters)
        
        # Basic counts
        total_count = base_query.count()
        published_count = base_query.filter(Content.status == ContentStatusEnum.PUBLISHED).count()
        draft_count = base_query.filter(Content.status == ContentStatusEnum.DRAFT).count()
        archived_count = base_query.filter(Content.status == ContentStatusEnum.ARCHIVED).count()
        
        # Content type breakdown
        type_stats = (
            db.query(Content.content_type, func.count(Content.id))
            .group_by(Content.content_type)
            .all()
        )
        
        # Engagement totals
        engagement_stats = (
            base_query
            .with_entities(
                func.sum(Content.view_count).label('total_views'),
                func.sum(Content.like_count).label('total_likes'),
                func.sum(Content.share_count).label('total_shares'),
                func.sum(Content.comment_count).label('total_comments')
            )
            .first()
        )
        
        return {
            "total_content": total_count,
            "published_content": published_count,
            "draft_content": draft_count,
            "archived_content": archived_count,
            "by_type": {str(ct): count for ct, count in type_stats},
            "engagement": {
                "total_views": engagement_stats.total_views or 0,
                "total_likes": engagement_stats.total_likes or 0,
                "total_shares": engagement_stats.total_shares or 0,
                "total_comments": engagement_stats.total_comments or 0
            }
        }
    
    def get_author_content_stats(
        self,
        db: Session,
        author_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get content statistics for specific author"""
        filters = {"author_id": author_id}
        return self.get_content_stats(db, filters)
    
    def get_category_content_count(
        self,
        db: Session,
        category_id: uuid.UUID,
        status: Optional[ContentStatusEnum] = None
    ) -> int:
        """Get content count for a specific category"""
        filters = {"primary_category_id": category_id}
        if status:
            filters["status"] = status
        
        return self.count(db, filters)
    
    # Content Management Operations
    
    def bulk_update_status(
        self,
        db: Session,
        content_ids: List[uuid.UUID],
        new_status: ContentStatusEnum
    ) -> int:
        """Bulk update content status"""
        updated_count = (
            db.query(Content)
            .filter(Content.id.in_(content_ids))
            .update(
                {
                    Content.status: new_status,
                    Content.updated_at: datetime.utcnow()
                },
                synchronize_session=False
            )
        )
        db.commit()
        return updated_count
    
    def bulk_update_category(
        self,
        db: Session,
        content_ids: List[uuid.UUID],
        new_category_id: uuid.UUID
    ) -> int:
        """Bulk update content category"""
        updated_count = (
            db.query(Content)
            .filter(Content.id.in_(content_ids))
            .update(
                {
                    Content.primary_category_id: new_category_id,
                    Content.updated_at: datetime.utcnow()
                },
                synchronize_session=False
            )
        )
        db.commit()
        return updated_count
    
    def archive_old_content(
        self,
        db: Session,
        days_old: int,
        status: ContentStatusEnum = ContentStatusEnum.DRAFT
    ) -> int:
        """Archive content older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        updated_count = (
            db.query(Content)
            .filter(
                Content.status == status,
                Content.created_at < cutoff_date
            )
            .update(
                {
                    Content.status: ContentStatusEnum.ARCHIVED,
                    Content.updated_at: datetime.utcnow()
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
        content_id: uuid.UUID,
        view_increment: int = 0,
        like_increment: int = 0,
        share_increment: int = 0,
        comment_increment: int = 0
    ) -> bool:
        """Increment engagement counters efficiently"""
        try:
            updates = {}
            if view_increment > 0:
                updates[Content.view_count] = Content.view_count + view_increment
            if like_increment > 0:
                updates[Content.like_count] = Content.like_count + like_increment
            if share_increment > 0:
                updates[Content.share_count] = Content.share_count + share_increment
            if comment_increment > 0:
                updates[Content.comment_count] = Content.comment_count + comment_increment
            
            if updates:
                updates[Content.updated_at] = datetime.utcnow()
                
                db.query(Content).filter(Content.id == content_id).update(
                    updates, synchronize_session=False
                )
                db.commit()
                return True
            
            return False
            
        except Exception as e:
            db.rollback()
            return False
    
    # Specialized Query Methods
    
    def find_content_by_slug(
        self,
        db: Session,
        slug: str,
        language: str = 'ar'
    ) -> Optional[Content]:
        """Find content by slug in specific language"""
        return (
            db.query(Content)
            .filter(Content.slug[language].astext == slug)
            .first()
        )
    
    def find_duplicate_titles(
        self,
        db: Session,
        title_text: str,
        language: str = 'ar',
        exclude_id: Optional[uuid.UUID] = None
    ) -> List[Content]:
        """Find content with duplicate titles"""
        query = (
            db.query(Content)
            .filter(Content.title[language].astext.ilike(f"%{title_text}%"))
        )
        
        if exclude_id:
            query = query.filter(Content.id != exclude_id)
        
        return query.all()
    
    def get_scheduled_content(
        self,
        db: Session,
        before_time: Optional[datetime] = None
    ) -> List[Content]:
        """Get content scheduled for publication"""
        if not before_time:
            before_time = datetime.utcnow()
        
        return (
            self.query_builder(db)
            .filter(
                Content.scheduled_at <= before_time,
                Content.status == ContentStatusEnum.DRAFT
            )
            .order_by('scheduled_at', 'asc')
            .all()
        )
    
    def get_expiring_content(
        self,
        db: Session,
        days_ahead: int = 7
    ) -> List[Content]:
        """Get content that will expire soon"""
        future_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        return (
            self.query_builder(db)
            .filter(
                Content.expires_at.isnot(None),
                Content.expires_at <= future_date,
                Content.status == ContentStatusEnum.PUBLISHED
            )
            .order_by('expires_at', 'asc')
            .include('primary_category')
            .all()
        )
    
    # Private Helper Methods
    
    def _apply_multilingual_search(
        self,
        builder: QueryBuilder[Content],
        query_text: str,
        language: str
    ) -> QueryBuilder[Content]:
        """Apply multilingual full-text search"""
        search_term = f"%{query_text.lower()}%"
        
        return builder.filter(
            or_(
                # Primary language search
                Content.title[language].astext.ilike(search_term),
                Content.description[language].astext.ilike(search_term),
                Content.body[language].astext.ilike(search_term),
                # Fallback to full JSON search
                func.lower(func.cast(Content.title, text('text'))).contains(query_text.lower()),
                func.lower(func.cast(Content.description, text('text'))).contains(query_text.lower()),
                func.lower(func.cast(Content.body, text('text'))).contains(query_text.lower()),
                # Tags search
                Content.tags.op('@>')([query_text.lower()])
            )
        )
    
    def _apply_content_filters(
        self,
        builder: QueryBuilder[Content],
        filters: Dict[str, Any]
    ) -> QueryBuilder[Content]:
        """Apply content-specific filters"""
        
        # Status filter
        if 'status' in filters and filters['status']:
            if isinstance(filters['status'], str):
                builder = builder.filter_by(status=ContentStatusEnum(filters['status']))
            else:
                builder = builder.filter_by(status=filters['status'])
        
        # Content type filter
        if 'content_type' in filters and filters['content_type']:
            if isinstance(filters['content_type'], str):
                builder = builder.filter_by(content_type=ContentTypeEnum(filters['content_type']))
            else:
                builder = builder.filter_by(content_type=filters['content_type'])
        
        # Visibility filter
        if 'visibility' in filters and filters['visibility']:
            if isinstance(filters['visibility'], str):
                builder = builder.filter_by(visibility=ContentVisibilityEnum(filters['visibility']))
            else:
                builder = builder.filter_by(visibility=filters['visibility'])
        
        # Category filter
        if 'category_id' in filters and filters['category_id']:
            builder = builder.filter_by(primary_category_id=filters['category_id'])
        
        # Author filter
        if 'author_id' in filters and filters['author_id']:
            builder = builder.filter_by(author_id=filters['author_id'])
        
        # Featured filter
        if 'is_featured' in filters and filters['is_featured'] is not None:
            builder = builder.filter_by(is_featured=filters['is_featured'])
        
        # Date range filters
        if 'created_after' in filters and filters['created_after']:
            builder = builder.filter(Content.created_at >= filters['created_after'])
        
        if 'created_before' in filters and filters['created_before']:
            builder = builder.filter(Content.created_at <= filters['created_before'])
        
        if 'published_after' in filters and filters['published_after']:
            builder = builder.filter(Content.published_at >= filters['published_after'])
        
        if 'published_before' in filters and filters['published_before']:
            builder = builder.filter(Content.published_at <= filters['published_before'])
        
        # Media filter
        if 'has_media' in filters and filters['has_media'] is not None:
            if filters['has_media']:
                builder = builder.filter(Content.file_url.isnot(None))
            else:
                builder = builder.filter(Content.file_url.is_(None))
        
        # View count range
        if 'min_views' in filters and filters['min_views'] is not None:
            builder = builder.filter(Content.view_count >= filters['min_views'])
        
        if 'max_views' in filters and filters['max_views'] is not None:
            builder = builder.filter(Content.view_count <= filters['max_views'])
        
        # Tags filter
        if 'tags' in filters and filters['tags']:
            for tag in filters['tags']:
                builder = builder.filter(Content.tags.op('@>')([tag]))
        
        return builder