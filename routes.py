import os
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from pydantic import BaseModel, Field, field_validator

from agent import DomainRestrictedAgent
from logger import logger


# --------------------------------------------------
# App Metadata
# --------------------------------------------------

app = FastAPI(
    title="PFA AI Agent API",
    description="PoC AI agent answering questions within a restricted knowledge domain.",
    version="1.1.0",
    contact={
        "name": "Tai Skadegaard",
        "email": "tai.skadegard@gmail.com",
    },
    docs_url=None, redoc_url=None,
)

# --------------------------------------------------
# Pydantic Models
# --------------------------------------------------

class ChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="User question to the AI agent."
    )
    chat_id: Optional[str] = Field(
        default="New",
        description="Existing chat ID. Use 'New' to create a new chat session."
    )
    temperature: Optional[float] = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Model creativity parameter."
    )

    @field_validator("question")
    def strip_whitespace(cls, v):
        return v.strip()


class ChatResponse(BaseModel):
    chat_id: str
    answer: str
    source_restricted: bool = Field(
        description="True if answer was restricted to knowledge base only."
    )


class MessageResponse(BaseModel):
    message: str


class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: str


class ChatHistoryResponse(BaseModel):
    chat_id: str
    history: List[ChatMessage]


# --------------------------------------------------
# Agent Loader
# --------------------------------------------------

agent = DomainRestrictedAgent()

# --------------------------------------------------
# Routes
# --------------------------------------------------

@app.get(
    "/",
    summary="Health check",
    response_model=MessageResponse,
    tags=["General"],
)
def read_root():
    return {"message": "PFA AI Agent API is running"}

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse('favicon.ico')

@app.get("/docs", include_in_schema=False)
def overridden_swagger():
	return get_swagger_ui_html(openapi_url="/openapi.json", title="PFA case swagger API documentation", swagger_favicon_url="/favicon.ico")

@app.get("/redoc", include_in_schema=False)
def overridden_redoc():
	return get_redoc_html(openapi_url="/openapi.json", title="PFA case ReDoc API documentation", redoc_favicon_url="/favicon.ico")

@app.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send a message to the AI agent",
    description="Creates a new chat or continues an existing one.",
    tags=["Chat"],
    responses={
        404: {"description": "Chat not found"},
        500: {"description": "Internal server error"},
        502: {"description": "AI provider error"}, #TODO: Include gateway timeout, and other 502 reasons, that could arise from infrastructure.
    },
)
def chat(request: ChatRequest):
    """
    Chat endpoint.

    - Creates new chat if chat_id == "New"
    - Continues existing chat otherwise
    - Returns chat_id so frontend can persist conversation
    """

    logger.info("Received question: %s (chat_id=%s)", request.question, request.chat_id)

    try:
        result = agent.chat(
            prompt=request.question,
            chat_id=request.chat_id,
            temperature=request.temperature,
        )

        answer = result["answer"]
        chat_id = result["chat_id"]

        restricted = "cannot answer" in answer.lower()

        return ChatResponse(
            chat_id=chat_id,
            answer=answer,
            source_restricted=restricted,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI provider error",
        )

    except Exception:
        logger.exception("Unexpected error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@app.get(
    "/chat/{chat_id}",
    response_model=ChatHistoryResponse,
    summary="Get chat history",
    description="Retrieve full conversation history for a given chat ID.",
    tags=["Chat"],
    responses={
        404: {"description": "Chat not found"},
        500: {"description": "Internal server error"},
    },
)
def get_chat_history(chat_id: str):
    """
    Returns stored chat history including timestamps.
    """

    try:
        history = agent.get_chat_history(chat_id)

        return ChatHistoryResponse(
            chat_id=chat_id,
            history=history,
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat with ID '{chat_id}' not found.",
        )

    except Exception:
        logger.exception("Failed retrieving chat history")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
