import os
import logging
from typing import List, Dict, Optional, Union
from openai import AsyncOpenAI
from admitplus.config import settings
from admitplus.llm.prompts.gpt_prompts.image_extraction_prompt import (
    build_image_extraction_prompt,
)


class OpenAIClient:
    _instance: Optional["OpenAIClient"] = None

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not configured")
        self.client = AsyncOpenAI(api_key=self.api_key)
        logging.info("[OpenAIClient] Initialized")

    @classmethod
    def get_instance(cls, api_key: Optional[str] = None) -> "OpenAIClient":
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

        model = model or settings.OPENAI_TEXT_MODEL_DEFAULT
        if not model:
            raise ValueError("OpenAI chat model not configured")

        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI")
            return content
        except Exception as e:
            logging.error(f"[OpenAIClient] Text generation error: {str(e)}")
            raise RuntimeError(f"OpenAI text generation error: {str(e)}") from e

    async def embedding(
        self, text: Union[str, List[str]], model: Optional[str] = None, **kwargs
    ) -> Union[List[float], List[List[float]]]:
        if not text:
            raise ValueError("Text cannot be empty")

        model = model or settings.OPENAI_EMBED_MODEL_DEFAULT
        if not model:
            raise ValueError("OpenAI embedding model not configured")

        try:
            response = await self.client.embeddings.create(
                model=model, input=text, **kwargs
            )
            if isinstance(text, list):
                return [item.embedding for item in response.data]
            return response.data[0].embedding
        except Exception as e:
            logging.error(f"[OpenAIClient] Embedding error: {str(e)}")
            raise RuntimeError(f"OpenAI embedding error: {str(e)}") from e

    @staticmethod
    def _normalize_image_url(image_url_or_base64: str) -> str:
        if image_url_or_base64.startswith("gcs://"):
            gcs_path = image_url_or_base64[6:]
            if settings.CDN_BASE_URL:
                path = gcs_path.split("/", 1)[1] if "/" in gcs_path else gcs_path
                return f"{settings.CDN_BASE_URL.rstrip('/')}/{path}"
            parts = gcs_path.split("/", 1)
            return (
                f"https://storage.googleapis.com/{parts[0]}/{parts[1]}"
                if len(parts) == 2
                else f"https://storage.googleapis.com/{gcs_path}"
            )

        if image_url_or_base64.startswith(("http://", "https://", "data:")):
            return image_url_or_base64

        return f"data:image/png;base64,{image_url_or_base64}"

    async def extract_text_from_image(self, image_url_or_base64: str) -> str:
        if not image_url_or_base64:
            raise ValueError("Image URL or base64 cannot be empty")

        image_url = self._normalize_image_url(image_url_or_base64)
        vision_model = os.getenv("OPENAI_VISION_MODEL", "gpt_prompts-4o")
        messages = build_image_extraction_prompt(image_url)

        try:
            response = await self.client.chat.completions.create(
                model=vision_model, messages=messages, temperature=0.3, max_tokens=4000
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI Vision API")
            return content
        except Exception as e:
            logging.error(f"[OpenAIClient] ExtractTextFromImage error: {str(e)}")
            raise RuntimeError(f"Error extracting text from image: {str(e)}") from e


# Public function API
async def generate_text(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    **kwargs,
) -> str:
    return await OpenAIClient.get_instance().generate_text(
        messages, model, temperature, max_tokens, **kwargs
    )


async def embedding(
    text: Union[str, List[str]], model: Optional[str] = None, **kwargs
) -> Union[List[float], List[List[float]]]:
    return await OpenAIClient.get_instance().embedding(text, model, **kwargs)


async def extract_text_from_image(image_url_or_base64: str) -> str:
    return await OpenAIClient.get_instance().extract_text_from_image(
        image_url_or_base64
    )


# Backward compatible aliases
chat = generate_text
openai_chat = generate_text
openai_embedding = embedding
openai_extract_image_text = extract_text_from_image
