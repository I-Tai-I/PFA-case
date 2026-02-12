from pathlib import Path

from google import genai
from google.genai import types

from logger import logger

# --------------------------------------------------
# AI Agent Logic
# --------------------------------------------------

class DomainRestrictedAgent:
    """
    Simple domain-restricted AI agent.
    Uses prompt-injection style context grounding.
    """

    def __init__(self, knowledge_base: str):
        self.knowledge_base = knowledge_base

        # Initialize client lazily if desired
        self.client = genai.Client()

    def answer(self, question: str, temperature: float) -> str:
        """
        Generate answer strictly based on knowledge base.
        """

        system_prompt = f"""
        You are a domain-restricted AI agent.
        You MUST only answer using the knowledge base below.
        If the answer is not found in the knowledge base, respond with:
        "I cannot answer that based on the available knowledge base."

        Knowledge Base:
        {self.knowledge_base}
        """

        try:
            response = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents=[
                    types.Content(role="user", parts=[types.Part(text=system_prompt)]),
                    types.Content(role="user", parts=[types.Part(text=question)])
                ],
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=512,
                )
            )

            return response.text.strip()

        except Exception as e:
            logger.exception("Model generation failed")
            raise RuntimeError("AI model failed") from e