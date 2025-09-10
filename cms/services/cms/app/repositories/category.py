"""
Category Repository

This module provides data access methods for category management including
hierarchical operations, path indexing, and efficient tree traversal.
"""

import uuid
from typing import List, Optional, Dict, Any, Union
from sqlalchemy import func, and_, or_, text
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from models.category import Category, CategoryTypeEnum, CategoryVisibilityEnum
from api.v1.models.categories import CategoryCreate, CategoryUpdate
from repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category, CategoryCreate, CategoryUpdate]):
    """
    Repository for category data access with hierarchical operations.
    
    Provides methods for:
    - CRUD operations with validation
    - Hierarchical tree management
    - Path-based queries
    - Multilingual search
    - Statistics updates
    """
    
    def __init__(self):
        super().__init__(Category)
    
    # Basic CRUD Operations
    
    def create_category(
        self, 
        db: Session, 
        *, 
        category_data: CategoryCreate
    ) -> Category:
        """
        Create a new category with hierarchy validation and path generation.
        
        Args:
            db: Database session
            category_data: Category creation data
            
        Returns:
            Created category instance
            
        Raises:
            ValueError: If parent validation fails or slug conflicts
        """
        # Convert Pydantic model to dict for processing
        category_dict = category_data.model_dump()
        
        # Validate parent category if specified
        parent_category = None
        if category_dict.get('parent_id'):
            parent_category = self.get_by_id(db, category_dict['parent_id'])
            if not parent_category:
                raise ValueError("Parent category not found")
            if not parent_category.is_active:
                raise ValueError("Cannot create category under inactive parent")
        
        # Calculate hierarchy level
        level = 0 if parent_category is None else parent_category.level + 1
        category_dict['level'] = level
        
        # Generate path
        path = self._generate_category_path(parent_category, category_dict['name'])
        category_dict['path'] = path
        
        # Auto-generate slugs if not provided
        if not category_dict.get('slug'):
            category_dict['slug'] = self._generate_slugs_from_name(category_dict['name'])
        
        # Validate slug uniqueness within parent
        self._validate_slug_uniqueness(db, category_dict['slug'], category_dict.get('parent_id'))
        
        try:
            # Create category instance
            db_category = Category(**category_dict)
            db.add(db_category)
            db.flush()  # Get ID without committing
            
            # Update parent statistics
            if parent_category:
                self._update_subcategory_count(db, parent_category.id, 1)
            
            db.commit()
            db.refresh(db_category)
            return db_category
            
        except IntegrityError as e:
            db.rollback()
            raise ValueError(f"Category creation failed: {str(e)}")
    
    def update_category(
        self,
        db: Session,
        *,
        category_id: uuid.UUID,
        category_update: CategoryUpdate
    ) -> Category:
        """
        Update existing category with hierarchy validation.
        
        Args:
            db: Database session
            category_id: Category to update
            category_update: Update data
            
        Returns:
            Updated category instance
        """
        db_category = self.get_by_id(db, category_id)
        if not db_category:
            raise ValueError("Category not found")
        
        update_data = category_update.model_dump(exclude_unset=True)
        
        # Handle parent change (requires path recalculation)
        if 'parent_id' in update_data:
            new_parent_id = update_data['parent_id']
            
            # Validate new parent
            if new_parent_id:
                new_parent = self.get_by_id(db, new_parent_id)
                if not new_parent:
                    raise ValueError("New parent category not found")
                if new_parent_id == category_id:
                    raise ValueError("Category cannot be its own parent")
                if self._would_create_cycle(db, category_id, new_parent_id):
                    raise ValueError("Parent change would create circular reference")
                
                update_data['level'] = new_parent.level + 1
            else:
                update_data['level'] = 0
            
            # Recalculate path
            if 'name' in update_data or 'parent_id' in update_data:
                new_name = update_data.get('name', db_category.name)
                new_parent = self.get_by_id(db, new_parent_id) if new_parent_id else None
                update_data['path'] = self._generate_category_path(new_parent, new_name)
        
        # Update name/slug requires path update
        elif 'name' in update_data or 'slug' in update_data:
            new_name = update_data.get('name', db_category.name)
            new_slug = update_data.get('slug', db_category.slug)
            parent = self.get_by_id(db, db_category.parent_id) if db_category.parent_id else None
            update_data['path'] = self._generate_category_path(parent, new_name, new_slug)
        
        # Validate slug uniqueness if slug is being updated
        if 'slug' in update_data:
            self._validate_slug_uniqueness(
                db, 
                update_data['slug'], 
                update_data.get('parent_id', db_category.parent_id),
                exclude_id=category_id
            )
        
        # Apply updates
        for field, value in update_data.items():
            setattr(db_category, field, value)
        
        db.commit()
        db.refresh(db_category)
        
        # Update child paths if necessary
        if 'name' in update_data or 'slug' in update_data or 'parent_id' in update_data:
            self._update_descendant_paths(db, db_category)
        
        return db_category
    
    def delete_category(
        self,
        db: Session,
        *,
        category_id: uuid.UUID,
        soft_delete: bool = True,
        cascade_delete: bool = False
    ) -> bool:
        """
        Delete category with options for soft/hard delete and handling children.
        
        Args:
            db: Database session
            category_id: Category to delete
            soft_delete: If True, mark as inactive instead of removing
            cascade_delete: If True, delete all descendants
            
        Returns:
            True if deleted successfully
        """
        try:
            db_category = self.get_by_id(db, category_id)
            if not db_category:
                return False
            
            # Check for children if not cascade delete
            if not cascade_delete:
                children_count = self.get_children_count(db, category_id)
                if children_count > 0:
                    raise ValueError("Cannot delete category with subcategories. Use cascade_delete=True or handle children first.")
            
            # Update parent statistics
            if db_category.parent_id:
                self._update_subcategory_count(db, db_category.parent_id, -1)
            
            if cascade_delete:
                # Handle descendants
                descendants = self.get_descendants(db, category_id)
                for descendant in descendants:
                    if soft_delete:
                        descendant.is_active = False
                    else:
                        db.delete(descendant)
            
            # Perform deletion
            if soft_delete:
                # Soft delete - mark as inactive
                db_category.is_active = False
                # Optionally add deleted_at timestamp if the model supports it
                if hasattr(db_category, 'deleted_at'):
                    from datetime import datetime
                    db_category.deleted_at = datetime.utcnow()
            else:
                # Hard delete - remove from database
                db.delete(db_category)
            
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise ValueError(f"Category deletion failed: {str(e)}")
    
    def get_children(self, db: Session, category_id: uuid.UUID) -> List[Category]:
        """Get direct children of a category"""
        return db.query(Category).filter(
            Category.parent_id == category_id,
            Category.is_active == True
        ).all()
    
    # Query Methods
    
    def get_by_id(self, db: Session, category_id: uuid.UUID) -> Optional[Category]:
        """Get category by ID"""
        return db.query(Category).filter(Category.id == category_id).first()
    
    def get_by_path(self, db: Session, path: str) -> Optional[Category]:
        """Get category by path"""
        return db.query(Category).filter(Category.path == path).first()
    
    def get_by_slug(
        self, 
        db: Session, 
        slug: str, 
        language: str = 'ar',
        parent_id: Optional[uuid.UUID] = None
    ) -> Optional[Category]:
        """Get category by slug in specific language"""
        query = db.query(Category).filter(
            Category.slug[language].astext == slug
        )
        
        if parent_id:
            query = query.filter(Category.parent_id == parent_id)
        
        return query.first()
    
    def search_categories(
        self,
        db: Session,
        *,
        query: Optional[str] = None,
        language: str = 'ar',
        category_type: Optional[CategoryTypeEnum] = None,
        parent_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
        visibility: Optional[CategoryVisibilityEnum] = None,
        include_descendants: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Category]:
        """
        Search categories with filters and text search.
        
        Args:
            db: Database session
            query: Text search query
            language: Search language
            category_type: Filter by category type
            parent_id: Filter by parent category
            is_active: Filter by active status
            visibility: Filter by visibility
            include_descendants: Include all descendants of parent_id
            skip: Pagination offset
            limit: Pagination limit
            
        Returns:
            List of matching categories
        """
        db_query = db.query(Category)
        
        # Text search in multilingual fields
        if query:
            search_term = f"%{query}%"
            db_query = db_query.filter(
                or_(
                    Category.name[language].astext.ilike(search_term),
                    Category.description[language].astext.ilike(search_term),
                    # Fallback to other languages if primary language doesn't match
                    func.lower(func.cast(Category.name, text('text'))).contains(query.lower()),
                    func.lower(func.cast(Category.description, text('text'))).contains(query.lower())
                )
            )
        
        # Apply filters
        if category_type:
            db_query = db_query.filter(Category.category_type == category_type)
        
        if parent_id is not None:
            if include_descendants:
                # Get all descendants using path prefix
                parent = self.get_by_id(db, parent_id)
                if parent:
                    db_query = db_query.filter(Category.path.startswith(parent.path + '/'))
            else:
                db_query = db_query.filter(Category.parent_id == parent_id)
        
        if is_active is not None:
            db_query = db_query.filter(Category.is_active == is_active)
        
        if visibility:
            db_query = db_query.filter(Category.visibility == visibility)
        
        # Order by hierarchy and sort order
        db_query = db_query.order_by(
            Category.level,
            Category.sort_order,
            Category.name['ar'].astext
        )
        
        return db_query.offset(skip).limit(limit).all()
    
    # Hierarchical Operations
    
    def get_root_categories(
        self, 
        db: Session,
        *,
        category_type: Optional[CategoryTypeEnum] = None,
        is_active: bool = True
    ) -> List[Category]:
        """Get all root categories (no parent)"""
        query = db.query(Category).filter(Category.parent_id.is_(None))
        
        if category_type:
            query = query.filter(Category.category_type == category_type)
        
        if is_active is not None:
            query = query.filter(Category.is_active == is_active)
        
        return query.order_by(Category.sort_order, Category.name['ar'].astext).all()
    
    def get_children(
        self, 
        db: Session, 
        parent_id: uuid.UUID,
        is_active: Optional[bool] = None
    ) -> List[Category]:
        """Get direct children of a category"""
        query = db.query(Category).filter(Category.parent_id == parent_id)
        
        if is_active is not None:
            query = query.filter(Category.is_active == is_active)
        
        return query.order_by(Category.sort_order, Category.name['ar'].astext).all()
    
    def get_children_count(self, db: Session, parent_id: uuid.UUID) -> int:
        """Get count of direct children"""
        return db.query(Category).filter(Category.parent_id == parent_id).count()
    
    def get_descendants(
        self, 
        db: Session, 
        parent_id: uuid.UUID,
        max_depth: Optional[int] = None
    ) -> List[Category]:
        """Get all descendants of a category"""
        parent = self.get_by_id(db, parent_id)
        if not parent:
            return []
        
        query = db.query(Category).filter(
            Category.path.startswith(parent.path + '/')
        )
        
        if max_depth:
            query = query.filter(Category.level <= parent.level + max_depth)
        
        return query.order_by(Category.level, Category.sort_order).all()
    
    def get_ancestors(self, db: Session, category_id: uuid.UUID) -> List[Category]:
        """Get all ancestors of a category (from parent to root)"""
        category = self.get_by_id(db, category_id)
        if not category or not category.parent_id:
            return []
        
        # Use path to find ancestors efficiently
        ancestors = []
        path_parts = category.path.strip('/').split('/')[:-1]  # Exclude current category
        current_path = ""
        
        for part in path_parts:
            current_path += f"/{part}"
            ancestor = db.query(Category).filter(Category.path == current_path).first()
            if ancestor:
                ancestors.append(ancestor)
        
        return ancestors
    
    def get_category_tree(
        self,
        db: Session,
        *,
        root_id: Optional[uuid.UUID] = None,
        max_depth: int = 5,
        include_inactive: bool = False
    ) -> List[Category]:
        """
        Get hierarchical category tree.
        
        Args:
            db: Database session
            root_id: Start from specific category (None for all roots)
            max_depth: Maximum tree depth
            include_inactive: Include inactive categories
            
        Returns:
            List of root categories with children loaded
        """
        if root_id:
            root_categories = [self.get_by_id(db, root_id)]
            root_categories = [cat for cat in root_categories if cat]
        else:
            query = db.query(Category).filter(Category.parent_id.is_(None))
            if not include_inactive:
                query = query.filter(Category.is_active == True)
            root_categories = query.order_by(Category.sort_order).all()
        
        # Load children recursively
        for root in root_categories:
            self._load_children_recursive(db, root, max_depth, include_inactive)
        
        return root_categories
    
    # Statistics and Analytics
    
    def update_content_count(
        self, 
        db: Session, 
        category_id: uuid.UUID, 
        delta: int
    ) -> None:
        """Update content count for category and all ancestors"""
        category = self.get_by_id(db, category_id)
        if not category:
            return
        
        # Update current category
        category.content_count += delta
        category.total_content_count += delta
        
        # Update all ancestors
        ancestors = self.get_ancestors(db, category_id)
        for ancestor in ancestors:
            ancestor.total_content_count += delta
        
        db.commit()
    
    def recalculate_statistics(self, db: Session, category_id: uuid.UUID) -> None:
        """Recalculate all statistics for a category"""
        category = self.get_by_id(db, category_id)
        if not category:
            return
        
        # Count direct subcategories
        category.subcategory_count = self.get_children_count(db, category_id)
        
        # Count direct content (this would need content table integration)
        # category.content_count = db.query(Content).filter(Content.category_id == category_id).count()
        
        # Calculate total content count including descendants
        descendants = self.get_descendants(db, category_id)
        total_content = category.content_count
        for descendant in descendants:
            total_content += descendant.content_count
        
        category.total_content_count = total_content
        
        db.commit()
    
    # Helper Methods
    
    def _generate_category_path(
        self, 
        parent: Optional[Category], 
        name: Dict[str, str],
        slug: Optional[Dict[str, str]] = None
    ) -> str:
        """Generate category path from parent and name/slug"""
        if slug:
            # Use primary language slug (Arabic first, then English)
            current_slug = slug.get('ar') or slug.get('en') or list(slug.values())[0]
        else:
            # Generate from name
            name_text = name.get('ar') or name.get('en') or list(name.values())[0]
            current_slug = name_text.lower().replace(' ', '-').replace('_', '-')
        
        if parent is None:
            return f"/{current_slug}"
        
        return f"{parent.path}/{current_slug}"
    
    def _generate_slugs_from_name(self, name: Dict[str, str]) -> Dict[str, str]:
        """Generate slugs from multilingual names"""
        slugs = {}
        for lang, text in name.items():
            if text:
                slugs[lang] = text.lower().replace(' ', '-').replace('_', '-')
        return slugs
    
    def _validate_slug_uniqueness(
        self,
        db: Session,
        slug_dict: Dict[str, str],
        parent_id: Optional[uuid.UUID],
        exclude_id: Optional[uuid.UUID] = None
    ) -> None:
        """Validate that slugs are unique within parent scope"""
        for language, slug in slug_dict.items():
            query = db.query(Category).filter(
                Category.slug[language].astext == slug,
                Category.parent_id == parent_id
            )
            
            if exclude_id:
                query = query.filter(Category.id != exclude_id)
            
            if query.first():
                raise ValueError(f"Slug '{slug}' already exists in {language} for this parent category")
    
    def _would_create_cycle(
        self,
        db: Session,
        category_id: uuid.UUID,
        new_parent_id: uuid.UUID
    ) -> bool:
        """Check if setting new_parent_id would create a circular reference"""
        current = self.get_by_id(db, new_parent_id)
        while current:
            if current.id == category_id:
                return True
            current = self.get_by_id(db, current.parent_id) if current.parent_id else None
        return False
    
    def _update_subcategory_count(
        self,
        db: Session,
        parent_id: uuid.UUID,
        delta: int
    ) -> None:
        """Update subcategory count for parent"""
        parent = self.get_by_id(db, parent_id)
        if parent:
            parent.subcategory_count += delta
    
    def _update_descendant_paths(self, db: Session, category: Category) -> None:
        """Update paths for all descendants when parent path changes"""
        descendants = self.get_descendants(db, category.id)
        for descendant in descendants:
            # Recalculate path based on new parent structure
            path_suffix = descendant.path[len(category.path):]  # Get relative path
            descendant.path = category.path + path_suffix
    
    def _load_children_recursive(
        self,
        db: Session,
        category: Category,
        max_depth: int,
        include_inactive: bool,
        current_depth: int = 0
    ) -> None:
        """Recursively load children for tree structure"""
        if current_depth >= max_depth:
            return
        
        children_query = db.query(Category).filter(Category.parent_id == category.id)
        if not include_inactive:
            children_query = children_query.filter(Category.is_active == True)
        
        category.children = children_query.order_by(Category.sort_order).all()
        
        for child in category.children:
            self._load_children_recursive(db, child, max_depth, include_inactive, current_depth + 1)