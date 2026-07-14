import logging
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from agents.coordinator import CoordinatorAgent
from memory.manager import memory_manager
from models.schemas import Token, UserCreate, UserRead
from services.auth import (
    authenticate_user,
    create_access_token,
    get_current_user_optional,
)
from services.user import create_user

logger = logging.getLogger("healthcare_ai_agent.api")

api_router = APIRouter(prefix="/api")

# A single shared CoordinatorAgent is reused across requests. It has no
# per-request mutable state of its own (all state lives in the database /
# memory manager), so this is safe and avoids re-instantiating every agent
# and tool on every single chat message.
coordinator = CoordinatorAgent()


# -----------------------------
# Request / Response Models
# -----------------------------
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    result: str
    conversation_history: list[str] | None = None


class HealthResponse(BaseModel):
    status: str
    app: str
    features: list[str]


# -----------------------------
# Health
# -----------------------------
@api_router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        app="AI Healthcare Care Coordinator",
        features=["chat", "chat_stream", "appointments", "medication", "treatment", "file_upload", "history"],
    )


# -----------------------------
# Register
# -----------------------------
@api_router.post("/auth/register", response_model=UserRead)
def register_user(user_data: UserCreate):
    try:
        return create_user(user_data)
    except ValueError as exc:
        # Duplicate username/email -> client error, not a server error.
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.exception("Unexpected error while registering user")
        raise HTTPException(status_code=500, detail="Could not register user.") from exc


# -----------------------------
# Login
# -----------------------------
@api_router.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(data={"sub": user.username})

    return {"access_token": token, "token_type": "bearer"}


# -----------------------------
# AI Assistant - standard (non-streaming) chat
# -----------------------------
@api_router.post("/assistant/chat", response_model=ChatResponse)
def assistant_chat(request: ChatRequest, current_user=Depends(get_current_user_optional)):
    try:
        logger.info("Chat request from user=%s message=%r", current_user.username, request.message)

        response = coordinator.handle_request(request.message, current_user)

        if not response:
            response = "No response generated."

        history = memory_manager.get_history(str(current_user.id), limit=10)
        return ChatResponse(result=str(response), conversation_history=history)

    except Exception as exc:
        logger.exception("Error handling chat request")
        raise HTTPException(status_code=500, detail=str(exc))


# -----------------------------
# AI Assistant - streaming chat
# -----------------------------
@api_router.post("/assistant/chat/stream")
def assistant_chat_stream(request: ChatRequest, current_user=Depends(get_current_user_optional)):
    """Streams the assistant's reply back to the client chunk by chunk.

    The response is plain incremental text (media type text/plain); the
    Streamlit frontend consumes this with a streaming HTTP request and
    renders tokens as they arrive, similar to ChatGPT / ChatGemini.
    """

    def token_generator():
        collected = []
        try:
            for chunk in coordinator.handle_request_stream(request.message, current_user):
                collected.append(chunk)
                yield chunk
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.exception("Error while streaming chat response")
            fallback = f"\n\n[The assistant hit an error while responding: {exc}]"
            collected.append(fallback)
            yield fallback

    return StreamingResponse(token_generator(), media_type="text/plain")


@api_router.get("/assistant/history")
def get_assistant_history(current_user=Depends(get_current_user_optional)):
    return {
        "user_id": current_user.id,
        "history": memory_manager.get_history(str(current_user.id), limit=20),
    }


@api_router.post("/assistant/upload")
def upload_assistant_file(
    file: Annotated[UploadFile, File(...)],
    current_user=Depends(get_current_user_optional),
):
    try:
        upload_dir = Path("uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{current_user.id}_{file.filename}"
        destination = upload_dir / filename
        with destination.open("wb") as handle:
            handle.write(file.file.read())

        return {
            "file_name": filename,
            "content_type": file.content_type,
            "saved_path": str(destination),
            "summary": f"File uploaded successfully for {current_user.username}.",
        }
    except Exception as exc:
        logger.exception("File upload failed")
        raise HTTPException(status_code=500, detail=f"File upload failed: {exc}")
