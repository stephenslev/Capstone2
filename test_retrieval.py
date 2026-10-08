from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


ROOT = Path(__file__).resolve().parent
CHROMA_PATH = ROOT / "data" / "chroma"
COLLECTION_NAME = "enterprise-docs"

TEST_QUERIES = [
    "Which changes require code review before merge?",
    "When are two reviewers required?",
    "What is required for emergency changes?",
    "What should a pull request include?",
    "How should reviewers provide feedback?",
]


def main() -> None:
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collection = client.get_collection(COLLECTION_NAME)
    model = SentenceTransformer("all-MiniLM-L6-v2")

    chunk_count = collection.count()
    print(f"Collection contains {chunk_count} chunks\n")

    if chunk_count == 0:
        raise ValueError("The collection contains no chunks.")

    for question in TEST_QUERIES:
        query_embedding = model.encode(
            question,
            convert_to_numpy=True,
            show_progress_bar=False,
        ).tolist()

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(3, chunk_count),
            include=["documents", "metadatas", "distances"],
        )

        print(f"QUERY: {question}")

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        for rank, (document, metadata, distance) in enumerate(
            zip(documents, metadatas, distances),
            start=1,
        ):
            preview = " ".join(document.split())[:300]
            print(
                f"{rank}. source={metadata['source']} "
                f"chunk={metadata['chunk']} "
                f"distance={distance:.4f}"
            )
            print(f"   {preview}...")

        print("-" * 80)


if __name__ == "__main__":
    main()
