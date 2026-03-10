"""HTTP client for fetching Smogon competitive sets from pkmn.github.io.

Data source: https://pkmn.github.io/smogon/data/sets/
Format: gen{N}{tier}.json — updated daily.

Local cache in data/smogon/ — re-fetches if older than 24 h or force=True.
"""

import json
import logging
import time
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

_BASE_URL = "https://pkmn.github.io/smogon/data/sets"
_CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "smogon"
_MAX_AGE_SECONDS = 24 * 60 * 60  # 24 hours


def _cache_path(generation: int, tier: str) -> Path:
    return _CACHE_DIR / f"gen{generation}{tier}.json"


def _is_cache_fresh(path: Path) -> bool:
    """Return True if the cached file exists and is younger than 24 h."""
    if not path.exists():
        return False
    age = time.time() - path.stat().st_mtime
    return age < _MAX_AGE_SECONDS


def fetch_smogon_sets(
    generation: int,
    tier: str = "ou",
    *,
    force: bool = False,
) -> dict:
    """Fetch Smogon sets for a generation/tier, using local cache.

    Returns the parsed JSON dict: ``{PokemonName: {SetName: {...}, ...}, ...}``.
    Returns an empty dict (and logs a warning) on HTTP errors so the rest
    of the pipeline can continue.
    """
    cache = _cache_path(generation, tier)

    # Return cached data if fresh (unless forced)
    if not force and _is_cache_fresh(cache):
        logger.info("Smogon gen%d%s: using cached %s", generation, tier, cache)
        return json.loads(cache.read_text(encoding="utf-8"))

    # Fetch from remote
    url = f"{_BASE_URL}/gen{generation}{tier}.json"
    logger.info("Smogon gen%d%s: fetching %s", generation, tier, url)

    try:
        resp = httpx.get(url, timeout=30, follow_redirects=True)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("Smogon gen%d%s: fetch failed (%s)", generation, tier, exc)
        # Fall back to stale cache if available
        if cache.exists():
            logger.info("  -> falling back to stale cache")
            return json.loads(cache.read_text(encoding="utf-8"))
        return {}

    data: dict = resp.json()

    # Persist to cache
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    logger.info(
        "Smogon gen%d%s: cached %d Pokemon (%s)",
        generation, tier, len(data), cache,
    )
    return data
