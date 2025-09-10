"""
Enhanced Base Repository

Improved repository pattern with better abstractions, query builders,
and clean architecture principles.
"""

import uuid
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union, Callable
from abc import ABC, abstractmethod
from datetime import datetime
from sqlalchemy.orm import Session, Query
from sqlalchemy import and_, or_, desc, asc, func, text
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from models.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class QueryBuilder(Generic[ModelType]):
    """
    Fluent query builder for constructing complex database queries
    """
    
    def __init__(self, session: Session, model: Type[ModelType]):
        self.session = session
        self.model = model
        self._query = session.query(model)
        self._filters = []
        self._includes = []
        self._order_by = []
    
    def filter_by(self, **kwargs) -> "QueryBuilder[ModelType]":
        """Add filter conditions"""
        for field, value in kwargs.items():
            if hasattr(self.model, field) and value is not None:
                self._filters.append(getattr(self.model, field) == value)
        return self
    
    def filter(self, *conditions) -> "QueryBuilder[ModelType]":
        """Add raw filter conditions"""
        self._filters.extend(conditions)
        return self
    
    def where(self, condition) -> "QueryBuilder[ModelType]":
        """Add where condition (alias for filter)"""
        return self.filter(condition)
    
    def include(self, *relationships) -> "QueryBuilder[ModelType]":
        """Include related entities (joinedload)"""
        from sqlalchemy.orm import joinedload
        for rel in relationships:
            if isinstance(rel, str):
                rel = getattr(self.model, rel)
            self._includes.append(joinedload(rel))
        return self
    
    def order_by(self, field: str, direction: str = "asc") -> "QueryBuilder[ModelType]":
        """Add ordering"""
        if hasattr(self.model, field):
            column = getattr(self.model, field)
            if direction.lower() == "desc":
                self._order_by.append(desc(column))
            else:
                self._order_by.append(asc(column))
        return self
    
    def search(self, query: str, fields: List[str]) -> "QueryBuilder[ModelType]":
        """Add full-text search across multiple fields"""
        if not query or not fields:
            return self
        
        search_conditions = []
        for field_name in fields:
            if hasattr(self.model, field_name):
                field = getattr(self.model, field_name)
                # Handle JSONB fields (multilingual)
                if hasattr(field.type, 'python_type') and field.type.python_type == dict:
                    search_conditions.append(
                        func.lower(func.cast(field, text('text'))).contains(query.lower())
                    )
                else:
                    search_conditions.append(field.ilike(f"%{query}%"))
        
        if search_conditions:
            self._filters.append(or_(*search_conditions))
        
        return self
    
    def paginate(self, page: int, limit: int) -> "QueryBuilder[ModelType]":
        """Add pagination"""
        offset = (page - 1) * limit
        self._query = self._query.offset(offset).limit(limit)
        return self
    
    def build(self) -> Query:
        """Build the final query"""
        query = self._query
        
        # Apply includes
        for include in self._includes:
            query = query.options(include)
        
        # Apply filters
        if self._filters:
            query = query.filter(and_(*self._filters))
        
        # Apply ordering
        if self._order_by:
            query = query.order_by(*self._order_by)
        
        return query
    
    def first(self) -> Optional[ModelType]:
        """Get first result"""
        return self.build().first()
    
    def all(self) -> List[ModelType]:
        """Get all results"""
        return self.build().all()
    
    def count(self) -> int:
        """Get count of results"""
        return self.build().count()
    
    def exists(self) -> bool:
        """Check if any results exist"""
        return self.session.query(self.build().exists()).scalar()


