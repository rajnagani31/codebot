"""
Database utility functions for common operations
"""

from typing import List, Optional, Type, TypeVar, Generic
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from ..core.database import get_db_sync

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """Base repository class for common database operations"""
    
    def __init__(self, model: Type[T], db: Optional[Session] = None):
        self.model = model
        self.db = db or get_db_sync()
    
    def create(self, **kwargs) -> T:
        """Create a new record"""
        instance = self.model(**kwargs)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance
    
    def get_by_id(self, record_id: int) -> Optional[T]:
        """Get record by ID"""
        return self.db.query(self.model).filter(self.model.id == record_id).first()
    
    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """Get all records with optional pagination"""
        query = self.db.query(self.model)
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        return query.all()
    
    def update(self, record_id: int, **kwargs) -> Optional[T]:
        """Update a record"""
        instance = self.get_by_id(record_id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            self.db.commit()
            self.db.refresh(instance)
        return instance
    
    def delete(self, record_id: int) -> bool:
        """Delete a record"""
        instance = self.get_by_id(record_id)
        if instance:
            self.db.delete(instance)
            self.db.commit()
            return True
        return False
    
    def find_by(self, **kwargs) -> List[T]:
        """Find records by multiple criteria"""
        conditions = []
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                conditions.append(getattr(self.model, key) == value)
        
        if conditions:
            return self.db.query(self.model).filter(and_(*conditions)).all()
        return []
    
    def search(self, search_term: str, search_fields: List[str]) -> List[T]:
        """Search records by text in specified fields"""
        if not search_term or not search_fields:
            return []
        
        search_conditions = []
        for field in search_fields:
            if hasattr(self.model, field):
                attr = getattr(self.model, field)
                search_conditions.append(attr.ilike(f"%{search_term}%"))
        
        if search_conditions:
            return self.db.query(self.model).filter(or_(*search_conditions)).all()
        return []
    
    def count(self) -> int:
        """Count all records"""
        return self.db.query(self.model).count()
    
    def exists(self, **kwargs) -> bool:
        """Check if record exists with given criteria"""
        conditions = []
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                conditions.append(getattr(self.model, key) == value)
        
        if conditions:
            return self.db.query(self.model).filter(and_(*conditions)).first() is not None
        return False


def with_transaction(func):
    """
    Decorator to wrap function in database transaction
    
    Usage:
    ```python
    @with_transaction
    def create_user_and_session(user_data, session_data):
        db = get_db_sync()
        user = BaseRepository(User, db).create(**user_data)
        session = BaseRepository(UserSession, db).create(user_id=user.id, **session_data)
        return user, session
    ```
    """
    def wrapper(*args, **kwargs):
        db = get_db_sync()
        try:
            result = func(*args, **kwargs, db=db)
            db.commit()
            return result
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    return wrapper
