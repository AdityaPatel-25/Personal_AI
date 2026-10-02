import json
import logging
import os
import uuid
from typing import Any, AsyncIterator, Dict, List, Optional

from dotenv import find_dotenv, load_dotenv
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# Enable flexible imports whether running from root or from within backend/
try:
    from backend import db, rag
except ImportError:
    import db, rag

# Load environment variables (.env in current directory or parent directories)
load_dotenv(find_dotenv(usecwd=True))

logger = logging.getLogger(__name__)

router = APIRouter()

SYSTEM_INSTRUCTION = """You are an expert AI coach for competitive programming and Data Structures & Algorithms (DSA).
Your mission is to guide students and engineers through problem-solving with algorithmic rigor, intuition, and encouragement.
When assisting:
1. Provide guiding questions or intuitive hints before giving away the full solution, promoting deep problem-solving skills.
2. When explaining solutions, detail intuition, step-by-step logic, edge cases, and time/space complexity (Big-O analysis).
3. If code is requested, provide clean, idiomatic code with clear explanatory comments.
4. Remember the student's prior questions and code within the conversation to provide coherent, contextual guidance.
5. If relevant DSA reference notes from the knowledge base are included in the prompt, prioritize and cite those specific patterns, rules, code templates, and complexity constraints.
"""


# Number of recent messages to pass to Gemini as context (10-15 messages)
CONTEXT_MESSAGE_LIMIT = 14


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        description="The user's prompt or DSA question",
        json_schema_extra={
            "example": "How do I choose between BFS and DFS for graph problems?"
        },
    )
    conversation_id: Optional[str] = Field(
        None,
        description="ID of the conversation to append to. Auto-generated if omitted.",
    )


class CreateConversationRequest(BaseModel):
    title: Optional[str] = Field(
        "New Chat",
        description="Title of the new conversation",
    )


def get_gemini_client() -> genai.Client:
    """Instantiates and returns the Google GenAI client using the configured API key."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.strip() in ("", "your_gemini_api_key_here"):
        raise HTTPException(
            status_code=500,
            detail=(
                "GEMINI_API_KEY environment variable is not configured. "
                "Please configure GEMINI_API_KEY in your .env file."
            ),
        )
    return genai.Client(api_key=api_key.strip())


def build_gemini_contents(raw_messages: List[Dict[str, Any]]) -> List[types.Content]:
    """Converts database messages into validated, alternating Gemini types.Content objects.
    
    Ensures:
    1. Roles are mapped: 'user' -> 'user', 'assistant' -> 'model'.
    2. Consecutive messages of the same role are merged to ensure strict alternation.
    3. Conversation context always begins with a 'user' turn.
    """
    contents: List[types.Content] = []

    for msg in raw_messages:
        role = "user" if msg["role"] == "user" else "model"
        text = (msg.get("content") or "").strip()
        if not text:
            continue

        if contents and contents[-1].role == role:
            # Merge with previous turn of same role to satisfy Gemini turn requirement
            prev_parts = contents[-1].parts
            prev_text = prev_parts[0].text if prev_parts and prev_parts[0].text else ""
            combined_text = f"{prev_text}\n\n{text}".strip()
            contents[-1] = types.Content(
                role=role,
                parts=[types.Part.from_text(text=combined_text)],
            )
        else:
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=text)],
                )
            )

    # Gemini conversation history must start with a user turn
    while contents and contents[0].role != "user":
        contents.pop(0)

    return contents


def derive_conversation_title(prompt: str) -> str:
    """Generates a concise, readable conversation title from the first prompt."""
    cleaned = " ".join(prompt.strip().split())
    if len(cleaned) <= 36:
        return cleaned
    truncated = cleaned[:36]
    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0]
    return f"{truncated}..."


async def generate_gemini_stream(
    contents: List[types.Content],
    conversation_id: str,
) -> AsyncIterator[str]:
    """Asynchronously calls Gemini's generate_content_stream, yields tokens, and saves assistant reply to DB."""
    client = get_gemini_client()

    configured_model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    models_to_try = [configured_model]
    for fallback in [
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash",
        "gemini-flash-latest",
        "gemini-3.8-flash",
        "gemini-3.7-flash",
    ]:
        if fallback not in models_to_try:
            models_to_try.append(fallback)

    full_response_chunks: List[str] = []
    stream_successful = False
    last_error = None

    try:
        for model_name in models_to_try:
            current_model_chunks: List[str] = []
            try:
                response = await client.aio.models.generate_content_stream(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                    ),
                )
                async for chunk in response:
                    if chunk.text:
                        stream_successful = True
                        current_model_chunks.append(chunk.text)
                        full_response_chunks.append(chunk.text)
                        yield chunk.text

                if stream_successful:
                    break
            except Exception as exc:
                logger.warning("Model %s encountered: %s. Trying fallback...", model_name, exc)
                last_error = exc
                # If this model produced no successful tokens, clean up partial list and try next
                if not current_model_chunks:
                    continue
                else:
                    # If it failed mid-stream, break
                    break

        if not stream_successful and last_error:
            err_str = str(last_error)
            if "503" in err_str or "high demand" in err_str.lower() or "UNAVAILABLE" in err_str:
                error_msg = (
                    "⚠️ **Google Gemini Service Spike (503):** Google's model servers are temporarily experiencing high demand. "
                    "Please click **Retry** or send your prompt again in a few seconds."
                )
            elif "429" in err_str or "quota" in err_str.lower():
                error_msg = (
                    "⚠️ **Rate Limit Reached (429):** Gemini API quota limit reached. Please wait a moment and try again."
                )
            else:
                error_msg = f"⚠️ **Connection Notice:** {err_str}"

            full_response_chunks.append(error_msg)
            yield error_msg


    finally:
        # Persist full or partial generated assistant response to SQLite database
        accumulated_text = "".join(full_response_chunks).strip()
        if accumulated_text:
            try:
                db.add_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=accumulated_text,
                )
                logger.info(
                    "Persisted assistant response (%d chars) to conversation %s",
                    len(accumulated_text),
                    conversation_id,
                )
            except Exception as save_err:
                logger.error("Failed to persist assistant message to DB: %s", save_err)


