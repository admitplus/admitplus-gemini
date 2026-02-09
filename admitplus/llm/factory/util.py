import asyncio
import logging
import time
from functools import wraps
from typing import Callable, Optional, Type, Any
from contextlib import asynccontextmanager


class LLMError(Exception):
    pass


class LLMAPIError(LLMError):
    pass


class LLMConfigError(LLMError):
    pass


class LLMValidationError(LLMError):
    pass


class LLMTimeoutError(LLMError):
    pass


def with_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        break

                    logger = None
                    if args and hasattr(args[0], "logger"):
                        logger = args[0].logger
                    else:
                        logger = logging.getLogger(func.__module__)

                    logger.warning(
                        f"[Retry {attempt + 1}/{max_retries}] {func.__name__} failed: {str(e)}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                    delay *= backoff_factor

            raise LLMAPIError(f"Failed after {max_retries} retries") from last_exception

        return wrapper

    return decorator


def with_timeout(timeout_seconds: float = 30.0):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs), timeout=timeout_seconds
                )
            except asyncio.TimeoutError as e:
                raise LLMTimeoutError(
                    f"{func.__name__} timed out after {timeout_seconds}s"
                ) from e

        return wrapper

    return decorator


def with_logging(log_request: bool = True, log_response: bool = True):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取 logger
            logger = None
            if args and hasattr(args[0], "logger"):
                logger = args[0].logger
            else:
                logger = logging.getLogger(func.__module__)

            if log_request:
                logger.info(f"[{func.__name__}] Starting request")
                logger.debug(f"[{func.__name__}] Args: {args[1:]}, Kwargs: {kwargs}")

            start_time = time.time()

            try:
                result = await func(*args, **kwargs)

                elapsed = time.time() - start_time
                if log_response:
                    logger.info(
                        f"[{func.__name__}] Completed successfully in {elapsed:.2f}s"
                    )
                    logger.debug(f"[{func.__name__}] Result: {result}")

                return result

            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    f"[{func.__name__}] Failed after {elapsed:.2f}s: {str(e)}",
                    exc_info=True,
                )
                raise

        return wrapper

    return decorator


def with_error_handling(error_class: Type[Exception] = LLMAPIError):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except error_class:
                raise
            except Exception as e:
                raise error_class(f"{func.__name__} error: {str(e)}") from e

        return wrapper

    return decorator


@asynccontextmanager
async def measure_time(operation_name: str, logger: Optional[logging.Logger] = None):
    if logger is None:
        logger = logging.getLogger(__name__)

    logger.info(f"[{operation_name}] Starting...")
    start_time = time.time()

    try:
        yield
    finally:
        elapsed = time.time() - start_time
        logger.info(f"[{operation_name}] Completed in {elapsed:.2f}s")


def validate_not_empty(value: Any, field_name: str):
    if not value:
        raise LLMValidationError(f"{field_name} cannot be empty")


def validate_api_key(api_key: Optional[str], provider: str):
    if not api_key:
        raise LLMConfigError(f"{provider} API key not configured")


def validate_model(model: Optional[str], provider: str):
    if not model:
        raise LLMConfigError(f"{provider} model not configured")
