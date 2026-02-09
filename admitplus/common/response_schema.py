from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    code: int
    message: str
    data: Optional[T] = None


class OperationSuccessResponse(BaseModel):
    """
    Operation success response model
    Used for operations that don't return data, just success status
    """

    success: bool = True
    message: str = "Operation completed successfully"
