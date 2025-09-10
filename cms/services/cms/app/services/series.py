"""
Series Service

This module provides business logic for series management including validation,
lifecycle management, multilingual support, subscription management, and episode organization.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

from models.series import Series, SeriesSubscription, SeriesTypeEnum, SeriesStatusEnum, SeriesVisibilityEnum
from repositories.series import SeriesRepository, SeriesSubscriptionRepository
from business.series_business_service import SeriesBusinessService
from api.v1.models.series import (
    SeriesCreate, SeriesUpdate, SeriesResponse, SeriesAnalytics,
    SeriesSearchFilters, SeriesSubscriptionCreate, SeriesSubscriptionUpdate,
    SeriesSubscriptionResponse, SeriesStatsResponse, SeriesRecommendationRequest,
    SeriesRecommendationResponse
)
from api.v1.models.common import PaginatedResponse, PaginationParams

logger = logging.getLogger(__name__)


class SeriesService:
    """
    Business service for series management.
    
    Handles:
    - Series CRUD with validation
    - Series lifecycle management (draft, published, completed)
    - Multilingual series support
    - Subscription management
    - Episode organization
    - Series analytics and engagement
    - Business rules enforcement
    """
    
    def __init__(self, series_repository: SeriesRepository, subscription_repository: SeriesSubscriptionRepository, db: Session):
        self.db = db
        self.series_repository = series_repository
        self.subscription_repository = subscription_repository
        self.business_service = None  # Will be injected by controller
    
    # Core CRUD Operations
    
    async def create_series(self, series_data: SeriesCreate, creator_id: uuid.UUID) -> SeriesResponse:
        """Create new series with business logic"""
        try:
            # Convert Pydantic model to dict
            series_dict = series_data.model_dump()
            
            # Use business service for rule enforcement
            series = self.business_service.create_series_with_business_rules(
                series_dict, creator_id
            )
            
            return self._convert_to_response(series)
            
        except Exception as e:
            logger.error(f"Failed to create series: {str(e)}")
            raise
    
    async def get_series_by_id(self, series_id: uuid.UUID) -> Optional[SeriesResponse]:
        """Get series by ID with relationships"""
        try:
            series = self.series_repository.get_series_with_relationships(self.db, series_id)
            
            if not series:
                return None
            
            return self._convert_to_response(series, include_relationships=True)
            
        except Exception as e:
            logger.error(f"Failed to get series {series_id}: {str(e)}")
            raise
    
    async def update_series(
        self, 
        series_id: uuid.UUID, 
        updates: SeriesUpdate, 
        updated_by_user_id: uuid.UUID
    ) -> SeriesResponse:
        """Update series with business logic"""
        try:
            # Convert Pydantic model to dict, excluding unset fields
            updates_dict = updates.model_dump(exclude_unset=True)
            
            # Use business service for rule enforcement
            series = self.business_service.update_series_with_business_rules(
                series_id, updates_dict, updated_by_user_id
            )
            
            return self._convert_to_response(series)
            
        except Exception as e:
            logger.error(f"Failed to update series {series_id}: {str(e)}")
            raise
    
    async def delete_series(
        self, 
        series_id: uuid.UUID, 
        deleted_by_user_id: uuid.UUID, 
        soft_delete: bool = True
    ) -> bool:
        """Delete series with business logic"""
        try:
            return self.business_service.delete_series_with_business_rules(
                series_id, deleted_by_user_id, soft_delete
            )
            
        except Exception as e:
            logger.error(f"Failed to delete series {series_id}: {str(e)}")
            raise
    
    # Search and Discovery Operations
    
    async def search_series(
        self,
        filters: SeriesSearchFilters,
        pagination: PaginationParams
    ) -> Tuple[List[SeriesResponse], int]:
        """Search series with advanced filtering"""
        try:
            # Convert filters to dict
            search_params = filters.model_dump(exclude_unset=True)
            pagination_dict = {
                'page': pagination.page,
                'limit': pagination.limit
            }
            
            # Execute search
            series_list, total_count = self.series_repository.search_series_advanced(
                self.db, search_params, pagination_dict
            )
            
            # Convert to response models
            response_list = [
                self._convert_to_response(series, include_relationships=True)
                for series in series_list
            ]
            
            return response_list, total_count
            
        except Exception as e:
            logger.error(f"Failed to search series: {str(e)}")
            raise
    
    # Series Management Operations
    
    async def publish_series(
        self,
        series_id: uuid.UUID,
        published_by_user_id: uuid.UUID,
        publish_immediately: bool = True,
        scheduled_start_date: Optional[datetime] = None
    ) -> SeriesResponse:
        """Publish series with business logic"""
        try:
            series = self.business_service.publish_series_with_business_rules(
                series_id, published_by_user_id, publish_immediately, scheduled_start_date
            )
            
            return self._convert_to_response(series)
            
        except Exception as e:
            logger.error(f"Failed to publish series {series_id}: {str(e)}")
            raise
    
    async def complete_series(
        self,
        series_id: uuid.UUID,
        completed_by_user_id: uuid.UUID
    ) -> SeriesResponse:
        """Complete series with business logic"""
        try:
            series = self.business_service.complete_series_with_business_rules(
                series_id, completed_by_user_id
            )
            
            return self._convert_to_response(series)
            
        except Exception as e:
            logger.error(f"Failed to complete series {series_id}: {str(e)}")
            raise
    
    # Subscription Management Operations
    
    async def create_subscription(
        self,
        user_id: uuid.UUID,
        subscription_data: SeriesSubscriptionCreate
    ) -> SeriesSubscriptionResponse:
        """Create series subscription"""
        try:
            subscription = self.subscription_repository.create_subscription(
                self.db,
                user_id,
                subscription_data.series_id,
                subscription_data.notification_enabled,
                subscription_data.auto_download
            )
            
            if not subscription:
                raise ValueError("Failed to create subscription")
            
            # Update series subscription count
            self.series_repository.increment_engagement_counters(
                self.db, subscription_data.series_id, subscription_increment=1
            )
            
            return self._convert_subscription_to_response(subscription)
            
        except Exception as e:
            logger.error(f"Failed to create subscription: {str(e)}")
            raise
    
    async def update_subscription(
        self,
        subscription_id: uuid.UUID,
        updates: SeriesSubscriptionUpdate,
        user_id: uuid.UUID
    ) -> SeriesSubscriptionResponse:
        """Update subscription"""
        try:
            updates_dict = updates.model_dump(exclude_unset=True)
            
            subscription = self.subscription_repository.update_subscription(
                self.db, subscription_id, updates_dict
            )
            
            if not subscription:
                raise ValueError("Subscription not found or update failed")
            
            return self._convert_subscription_to_response(subscription)
            
        except Exception as e:
            logger.error(f"Failed to update subscription {subscription_id}: {str(e)}")
            raise
    
    async def cancel_subscription(
        self,
        subscription_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> bool:
        """Cancel subscription"""
        try:
            # Get subscription to update series count
            subscription = self.subscription_repository.get_by_id(self.db, subscription_id)
            if not subscription:
                raise ValueError("Subscription not found")
            
            # Update subscription status
            success = self.subscription_repository.update_subscription(
                self.db, subscription_id, {'status': 'CANCELLED'}
            )
            
            if success:
                # Update series subscription count
                self.series_repository.increment_engagement_counters(
                    self.db, subscription.series_id, subscription_increment=-1
                )
            
            return success is not None
            
        except Exception as e:
            logger.error(f"Failed to cancel subscription {subscription_id}: {str(e)}")
            raise
    
    async def get_user_subscriptions(
        self,
        user_id: uuid.UUID,
        pagination: PaginationParams
    ) -> List[SeriesSubscriptionResponse]:
        """Get user subscriptions"""
        try:
            pagination_dict = {
                'page': pagination.page,
                'limit': pagination.limit
            }
            
            subscriptions, total = self.subscription_repository.get_user_subscriptions(
                self.db, user_id, pagination=pagination_dict
            )
            
            return [
                self._convert_subscription_to_response(sub)
                for sub in subscriptions
            ]
            
        except Exception as e:
            logger.error(f"Failed to get user subscriptions for {user_id}: {str(e)}")
            raise
    
    async def get_subscription_by_id(self, subscription_id: uuid.UUID) -> Optional[SeriesSubscriptionResponse]:
        """Get subscription by ID"""
        try:
            subscription = self.subscription_repository.get_by_id(self.db, subscription_id)
            
            if not subscription:
                return None
            
            return self._convert_subscription_to_response(subscription)
            
        except Exception as e:
            logger.error(f"Failed to get subscription {subscription_id}: {str(e)}")
            raise
    
    # Analytics and Stats Operations
    
    async def get_series_analytics(self, series_id: uuid.UUID) -> SeriesAnalytics:
        """Get series analytics"""
        try:
            series = self.series_repository.get_by_id(self.db, series_id)
            if not series:
                raise ValueError("Series not found")
            
            return SeriesAnalytics(
                series_id=series.id,
                series_title=series.title,
                subscription_count=series.subscription_count,
                total_views=series.view_count,
                total_likes=series.like_count,
                total_shares=series.share_count,
                total_comments=series.comment_count,
                episode_count=series.episode_count,
                average_episode_duration=None,  # Would calculate from episodes
                completion_rate=0.0,  # Would calculate from user analytics
                average_rating=series.rating,
                rating_count=series.rating_count,
                subscriber_retention_rate=0.0,  # Would calculate from subscriptions
                episode_drop_off_rate=0.0,  # Would calculate from episode analytics
                published_at=series.published_at,
                category_name=series.primary_category.name if series.primary_category else None
            )
            
        except Exception as e:
            logger.error(f"Failed to get analytics for series {series_id}: {str(e)}")
            raise
    
    async def get_series_stats(self, filters: Optional[Dict[str, Any]] = None) -> SeriesStatsResponse:
        """Get series statistics"""
        try:
            stats = self.series_repository.get_series_stats(self.db, filters)
            
            return SeriesStatsResponse(
                total_series=stats["total_series"],
                published_series=stats["published_series"],
                draft_series=stats["draft_series"],
                completed_series=stats["completed_series"],
                active_series=stats["active_series"],
                by_type=stats["by_type"],
                by_category={},  # Would need category join
                by_creator={},   # Would need creator join
                total_subscriptions=stats["engagement"]["total_subscriptions"],
                total_episodes=stats["episodes"]["total_episodes"],
                average_episodes_per_series=stats["episodes"]["average_episodes_per_series"],
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to get series stats: {str(e)}")
            raise
    
    async def get_series_recommendations(
        self,
        request: SeriesRecommendationRequest,
        user_id: Optional[uuid.UUID] = None
    ) -> SeriesRecommendationResponse:
        """Get series recommendations"""
        try:
            # Placeholder recommendation logic
            # In production, this would use sophisticated ML algorithms
            
            filters = SeriesSearchFilters(
                category_id=request.category_id,
                series_type=request.series_type,
                status="PUBLISHED",
                visibility="PUBLIC",
                sort_by="subscription_count",
                sort_order="desc"
            )
            
            pagination = PaginationParams(page=1, limit=request.limit)
            recommendations, _ = await self.search_series(filters, pagination)
            
            # Filter out subscribed series if requested
            if request.exclude_subscribed and user_id:
                user_subscriptions = await self.get_user_subscriptions(
                    user_id, PaginationParams(page=1, limit=1000)
                )
                subscribed_series_ids = {sub.series_id for sub in user_subscriptions}
                recommendations = [
                    rec for rec in recommendations
                    if rec.id not in subscribed_series_ids
                ]
                recommendations = recommendations[:request.limit]
            
            return SeriesRecommendationResponse(
                recommendations=recommendations,
                recommendation_reason="Based on popularity and category preferences",
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to get series recommendations: {str(e)}")
            raise
    
    # Helper Methods
    
    def _convert_to_response(
        self, 
        series: Series, 
        include_relationships: bool = False
    ) -> SeriesResponse:
        """Convert ORM model to response model"""
        response_data = {
            "id": series.id,
            "title": series.title,
            "description": series.description,
            "slug": series.slug,
            "series_type": series.series_type,
            "primary_category_id": series.primary_category_id,
            "status": series.status,
            "visibility": series.visibility,
            "is_featured": series.is_featured,
            "published_at": series.published_at,
            "scheduled_start_date": series.scheduled_start_date,
            "expected_end_date": series.expected_end_date,
            "actual_start_date": series.actual_start_date,
            "actual_end_date": series.actual_end_date,
            "creator_id": series.creator_id,
            "creator_name": series.creator_name,
            "thumbnail_url": series.thumbnail_url,
            "banner_url": series.banner_url,
            "trailer_url": series.trailer_url,
            "episode_count": series.episode_count,
            "expected_episode_count": series.expected_episode_count,
            "season_count": series.season_count,
            "release_schedule": series.release_schedule,
            "subscription_count": series.subscription_count,
            "view_count": series.view_count,
            "like_count": series.like_count,
            "share_count": series.share_count,
            "comment_count": series.comment_count,
            "rating": series.rating,
            "rating_count": series.rating_count,
            "seo_title": series.seo_title,
            "seo_description": series.seo_description,
            "seo_keywords": series.seo_keywords,
            "tags": series.tags,
            "metadata": series._metadata,  # Map _metadata to metadata
            "created_at": series.created_at,
            "updated_at": series.updated_at
        }
        
        # Include relationships if requested
        if include_relationships:
            if series.primary_category:
                response_data["primary_category"] = {
                    "id": series.primary_category.id,
                    "name": series.primary_category.name,
                    "path": getattr(series.primary_category, 'path', '')
                }
            
            # Include latest episodes if available
            if hasattr(series, 'episodes') and series.episodes:
                response_data["latest_episodes"] = [
                    {
                        "id": episode.id,
                        "title": episode.title,
                        "episode_number": getattr(episode, 'episode_number', 0),
                        "season_number": getattr(episode, 'season_number', 1),
                        "duration": episode.duration,
                        "published_at": episode.published_at,
                        "is_free": getattr(episode, 'is_free', True)
                    }
                    for episode in series.episodes[:5]  # Latest 5 episodes
                ]
        
        return SeriesResponse(**response_data)
    
    def _convert_subscription_to_response(self, subscription: SeriesSubscription) -> SeriesSubscriptionResponse:
        """Convert subscription ORM model to response model"""
        response_data = {
            "id": subscription.id,
            "user_id": subscription.user_id,
            "series_id": subscription.series_id,
            "status": subscription.status,
            "notification_enabled": subscription.notification_enabled,
            "auto_download": subscription.auto_download,
            "last_watched_episode_id": subscription.last_watched_episode_id,
            "watch_progress": subscription.watch_progress,
            "created_at": subscription.created_at,
            "updated_at": subscription.updated_at
        }
        
        # Include series information if loaded
        if hasattr(subscription, 'series') and subscription.series:
            response_data["series"] = self._convert_to_response(subscription.series)
        
        return SeriesSubscriptionResponse(**response_data)