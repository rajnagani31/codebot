from vector_service import VectorService


def main():
    service = VectorService()
    user_id = 1

    print("📦 Storing dummy records...")

    dummy_data = [
        "User: My name is Raj\nAI: Nice to meet you Raj!",
        "User: I like Django\nAI: Django is a powerful web framework.",
        "User: How to create Django project?\nAI: Use django-admin startproject project_name",
    ]

    for text in dummy_data:
        service.store(user_id=user_id, text=text, type_="chat")
        print("Stored:", text[:50])

    query = "how to create a django project?"
    print(f"\n🔍 Searching for: {query}")

    results = service.search(user_id=user_id, query=query, k=3)

    print("\n✅ Results:")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r}")


if __name__ == "__main__":
    main()
