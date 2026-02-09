import logging
from typing import Optional, Dict, Any, List

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


class GeminiClient(BaseLLMClient):
    _instance: Optional["GeminiClient"] = None
    _model_cache: Dict[str, Any] = {}

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_text_model: str = "gemini-2.0-flash-exp",
        default_embed_model: str = "models/text-embedding-004",
    ):
        super().__init__(api_key)
        try:
            import google.generativeai as genai  # type: ignore
        except ImportError:
            raise ImportError(
                "google-generativeai library not found. "
                "Please install it with: pip install google-generativeai"
            )

        try:
            from admitplus.config import settings

            self.api_key = api_key or settings.GEMINI_API_KEY
            self.default_text_model = (
                default_text_model or settings.GEMINI_TEXT_MODEL_DEFAULT
            )
            self.default_embed_model = (
                default_embed_model or settings.GEMINI_EMBED_MODEL_DEFAULT
            )
        except ImportError:
            self.api_key = api_key
            self.default_text_model = default_text_model
            self.default_embed_model = default_embed_model

        validate_api_key(self.api_key, "Gemini")

        genai.configure(api_key=self.api_key)
        self.genai = genai
        self.logger.info("[GeminiClient] Initialized successfully")

    @classmethod
    def get_instance(cls, **kwargs) -> "GeminiClient":
        if cls._instance is None:
            cls._instance = cls(**kwargs)
        return cls._instance

    @property
    def provider(self) -> ModelProvider:
        return ModelProvider.GEMINI

    @property
    def supported_capabilities(self) -> List[ModelCapability]:
        return [
            ModelCapability.TEXT_GENERATION,
            ModelCapability.EMBEDDING,
        ]

    def _get_model(self, model_name: str) -> Any:
        if model_name not in GeminiClient._model_cache:
            GeminiClient._model_cache[model_name] = self.genai.GenerativeModel(
                model_name
            )
        return GeminiClient._model_cache[model_name]

    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        prompt_parts = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")

            if role == "system":
                prompt_parts.append(f"[System Instructions]: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")

        return "\n\n".join(prompt_parts)

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
        validate_model(model, "Gemini")

        gemini_model = self._get_model(model)

        messages_dict = request.to_messages_dict()
        prompt = self._convert_messages_to_prompt(messages_dict)

        generation_config = self.genai.types.GenerationConfig(
            temperature=request.temperature,
            max_output_tokens=request.max_tokens,
            **request.extra_params,
        )

        response = await gemini_model.generate_content_async(
            prompt, generation_config=generation_config
        )

        content = response.text
        validate_not_empty(content, "response content")

        usage = None
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = {
                "prompt_tokens": getattr(
                    response.usage_metadata, "prompt_token_count", 0
                ),
                "completion_tokens": getattr(
                    response.usage_metadata, "candidates_token_count", 0
                ),
                "total_tokens": getattr(
                    response.usage_metadata, "total_token_count", 0
                ),
            }

        return LLMResponse(
            content=content,
            model=model,
            provider=self.provider,
            usage=usage,
            metadata={
                "finish_reason": getattr(response.candidates[0], "finish_reason", None)
                if response.candidates
                else None,
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
        validate_model(model, "Gemini")

        if isinstance(request.text, list):
            # 批量处理
            embeddings = []
            for text in request.text:
                result = await self.genai.embed_content_async(
                    model=model,
                    content=text,
                    **request.extra_params,
                )
                embedding = result.get("embedding", [])
                validate_not_empty(embedding, "embedding")
                embeddings.append(embedding)

            dimensions = len(embeddings[0]) if embeddings else 0
        else:
            result = await self.genai.embed_content_async(
                model=model,
                content=request.text,
                **request.extra_params,
            )
            embeddings = result.get("embedding", [])
            validate_not_empty(embeddings, "embedding")
            dimensions = len(embeddings) if embeddings else 0

        return EmbeddingResponse(
            embeddings=embeddings,
            model=model,
            provider=self.provider,
            dimensions=dimensions,
            metadata={},
        )
