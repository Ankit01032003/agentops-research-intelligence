
import hashlib
import io
from pathlib import Path

import chromadb
from openai import OpenAI
from pypdf import PdfReader

from app.config import settings


def get_collection():
    """Create or retrieve the persistent ChromaDB collection."""
    Path(settings.chroma_directory).mkdir(
        parents=True,
        exist_ok=True,
    )

    client = chromadb.PersistentClient(
        path=settings.chroma_directory
    )

    return client.get_or_create_collection(
        name=settings.collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def get_embedding_client() -> OpenAI:
    """Create the OpenAI client used for document embeddings."""
    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is required for document embeddings."
        )

    return OpenAI(api_key=settings.openai_api_key)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Convert text into embedding vectors."""
    if not texts:
        return []

    client = get_embedding_client()

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
    )

    return [
        item.embedding
        for item in response.data
    ]


def extract_text(filename: str, file_bytes: bytes) -> str:
    """Extract readable text from PDF, TXT, or Markdown files."""
    suffix = Path(filename).suffix.lower()

    if suffix == ".pdf":
        reader = PdfReader(io.BytesIO(file_bytes))

        return "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

    if suffix in {".txt", ".md"}:
        return file_bytes.decode(
            "utf-8",
            errors="replace",
        )

    raise ValueError(
        "Only PDF, TXT, and MD files are supported."
    )


def chunk_text(
    text: str,
    chunk_size: int = 1200,
    overlap: int = 200,
) -> list[str]:
    """Split text into overlapping chunks."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "overlap must be non-negative and smaller than chunk_size."
        )

    text = " ".join(text.split())

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])

        if end == len(text):
            break

        start = end - overlap

    return chunks


def ingest_document(
    filename: str,
    file_bytes: bytes,
) -> int:
    """
    Extract, chunk, embed, and store a document.

    Re-uploading the same filename replaces its existing version
    instead of adding another copy of its chunks.
    """
    text = extract_text(filename, file_bytes)
    chunks = chunk_text(text)

    if not chunks:
        raise ValueError(
            "No readable text was found in the uploaded document."
        )

    # Complete extraction and embedding before changing stored data.
    embeddings = embed_texts(chunks)

    if len(embeddings) != len(chunks):
        raise RuntimeError(
            "Embedding count does not match the chunk count."
        )

    collection = get_collection()

    # Create deterministic IDs from the filename, file contents,
    # and chunk index.
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    document_key = hashlib.sha256(
        f"{filename}:{file_hash}".encode("utf-8")
    ).hexdigest()

    ids = [
        hashlib.sha256(
            f"{document_key}:{index}".encode("utf-8")
        ).hexdigest()
        for index in range(len(chunks))
    ]

    metadatas = [
        {
            "filename": filename,
            "chunk_index": index,
            "file_hash": file_hash,
        }
        for index in range(len(chunks))
    ]

    # Replace the previous version of this filename.
    # Different filenames can coexist in the collection.
    collection.delete(
        where={"filename": filename}
    )

    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    return len(chunks)


def search_documents(
    query: str,
    top_k: int = 4,
) -> list[dict]:
    """Retrieve the most relevant document chunks for a query."""
    if not query or not query.strip():
        return []

    if top_k <= 0:
        return []

    collection = get_collection()
    total_documents = collection.count()

    if total_documents == 0:
        return []

    query_embedding = embed_texts([query])[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, total_documents),
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    evidence = []

    documents = results.get("documents") or [[]]
    metadatas = results.get("metadatas") or [[]]
    distances = results.get("distances") or [[]]

    result_documents = documents[0]
    result_metadatas = metadatas[0]
    result_distances = distances[0]

    for index, content in enumerate(result_documents):
        metadata = result_metadatas[index] or {}

        distance = (
            result_distances[index]
            if index < len(result_distances)
            else None
        )

        evidence.append(
            {
                "title": metadata.get(
                    "filename",
                    "Uploaded document",
                ),
                "url": "",
                "content": content,
                "source_type": "document",
                "chunk_index": metadata.get(
                    "chunk_index",
                    index,
                ),
                "distance": distance,
            }
        )

    return evidence