class IRepository(ABC, Generic[ModelType]):
    """
    Repository interface defining the contract for data access
    """
    
    @abstractmethod
    def get_by_id(self, db: Session, entity_id: uuid.UUID) -> Optional[ModelType]:
        """Get entity by ID"""
        pass
    
    @abstractmethod
    def create(self, db: Session, entity_data: Dict[str, Any]) -> ModelType:
        """Create new entity"""
        pass
    
    @abstractmethod
    def update(self, db: Session, entity_id: uuid.UUID, update_data: Dict[str, Any]) -> ModelType:
        """Update existing entity"""
        pass
    
    @abstractmethod
    def delete(self, db: Session, entity_id: uuid.UUID) -> bool:
        """Delete entity"""
        pass
    
    @abstractmethod
    def list(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """List entities with filtering"""
        pass
    
    @abstractmethod
    def count(
        self,
        db: Session,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """Count entities with filtering"""
        pass


class BaseRepository(IRepository[ModelType], Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Enhanced base repository with improved patterns and functionality
    """
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    def get_by_id(self, db: Session, entity_id: uuid.UUID) -> Optional[ModelType]:
        """Get entity by ID with proper UUID handling"""
        return db.query(self.model).filter(self.model.id == entity_id).first()
    
    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_direction: str = "asc"
    ) -> List[ModelType]:
        """Get multiple entities with filtering and ordering"""
        query = self._build_base_query(db, filters)
        
        if order_by and hasattr(self.model, order_by):
            column = getattr(self.model, order_by)
            if order_direction.lower() == "desc":
                query = query.order_by(desc(column))
            else:
                query = query.order_by(asc(column))
        
        return query.offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: Union[CreateSchemaType, Dict[str, Any]]) -> ModelType:
        """Create entity with proper data handling"""
        if isinstance(obj_in, dict):
            obj_in_data = obj_in
        else:
            obj_in_data = obj_in.model_dump() if hasattr(obj_in, 'model_dump') else obj_in.dict()
        
        # Remove None values
        obj_in_data = {k: v for k, v in obj_in_data.items() if v is not None}
        
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Update entity with partial update support"""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, 'model_dump') else obj_in.dict(exclude_unset=True)
        
        # Apply updates
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        # Update timestamp if available
        if hasattr(db_obj, 'updated_at'):
            setattr(db_obj, 'updated_at', datetime.utcnow())
        
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update_by_id(
        self,
        db: Session,
        entity_id: uuid.UUID,
        update_data: Dict[str, Any]
    ) -> Optional[ModelType]:
        """Update entity by ID"""
        db_obj = self.get_by_id(db, entity_id)
        if not db_obj:
            return None
        
        return self.update(db=db, db_obj=db_obj, obj_in=update_data)
    
    def delete(self, db: Session, entity_id: uuid.UUID) -> bool:
        """Delete entity by ID"""
        db_obj = self.get_by_id(db, entity_id)
        if not db_obj:
            return False
        
        db.delete(db_obj)
        db.commit()
        return True
    
    def soft_delete(self, db: Session, entity_id: uuid.UUID) -> bool:
        """Soft delete entity (if it has deleted_at field)"""
        db_obj = self.get_by_id(db, entity_id)
        if not db_obj:
            return False
        
        if hasattr(db_obj, 'deleted_at'):
            setattr(db_obj, 'deleted_at', datetime.utcnow())
            db.commit()
            return True
        
        return False
    
    def restore(self, db: Session, entity_id: uuid.UUID) -> bool:
        """Restore soft-deleted entity"""
        db_obj = self.get_by_id(db, entity_id)
        if not db_obj:
            return False
        
        if hasattr(db_obj, 'deleted_at'):
            setattr(db_obj, 'deleted_at', None)
            db.commit()
            return True
        
        return False
    
    def list(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """List entities with filters"""
        return self.get_multi(db, skip=skip, limit=limit, filters=filters)
    
    def count(
        self,
        db: Session,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """Count entities with filters"""
        query = self._build_base_query(db, filters)
        return query.count()
    
    def exists(
        self,
        db: Session,
        entity_id: uuid.UUID
    ) -> bool:
        """Check if entity exists"""
        return db.query(
            db.query(self.model).filter(self.model.id == entity_id).exists()
        ).scalar()
    
    def exists_by_field(
        self,
        db: Session,
        field_name: str,
        field_value: Any
    ) -> bool:
        """Check if entity exists by field value"""
        if not hasattr(self.model, field_name):
            return False
        
        field = getattr(self.model, field_name)
        return db.query(
            db.query(self.model).filter(field == field_value).exists()
        ).scalar()
    
    def query_builder(self, db: Session) -> QueryBuilder[ModelType]:
        """Get a query builder for complex queries"""
        return QueryBuilder(db, self.model)
    
    def batch_create(
        self,
        db: Session,
        objects: List[Union[CreateSchemaType, Dict[str, Any]]]
    ) -> List[ModelType]:
        """Create multiple entities in a batch"""
        db_objects = []
        
        for obj_in in objects:
            if isinstance(obj_in, dict):
                obj_in_data = obj_in
            else:
                obj_in_data = obj_in.model_dump() if hasattr(obj_in, 'model_dump') else obj_in.dict()
            
            # Remove None values
            obj_in_data = {k: v for k, v in obj_in_data.items() if v is not None}
            
            db_obj = self.model(**obj_in_data)
            db_objects.append(db_obj)
        
        db.add_all(db_objects)
        db.commit()
        
        for db_obj in db_objects:
            db.refresh(db_obj)
        
        return db_objects
    
    def batch_update(
        self,
        db: Session,
        updates: List[Dict[str, Any]]
    ) -> int:
        """Update multiple entities in a batch"""
        updated_count = 0
        
        for update_item in updates:
            entity_id = update_item.get('id')
            if not entity_id:
                continue
            
            update_data = {k: v for k, v in update_item.items() if k != 'id'}
            if self.update_by_id(db, entity_id, update_data):
                updated_count += 1
        
        return updated_count
    
    def find_by_field(
        self,
        db: Session,
        field_name: str,
        field_value: Any,
        limit: Optional[int] = None
    ) -> List[ModelType]:
        """Find entities by field value"""
        if not hasattr(self.model, field_name):
            return []
        
        field = getattr(self.model, field_name)
        query = db.query(self.model).filter(field == field_value)
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def find_one_by_field(
        self,
        db: Session,
        field_name: str,
        field_value: Any
    ) -> Optional[ModelType]:
        """Find single entity by field value"""
        results = self.find_by_field(db, field_name, field_value, limit=1)
        return results[0] if results else None
    
    # Protected helper methods
    
    def _build_base_query(
        self,
        db: Session,
        filters: Optional[Dict[str, Any]] = None
    ) -> Query:
        """Build base query with optional filters"""
        query = db.query(self.model)
        
        if filters:
            conditions = []
            for field_name, field_value in filters.items():
                if field_value is not None and hasattr(self.model, field_name):
                    field = getattr(self.model, field_name)
                    
                    # Handle different filter types
                    if isinstance(field_value, dict):
                        # Range filters like {'gte': 10, 'lte': 20}
                        if 'gte' in field_value:
                            conditions.append(field >= field_value['gte'])
                        if 'lte' in field_value:
                            conditions.append(field <= field_value['lte'])
                        if 'gt' in field_value:
                            conditions.append(field > field_value['gt'])
                        if 'lt' in field_value:
                            conditions.append(field < field_value['lt'])
                    elif isinstance(field_value, list):
                        # IN conditions
                        conditions.append(field.in_(field_value))
                    else:
                        # Exact match
                        conditions.append(field == field_value)
            
            if conditions:
                query = query.filter(and_(*conditions))
        
        return query


class UnitOfWork:
    """
    Unit of Work pattern for managing database transactions
    """
    
    def __init__(self, db: Session):
        self.db = db
        self._repositories: Dict[str, Any] = {}
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
    
    def commit(self):
        """Commit the transaction"""
        try:
            self.db.commit()
        except Exception:
            self.rollback()
            raise
    
    def rollback(self):
        """Rollback the transaction"""
        self.db.rollback()
    
    def get_repository(self, repository_class: Type) -> Any:
        """Get repository instance"""
        repo_name = repository_class.__name__
        if repo_name not in self._repositories:
            self._repositories[repo_name] = repository_class()
        return self._repositories[repo_name]