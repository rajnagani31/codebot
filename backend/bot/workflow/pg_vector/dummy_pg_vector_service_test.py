import os
from dotenv import load_dotenv
from pg_vector_service import PGVectorService

load_dotenv()


def main():
    print("🚀 Initializing PGVector Service...")
    
    service = PGVectorService()
    user_id = 1

    # =========================
    # STORE TEST DATA
    # =========================
    print("\n📦 Storing dummy records...\n")

    dummy_data = [
        "User: My name is Raj\nAI: Nice to meet you Raj!",
        "User: I like Django\nAI: Django is a powerful web framework.",
        "User: How to create Django project?\nAI: Use django-admin startproject project_name",
        "User: What is pgvector?\nAI: pgvector is a PostgreSQL extension for vector similarity search.",
    ]

    for text in dummy_data:
        try:
            service.store(user_id=user_id, text=text, type_="chat")
            print(f"✅ Stored: {text[:60]}...")
        except Exception as e:
            print(f"❌ Error storing data: {e}")

    # =========================
    # SEARCH TEST
    # =========================
    query = "how to create a django project?"
    print(f"\n🔍 Searching for: '{query}'\n")

    try:
        results = service.search(user_id=user_id, query=query, k=3)

        print("✅ Top Results:\n")
        for i, r in enumerate(results, 1):
            print(f"{i}. {r}\n")

    except Exception as e:
        print(f"❌ Search error: {e}")


if __name__ == "__main__":
    main()