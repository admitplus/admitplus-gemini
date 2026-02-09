from typing import Optional, Union, List, Dict, Any
from enum import Enum

from .base import (
    BaseLLMClient,
    ModelProvider,
    LLMRequest,
    LLMResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    Message,
)
from .util import LLMConfigError
from .openai_client import OpenAIClient
from .gemini_client import GeminiClient


class LLMFactory:
    _clients: Dict[ModelProvider, BaseLLMClient] = {}
    _default_provider: ModelProvider = ModelProvider.OPENAI

    @classmethod
    def get_client(
        cls, provider: Optional[Union[ModelProvider, str]] = None, **kwargs
    ) -> BaseLLMClient:
        if provider is None:
            provider = cls._default_provider
        elif isinstance(provider, str):
            try:
                provider = ModelProvider(provider.lower())
            except ValueError:
                raise LLMConfigError(f"Unsupported provider: {provider}")

        if provider in cls._clients and not kwargs:
            return cls._clients[provider]

        if provider == ModelProvider.OPENAI:
            client = OpenAIClient.get_instance(**kwargs)
        elif provider == ModelProvider.GEMINI:
            client = GeminiClient.get_instance(**kwargs)
        else:
            raise LLMConfigError(f"Unsupported provider: {provider}")

        cls._clients[provider] = client
        return client

    @classmethod
    def set_default_provider(cls, provider: Union[ModelProvider, str]):
        if isinstance(provider, str):
            provider = ModelProvider(provider.lower())
        cls._default_provider = provider

    @classmethod
    def clear_cache(cls):
        cls._clients.clear()


async def generate_text(
    messages: Union[List[Dict[str, str]], List[Message]],
    provider: Optional[Union[ModelProvider, str]] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    **kwargs,
) -> LLMResponse:
    client = LLMFactory.get_client(provider)

    request = LLMRequest.from_messages(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        extra_params=kwargs,
    )

    return await client.generate_text(request)


async def generate_embedding(
    text: Union[str, List[str]],
    provider: Optional[Union[ModelProvider, str]] = None,
    model: Optional[str] = None,
    **kwargs,
) -> EmbeddingResponse:
    client = LLMFactory.get_client(provider)

    request = EmbeddingRequest(text=text, model=model, extra_params=kwargs)

    return await client.generate_embedding(request)


async def extract_text_from_image(
    image_url_or_base64: str,
    provider: Optional[Union[ModelProvider, str]] = None,
    model: Optional[str] = None,
    instruction: str = "Extract all text from this image.",
) -> LLMResponse:
    client = LLMFactory.get_client(provider or ModelProvider.OPENAI)

    if not isinstance(client, OpenAIClient):
        raise LLMConfigError("Image extraction only supported by OpenAI")

    return await client.extract_text_from_image(
        image_url_or_base64=image_url_or_base64, model=model, instruction=instruction
    )


openai_generate_text = lambda *args, **kwargs: generate_text(
    *args, provider=ModelProvider.OPENAI, **kwargs
)
openai_embedding = lambda *args, **kwargs: generate_embedding(
    *args, provider=ModelProvider.OPENAI, **kwargs
)
openai_extract_image_text = extract_text_from_image

gemini_generate_text = lambda *args, **kwargs: generate_text(
    *args, provider=ModelProvider.GEMINI, **kwargs
)
gemini_embedding = lambda *args, **kwargs: generate_embedding(
    *args, provider=ModelProvider.GEMINI, **kwargs
)
