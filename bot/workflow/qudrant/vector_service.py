from langchain_qdrant import QdrantVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from datetime import datetime
import os
import uuid
from dotenv import load_dotenv
from qdrant_client.http import models

load_dotenv()


class VectorService:

    def __init__(self):
        collection_name = os.getenv("QDRANT_COLLECTION_NAME", "codebot_data")
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")

        self.embedding = OpenAIEmbeddings(model="text-embedding-3-small")

        self.vector_db = QdrantVectorStore.from_existing_collection(
            url=qdrant_url,
            collection_name=collection_name,
            embedding=self.embedding,
            vector_name=collection_name,
        )

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

    # ✅ Store vector (query or response)
    def store(self, user_id: int, text: str, type_: str):
        chunks = self.splitter.split_text(text)

        docs = []
        for chunk in chunks:
            docs.append({
                "page_content": chunk,
                "metadata": {
                    "user_id": user_id,
                    "type": type_,
                    "timestamp": datetime.utcnow().isoformat(),
                    "id": str(uuid.uuid4())
                }
            })

        self.vector_db.add_texts(
            texts=[d["page_content"] for d in docs],
            metadatas=[d["metadata"] for d in docs]
        )

    # ✅ Get last 5 similar vectors
    def search(self, user_id: int, query: str, k=5):
        results = self.vector_db.similarity_search(
            query=query,
            k=k,
            filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="user_id",
                    match=models.MatchValue(value=user_id)
                )
            ]
        )
        )

        return [r.page_content for r in results]