async def sse_stream_generator(
    contents: List[types.Content],
    conversation_id: str,
) -> AsyncIterator[str]:
    """Wraps token chunks into standard Server-Sent Events (SSE) data frames."""
    async for token in generate_gemini_stream(contents, conversation_id):
        payload = json.dumps({"text": token})
        yield f"data: {payload}\n\n"
    yield "data: [DONE]\n\n"


# ============================================================================
# Conversation Endpoints
# ============================================================================


@router.post("/conversations", status_code=201)
async def create_conversation_endpoint(body: Optional[CreateConversationRequest] = None):
    """Creates a new conversation record and returns its metadata."""
    title = (body.title if body and body.title else "New Chat").strip()
    conversation = db.create_conversation(title=title)
    return conversation


@router.get("/conversations")
async def list_conversations_endpoint():
    """Lists all past conversations for the sidebar/history view."""
    return db.list_conversations()


@router.get("/conversations/{conversation_id}")
async def get_conversation_endpoint(conversation_id: str):
    """Retrieves full conversation details including all saved messages in chronological order."""
    conv = db.get_conversation_with_messages(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conv


@router.delete("/conversations/{conversation_id}")
async def delete_conversation_endpoint(conversation_id: str):
    """Deletes a conversation and its messages."""
    success = db.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"status": "deleted", "id": conversation_id}


# ============================================================================
# Streaming Chat Endpoint
# ============================================================================


