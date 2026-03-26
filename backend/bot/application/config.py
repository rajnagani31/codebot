import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.application.model.pg_vectore import Base
from bot.application.model import chat_history  # noqa: F401


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost/pgvector",
)
JWT_SECRET = os.getenv("JWT_SECRET", "codebot-dev-jwt-secret")
JWT_EXPIRES_SECONDS = int(os.getenv("JWT_EXPIRES_SECONDS", str(60 * 60 * 24 * 30)))

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def initialize_database() -> None:
    Base.metadata.create_all(engine)
