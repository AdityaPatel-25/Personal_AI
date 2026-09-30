import json
import logging
import os
from typing import AsyncIterator

from dotenv import find_dotenv, load_dotenv
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

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
"""


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        description="The user's prompt or DSA question",
        json_schema_extra={
            "example": "How do I choose between BFS and DFS for graph problems?"
        },
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


async def generate_gemini_stream(message: str) -> AsyncIterator[str]:
    """Asynchronously calls Gemini's generate_content_stream and yields raw token chunks."""
    client = get_gemini_client()
    
    # Preferred models for DSA coaching: defaults to gemini-3.5-flash with smart fallback
    configured_model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    models_to_try = [configured_model]
    for fallback in ["gemini-3.5-flash", "gemini-3.7-flash", "gemini-3.8-flash", "gemini-3.1-flash-lite"]:
        if fallback not in models_to_try:
            models_to_try.append(fallback)

    last_error = None
    for model_name in models_to_try:
        try:
            response = await client.aio.models.generate_content_stream(
                model=model_name,
                contents=message,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                ),
            )
            has_yielded = False
            async for chunk in response:
                if chunk.text:
                    has_yielded = True
                    yield chunk.text
            if has_yielded:
                return
        except Exception as exc:
            logger.warning("Model %s encountered: %s. Trying fallback...", model_name, exc)
            last_error = exc
            continue

    if last_error:
        yield f"\n[Stream Error: {str(last_error)}]"


async def sse_stream_generator(message: str) -> AsyncIterator[str]:
    """Wraps token chunks into standard Server-Sent Events (SSE) data frames."""
    async for token in generate_gemini_stream(message):
        # Format payload as JSON so newlines and quotes in code blocks are properly preserved
        payload = json.dumps({"text": token})
        yield f"data: {payload}\n\n"
    yield "data: [DONE]\n\n"


@router.post("/chat")
async def chat(request_body: ChatRequest, raw_request: Request):
    """Streaming chat endpoint for DSA coaching.

    Accepts:
        { "message": "string" }

    Streaming Modes:
        - Chunked HTTP Response (media_type: text/plain) [Default]
          Ideal for terminal / curl testing and simple fetch streams.
        - Server-Sent Events (media_type: text/event-stream)
          Triggered when client specifies header `Accept: text/event-stream`.
    """
    # Pre-flight check: verify API key is present before initiating response stream
    get_gemini_client()

    accept_header = raw_request.headers.get("accept", "")

    # Check if client requested Server-Sent Events (SSE)
    if "text/event-stream" in accept_header:
        return StreamingResponse(
            sse_stream_generator(request_body.message),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # Default: Chunked plain text stream (Transfer-Encoding: chunked)
    return StreamingResponse(
        generate_gemini_stream(request_body.message),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
