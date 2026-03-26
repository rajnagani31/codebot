import os
import sys
import uuid
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from bot.application.model.pg_vectore import Base, VectorData

load_dotenv()


class PGVectorService:
    def __init__(
        self,
        db_url: str | None = None,
        *,
        embedding_client=None,
        splitter=None,
        session_factory=None,
        create_schema: bool = True,
    ):
        self.embedding = embedding_client or OpenAIEmbeddings(
            model="text-embedding-3-small"
        )
        self.splitter = splitter or RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
        )

        if session_factory is not None:
            self.engine = None
            self.Session = session_factory
            return

        resolved_db_url = db_url or os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg2://postgres:postgres@localhost/pgvector",
        )
        self.engine = create_engine(resolved_db_url)
        self.Session = sessionmaker(bind=self.engine)

        if create_schema:
            Base.metadata.create_all(self.engine)

    # =========================
    # STORE
    # =========================
    def store(
        self,
        user_id: int,
        text: str,
        type_: str,
        *,
        metadata: dict | None = None,
        user_session_id: str | None = None,
    ):
        session = self.Session()

        try:
            chunks = self.splitter.split_text(text)

            for chunk in chunks:
                embedding = self.embedding.embed_query(chunk)
                extra_metadata = {
                    "timestamp": datetime.utcnow().isoformat()
                }

                if metadata:
                    extra_metadata.update(metadata)

                row = VectorData(
                    id=str(uuid.uuid4()),
                    user_session_id=user_session_id,
                    user_id=user_id,
                    content=chunk,
                    embedding=embedding,
                    type=type_,
                    extra_metadata=extra_metadata,
                )

                session.add(row)

            session.commit()

        except Exception as e:
            session.rollback()
            raise

        finally:
            session.close()

    # =========================
    # SEARCH (COSINE SIMILARITY)
    # =========================
    def search(self, user_id: int, query: str, k=5):
        session = self.Session()

        try:
            query_vector = self.embedding.embed_query(query)

            stmt = (
                select(VectorData)
                .where(VectorData.user_id == user_id)
                .order_by(VectorData.embedding.cosine_distance(query_vector))
                .limit(k)
            )

            results = session.execute(stmt).scalars().all()

            return [r.content for r in results]

        finally:
            session.close()
