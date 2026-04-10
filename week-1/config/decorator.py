import inspect
import functools
import logging
import time
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar

import httpx
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


def log_and_time_it(func: Callable[P, R]) -> Callable[P, R]:
    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            start_time = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.exception("Error in %s", func.__qualname__, str(e))
                raise
            finally:
                elapsed = time.perf_counter() - start_time
                logger.info("Finished %s in %.4f seconds", func.__qualname__, elapsed)

        return async_wrapper  # type: ignore[return-value]

    @functools.wraps(func)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
        start_time = time.perf_counter()
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception("Error in %s", func.__qualname__, str(e))
            raise
        finally:
            elapsed = time.perf_counter() - start_time
            logger.info("Finished %s in %.4f seconds", func.__qualname__, elapsed)

    return sync_wrapper 


retry_call = retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential_jitter(initial=1, max=10, jitter=2),
    retry=retry_if_exception_type(
        (httpx.ConnectError, httpx.TimeoutException)
    ),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)