from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union, Any
from enum import Enum
import logging


class ModelProvider(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"


class ModelCapability(str, Enum):
    TEXT_GENERATION = "text_generation"
    EMBEDDING = "embedding"
    VISION = "vision"
    IMAGE_GENERATION = "image_generation"


@dataclass
class Message:
    role: str
    content: str

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "Message":
        return cls(role=data.get("role", "user"), content=data.get("content", ""))


@dataclass
class LLMRequest:
    messages: List[Message]
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    extra_params: Dict[str, Any] = field(default_factory=dict)

    def to_messages_dict(self) -> List[Dict[str, str]]:
        return [msg.to_dict() for msg in self.messages]

    @classmethod
    def from_messages(
        cls, messages: Union[List[Dict[str, str]], List[Message]], **kwargs
    ) -> "LLMRequest":
        if not messages:
            raise ValueError("Messages cannot be empty")

        msg_objects = []
        for msg in messages:
            if isinstance(msg, Message):
                msg_objects.append(msg)
            elif isinstance(msg, dict):
                msg_objects.append(Message.from_dict(msg))
            else:
                raise TypeError(f"Unsupported message type: {type(msg)}")

        return cls(messages=msg_objects, **kwargs)


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: ModelProvider
    usage: Optional[Dict[str, int]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.content


@dataclass
class EmbeddingRequest:
    text: Union[str, List[str]]
    model: Optional[str] = None
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EmbeddingResponse:
    embeddings: Union[List[float], List[List[float]]]
    model: str
    provider: ModelProvider
    dimensions: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseLLMClient(ABC):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.logger = logging.getLogger(self.__class__.__name__)

    @property
    @abstractmethod
    def provider(self) -> ModelProvider:
        pass

    @property
    @abstractmethod
    def supported_capabilities(self) -> List[ModelCapability]:
        pass

    @abstractmethod
    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        pass

    @abstractmethod
    async def generate_embedding(self, request: EmbeddingRequest) -> EmbeddingResponse:
        pass

    def supports_capability(self, capability: ModelCapability) -> bool:
        return capability in self.supported_capabilities

    def _validate_capability(self, capability: ModelCapability):
        if not self.supports_capability(capability):
            raise NotImplementedError(
                f"{self.provider.value} does not support {capability.value}"
            )
