import logging
from typing import List, Dict, Optional, Any

from admitplus.config import settings


class GeminiClient:
    _instance: Optional["GeminiClient"] = None
    _model_cache: Dict[str, Any] = {}

    def __init__(self, api_key: Optional[str] = None):
        try:
            import google.generativeai as genai  # type: ignore
        except ImportError:
            raise ImportError(
                "google-generativeai library not found. "
                "Please install it with: pip install google-generativeai"
            )

        self.api_key = api_key or settings.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not configured")

        genai.configure(api_key=self.api_key)
        self.genai = genai
        logging.info("[GeminiClient] Initialized")

    @classmethod
    def get_instance(cls, api_key: Optional[str] = None) -> "GeminiClient":
        if cls._instance is None:
            cls._instance = cls(api_key)
        return cls._instance

    async def generate_text(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> str:
        if not messages:
            raise ValueError("Messages cannot be empty")

        model_name = model or settings.GEMINI_TEXT_MODEL_DEFAULT
        if not model_name:
            raise ValueError("Gemini chat model not configured")

        if model_name not in GeminiClient._model_cache:
            GeminiClient._model_cache[model_name] = self.genai.GenerativeModel(
                model_name
            )
        gemini_model = GeminiClient._model_cache[model_name]

        # Convert OpenAI-style messages into a single text prompt
        prompt = "\n".join(
            f"{message.get('role', 'user')}: {message.get('content', '')}"
            for message in messages
        )

        generation_config = self.genai.types.GenerationConfig(
            temperature=temperature, max_output_tokens=max_tokens, **kwargs
        )

        try:
            response = await gemini_model.generate_content_async(
                prompt, generation_config=generation_config
            )
            content = response.text
            if not content:
                raise ValueError("Empty response from Gemini")
            return content
        except Exception as e:
            logging.error(f"[GeminiClient] Text generation error: {str(e)}")
            raise RuntimeError(f"Gemini text generation error: {str(e)}") from e

    async def embedding(
        self, text: str, model: Optional[str] = None, **kwargs
    ) -> List[float]:
        if not text:
            raise ValueError("Text cannot be empty")

        model_name = model or settings.GEMINI_EMBED_MODEL_DEFAULT
        if not model_name:
            raise ValueError("Gemini embedding model not configured")

        try:
            result = await self.genai.embed_content_async(
                model=model_name, content=text, **kwargs
            )
            embedding = result.get("embedding", [])
            if not embedding:
                raise ValueError("Empty embedding from Gemini")
            return embedding
        except Exception as e:
            logging.error(f"[GeminiClient] Embedding error: {str(e)}")
            raise RuntimeError(f"Gemini embedding error: {str(e)}") from e

    async def image(self, prompt: str, model: Optional[str] = None, **kwargs) -> str:
        raise NotImplementedError(
            "Gemini does not currently support image generation. "
            "Use openai_image() for image generation."
        )


# Public function API (recommended)
async def generate_text(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    **kwargs,
) -> str:
    """Text generation using Gemini API."""
    return await GeminiClient.get_instance().generate_text(
        messages, model, temperature, max_tokens, **kwargs
    )


async def embedding(text: str, model: Optional[str] = None, **kwargs) -> List[float]:
    """Generate embeddings using Gemini API."""
    return await GeminiClient.get_instance().embedding(text, model, **kwargs)


async def image(prompt: str, model: Optional[str] = None, **kwargs) -> str:
    """Image generation using Gemini API."""
    return await GeminiClient.get_instance().image(prompt, model, **kwargs)
