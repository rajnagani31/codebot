from vector_service import QdrantVectorService


def main():
    service = QdrantVectorService()
    user_id = 1

    print("📦 Storing dummy records...")

    # dummy_data = [
    #     "User: My name is Raj\nAI: Nice to meet you Raj!",
    #     "User: I like Django\nAI: Django is a powerful web framework.",
    #     "User: How to create Django project?\nAI: Use django-admin startproject project_name",
    # ]
    dummy_data = [
        "Retrieval-Augmented Generation (RAG) is an AI architecture that combines the reasoning capabilities of large language models with information retrieved from external knowledge sources. Instead of relying only on the data used during model training, a RAG system searches documents, databases, or vector stores to find information relevant to a user's question. The retrieved content is then provided as additional context to the language model before it generates a response. This approach improves factual accuracy, reduces hallucinations, and allows AI applications to answer questions about private or frequently changing data. A typical RAG pipeline consists of document ingestion, text chunking, embedding generation, vector database storage, similarity search, context retrieval, and response generation. During ingestion, documents are divided into smaller chunks to preserve semantic meaning while fitting within embedding model limits. Each chunk is converted into a high-dimensional vector using an embedding model and stored in a vector database such as Qdrant, Pinecone, Weaviate, or Milvus. When a user submits a query, the query is embedded into the same vector space, and the database returns the most semantically similar chunks. These retrieved chunks are included in the prompt sent to the language model, enabling it to generate responses grounded in relevant knowledge. RAG is widely used in enterprise chatbots, document search, customer support, internal knowledge bases, code assistants, and AI-powered research tools because it provides accurate, explainable, and up-to-date answers without requiring expensive model retraining."
    ]

    # for text in dummy_data:
    #     service.store(user_id=user_id, text=text, type_="chat")
    #     print("Stored:", text[:50])

    query = "What is RAG?"
    print(f"\n🔍 Searching for: {query}")

    results = service.search(user_id=user_id, query=query, k=5)

    print("\n✅ Results:")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r}")


if __name__ == "__main__":
    main()
