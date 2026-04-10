import asyncio
import httpx
import logging
from typing import Any
# Assuming these are your custom decorators
from config.decorator import retry_call, log_and_time_it

logger = logging.getLogger(__name__)

class Fetch:
    def __init__(self, request: list[dict[str, Any]]):
        self.request = request
        # Physical Resource Management
        self.limits = httpx.Limits(max_connections=100, max_keepalive_connections=20)
        self.timeout = httpx.Timeout(connect=2.0, read=60.0, write=5.0, pool=10.0)
        self.client = httpx.AsyncClient(limits=self.limits, timeout=self.timeout)
        
        # Logical Resource Management (Rate Limiting)
        self.semaphore = asyncio.Semaphore(5)

    
    @retry_call
    async def _internal_fetch(self, data: dict[str, Any]) -> dict[str, Any]:
        """Logic for a single request with its own semaphore and retry."""

        url = data['url']
        params = data['params']

        async with self.semaphore:
            response = await self.client.get(url, params=params)

            response.raise_for_status()
            return {
                "source": data["source"],
                "q":data["params"]["q"],
                "payload": response.json(),
            }

    @log_and_time_it
    async def fetch(self) -> list[dict[str, Any]]:
        tasks = [asyncio.create_task(self._internal_fetch(r)) for r in self.request]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        output: list[dict[str, Any]] = []
        for item in results:
            if isinstance(item, Exception):
                logger.exception("Request failed", exc_info=item)
                continue
            output.append(item)

        return output

    async def close(self) -> None:
        await self.client.aclose()
            