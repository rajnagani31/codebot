"""
Centralized database configuration for the application
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os
from dotenv import load_dotenv

load_dotenv()

# Create Base that all models will inherit from
Base = declarative_base()

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+psycopg2://postgres:postgres@localhost:5433/codebot"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=os.getenv("DEBUG", "false").lower() == "true"
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    Dependency function to get database session
    
    Usage:
    ```python
    def some_function():
        db = next(get_db())
        try:
            # Use db here
            result = db.query(SomeModel).all()
            return result
        finally:
            db.close()
    ```
    
    Or with FastAPI:
    ```python
    @app.get("/items")
    def read_items(db: Session = Depends(get_db)):
        return db.query(Item).all()
    ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_sync() -> Session:
    """
    Get database session for synchronous use
    
    Usage:
    ```python
    def some_function():
        db = get_db_sync()
        try:
            # Use db here
            result = db.query(SomeModel).all()
            return result
        finally:
            db.close()
    ```
    """
    return SessionLocal()


# Create all tables (useful for testing)
# def create_tables():
#     """Create all database tables"""
#     Base.metadata.create_all(bind=engine)


# # Drop all tables (useful for testing)
# def drop_tables():
#     """Drop all database tables"""
#     Base.metadata.drop_all(bind=engine)


# # Get database URL for migrations
# def get_database_url() -> str:
#     """Get database URL for Alembic"""
#     return DATABASE_URL
