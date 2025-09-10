"""
Categories Service

This module provides business logic for category management including validation,
hierarchy management, path indexing, and content organization.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

from models.category import Category, CategoryTypeEnum, CategoryVisibilityEnum
from repositories.category import CategoryRepository
from api.v1.models.categories import (
    CategoryCreate, 
    CategoryUpdate, 
    CategoryResponse,
    CategoryTreeNode,
    CategoryAnalytics
)
from api.v1.models.common import PaginatedResponse


logger = logging.getLogger(__name__)


class CategoryService:
    """
    Business service for category management.
    
    Handles:
    - Category CRUD with validation
    - Hierarchy management and path indexing
    - Multilingual content support
    - Business rules enforcement
    - Content statistics tracking
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = CategoryRepository()
    
    # Core CRUD Operations
    
    async def create_category(
        self, 
        category_data: CategoryCreate,
        current_user_id: uuid.UUID
    ) -> CategoryResponse:
        """
        Create new category with validation and hierarchy setup.
        
        Args:
            category_data: Category creation data
            current_user_id: ID of user creating the category
            
        Returns:
            Created category response
            
        Raises:
            ValueError: For validation errors
        """
        try:
            # Business validation
            self._validate_category_creation(category_data)
            
            # Create category via repository
            db_category = self.repository.create_category(
                db=self.db,
                category_data=category_data
            )
            
            # Log creation
            logger.info(
                f"Category created: {db_category.id} by user {current_user_id}",
                extra={
                    "category_id": str(db_category.id),
                    "user_id": str(current_user_id),
                    "category_name": db_category.get_name()
                }
            )
            
            # Convert to response model
            return self._category_to_response(db_category)
            
        except ValueError as e:
            logger.warning(f"Category creation validation failed: {str(e)}")
            raise
        except IntegrityError as e:
            logger.error(f"Database integrity error during category creation: {str(e)}")
            raise ValueError("Category creation failed due to data conflicts")
        except Exception as e:
            logger.error(f"Unexpected error during category creation: {str(e)}")
            raise ValueError("Category creation failed")
    
    async def get_category(
        self, 
        category_id: uuid.UUID,
        include_parent: bool = False,
        include_children: bool = False,
        include_statistics: bool = False
    ) -> Optional[CategoryResponse]:
        """
        Get category by ID with optional related data.
        
        Args:
            category_id: Category ID to retrieve
            include_parent: Include parent category info
            include_children: Include direct children
            include_statistics: Include content statistics
            
        Returns:
            Category response or None if not found
        """
        try:
            db_category = self.repository.get_by_id(self.db, category_id)
            if not db_category:
                return None
            
            response = self._category_to_response(
                db_category,
                include_parent=include_parent,
                include_children=include_children,
                include_statistics=include_statistics
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error retrieving category {category_id}: {str(e)}")
            raise ValueError("Failed to retrieve category")
    
    async def update_category(
        self,
        category_id: uuid.UUID,
        category_update: CategoryUpdate,
        current_user_id: uuid.UUID
    ) -> CategoryResponse:
        """
        Update existing category with validation.
        
        Args:
            category_id: Category to update
            category_update: Update data
            current_user_id: ID of user making update
            
        Returns:
            Updated category response
        """
        try:
            # Business validation
            self._validate_category_update(category_id, category_update)
            
            # Update via repository
            db_category = self.repository.update_category(
                db=self.db,
                category_id=category_id,
                category_update=category_update
            )
            
            # Log update
            logger.info(
                f"Category updated: {category_id} by user {current_user_id}",
                extra={
                    "category_id": str(category_id),
                    "user_id": str(current_user_id),
                    "updates": category_update.model_dump(exclude_unset=True)
                }
            )
            
            return self._category_to_response(db_category)
            
        except ValueError as e:
            logger.warning(f"Category update validation failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error updating category {category_id}: {str(e)}")
            raise ValueError("Category update failed")
    
    async def delete_category(
        self,
        category_id: uuid.UUID,
        current_user_id: uuid.UUID,
        content_action: str = "move_to_parent",
        subcategory_action: str = "move_to_parent",
        target_category_id: Optional[uuid.UUID] = None,
        force_delete: bool = False
    ) -> Dict[str, Any]:
        """
        Delete category with comprehensive content and subcategory handling.
        
        Args:
            category_id: Category to delete
            current_user_id: ID of user performing deletion
            content_action: Action for content (move_to_parent, move_to_category, archive)
            subcategory_action: Action for subcategories (move_to_parent, move_to_category, delete)
            target_category_id: Target category for move operations
            force_delete: Force delete even with content/subcategories
            
        Returns:
            Dict with deletion results and statistics
        """
        try:
            # Get category details before deletion
            category = await self.get_category(category_id, current_user_id)
            if not category:
                raise ValueError(f"Category {category_id} not found")
            
            # Business validation
            deletion_stats = await self._validate_and_prepare_deletion(
                category_id=category_id,
                content_action=content_action,
                subcategory_action=subcategory_action,
                target_category_id=target_category_id,
                force_delete=force_delete
            )
            
            # Handle content migration/archival
            if deletion_stats["content_count"] > 0:
                await self._handle_category_content(
                    category_id=category_id,
                    content_action=content_action,
                    target_category_id=target_category_id,
                    parent_id=category.parent_id
                )
            
            # Handle subcategory migration/deletion
            if deletion_stats["subcategory_count"] > 0:
                await self._handle_category_subcategories(
                    category_id=category_id,
                    subcategory_action=subcategory_action,
                    target_category_id=target_category_id,
                    parent_id=category.parent_id
                )
            
            # Delete via repository
            result = self.repository.delete_category(
                db=self.db,
                category_id=category_id,
                soft_delete=True  # Always do soft delete for audit trail
            )
            
            if result:
                # Update parent category statistics
                if category.parent_id:
                    await self._update_parent_statistics(category.parent_id)
                
                deletion_result = {
                    "success": True,
                    "category_id": str(category_id),
                    "category_name": category.name,
                    "deletion_timestamp": datetime.utcnow().isoformat(),
                    "deleted_by": str(current_user_id),
                    "statistics": deletion_stats,
                    "actions_taken": {
                        "content_action": content_action,
                        "subcategory_action": subcategory_action,
                        "target_category_id": str(target_category_id) if target_category_id else None
                    }
                }
                
                logger.info(
                    f"Category deleted successfully: {category_id}",
                    extra={
                        "category_id": str(category_id),
                        "user_id": str(current_user_id),
                        "content_action": content_action,
                        "subcategory_action": subcategory_action,
                        "deletion_stats": deletion_stats
                    }
                )
                
                return deletion_result
            
            raise ValueError("Category deletion failed in repository")
            
        except ValueError as e:
            logger.warning(f"Category deletion validation failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error deleting category {category_id}: {str(e)}")
            raise ValueError(f"Category deletion failed: {str(e)}")
    
    # Search and Listing
    
    async def search_categories(
        self,
        *,
        query: Optional[str] = None,
        language: str = 'ar',
        category_type: Optional[CategoryTypeEnum] = None,
        parent_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
        visibility: Optional[CategoryVisibilityEnum] = None,
        include_descendants: bool = False,
        page: int = 1,
        limit: int = 20
    ) -> PaginatedResponse[CategoryResponse]:
        """
        Search categories with filters and pagination.
        
        Args:
            query: Text search query
            language: Search language preference
            category_type: Filter by category type
            parent_id: Filter by parent category
            is_active: Filter by active status
            visibility: Filter by visibility
            include_descendants: Include descendants of parent_id
            page: Page number (1-based)
            limit: Items per page
            
        Returns:
            Paginated category responses
        """
        try:
            skip = (page - 1) * limit
            
            # Get categories from repository
            categories = self.repository.search_categories(
                db=self.db,
                query=query,
                language=language,
                category_type=category_type,
                parent_id=parent_id,
                is_active=is_active,
                visibility=visibility,
                include_descendants=include_descendants,
                skip=skip,
                limit=limit + 1  # Get one extra to check for next page
            )
            
            has_next = len(categories) > limit
            if has_next:
                categories = categories[:limit]
            
            # Convert to response models
            category_responses = [
                self._category_to_response(cat) for cat in categories
            ]
            
            # Create pagination info
            total = self._get_search_total(
                query=query,
                language=language,
                category_type=category_type,
                parent_id=parent_id,
                is_active=is_active,
                visibility=visibility,
                include_descendants=include_descendants
            )
            
            return PaginatedResponse(
                data=category_responses,
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
            logger.error(f"Error searching categories: {str(e)}")
            raise ValueError("Category search failed")
    
    async def get_category_tree(
        self,
        *,
        root_id: Optional[uuid.UUID] = None,
        max_depth: int = 5,
        include_inactive: bool = False,
        language: str = 'ar'
    ) -> List[CategoryTreeNode]:
        """
        Get hierarchical category tree.
        
        Args:
            root_id: Start from specific category (None for all roots)
            max_depth: Maximum tree depth
            include_inactive: Include inactive categories
            language: Preferred language for display
            
        Returns:
            List of category tree nodes
        """
        try:
            categories = self.repository.get_category_tree(
                db=self.db,
                root_id=root_id,
                max_depth=max_depth,
                include_inactive=include_inactive
            )
            
            return [
                self._category_to_tree_node(cat, language) 
                for cat in categories
            ]
            
        except Exception as e:
            logger.error(f"Error getting category tree: {str(e)}")
            raise ValueError("Failed to retrieve category tree")
    
    # Hierarchy Operations
    
    async def move_category(
        self,
        category_id: uuid.UUID,
        new_parent_id: Optional[uuid.UUID],
        current_user_id: uuid.UUID
    ) -> CategoryResponse:
        """
        Move category to new parent.
        
        Args:
            category_id: Category to move
            new_parent_id: New parent (None for root)
            current_user_id: User performing action
            
        Returns:
            Updated category
        """
        try:
            # Use update with parent_id change
            update_data = CategoryUpdate(parent_id=new_parent_id)
            
            return await self.update_category(
                category_id=category_id,
                category_update=update_data,
                current_user_id=current_user_id
            )
            
        except Exception as e:
            logger.error(f"Error moving category {category_id}: {str(e)}")
            raise ValueError("Failed to move category")
    
    async def reorder_categories(
        self,
        category_orders: List[Dict[str, Union[uuid.UUID, int]]],
        current_user_id: uuid.UUID
    ) -> List[CategoryResponse]:
        """
        Reorder categories within their parent.
        
        Args:
            category_orders: List of {"category_id": uuid, "sort_order": int}
            current_user_id: User performing action
            
        Returns:
            Updated categories
        """
        try:
            updated_categories = []
            
            for item in category_orders:
                category_id = item["category_id"]
                sort_order = item["sort_order"]
                
                update_data = CategoryUpdate(sort_order=sort_order)
                updated_category = await self.update_category(
                    category_id=category_id,
                    category_update=update_data,
                    current_user_id=current_user_id
                )
                updated_categories.append(updated_category)
            
            logger.info(
                f"Categories reordered by user {current_user_id}",
                extra={
                    "user_id": str(current_user_id),
                    "categories_count": len(category_orders)
                }
            )
            
            return updated_categories
            
        except Exception as e:
            logger.error(f"Error reordering categories: {str(e)}")
            raise ValueError("Failed to reorder categories")
    
    # Content Management
    
    async def update_content_count(
        self,
        category_id: uuid.UUID,
        delta: int
    ) -> None:
        """
        Update content count for category and ancestors.
        
        Args:
            category_id: Category to update
            delta: Change in content count (+/-)
        """
        try:
            self.repository.update_content_count(
                db=self.db,
                category_id=category_id,
                delta=delta
            )
            
        except Exception as e:
            logger.error(f"Error updating content count for {category_id}: {str(e)}")
            raise ValueError("Failed to update content count")
    
    async def get_category_statistics(
        self,
        category_id: uuid.UUID,
        include_descendants: bool = True
    ) -> CategoryAnalytics:
        """
        Get comprehensive category analytics.
        
        Args:
            category_id: Category to analyze
            include_descendants: Include descendant statistics
            
        Returns:
            Category analytics data
        """
        try:
            category = self.repository.get_by_id(self.db, category_id)
            if not category:
                raise ValueError("Category not found")
            
            # This would integrate with content analytics
            # For now, return basic structure
            analytics = CategoryAnalytics(
                category_id=category_id,
                category_name=category.name,
                total_content=category.total_content_count,
                published_content=category.content_count,  # Simplified
                draft_content=0,  # Would need content integration
                total_views=0,  # Would need analytics integration
                unique_visitors=0,
                avg_engagement_time=0.0,
                views_last_7_days=0,
                views_last_30_days=0,
                growth_rate=0.0,
                top_content=[],
                popular_subcategories=[]
            )
            
            return analytics
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error getting category statistics {category_id}: {str(e)}")
            raise ValueError("Failed to retrieve category statistics")
    
    # Validation Methods
    
    def _validate_category_creation(self, category_data: CategoryCreate) -> None:
        """Validate category creation data"""
        # Check name is provided
        if not category_data.name or not any(category_data.name.values()):
            raise ValueError("Category name is required in at least one language")
        
        # Validate parent exists if provided
        if category_data.parent_id:
            parent = self.repository.get_by_id(self.db, category_data.parent_id)
            if not parent:
                raise ValueError("Parent category not found")
            if not parent.is_active:
                raise ValueError("Cannot create category under inactive parent")
        
        # Validate category type
        if category_data.category_type not in CategoryTypeEnum:
            raise ValueError("Invalid category type")
        
        # Additional business rules can be added here
    
    def _validate_category_update(
        self, 
        category_id: uuid.UUID, 
        category_update: CategoryUpdate
    ) -> None:
        """Validate category update data"""
        # Check category exists
        category = self.repository.get_by_id(self.db, category_id)
        if not category:
            raise ValueError("Category not found")
        
        # Validate parent change if specified
        if hasattr(category_update, 'parent_id') and category_update.parent_id:
            if category_update.parent_id == category_id:
                raise ValueError("Category cannot be its own parent")
            
            new_parent = self.repository.get_by_id(self.db, category_update.parent_id)
            if not new_parent:
                raise ValueError("New parent category not found")
    
    def _validate_category_deletion(
        self,
        category_id: uuid.UUID,
        cascade_delete: bool,
        move_content_to: Optional[uuid.UUID]
    ) -> None:
        """Validate category deletion"""
        category = self.repository.get_by_id(self.db, category_id)
        if not category:
            raise ValueError("Category not found")
        
        # Check for children
        children_count = self.repository.get_children_count(self.db, category_id)
        if children_count > 0 and not cascade_delete:
            raise ValueError("Cannot delete category with subcategories without cascade")
        
        # Validate move target if specified
        if move_content_to:
            target = self.repository.get_by_id(self.db, move_content_to)
            if not target:
                raise ValueError("Target category for content move not found")
            if not target.is_active:
                raise ValueError("Cannot move content to inactive category")
    
    # Helper Methods
    
    def _category_to_response(
        self,
        category: Category,
        include_parent: bool = False,
        include_children: bool = False,
        include_statistics: bool = False
    ) -> CategoryResponse:
        """Convert Category ORM to CategoryResponse"""
        response_data = {
            "id": category.id,
            "name": category.name,
            "description": category.description,
            "slug": category.slug,
            "category_type": category.category_type,
            "parent_id": category.parent_id,
            "level": category.level,
            "path": category.path,
            "is_active": category.is_active,
            "visibility": category.visibility,
            "content_count": category.content_count,
            "subcategory_count": category.subcategory_count,
            "total_content_count": category.total_content_count,
            "icon_url": category.icon_url,
            "banner_url": category.banner_url,
            "color_scheme": category.color_scheme,
            "sort_order": category.sort_order,
            "seo_title": category.seo_title,
            "seo_description": category.seo_description,
            "seo_keywords": category.seo_keywords,
            "metadata": category._metadata,
            "created_at": category.created_at,
            "updated_at": category.updated_at
        }
        
        if include_parent and category.parent:
            response_data["parent"] = {
                "id": category.parent.id,
                "name": category.parent.name,
                "path": category.parent.path
            }
        
        return CategoryResponse(**response_data)
    
    def _category_to_tree_node(
        self, 
        category: Category, 
        language: str = 'ar'
    ) -> CategoryTreeNode:
        """Convert Category to CategoryTreeNode recursively"""
        children = []
        if hasattr(category, 'children') and category.children:
            children = [
                self._category_to_tree_node(child, language)
                for child in category.children
            ]
        
        return CategoryTreeNode(
            id=category.id,
            name=category.name,
            slug=category.slug or category.name,  # Fallback to name if no slug
            category_type=category.category_type,
            level=category.level,
            path=category.path,
            parent_id=category.parent_id,
            is_active=category.is_active,
            content_count=category.content_count,
            total_content_count=category.total_content_count,
            icon_url=category.icon_url,
            color_scheme=category.color_scheme,
            sort_order=category.sort_order,
            children=children
        )
    
    def _get_search_total(self, **kwargs) -> int:
        """Get total count for search results (simplified)"""
        # This would implement the same query as search_categories
        # but with count() instead of getting records
        # For now, return a placeholder
        return 0
    
    async def _validate_and_prepare_deletion(
        self,
        category_id: uuid.UUID,
        content_action: str,
        subcategory_action: str,
        target_category_id: Optional[uuid.UUID] = None,
        force_delete: bool = False
    ) -> Dict[str, Any]:
        """Validate deletion request and prepare statistics"""
        category = self.repository.get_by_id(self.db, category_id)
        if not category:
            raise ValueError("Category not found")
        
        # Get content and subcategory counts
        content_count = category.content_count or 0
        subcategory_count = category.subcategory_count or 0
        
        # Validate actions
        valid_content_actions = ["move_to_parent", "move_to_category", "archive"]
        valid_subcategory_actions = ["move_to_parent", "move_to_category", "delete"]
        
        if content_action not in valid_content_actions:
            raise ValueError(f"Invalid content_action. Must be one of: {valid_content_actions}")
        
        if subcategory_action not in valid_subcategory_actions:
            raise ValueError(f"Invalid subcategory_action. Must be one of: {valid_subcategory_actions}")
        
        # Validate target category if needed
        if (content_action == "move_to_category" or subcategory_action == "move_to_category"):
            if not target_category_id:
                raise ValueError("target_category_id required for move_to_category actions")
            
            target_category = self.repository.get_by_id(self.db, target_category_id)
            if not target_category:
                raise ValueError("Target category not found")
            if not target_category.is_active:
                raise ValueError("Cannot move to inactive target category")
            if target_category_id == category_id:
                raise ValueError("Cannot move to the same category being deleted")
        
        # Check if deletion is allowed without force
        if not force_delete:
            if content_count > 0 and content_action not in ["move_to_parent", "move_to_category", "archive"]:
                raise ValueError("Cannot delete category with content without specifying content action")
            if subcategory_count > 0 and subcategory_action not in ["move_to_parent", "move_to_category", "delete"]:
                raise ValueError("Cannot delete category with subcategories without specifying subcategory action")
        
        # Check parent exists for move_to_parent actions
        if (content_action == "move_to_parent" or subcategory_action == "move_to_parent"):
            if not category.parent_id:
                raise ValueError("Cannot move to parent - category has no parent. Use move_to_category instead.")
        
        return {
            "content_count": content_count,
            "subcategory_count": subcategory_count,
            "total_content_count": category.total_content_count or 0,
            "category_name": category.get_name(),
            "category_path": category.path,
            "has_parent": category.parent_id is not None
        }
    
    async def _handle_category_content(
        self,
        category_id: uuid.UUID,
        content_action: str,
        target_category_id: Optional[uuid.UUID] = None,
        parent_id: Optional[uuid.UUID] = None
    ) -> None:
        """Handle content when deleting a category"""
        try:
            if content_action == "move_to_parent":
                if parent_id:
                    await self._move_category_content(category_id, parent_id)
                    logger.info(f"Moved content from category {category_id} to parent {parent_id}")
            
            elif content_action == "move_to_category":
                if target_category_id:
                    await self._move_category_content(category_id, target_category_id)
                    logger.info(f"Moved content from category {category_id} to target {target_category_id}")
            
            elif content_action == "archive":
                await self._archive_category_content(category_id)
                logger.info(f"Archived content from category {category_id}")
            
        except Exception as e:
            logger.error(f"Error handling category content during deletion: {str(e)}")
            raise ValueError(f"Failed to handle category content: {str(e)}")
    
    async def _handle_category_subcategories(
        self,
        category_id: uuid.UUID,
        subcategory_action: str,
        target_category_id: Optional[uuid.UUID] = None,
        parent_id: Optional[uuid.UUID] = None
    ) -> None:
        """Handle subcategories when deleting a category"""
        try:
            # Get all direct subcategories
            subcategories = self.repository.get_children(self.db, category_id)
            
            if subcategory_action == "move_to_parent":
                if parent_id:
                    for subcat in subcategories:
                        update_data = CategoryUpdate(parent_id=parent_id)
                        self.repository.update_category(
                            db=self.db,
                            category_id=subcat.id,
                            category_update=update_data
                        )
                    logger.info(f"Moved {len(subcategories)} subcategories to parent {parent_id}")
            
            elif subcategory_action == "move_to_category":
                if target_category_id:
                    for subcat in subcategories:
                        update_data = CategoryUpdate(parent_id=target_category_id)
                        self.repository.update_category(
                            db=self.db,
                            category_id=subcat.id,
                            category_update=update_data
                        )
                    logger.info(f"Moved {len(subcategories)} subcategories to target {target_category_id}")
            
            elif subcategory_action == "delete":
                for subcat in subcategories:
                    # Recursively delete subcategories
                    await self.delete_category(
                        category_id=subcat.id,
                        current_user_id=uuid.uuid4(),  # System deletion
                        content_action="archive",  # Archive content of deleted subcategories
                        subcategory_action="delete",  # Continue cascade delete
                        force_delete=True
                    )
                logger.info(f"Deleted {len(subcategories)} subcategories")
            
        except Exception as e:
            logger.error(f"Error handling subcategories during deletion: {str(e)}")
            raise ValueError(f"Failed to handle subcategories: {str(e)}")
    
    async def _update_parent_statistics(self, parent_id: uuid.UUID) -> None:
        """Update parent category statistics after child deletion"""
        try:
            parent = self.repository.get_by_id(self.db, parent_id)
            if parent:
                # Recalculate subcategory count
                children_count = self.repository.get_children_count(self.db, parent_id)
                
                # Update parent statistics
                update_data = CategoryUpdate(subcategory_count=children_count)
                self.repository.update_category(
                    db=self.db,
                    category_id=parent_id,
                    category_update=update_data
                )
                
                # Recursively update ancestors if needed
                if parent.parent_id:
                    await self._update_parent_statistics(parent.parent_id)
                
                logger.info(f"Updated statistics for parent category {parent_id}")
                
        except Exception as e:
            logger.error(f"Error updating parent statistics: {str(e)}")
    
    async def _archive_category_content(self, category_id: uuid.UUID) -> None:
        """Archive all content in a category"""
        # This would integrate with content service to mark content as archived
        # For now, this is a placeholder that logs the action
        logger.info(f"Archiving content for category {category_id}")
        
        # In a real implementation, this would:
        # 1. Get all content items in the category
        # 2. Update their status to 'archived'
        # 3. Update search indices
        # 4. Notify relevant services
        pass
    
    async def _move_category_content(
        self, 
        from_category_id: uuid.UUID, 
        to_category_id: uuid.UUID
    ) -> None:
        """Move all content from one category to another"""
        # This would integrate with content service
        # to move all content items from source to target category
        logger.info(f"Moving content from {from_category_id} to {to_category_id}")
        
        # In a real implementation, this would:
        # 1. Get all content items in the source category
        # 2. Update their category_id to the target category
        # 3. Update content counts in both categories
        # 4. Update search indices
        # 5. Notify relevant services
        pass


# Background Task Functions for Category Operations


async def _process_category_deletion_cleanup(
    category_id: str, 
    deletion_stats: Dict[str, Any]
) -> None:
    """Background task to clean up after category deletion"""
    try:
        # Update search indices
        logger.info(f"Updating search indices after category {category_id} deletion")
        
        # Clear cached category data
        logger.info(f"Clearing cached data for category {category_id}")
        
        # Notify related services
        logger.info(f"Notifying services about category {category_id} deletion")
        
        # Update category hierarchy cache
        logger.info(f"Updating category hierarchy cache after deletion")
        
    except Exception as e:
        logger.error(f"Error in category deletion cleanup: {str(e)}")


async def _audit_category_deletion(
    category_id: str,
    user_id: str,
    deletion_details: Dict[str, Any]
) -> None:
    """Background task to create audit log for category deletion"""
    try:
        audit_entry = {
            "action": "category_deletion",
            "category_id": category_id,
            "performed_by": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "details": deletion_details
        }
        
        logger.info(f"Created audit log for category deletion: {audit_entry}")
        # In real implementation, this would save to audit log database
        
    except Exception as e:
        logger.error(f"Error creating audit log for category deletion: {str(e)}")


async def _update_category_statistics_cascade(
    affected_category_ids: List[str]
) -> None:
    """Background task to update statistics for affected categories"""
    try:
        for cat_id in affected_category_ids:
            logger.info(f"Updating statistics for affected category {cat_id}")
            # In real implementation, this would recalculate and update statistics
        
    except Exception as e:
        logger.error(f"Error updating cascade statistics: {str(e)}")


async def _notify_content_owners_category_change(
    moved_content_ids: List[str],
    old_category_name: str,
    new_category_name: str
) -> None:
    """Background task to notify content owners about category changes"""
    try:
        for content_id in moved_content_ids:
            logger.info(
                f"Notifying content owner about category change for content {content_id}: "
                f"{old_category_name} -> {new_category_name}"
            )
            # In real implementation, this would send notifications
        
    except Exception as e:
        logger.error(f"Error notifying content owners: {str(e)}")


async def _rebuild_category_search_index(root_category_id: Optional[str] = None) -> None:
    """Background task to rebuild category search indices"""
    try:
        if root_category_id:
            logger.info(f"Rebuilding search index for category tree starting at {root_category_id}")
        else:
            logger.info("Rebuilding complete category search index")
            
        # In real implementation, this would update search engine indices
        
    except Exception as e:
        logger.error(f"Error rebuilding search index: {str(e)}")