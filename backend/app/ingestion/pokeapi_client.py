import asyncio
import json
import logging
from pathlib import Path

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

BASE_URL = "https://pokeapi.co/api/v2"


def _is_retryable(exc: BaseException) -> bool:
    """Retry solo su errori server/rete, non su 404 e altri errori client."""
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500
    return True  # Retry su connection errors, timeouts, etc.


class PokeAPIClient:
    """Async PokeAPI client with disk cache and rate limiting."""

    def __init__(self, cache_dir: str = "data/raw", max_concurrent: int = 20):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=BASE_URL,
            timeout=30.0,
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()

    def _cache_path(self, path: str) -> Path:
        safe_name = path.strip("/").replace("/", "_")
        return self.cache_dir / f"{safe_name}.json"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception(_is_retryable),
    )
    async def _fetch(self, path: str) -> dict:
        assert self._client is not None
        async with self._semaphore:
            resp = await self._client.get(f"/{path}")
            resp.raise_for_status()
            return resp.json()

    async def get(self, path: str) -> dict:
        """GET with local file cache."""
        cache_file = self._cache_path(path)
        if cache_file.exists():
            return json.loads(cache_file.read_text(encoding="utf-8"))

        data = await self._fetch(path)
        cache_file.write_text(
            json.dumps(data, ensure_ascii=False),
            encoding="utf-8",
        )
        return data

    async def get_pokemon(self, pokemon_id: int) -> dict:
        return await self.get(f"pokemon/{pokemon_id}")

    async def get_species(self, pokemon_id: int) -> dict:
        return await self.get(f"pokemon-species/{pokemon_id}")

    async def get_evolution_chain(self, chain_id: int) -> dict:
        return await self.get(f"evolution-chain/{chain_id}")

    async def get_move(self, move_id: int) -> dict:
        return await self.get(f"move/{move_id}")

    async def get_type(self, type_id: int) -> dict:
        return await self.get(f"type/{type_id}")

    async def get_ability(self, ability_id: int) -> dict:
        return await self.get(f"ability/{ability_id}")

    async def get_item(self, item_id: int) -> dict:
        return await self.get(f"item/{item_id}")

    async def get_nature(self, nature_id: int) -> dict:
        return await self.get(f"nature/{nature_id}")

    async def get_generation(self, gen_id: int) -> dict:
        return await self.get(f"generation/{gen_id}")
