import json
from pathlib import Path
from uuid import uuid4
from typing import Dict, List
from datetime import datetime

from google import genai

from logger import logger


class DomainRestrictedAgent:
    """
    Domain-restricted chat agent with persistent JSON-based storage.

    Storage format (chats.json):
    {
        "chat_id": [
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."}
        ]
    }
    """

    def __init__(self, knowledge_base: str):
        self.knowledge_base = knowledge_base
        self.client = genai.Client()

        self.storage_path = Path(__file__).parent / "chats.json"

        # Ensure storage file exists
        if not self.storage_path.exists():
            self.storage_path.write_text("{}", encoding="utf-8")

    # --------------------------------------------------
    # Internal Helpers
    # --------------------------------------------------

    def _load_all_chats(self) -> Dict[str, List[Dict]]:
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.exception("Failed loading chats.json")
            raise RuntimeError("Chat storage corrupted") from e

    def _write_all_chats(self, chats: Dict[str, List[Dict]]) -> None:
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(chats, f, indent=2)
        except Exception as e:
            logger.exception("Failed writing chats.json")
            raise RuntimeError("Failed to persist chat history") from e

    def _convert_history_to_genai_format(self, history: List[Dict]) -> List[genai.types.Content]:
        """
        Convert stored chat history into Google GenAI Content objects.
        Ensures compatibility with chats.create().
        """

        converted = []

        for message in history:
            converted.append(
                genai.types.Content(
                    role=message["role"],
                    parts=[genai.types.Part(text=message["content"])]
                )
            )

        return converted

    # --------------------------------------------------
    # Public Methods
    # --------------------------------------------------

    def get_chat_history(self, chat_id: str) -> List[Dict]:
        """
        Retrieve chat history by ID.
        Raises ValueError if chat does not exist.
        """
        chats = self._load_all_chats()

        if chat_id not in chats:
            raise ValueError(f"Chat with ID '{chat_id}' does not exist.")

        return chats[chat_id]

    def save_chat_history(self, chat_id: str, history: List[Dict]) -> None:
        """
        Persist updated chat history.
        """
        chats = self._load_all_chats()
        chats[chat_id] = history
        self._write_all_chats(chats)

    def chat(self, prompt: str, chat_id: str = "New", temperature: float = 0.2) -> Dict:
        """
        Chat interface.

        If chat_id == "New":
            - Generates new UUID
            - Creates new empty history

        Otherwise:
            - Loads existing history
            - Raises ValueError if not found

        Returns:
        {
            "chat_id": str,
            "answer": str
        }
        """

        # --------------------------------------------------
        # Initialize or Load Chat
        # --------------------------------------------------

        if chat_id == "New":
            chat_id = str(uuid4())
            history_json=[]
            history = None
            logger.info("Creating new chat with ID %s", chat_id)
        else:
            history_json = self.get_chat_history(chat_id)
            history = self._convert_history_to_genai_format(history_json)

        # --------------------------------------------------
        # System Instruction
        # --------------------------------------------------

        system_instruction = f"""
        You are a domain-restricted AI agent.
        You MUST only answer using the knowledge base below.
        If the answer is not found in the knowledge base, respond with:
        "I cannot answer that based on the available knowledge base."

        Knowledge Base:
        {self.knowledge_base}
        """

        try:
            # Create chat session
            # TODO: persist chat session in memory, in order to avoid reinitialization on every message. Look into ways to persist chats efficiently.
            chat_session = self.client.chats.create(
                model="gemini-1.5-flash",
                config=genai.types.GenerateContentConfig(
                    temperature=temperature,
                    system_instruction=system_instruction,
                ),
                history=history, 
            )

            # Send new prompt
            promt_timestamp = datetime.utcnow().isoformat()
            response = chat_session.send_message(prompt)
            response_timestamp = datetime.utcnow().isoformat()

            answer = response.text.strip()

        except Exception as e:
            logger.exception("Model generation failed")
            raise RuntimeError("AI model failed") from e

        # --------------------------------------------------
        # Update History Locally
        # --------------------------------------------------

        # TODO: Handle content better, for example if the model returns multiple parts, or if we want to store metadata about each message. For now we just store the raw text.
        updated_history = history_json + [
            {"role": "user", "content": prompt, "timestamp": promt_timestamp},
            {"role": "assistant", "content": answer, "timestamp": response_timestamp},
        ]

        self.save_chat_history(chat_id, updated_history)

        return {
            "chat_id": chat_id,
            "answer": answer,
        }
