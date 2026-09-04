import random
import time

from openai import OpenAI

from config.config import Config
from src.model import Message
from src.adapters.logger import logger

class OpenRouterService:
    """
    Helper class for interacting with OpenRouter (OpenAI-compatible API) for
    chat completions and embedding generation, with retry/backoff handling.
    """

    def __init__(self):
        self._client = OpenAI(api_key=Config.OPENROUTER_API_KEY, base_url=Config.OPENAI_BASE_URL)
        self._model = Config.MODEL
        logger.info("STATUS: OpenRouter client created successfully!")

    @staticmethod
    def _backoff_delay(attempt: int) -> float:
        """Exponential backoff delay with jitter for retry attempts."""
        return (2 ** attempt) + random.uniform(0, 1)

    @staticmethod
    def _usage_details(usage) -> dict:
        return {
            "input": usage.prompt_tokens,
            "output": usage.completion_tokens,
            "total": usage.total_tokens,
        }

    def chat(self, messages: list[Message], json_mode: bool = False, max_retries: int = 2) -> tuple[str, int]:
        message_dicts = [m.to_dict() for m in messages]

        for attempt in range(max_retries):
            try:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=message_dicts,
                    temperature=0,
                    **({"response_format": {"type": "json_object"}} if json_mode else {}),
                )
                content = response.choices[0].message.content
                return content, response.usage.total_tokens
            except Exception as ex:
                logger.error(f"OpenRouter chat request failed on attempt {attempt + 1}: {ex}", exc_info=True)
                if attempt < max_retries - 1:
                    time.sleep(self._backoff_delay(attempt))

        fallback = "Sorry, I'm having trouble responding right now. Please try again."
        return fallback, 0

openrouter = OpenRouterService()