@router.post("/chat")
async def chat(request_body: ChatRequest, raw_request: Request):
    """Streaming chat endpoint for DSA coaching with persistent memory & RAG retrieval.

    Accepts:
        {
            "message": "Explain 0/1 knapsack space optimization",
            "conversation_id": "optional-uuid"
        }

    Features:
        - Resolves or creates conversation in SQLite.
        - Persists the incoming user message to SQLite (as typed).
        - Updates conversation title if initial.
        - Retrieves top relevant chunks from ChromaDB vector store based on user prompt.
        - Injects retrieved notes into the prompt for Gemini with clear distinction from conversation history.
        - Extracts recent history (last 10-15 messages) and formats for Gemini.
        - Streams response chunk-by-chunk and persists assistant message on completion.
        - Returns active conversation ID and RAG metrics in HTTP response headers.
    """
    # Pre-flight check: verify API key before initiating response stream
    get_gemini_client()

    # 1. Resolve or create conversation
    conv_id = request_body.conversation_id
    if conv_id:
        existing_conv = db.get_conversation(conv_id)
        if not existing_conv:
            conv_id = db.create_conversation(title="New Chat", conversation_id=conv_id)["id"]
    else:
        conv_id = db.create_conversation(title="New Chat")["id"]

    # 2. Persist the user message to SQLite (preserves pure user prompt for UI & DB history)
    db.add_message(
        conversation_id=conv_id,
        role="user",
        content=request_body.message,
    )

    # 3. Update title if this conversation still has the default title
    current_conv = db.get_conversation(conv_id)
    if current_conv and current_conv.get("title") in ("New Chat", "New Conversation", ""):
        new_title = derive_conversation_title(request_body.message)
        db.update_conversation_title(conv_id, new_title)

    # 4. RAG Step: Retrieve relevant notes from ChromaDB vector store
    retrieved_chunks: List[Dict[str, Any]] = []
    rag_context = ""
    try:
        retrieved_chunks = rag.retrieve(request_body.message, top_k=4)
        rag_context = rag.format_retrieved_context(retrieved_chunks)
        if retrieved_chunks:
            sources = sorted({c.get("source", "DSA Notes") for c in retrieved_chunks})
            logger.info(
                "RAG retrieved %d chunk(s) from %s for query: %s",
                len(retrieved_chunks),
                sources,
                request_body.message[:45],
            )
    except Exception as rag_err:
        logger.warning("RAG retrieval failed (continuing without RAG context): %s", rag_err)

    # 5. Fetch recent history (last 14 messages) for conversation memory
    raw_history = db.get_messages(conv_id, limit=CONTEXT_MESSAGE_LIMIT)

    # 6. Build Gemini contents: augment the latest user turn with the retrieved RAG notes,
    # keeping previous conversation turns intact so past context is preserved.
    if raw_history and raw_history[-1]["role"] == "user" and rag_context:
        augmented_prompt = (
            f"{rag_context}\n\n"
            f"=== Student Question ===\n"
            f"{request_body.message}"
        )
        augmented_history = [dict(m) for m in raw_history]
        augmented_history[-1]["content"] = augmented_prompt
        gemini_contents = build_gemini_contents(augmented_history)
    else:
        gemini_contents = build_gemini_contents(raw_history)

    # Fallback to single message if formatted history somehow empty
    if not gemini_contents:
        augmented_prompt = (
            f"{rag_context}\n\n=== Student Question ===\n{request_body.message}"
            if rag_context
            else request_body.message
        )
        gemini_contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=augmented_prompt)],
            )
        ]

    accept_header = raw_request.headers.get("accept", "")
    response_headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
        "X-Conversation-Id": conv_id,
        "X-Rag-Chunks": str(len(retrieved_chunks)),
    }
    if retrieved_chunks:
        sources_str = ", ".join(sorted({c.get("source", "") for c in retrieved_chunks if c.get("source")}))
        response_headers["X-Rag-Sources"] = sources_str

    # 7. Check if client requested Server-Sent Events (SSE)
    if "text/event-stream" in accept_header:
        return StreamingResponse(
            sse_stream_generator(gemini_contents, conv_id),
            media_type="text/event-stream",
            headers=response_headers,
        )

    # 8. Default: Chunked plain text stream
    return StreamingResponse(
        generate_gemini_stream(gemini_contents, conv_id),
        media_type="text/plain; charset=utf-8",
        headers=response_headers,
    )


# ============================================================================
# RAG Management Endpoints
# ============================================================================


@router.get("/rag/status")
async def rag_status():
    """Returns status of ChromaDB vector store and indexed DSA notes."""
    try:
        client = rag.get_chroma_client()
        col = rag.get_or_create_collection()
        return {
            "status": "online",
            "collection_name": rag.CHROMA_COLLECTION_NAME,
            "total_chunks": col.count(),
            "chroma_db_path": rag.CHROMA_DB_PATH,
            "embedding_model": rag.DEFAULT_EMBEDDING_MODEL,
        }
    except Exception as e:
        return {
            "status": "error",
            "detail": str(e),
        }


@router.get("/rag/query")
async def rag_query(q: str, top_k: int = 4):
    """Directly query the RAG vector store for inspection and verification."""
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required.")
    chunks = rag.retrieve(query=q, top_k=top_k)
    return {
        "query": q,
        "top_k": top_k,
        "results_count": len(chunks),
        "results": chunks,
    }


@router.post("/rag/index")
async def rag_reindex(chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None):
    """Triggers indexing of documents in /data folder into ChromaDB."""
    try:
        stats = rag.index_data(
            chunk_size=chunk_size or rag.DEFAULT_CHUNK_SIZE,
            chunk_overlap=chunk_overlap or rag.DEFAULT_CHUNK_OVERLAP,
            reset_collection=True,
        )
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {e}")

