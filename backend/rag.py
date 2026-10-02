"""RAG (Retrieval-Augmented Generation) & DSA Knowledge Base Module.

Provides:
- Document loading for markdown (.md) and text (.txt) DSA topic notes
- Configurable text chunking with adjustable chunk size and overlap
- Persistent ChromaDB vector store integration
- Gemini API embeddings (gemini-embedding-001)
- Manual/automated indexing pipeline
- Semantic retrieval (retrieve) for augmenting DSA chat prompts
"""

import hashlib
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import chromadb
from dotenv import find_dotenv, load_dotenv
from google import genai

# Load environment variables (.env in workspace or parent directory)
load_dotenv(find_dotenv(usecwd=True))

logger = logging.getLogger(__name__)

# Default paths
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, ".."))
DEFAULT_DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DEFAULT_CHROMA_PATH = os.path.join(BACKEND_DIR, "chroma_db")

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", DEFAULT_CHROMA_PATH)
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "dsa_notes")

# Default Embedding Model: gemini-embedding-001 is stable on v1beta API
DEFAULT_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")

# Default Chunking Parameters (in characters)
# 600 chars (~100-150 words) captures a complete concept/pattern snippet
# 120 chars (~20-25 words) provides ~20% overlap across consecutive chunks
DEFAULT_CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "600"))
DEFAULT_CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "120"))


# ============================================================================
# Gemini Client & Embeddings
# ============================================================================


