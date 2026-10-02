"""CLI Script to Index DSA Notes into ChromaDB Vector Store.

Usage:
    # 1. Index all markdown notes in data/ with default chunking (chunk_size=600, overlap=120):
    python scripts/index_data.py

    # 2. Experiment with custom chunk size and overlap:
    python scripts/index_data.py --chunk-size 800 --chunk-overlap 150

    # 3. Index and immediately test retrieval with a question:
    python scripts/index_data.py --query "How do I choose between BFS and DFS?"

    # 4. Only test retrieval on already indexed database without re-indexing:
    python scripts/index_data.py --query "Explain Dijkstra algorithm complexity" --test-only
"""

import argparse
import os
import sys

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ensure backend directory is in Python path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend import rag


def main():
    parser = argparse.ArgumentParser(
        description="Index DSA topic notes into ChromaDB vector store for RAG retrieval.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=os.path.join(PROJECT_ROOT, "data"),
        help="Path to folder containing markdown/text notes",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=rag.DEFAULT_CHUNK_SIZE,
        help="Target character length per chunk (configurable)",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=rag.DEFAULT_CHUNK_OVERLAP,
        help="Overlapping characters between adjacent chunks (configurable)",
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Optional test query to run immediately after indexing (or standalone)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=4,
        help="Number of relevant chunks to retrieve when testing query",
    )
    parser.add_argument(
        "--test-only",
        action="store_true",
        help="Skip re-indexing and only run retrieval query against existing collection",
    )
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="Append to existing collection instead of fresh overwrite",
    )

    args = parser.parse_args()

    print("=" * 72)
    print("[*] Personal AI - DSA Knowledge Base Indexer (ChromaDB + Gemini)")
    print("=" * 72)

    if not args.test_only:
        print(f"\n[+] Data Directory   : {args.data_dir}")
        print(f"[+] Chunk Size       : {args.chunk_size} characters")
        print(f"[+] Chunk Overlap    : {args.chunk_overlap} characters")
        print(f"[+] ChromaDB Storage : {rag.CHROMA_DB_PATH}")
        print(f"[+] Collection Name  : {rag.CHROMA_COLLECTION_NAME}")
        print(f"[+] Embedding Model  : {rag.DEFAULT_EMBEDDING_MODEL}")
        print("\nIndexing in progress...")

        try:
            stats = rag.index_data(
                data_dir=args.data_dir,
                chunk_size=args.chunk_size,
                chunk_overlap=args.chunk_overlap,
                reset_collection=not args.no_reset,
            )

            if stats.get("status") == "warning":
                print(f"[!] Warning: {stats.get('message')}")
                return

            print("\n[OK] Indexing Completed Successfully!")
            print(f"   * Documents Indexed : {stats['documents_count']}")
            print(f"   * Chunks Generated  : {stats['chunks_count']}")
            print(f"   * Files Processed   : {', '.join(stats.get('documents', []))}")
            print(f"   * Database Path     : {stats['chroma_db_path']}")
        except Exception as e:
            print(f"\n[ERROR] Indexing Failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    # If query was provided, perform retrieval test
    if args.query:
        print("\n" + "=" * 72)
        print(f"[?] Testing Retrieval for Query: \"{args.query}\"")
        print(f"[*] Top-K: {args.top_k}")
        print("=" * 72)

        try:
            results = rag.retrieve(args.query, top_k=args.top_k)
            if not results:
                print("[!] No matching chunks found. Make sure data is indexed.")
                return

            print(f"\nFound {len(results)} relevant chunk(s):\n")
            for idx, r in enumerate(results, 1):
                sim = r.get("similarity", 0.0)
                dist = r.get("distance", 0.0)
                source = r.get("source", "Unknown")
                title = r.get("title", source)
                meta = r.get("metadata", {})
                chunk_idx = meta.get("chunk_index", 0)
                total_chunks = meta.get("total_chunks", 1)

                print(f"--- [Result #{idx}] ---")
                print(f"Source     : {source} (Chunk {chunk_idx + 1}/{total_chunks})")
                print(f"Section    : {title}")
                print(f"Similarity : {sim:.4f} (Cosine distance: {dist:.4f})")
                print("Content:")
                indented = "\n".join("   " + line for line in r["text"].splitlines()[:15])
                print(indented)
                if len(r["text"].splitlines()) > 15:
                    print("   ... [truncated preview]")
                print()

            print("=" * 72)
            print("[OK] Retrieval verification completed!")
        except Exception as e:
            print(f"[ERROR] Retrieval failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()
