from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parent
DOCUMENTS_PATH = PROJECT_ROOT / "data" / "documents"
CHROMA_PATH = PROJECT_ROOT / "data" / "chroma"


def chunk_document(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[str]:
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")

    words = text.split()
    step = chunk_size - overlap

    return [
        " ".join(words[index:index + chunk_size])
        for index in range(0, len(words), step)
    ]


def ingest() -> None:
    if not DOCUMENTS_PATH.is_dir():
        raise FileNotFoundError(
            f"Documents folder not found: {DOCUMENTS_PATH}"
        )

    files = sorted(
        file_path
        for file_path in DOCUMENTS_PATH.rglob("*")
        if file_path.is_file()
        and file_path.suffix.lower() == ".txt"
    )

    print(f"Reading documents from: {DOCUMENTS_PATH}")
    print(f"Found {len(files)} .txt file(s)")

    if not files:
        raise ValueError(
            "No .txt files found. Check the filename and extension."
        )

    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collection = client.get_or_create_collection("enterprise-docs")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    total_chunks = 0

    for file_path in files:
        text = file_path.read_text(
            encoding="utf-8-sig",
            errors="replace",
        ).strip()

        print(
            f"Checking {file_path.name}: "
            f"{len(text)} characters, {len(text.split())} words"
        )

        if not text:
            print(f"Skipped empty document: {file_path}")
            continue

        chunks = chunk_document(text)

        if not chunks:
            print(f"Skipped document with no chunks: {file_path}")
            continue

        embeddings = model.encode(
            chunks,
            convert_to_numpy=True,
            show_progress_bar=False,
        ).tolist()

        ids = [
            f"{file_path.name}-{index}"
            for index in range(len(chunks))
        ]
        metadatas = [
            {
                "source": file_path.name,
                "chunk": index,
            }
            for index in range(len(chunks))
        ]

        collection.upsert(
            documents=chunks,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas,
        )

        total_chunks += len(chunks)
        print(
            f"Ingested {len(chunks)} chunk(s) from {file_path.name}"
        )

    if total_chunks == 0:
        raise ValueError(
            "No text chunks were created. Verify the file contents "
            "and location."
        )

    print(f"Ingestion complete: {total_chunks} total chunk(s)")


if __name__ == "__main__":
    ingest()