def get_gemini_client() -> genai.Client:
    """Instantiates and returns the Google GenAI client."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.strip() in ("", "your_actual_key_here"):
        raise ValueError(
            "GEMINI_API_KEY is not set or invalid in environment/.env file."
        )
    return genai.Client(api_key=api_key.strip())


def embed_texts(
    texts: List[str],
    model: Optional[str] = None,
    batch_size: int = 30,
) -> List[List[float]]:
    """Generates embedding vectors for a list of strings using the Gemini API.

    Handles batching to avoid API payload size limits and retries alternate model names
    if the primary model encounters version differences.
    """
    if not texts:
        return []

    client = get_gemini_client()
    selected_model = model or DEFAULT_EMBEDDING_MODEL

    candidate_models = [selected_model]
    for fallback in ["gemini-embedding-001", "models/gemini-embedding-001", "gemini-embedding-2-preview"]:
        if fallback not in candidate_models:
            candidate_models.append(fallback)

    all_embeddings: List[List[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        batch_success = False
        last_error = None

        for mod in candidate_models:
            try:
                response = client.models.embed_content(
                    model=mod,
                    contents=batch,
                )
                if response and response.embeddings:
                    for emb in response.embeddings:
                        all_embeddings.append(list(emb.values))
                    batch_success = True
                    break
            except Exception as exc:
                last_error = exc
                logger.debug("Model %s failed for batch (%s). Trying next...", mod, exc)
                continue

        if not batch_success:
            raise RuntimeError(
                f"Failed to generate embeddings via Gemini API: {last_error}"
            )

    return all_embeddings


def embed_query(query: str, model: Optional[str] = None) -> List[float]:
    """Generates an embedding vector for a single search query."""
    embeddings = embed_texts([query], model=model, batch_size=1)
    if not embeddings:
        raise RuntimeError("No embedding returned for query.")
    return embeddings[0]


# ============================================================================
# Document Loading & Configurable Chunking
# ============================================================================


def load_documents(data_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """Loads all markdown (.md) and text (.txt) files from the specified data directory.

    Returns:
        List of dicts:
        [
            {
                "source": "dynamic_programming.md",
                "path": "/abs/path/to/file.md",
                "content": "...raw text...",
                "title": "Dynamic Programming",
            },
            ...
        ]
    """
    target_dir = Path(data_dir or DEFAULT_DATA_DIR)
    if not target_dir.exists() or not target_dir.is_dir():
        logger.warning("Data directory does not exist: %s", target_dir)
        return []

    documents: List[Dict[str, Any]] = []

    for file_path in sorted(target_dir.glob("**/*")):
        if file_path.is_file() and file_path.suffix.lower() in (".md", ".txt"):
            try:
                content = file_path.read_text(encoding="utf-8").strip()
                if not content:
                    continue

                # Extract first markdown header as title if available
                title = file_path.stem.replace("_", " ").title()
                for line in content.splitlines():
                    if line.startswith("#"):
                        header_text = line.lstrip("#").strip()
                        if header_text:
                            title = header_text
                            break

                documents.append(
                    {
                        "source": file_path.name,
                        "path": str(file_path.resolve()),
                        "content": content,
                        "title": title,
                    }
                )
            except Exception as e:
                logger.error("Error reading file %s: %s", file_path, e)

    logger.info("Loaded %d document(s) from %s", len(documents), target_dir)
    return documents


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    metadata: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Splits a document text into overlapping chunks with section/paragraph awareness.

    Parameters:
        text: The text to chunk.
        chunk_size: Maximum target number of characters per chunk (e.g., 600).
        chunk_overlap: Number of characters to overlap between consecutive chunks (e.g., 120).
        metadata: Optional metadata dictionary to attach to each chunk.

    Returns:
        List of chunk dictionaries with unique IDs, text content, and metadata.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer.")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must be non-negative.")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be strictly less than chunk_size.")

    cleaned_text = text.strip()
    if not cleaned_text:
        return []

    # If entire document is smaller than or equal to chunk_size, return single chunk
    if len(cleaned_text) <= chunk_size:
        base_meta = dict(metadata or {})
        base_meta["chunk_index"] = 0
        base_meta["total_chunks"] = 1
        base_meta["char_length"] = len(cleaned_text)
        return [
            {
                "id": f"{base_meta.get('source', 'doc')}_chunk_0",
                "text": cleaned_text,
                "metadata": base_meta,
            }
        ]

    # Split text into logical paragraph blocks (double newline)
    paragraphs = re.split(r"\n\s*\n", cleaned_text)
    blocks: List[str] = []

    for para in paragraphs:
        p = para.strip()
        if not p:
            continue
        # If a single paragraph is longer than chunk_size, split by lines or sentences
        if len(p) > chunk_size:
            lines = p.splitlines()
            sub_accum: List[str] = []
            sub_len = 0
            for line in lines:
                l_str = line.strip()
                if not l_str:
                    continue
                if sub_len + len(l_str) + 1 > chunk_size and sub_accum:
                    blocks.append("\n".join(sub_accum))
                    sub_accum = [l_str]
                    sub_len = len(l_str)
                else:
                    sub_accum.append(l_str)
                    sub_len += len(l_str) + 1
            if sub_accum:
                blocks.append("\n".join(sub_accum))
        else:
            blocks.append(p)

    # Assemble blocks into chunks using sliding window with chunk_overlap
    chunks: List[str] = []
    current_chunk: List[str] = []
    current_length = 0

    for block in blocks:
        block_len = len(block)
        # Check if adding this block exceeds target chunk_size
        if current_length + block_len + 2 > chunk_size and current_chunk:
            chunk_str = "\n\n".join(current_chunk).strip()
            chunks.append(chunk_str)

            # Calculate overlap text from the end of the current chunk
            overlap_target = chunk_overlap
            overlap_accum: List[str] = []
            overlap_len = 0
            for prev_block in reversed(current_chunk):
                if overlap_len + len(prev_block) + 2 <= overlap_target:
                    overlap_accum.insert(0, prev_block)
                    overlap_len += len(prev_block) + 2
                else:
                    break

            current_chunk = overlap_accum + [block]
            current_length = sum(len(b) for b in current_chunk) + 2 * (len(current_chunk) - 1)
        else:
            current_chunk.append(block)
            current_length += block_len + (2 if current_length > 0 else 0)

    if current_chunk:
        chunk_str = "\n\n".join(current_chunk).strip()
        if not chunks or chunk_str != chunks[-1]:
            chunks.append(chunk_str)

    # Format result with IDs and metadata
    doc_source = (metadata or {}).get("source", "doc")
    source_hash = hashlib.md5(doc_source.encode("utf-8")).hexdigest()[:8]

    result: List[Dict[str, Any]] = []
    for idx, c_text in enumerate(chunks):
        chunk_meta = dict(metadata or {})
        chunk_meta["chunk_index"] = idx
        chunk_meta["total_chunks"] = len(chunks)
        chunk_meta["char_length"] = len(c_text)

        result.append(
            {
                "id": f"{source_hash}_chunk_{idx}",
                "text": c_text,
                "metadata": chunk_meta,
            }
        )

    return result


def chunk_documents(
    documents: List[Dict[str, Any]],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[Dict[str, Any]]:
    """Processes multiple documents and chunks each with common configurable settings."""
    all_chunks: List[Dict[str, Any]] = []

    for doc in documents:
        meta = {
            "source": doc["source"],
            "title": doc.get("title", doc["source"]),
            "path": doc["path"],
        }
        chunks = chunk_text(
            text=doc["content"],
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            metadata=meta,
        )
        all_chunks.extend(chunks)

    logger.info(
        "Generated %d total chunks across %d documents (size=%d, overlap=%d)",
        len(all_chunks),
        len(documents),
        chunk_size,
        chunk_overlap,
    )
    return all_chunks


# ============================================================================
# ChromaDB Persistent Vector Store
# ============================================================================


def get_chroma_client() -> chromadb.PersistentClient:
    """Returns a persistent ChromaDB client pointing to the local storage directory."""
    os.makedirs(CHROMA_DB_PATH, exist_ok=True)
    return chromadb.PersistentClient(path=CHROMA_DB_PATH)


def get_or_create_collection(
    collection_name: str = CHROMA_COLLECTION_NAME,
) -> chromadb.Collection:
    """Retrieves or creates a ChromaDB collection with cosine distance metric."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )


