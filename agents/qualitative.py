import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHROMA_PATH = PROJECT_ROOT / "data" / "chroma"
COLLECTION_NAME = "enterprise-docs"
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY is missing from the .env file")

client = OpenAI(
    api_key=api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


def retrieve(query: str, top_k: int = 5) -> list[dict]:
    chroma = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collection = chroma.get_collection(COLLECTION_NAME)

    collection_size = collection.count()
    if collection_size == 0:
        return []

    embedding = embedding_model.encode(
        query,
        convert_to_numpy=True,
        show_progress_bar=False,
    ).tolist()

    results = collection.query(
        query_embeddings=[embedding],
        n_results=min(top_k, collection_size),
        include=["documents", "metadatas", "distances"],
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    return [
        {
            "content": document,
            "source": metadata["source"],
            "chunk": metadata["chunk"],
            "distance": distance,
        }
        for document, metadata, distance in zip(
            documents,
            metadatas,
            distances,
        )
    ]


def build_prompt(query: str, chunks: list[dict]) -> str:
    context = "\n\n".join(
        (
            f"[Source {index}: {chunk['source']}, "
            f"chunk {chunk['chunk']}]\n{chunk['content']}"
        )
        for index, chunk in enumerate(chunks, start=1)
    )

    return f"""
Answer the user's question using ONLY the context below.

If the answer is not in the context, say:
"I cannot find this information in the provided documents."

Always cite the source number or numbers used.
Always cite the source file name where the information was found

If the answer can be partially answered, state so and explain the partial answer that can be provided rather than saying information cannot be found.

CONTEXT:
{context}

QUESTION:
{query}

ANSWER:
"""


def run(query: str) -> dict:
    chunks = retrieve(query)

    if not chunks:
        return {
            "answer": (
                "I cannot find this information in the provided documents."
            ),
            "chunks": [],
            "input_tokens": 0,
            "output_tokens": 0,
        }

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful enterprise documentation assistant. "
                    "Be accurate and grounded in the supplied context."
                    "Answer using only the supplied content"
                    "Do not use outside knowledge or invent facts."
                    "If the answer is not in the content, responde exactly:"
                    "'I cannot find this information in the provided documents'"
                    "Always cite the source number or numbers used"
                    "Always cite the source file name where the information was found"
                    "If the answer can be partially answered, state so and explain the partial answer that can be provided rather than saying information cannot be found."
                ),
            },
            {
                "role": "user",
                "content": build_prompt(query, chunks),
            },
        ],
        temperature=0.2,
        max_tokens=1024,
    )

    answer = response.choices[0].message.content or ""
    usage = response.usage

    return {
        "answer": answer,
        "chunks": chunks,
        "input_tokens": getattr(usage, "prompt_tokens", 0),
        "output_tokens": getattr(usage, "completion_tokens", 0),
    }



