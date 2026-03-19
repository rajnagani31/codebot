import os

from sqlalchemy import create_engine

from bot.application.model.pg_vectore import Base


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost/pgvector",
)

engine = create_engine(DATABASE_URL)


def initialize_database() -> None:
    Base.metadata.create_all(engine)
