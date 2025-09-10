"""
Series Controller

Application layer controller for series management operations.
Coordinates between REST endpoints and business services while handling
request validation, permission checking, and response formatting.
"""

import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from api.v1.models.series import (
    SeriesCreate, SeriesUpdate, SeriesResponse, SeriesSearchFilters,
    SeriesPublishRequest, SeriesSubscriptionCreate, SeriesSubscriptionUpdate,
    SeriesSubscriptionResponse, SeriesListResponse, SeriesAnalytics,
    SeriesStatsResponse, SeriesRecommendationRequest, SeriesRecommendationResponse
)
from api.v1.models.common import PaginationParams
from business.series_business_service import SeriesBusinessService
from services.series import SeriesService
from repositories.interfaces import IUserRepository


class SeriesController:
    """
    Application controller for series management.
    
    Handles request coordination, validation, permission checking,
    and response formatting for series operations.
    """
    
    def __init__(
        self,
        series_service: SeriesService,
        business_service: SeriesBusinessService,
        user_repository: IUserRepository,
        db: Session
    ):
        self.series_service = series_service
        self.business_service = business_service
        self.user_repository = user_repository
        self.db = db
    
    # Core Series Operations
    
    async def create_series(
        self,
        series_data: SeriesCreate,
        current_user_id: uuid.UUID
    ) -> SeriesResponse:
        """
        Create new series with validation and business rules.
        
        Handles:
        - User permission validation
        - Input data validation
        - Business rule enforcement
        - Response formatting
        """
        try:
            # Validate create permissions
            self._validate_create_permissions(current_user_id)
            
            # Validate series data
            self._validate_series_data(series_data)
            
            # Create series through service layer
            series_response = await self.series_service.create_series(series_data, current_user_id)
            
            return series_response
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except PermissionError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create series"
            )
    
    async def get_series(
        self,
        series_id: uuid.UUID,
        current_user_id: Optional[uuid.UUID] = None
    ) -> SeriesResponse:
        """
        Get series by ID with access control.
        
        Handles:
        - Series existence validation
        - Access permission checking
        - Response formatting with relationships
        """
        try:
            series_response = await self.series_service.get_series_by_id(series_id)
            
            if not series_response:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Series not found"
                )
            
            # Check access permissions
            self._validate_series_access(series_response, current_user_id)
            
            return series_response
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve series"
            )
    
    async def update_series(
        self,
        series_id: uuid.UUID,
        updates: SeriesUpdate,
        current_user_id: uuid.UUID
    ) -> SeriesResponse:
        """
        Update series with validation and business rules.
        
        Handles:
        - Series existence validation
        - Update permission checking
        - Business rule enforcement
        - Response formatting
        """
        try:
            # Validate update permissions
            await self._validate_update_permissions(series_id, current_user_id)
            
            # Validate update data
            self._validate_series_update_data(updates)
            
            # Update series through service layer
            updated_series = await self.series_service.update_series(
                series_id, updates, current_user_id
            )
            
            return updated_series
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except PermissionError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update series"
            )
    
    async def delete_series(
        self,
        series_id: uuid.UUID,
        current_user_id: uuid.UUID,
        soft_delete: bool = True
    ) -> Dict[str, str]:
        """
        Delete series with validation and business rules.
        
        Handles:
        - Delete permission validation
        - Dependency checking
        - Business rule enforcement
        """
        try:
            # Validate delete permissions
            await self._validate_delete_permissions(series_id, current_user_id)
            
            # Delete series through service layer
            success = await self.series_service.delete_series(
                series_id, current_user_id, soft_delete
            )
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to delete series"
                )
            
            return {"message": "Series deleted successfully"}
            
        except PermissionError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete series"
            )
    
    async def search_series(
        self,
        filters: SeriesSearchFilters,
        pagination: PaginationParams,
        current_user_id: Optional[uuid.UUID] = None
    ) -> SeriesListResponse:
        """
        Search series with filtering and pagination.
        
        Handles:
        - Filter validation
        - Access control for private series
        - Pagination
        - Response formatting
        """
        try:
            # Validate search filters
            self._validate_search_filters(filters)
            
            # Apply access control filters
            effective_filters = self._apply_access_control_filters(filters, current_user_id)
            
            # Search through service layer
            series_list, total_count = await self.series_service.search_series(
                effective_filters, pagination
            )
            
            return SeriesListResponse(
                items=series_list,
                total=total_count,
                page=pagination.page,
                limit=pagination.limit,
                has_more=self._calculate_has_more(pagination.page, pagination.limit, total_count)
            )
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to search series"
            )
    
    # Series Management Operations
    
    async def publish_series(
        self,
        series_id: uuid.UUID,
        publish_request: SeriesPublishRequest,
        current_user_id: uuid.UUID
    ) -> SeriesResponse:
        """
        Publish series with business rule validation.
        """
        try:
            # Validate publish permissions
            await self._validate_publish_permissions(series_id, current_user_id)
            
            # Publish through service layer
            published_series = await self.series_service.publish_series(
                series_id,
                current_user_id,
                publish_request.publish_immediately,
                publish_request.scheduled_start_date
            )
            
            return published_series
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except PermissionError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to publish series"
            )
    
    async def complete_series(
        self,
        series_id: uuid.UUID,
        current_user_id: uuid.UUID
    ) -> SeriesResponse:
        """
        Mark series as completed with business rule validation.
        """
        try:
            # Validate completion permissions
            await self._validate_completion_permissions(series_id, current_user_id)
            
            # Complete through service layer
            completed_series = await self.series_service.complete_series(
                series_id, current_user_id
            )
            
            return completed_series
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except PermissionError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to complete series"
            )
    
    # Series Subscription Operations
    
    async def subscribe_to_series(
        self,
        subscription_data: SeriesSubscriptionCreate,
        current_user_id: uuid.UUID
    ) -> SeriesSubscriptionResponse:
        """
        Subscribe user to series.
        """
        try:
            # Validate series exists and is accessible
            series = await self.series_service.get_series_by_id(subscription_data.series_id)
            if not series:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Series not found"
                )
            
            # Create subscription through service layer
            subscription = await self.series_service.create_subscription(
                current_user_id, subscription_data
            )
            
            return subscription
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create subscription"
            )
    
    async def update_subscription(
        self,
        subscription_id: uuid.UUID,
        updates: SeriesSubscriptionUpdate,
        current_user_id: uuid.UUID
    ) -> SeriesSubscriptionResponse:
        """
        Update series subscription.
        """
        try:
            # Validate subscription ownership
            await self._validate_subscription_ownership(subscription_id, current_user_id)
            
            # Update through service layer
            updated_subscription = await self.series_service.update_subscription(
                subscription_id, updates, current_user_id
            )
            
            return updated_subscription
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except PermissionError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update subscription"
            )
    
    async def cancel_subscription(
        self,
        subscription_id: uuid.UUID,
        current_user_id: uuid.UUID
    ) -> Dict[str, str]:
        """
        Cancel series subscription.
        """
        try:
            # Validate subscription ownership
            await self._validate_subscription_ownership(subscription_id, current_user_id)
            
            # Cancel through service layer
            success = await self.series_service.cancel_subscription(
                subscription_id, current_user_id
            )
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to cancel subscription"
                )
            
            return {"message": "Subscription cancelled successfully"}
            
        except PermissionError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel subscription"
            )
    
    async def get_user_subscriptions(
        self,
        current_user_id: uuid.UUID,
        pagination: PaginationParams
    ) -> List[SeriesSubscriptionResponse]:
        """
        Get user's series subscriptions.
        """
        try:
            subscriptions = await self.series_service.get_user_subscriptions(
                current_user_id, pagination
            )
            
            return subscriptions
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve subscriptions"
            )
    
    # Analytics and Stats Operations
    
    async def get_series_analytics(
        self,
        series_id: uuid.UUID,
        current_user_id: uuid.UUID
    ) -> SeriesAnalytics:
        """
        Get series analytics with permission validation.
        """
        try:
            # Validate analytics access permissions
            await self._validate_analytics_permissions(series_id, current_user_id)
            
            # Get analytics through service layer
            analytics = await self.series_service.get_series_analytics(series_id)
            
            return analytics
            
        except PermissionError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve analytics"
            )
    
    async def get_series_stats(
        self,
        current_user_id: uuid.UUID,
        filters: Optional[Dict[str, Any]] = None
    ) -> SeriesStatsResponse:
        """
        Get series statistics with access control.
        """
        try:
            # Validate stats access permissions
            self._validate_stats_permissions(current_user_id)
            
            # Apply user-specific filters
            effective_filters = self._apply_user_stats_filters(filters, current_user_id)
            
            # Get stats through service layer
            stats = await self.series_service.get_series_stats(effective_filters)
            
            return stats
            
        except PermissionError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve stats"
            )
    
    async def get_series_recommendations(
        self,
        request: SeriesRecommendationRequest,
        current_user_id: Optional[uuid.UUID] = None
    ) -> SeriesRecommendationResponse:
        """
        Get series recommendations.
        """
        try:
            # Get recommendations through service layer
            recommendations = await self.series_service.get_series_recommendations(
                request, current_user_id
            )
            
            return recommendations
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get recommendations"
            )
    
    # Validation Methods
    
    def _validate_create_permissions(self, user_id: uuid.UUID) -> None:
        """Validate user has permission to create series"""
        if not self.user_repository.has_permission(self.db, user_id, 'create_series'):
            raise PermissionError("User does not have permission to create series")
    
    async def _validate_update_permissions(
        self, 
        series_id: uuid.UUID, 
        user_id: uuid.UUID
    ) -> None:
        """Validate user has permission to update series"""
        series = await self.series_service.get_series_by_id(series_id)
        if not series:
            raise ValueError("Series not found")
        
        if (series.creator_id != user_id and 
            not self.user_repository.has_permission(self.db, user_id, 'edit_any_series')):
            raise PermissionError("User does not have permission to update this series")
    
    async def _validate_delete_permissions(
        self, 
        series_id: uuid.UUID, 
        user_id: uuid.UUID
    ) -> None:
        """Validate user has permission to delete series"""
        series = await self.series_service.get_series_by_id(series_id)
        if not series:
            raise ValueError("Series not found")
        
        if (series.creator_id != user_id and 
            not self.user_repository.has_permission(self.db, user_id, 'delete_any_series')):
            raise PermissionError("User does not have permission to delete this series")
    
    async def _validate_publish_permissions(
        self, 
        series_id: uuid.UUID, 
        user_id: uuid.UUID
    ) -> None:
        """Validate user has permission to publish series"""
        series = await self.series_service.get_series_by_id(series_id)
        if not series:
            raise ValueError("Series not found")
        
        if (series.creator_id != user_id and 
            not self.user_repository.has_permission(self.db, user_id, 'publish_any_series')):
            raise PermissionError("User does not have permission to publish this series")
    
    async def _validate_completion_permissions(
        self, 
        series_id: uuid.UUID, 
        user_id: uuid.UUID
    ) -> None:
        """Validate user has permission to complete series"""
        series = await self.series_service.get_series_by_id(series_id)
        if not series:
            raise ValueError("Series not found")
        
        if (series.creator_id != user_id and 
            not self.user_repository.has_permission(self.db, user_id, 'manage_any_series')):
            raise PermissionError("User does not have permission to complete this series")
    
    async def _validate_analytics_permissions(
        self, 
        series_id: uuid.UUID, 
        user_id: uuid.UUID
    ) -> None:
        """Validate user has permission to view series analytics"""
        series = await self.series_service.get_series_by_id(series_id)
        if not series:
            raise ValueError("Series not found")
        
        if (series.creator_id != user_id and 
            not self.user_repository.has_permission(self.db, user_id, 'view_any_analytics')):
            raise PermissionError("User does not have permission to view analytics for this series")
    
    def _validate_stats_permissions(self, user_id: uuid.UUID) -> None:
        """Validate user has permission to view stats"""
        if not self.user_repository.has_permission(self.db, user_id, 'view_stats'):
            raise PermissionError("User does not have permission to view stats")
    
    async def _validate_subscription_ownership(
        self, 
        subscription_id: uuid.UUID, 
        user_id: uuid.UUID
    ) -> None:
        """Validate user owns the subscription"""
        subscription = await self.series_service.get_subscription_by_id(subscription_id)
        if not subscription:
            raise ValueError("Subscription not found")
        
        if subscription.user_id != user_id:
            raise PermissionError("User does not own this subscription")
    
    def _validate_series_data(self, series_data: SeriesCreate) -> None:
        """Validate series creation data"""
        # Additional business validation beyond Pydantic
        if not series_data.title or not any(series_data.title.values()):
            raise ValueError("Series title is required")
        
        # Add more validation as needed
    
    def _validate_series_update_data(self, updates: SeriesUpdate) -> None:
        """Validate series update data"""
        # Additional business validation for updates
        pass
    
    def _validate_search_filters(self, filters: SeriesSearchFilters) -> None:
        """Validate search filters"""
        # Validate filter combinations and constraints
        pass
    
    def _validate_series_access(
        self, 
        series: SeriesResponse, 
        current_user_id: Optional[uuid.UUID]
    ) -> None:
        """Validate user can access series"""
        if series.visibility == 'PRIVATE':
            if not current_user_id or series.creator_id != current_user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to private series"
                )
        elif series.visibility == 'RESTRICTED':
            if not current_user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required to access restricted series"
                )
    
    # Helper Methods
    
    def _apply_access_control_filters(
        self, 
        filters: SeriesSearchFilters, 
        current_user_id: Optional[uuid.UUID]
    ) -> SeriesSearchFilters:
        """Apply access control to search filters"""
        # Modify filters based on user permissions
        if not current_user_id:
            # Anonymous users can only see public series
            filters.visibility = 'PUBLIC'
        
        return filters
    
    def _apply_user_stats_filters(
        self, 
        filters: Optional[Dict[str, Any]], 
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Apply user-specific filters to stats"""
        if not filters:
            filters = {}
        
        # Non-admin users can only see their own series stats
        if not self.user_repository.has_permission(self.db, user_id, 'view_all_stats'):
            filters['creator_id'] = user_id
        
        return filters
    
    def _calculate_has_more(self, page: int, limit: int, total: int) -> bool:
        """Calculate if there are more items"""
        return (page * limit) < total