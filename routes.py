from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, validator

from agent import DomainRestrictedAgent
from logger import logger


# --------------------------------------------------
# App Metadata
# --------------------------------------------------

app = FastAPI(
    title="PFA AI Agent API",
    description="PoC AI agent answering questions within a restricted knowledge domain.",
    version="1.0.0",
    contact={
        "name": "Tai Skadegaard",
        "email": "tai.skadegard@gmail.com",
    },
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
    temperature: Optional[float] = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Model creativity parameter."
    )

    @validator("question")
    def strip_whitespace(cls, v):
        return v.strip()


class ChatResponse(BaseModel):
    answer: str
    source_restricted: bool = Field(
        description="True if answer was restricted to knowledge base only."
    )


class MessageResponse(BaseModel):
    message: str


    
# --------------------------------------------------
# Knowledge Base and Agent Loader
# --------------------------------------------------
KB_PATH = Path(__file__).parent / "fictional_knowledge_base.txt"

try:
    KNOWLEDGE_BASE = KB_PATH.read_text(encoding="utf-8")
except Exception as e:
    logger.error("Failed to load knowledge base: %s", str(e))
    KNOWLEDGE_BASE = ""

# Initialize agent
agent = DomainRestrictedAgent(KNOWLEDGE_BASE)

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


@app.post(
    "/chat",
    response_model=ChatResponse,
    summary="Ask the AI agent a question",
    description="Returns an answer strictly based on the fictional knowledge base.",
    tags=["Chat"],
)
def chat(request: ChatRequest):
    """
    Chat endpoint for interacting with the domain-restricted AI agent.

    - Validates input
    - Restricts answers to the knowledge base
    - Handles model errors gracefully
    """

    logger.info("Received question: %s", request.question)

    try:
        answer = agent.answer(
            question=request.question,
            temperature=request.temperature,
        )

        restricted = "cannot answer" in answer.lower()

        return ChatResponse(
            answer=answer,
            source_restricted=restricted
        )

    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI provider error"
        )

    except Exception as e:
        logger.exception("Unexpected error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
