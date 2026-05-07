from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import id
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class QdrantVectorService:

    def __init__(self):
        self.collection_name = os.getenv("QDRANT_COLLECTION_NAME", "codebot_data")
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")

        self.client = QdrantClient(url=self.qdrant_url)
        self.embedding = OpenAIEmbeddings(model="text-embedding-3-small")

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=500, chunk_overlap=100
        )

        self._create_collection()

    def _create_collection(self):
        collections = self.client.get_collections().collections
        names = [c.name for c in collections]

        if self.collection_name not in names:
            print("🚀 Creating new collection...")

            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=1536, distance=models.Distance.COSINE
                ),
            )

    # =========================
    # STORE
    # =========================
    def store(self, user_id: int, text: str, type_: str):
        chunks = self.splitter.split_text(text)

        points = []

        for chunk in chunks:
            embedding = self.embedding.embed_query(chunk)

            points.append(
                models.PointStruct(
                    id=str(id.id4()),
                    vector=embedding,
                    payload={
                        "user_id": user_id,
                        "text": chunk,
                        "type": type_,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )
            )

        self.client.upsert(collection_name=self.collection_name, points=points)

    # =========================
    # SEARCH
    # =========================
    def search(self, user_id: int, query: str, k=5):
        query_vector = self.embedding.embed_query(query)

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=k,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="user_id", match=models.MatchValue(value=user_id)
                    )
                ]
            ),
        )

        return [r.payload.get("text", "") for r in response.points if r.payload]