# ============================================================================
# Indexing & Storage Pipeline
# ============================================================================


def index_data(
    data_dir: Optional[str] = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    reset_collection: bool = True,
    embedding_model: Optional[str] = None,
) -> Dict[str, Any]:
    """Indexes all notes in data_dir into the local persistent ChromaDB collection.

    Parameters:
        data_dir: Directory containing notes (.md, .txt). Defaults to /data.
        chunk_size: Character length limit per chunk.
        chunk_overlap: Overlapping characters between consecutive chunks.
        reset_collection: If True, clears existing collection entries before re-indexing.
        embedding_model: Gemini embedding model name (e.g. 'gemini-embedding-001').

    Returns:
        Summary statistics dictionary.
    """
    resolved_data_dir = data_dir or DEFAULT_DATA_DIR
    logger.info("Starting indexing for data directory: %s", resolved_data_dir)

    # 1. Load documents
    docs = load_documents(resolved_data_dir)
    if not docs:
        logger.warning("No documents found in %s to index.", resolved_data_dir)
        return {
            "status": "warning",
            "message": "No documents found to index.",
            "documents_count": 0,
            "chunks_count": 0,
        }

    # 2. Chunk documents
    chunks = chunk_documents(
        documents=docs,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    if not chunks:
        return {
            "status": "warning",
            "message": "Documents produced 0 chunks.",
            "documents_count": len(docs),
            "chunks_count": 0,
        }

    # 3. Generate embeddings
    texts = [c["text"] for c in chunks]
    logger.info("Generating Gemini embeddings for %d text chunks...", len(texts))
    embeddings = embed_texts(texts, model=embedding_model)

    # 4. Store in ChromaDB
    client = get_chroma_client()
    if reset_collection:
        try:
            client.delete_collection(name=CHROMA_COLLECTION_NAME)
            logger.info("Deleted previous collection '%s' for fresh re-index.", CHROMA_COLLECTION_NAME)
        except Exception:
            pass  # Collection did not exist yet

    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    ids = [c["id"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    logger.info(
        "Successfully indexed %d chunks from %d document(s) into ChromaDB ('%s').",
        len(chunks),
        len(docs),
        CHROMA_COLLECTION_NAME,
    )

    return {
        "status": "success",
        "documents_count": len(docs),
        "chunks_count": len(chunks),
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "collection_name": CHROMA_COLLECTION_NAME,
        "chroma_db_path": CHROMA_DB_PATH,
        "embedding_model": embedding_model or DEFAULT_EMBEDDING_MODEL,
        "documents": [d["source"] for d in docs],
    }


# ============================================================================
# Retrieval & Prompt Augmentation
# ============================================================================


def retrieve(
    query: str,
    top_k: int = 4,
    collection_name: str = CHROMA_COLLECTION_NAME,
    embedding_model: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieves top_k most relevant chunks for a given query string.

    Parameters:
        query: The user prompt or question to find context for.
        top_k: Maximum number of relevant chunks to return (default 4).
        collection_name: ChromaDB collection to query.
        embedding_model: Model name for embedding query.

    Returns:
        List of dictionaries with document text, source, metadata, and distance.
    """
    clean_query = (query or "").strip()
    if not clean_query:
        return []

    client = get_chroma_client()
    try:
        collection = client.get_collection(name=collection_name)
    except Exception:
        logger.warning("ChromaDB collection '%s' not found. Run index_data first.", collection_name)
        return []

    total_count = collection.count()
    if total_count == 0:
        logger.info("ChromaDB collection '%s' is empty.", collection_name)
        return []

    actual_k = min(top_k, total_count)

    # 1. Embed query
    query_vector = embed_query(clean_query, model=embedding_model)

    # 2. Query collection
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=actual_k,
        include=["documents", "metadatas", "distances"],
    )

    retrieved: List[Dict[str, Any]] = []
    if not results or not results.get("documents") or not results["documents"][0]:
        return []

    docs = results["documents"][0]
    metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
    distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)
    ids = results["ids"][0] if results.get("ids") else [""] * len(docs)

    for doc_id, doc_text, meta, dist in zip(ids, docs, metas, distances):
        # Cosine distance ranges from 0 (identical) to 2 (opposite)
        # Cosine similarity = 1 - distance
        similarity_score = max(0.0, 1.0 - float(dist)) if dist is not None else 0.0
        retrieved.append(
            {
                "id": doc_id,
                "text": doc_text,
                "metadata": meta,
                "source": meta.get("source", "DSA Notes"),
                "title": meta.get("title", meta.get("source", "DSA Notes")),
                "distance": float(dist) if dist is not None else 0.0,
                "similarity": round(similarity_score, 4),
            }
        )

    return retrieved


def format_retrieved_context(chunks: List[Dict[str, Any]]) -> str:
    """Formats a list of retrieved chunks into a clearly labeled context section.

    If chunks list is empty, returns an empty string so prompt remains clean.
    """
    if not chunks:
        return ""

    formatted_parts: List[str] = [
        "### Relevant DSA Reference Notes from Knowledge Base:",
    ]

    for idx, c in enumerate(chunks, 1):
        source = c.get("source") or "DSA Notes"
        title = c.get("title") or source
        similarity = c.get("similarity", "")
        sim_badge = f" (relevance: {similarity:.2f})" if isinstance(similarity, (int, float)) else ""
        formatted_parts.append(
            f"--- Reference Note #{idx} [Source: {source} | {title}]{sim_badge} ---\n{c['text']}"
        )

    formatted_parts.append(
        "--- End of Knowledge Base Reference Notes ---"
    )

    return "\n\n".join(formatted_parts)
