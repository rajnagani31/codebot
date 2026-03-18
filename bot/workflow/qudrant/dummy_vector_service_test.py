from vector_service import VectorService


def main():
    service = VectorService()
    user_id = 1

    dummy_texts = [
        ("My name is Raj and I work on the Codebot project.", "profile"),
        ("I like FastAPI, LangChain, and Qdrant for AI apps.", "preferences"),
        ("My favorite database for vectors is Qdrant.", "preferences"),
    ]

    print("Storing dummy records...")
    for text, type_ in dummy_texts:
        service.store(user_id=user_id, text=text, type_=type_)
        print(f"Stored: {text}")

    query = "my name is raj"
    print(f"\nSearching for: {query}")

    results = service.search(user_id=user_id, query=query, k=3)

    print("\nTop matches:")
    for index, result in enumerate(results, start=1):
        print(f"{index}. {result}")


if __name__ == "__main__":
    main()
