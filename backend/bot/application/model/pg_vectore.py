from sqlalchemy import JSON, Column, Integer, Text, String, DateTime
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from ..core.database import Base
# from sqlalchemy.ext.mutable import JSONB


class DocumentData(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    content = Column(Text)
    embedding = Column(JSON, nullable=False)


class VectorData(Base):
    __tablename__ = "vector_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_session_id = Column(Integer, nullable=True)
    user_id = Column(Integer, index=True)
    content = Column(Text)
    embedding = Column(Vector(1536))  # 👈 important
    type = Column(String)
    extra_metadata = Column("metadata", JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
