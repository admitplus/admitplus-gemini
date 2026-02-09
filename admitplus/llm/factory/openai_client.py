import logging
from typing import Optional, Union, List
from openai import AsyncOpenAI

from .base import (
    BaseLLMClient,
    ModelProvider,
    ModelCapability,
    LLMRequest,
    LLMResponse,
    EmbeddingRequest,
    EmbeddingResponse,
)
from .util import (
    with_retry,
    with_timeout,
    with_logging,
    with_error_handling,
    validate_api_key,
    validate_model,
    validate_not_empty,
    LLMAPIError,
)


class OpenAIClient(BaseLLMClient):
    _instance: Optional["OpenAIClient"] = None

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_text_model: str = "gpt-4o",
        default_embed_model: str = "text-embedding-3-small",
        default_vision_model: str = "gpt-4o",
    ):
        super().__init__(api_key)

        try:
            from admitplus.config import settings

            self.api_key = api_key or settings.OPENAI_API_KEY
            self.default_text_model = (
                default_text_model or settings.OPENAI_TEXT_MODEL_DEFAULT
            )
            self.default_embed_model = (
                default_embed_model or settings.OPENAI_EMBED_MODEL_DEFAULT
            )
        except ImportError:
            self.api_key = api_key
            self.default_text_model = default_text_model
            self.default_embed_model = default_embed_model

        validate_api_key(self.api_key, "OpenAI")

        self.default_vision_model = default_vision_model
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.logger.info("[OpenAIClient] Initialized successfully")

    @classmethod
    def get_instance(cls, **kwargs) -> "OpenAIClient":
        if cls._instance is None:
            cls._instance = cls(**kwargs)
        return cls._instance

    @property
    def provider(self) -> ModelProvider:
        return ModelProvider.OPENAI

    @property
    def supported_capabilities(self) -> List[ModelCapability]:
        return [
            ModelCapability.TEXT_GENERATION,
            ModelCapability.EMBEDDING,
            ModelCapability.VISION,
        ]

    @with_logging()
    @with_error_handling(LLMAPIError)
    @with_timeout(timeout_seconds=60.0)
    @with_retry(max_retries=3, initial_delay=1.0)
    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        """
        文本生成
        """
        self._validate_capability(ModelCapability.TEXT_GENERATION)
        validate_not_empty(request.messages, "messages")

        model = request.model or self.default_text_model
        validate_model(model, "OpenAI")

        messages_dict = request.to_messages_dict()

        response = await self.client.chat.completions.create(
            model=model,
            messages=messages_dict,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            **request.extra_params,
        )

        content = response.choices[0].message.content
        validate_not_empty(content, "response content")

        usage = None
        if hasattr(response, "usage") and response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return LLMResponse(
            content=content,
            model=model,
            provider=self.provider,
            usage=usage,
            metadata={
                "finish_reason": response.choices[0].finish_reason,
                "response_id": response.id,
            },
        )

    @with_logging()
    @with_error_handling(LLMAPIError)
    @with_timeout(timeout_seconds=30.0)
    @with_retry(max_retries=3, initial_delay=1.0)
    async def generate_embedding(self, request: EmbeddingRequest) -> EmbeddingResponse:
        self._validate_capability(ModelCapability.EMBEDDING)
        validate_not_empty(request.text, "text")

        model = request.model or self.default_embed_model
        validate_model(model, "OpenAI")

        response = await self.client.embeddings.create(
            model=model,
            input=request.text,
            **request.extra_params,
        )

        if isinstance(request.text, list):
            embeddings = [item.embedding for item in response.data]
            dimensions = len(embeddings[0]) if embeddings else 0
        else:
            embeddings = response.data[0].embedding
            dimensions = len(embeddings) if embeddings else 0

        return EmbeddingResponse(
            embeddings=embeddings,
            model=model,
            provider=self.provider,
            dimensions=dimensions,
            metadata={
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            },
        )

    async def extract_text_from_image(
        self,
        image_url_or_base64: str,
        model: Optional[str] = None,
        instruction: str = "Extract all text from this image.",
    ) -> LLMResponse:
        self._validate_capability(ModelCapability.VISION)
        validate_not_empty(image_url_or_base64, "image_url_or_base64")

        image_url = self._normalize_image_url(image_url_or_base64)
        model = model or self.default_vision_model

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": instruction},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ]

        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=4000,
        )

        content = response.choices[0].message.content
        validate_not_empty(content, "vision response content")

        return LLMResponse(
            content=content,
            model=model,
            provider=self.provider,
            metadata={"task": "vision", "image_url": image_url},
        )

    @staticmethod
    def _normalize_image_url(image_url_or_base64: str) -> str:
        if image_url_or_base64.startswith("gcs://"):
            try:
                from admitplus.config import settings

                gcs_path = image_url_or_base64[6:]
                if settings.CDN_BASE_URL:
                    path = gcs_path.split("/", 1)[1] if "/" in gcs_path else gcs_path
                    return f"{settings.CDN_BASE_URL.rstrip('/')}/{path}"
            except ImportError:
                pass

            gcs_path = image_url_or_base64[6:]
            parts = gcs_path.split("/", 1)
            return (
                f"https://storage.googleapis.com/{parts[0]}/{parts[1]}"
                if len(parts) == 2
                else f"https://storage.googleapis.com/{gcs_path}"
            )

        if image_url_or_base64.startswith(("http://", "https://", "data:")):
            return image_url_or_base64

        return f"data:image/png;base64,{image_url_or_base64}"
