import asyncio
import logging

from tqdm import tqdm

from app.ingestion.pokeapi_client import PokeAPIClient

logger = logging.getLogger(__name__)


async def _fetch_batch(client: PokeAPIClient, coro_fn, ids: list[int], desc: str):
    """Fetch a batch of items with progress bar. Skips 404s gracefully."""
    results = {}
    tasks = [coro_fn(i) for i in ids]
    skipped = 0

    with tqdm(total=len(ids), desc=desc) as pbar:
        for coro in asyncio.as_completed(tasks):
            try:
                data = await coro
                item_id = data.get("id", None)
                if item_id is not None:
                    results[item_id] = data
            except Exception as e:
                skipped += 1
                logger.debug("Skipped: %s", e)
            pbar.update(1)

    if skipped:
        logger.info(
            "%s: fetched %d, skipped %d (not found/errors)",
            desc, len(results), skipped,
        )
    return results


async def fetch_all_pokemon(client: PokeAPIClient, max_id: int = 1025):
    """Fetch base Pokemon data for IDs 1..max_id."""
    ids = list(range(1, max_id + 1))
    return await _fetch_batch(client, client.get_pokemon, ids, "Pokemon")


async def fetch_all_species(client: PokeAPIClient, max_id: int = 1025):
    """Fetch species data (flavor text, evolution chain, etc.)."""
    ids = list(range(1, max_id + 1))
    return await _fetch_batch(client, client.get_species, ids, "Species")


async def fetch_all_evolution_chains(
    client: PokeAPIClient,
    species_data: dict[int, dict],
):
    """Fetch unique evolution chains referenced by species."""
    chain_ids: set[int] = set()
    for sp in species_data.values():
        url = sp.get("evolution_chain", {}).get("url", "")
        if url:
            # Extract ID from URL like ".../evolution-chain/67/"
            chain_id = int(url.rstrip("/").split("/")[-1])
            chain_ids.add(chain_id)

    ids = sorted(chain_ids)
    return await _fetch_batch(client, client.get_evolution_chain, ids, "Evo Chains")


async def fetch_all_moves(client: PokeAPIClient, max_id: int = 919):
    """Fetch all move data (with past_values)."""
    ids = list(range(1, max_id + 1))
    return await _fetch_batch(client, client.get_move, ids, "Moves")


async def fetch_all_types(client: PokeAPIClient):
    """Fetch all 18 types (with past_damage_relations)."""
    ids = list(range(1, 19))
    return await _fetch_batch(client, client.get_type, ids, "Types")


async def fetch_all_abilities(client: PokeAPIClient, max_id: int = 307):
    """Fetch all abilities."""
    ids = list(range(1, max_id + 1))
    return await _fetch_batch(client, client.get_ability, ids, "Abilities")


async def fetch_all_items(client: PokeAPIClient, max_id: int = 2180):
    """Fetch all items."""
    ids = list(range(1, max_id + 1))
    return await _fetch_batch(client, client.get_item, ids, "Items")


async def fetch_all_natures(client: PokeAPIClient):
    """Fetch all 25 natures."""
    ids = list(range(1, 26))
    return await _fetch_batch(client, client.get_nature, ids, "Natures")


async def fetch_regional_variants(
    client: PokeAPIClient,
    species_data: dict[int, dict],
) -> dict[str, dict]:
    """Fetch Pokemon data for regional variants (Alola, Galar, Hisui, Paldea).

    Scans species data for non-default varieties with regional suffixes.
    Returns dict keyed by variant name (e.g. 'raichu-alola').
    """
    REGIONAL_SUFFIXES = ("-alola", "-galar", "-hisui", "-paldea")
    variant_names: list[str] = []

    for sp in species_data.values():
        for v in sp.get("varieties", []):
            if v.get("is_default"):
                continue
            name = v["pokemon"]["name"]
            if any(name.endswith(s) for s in REGIONAL_SUFFIXES):
                variant_names.append(name)

    results: dict[str, dict] = {}
    skipped = 0
    with tqdm(total=len(variant_names), desc="Regional Variants") as pbar:
        for name in variant_names:
            try:
                data = await client.get_pokemon_by_name(name)
                results[name] = data
            except Exception as e:
                skipped += 1
                logger.debug("Skipped variant %s: %s", name, e)
            pbar.update(1)

    if skipped:
        logger.info(
            "Regional variants: fetched %d, skipped %d",
            len(results), skipped,
        )
    return results


async def fetch_all_encounters(
    client: PokeAPIClient, max_id: int = 1025,
) -> dict[int, list]:
    """Fetch encounter data for all Pokemon. Returns {pokemon_id: encounter_list}.

    The encounter endpoint returns a list (not a dict with 'id'), so we
    cannot use _fetch_batch directly.
    """
    results: dict[int, list] = {}
    skipped = 0
    ids = list(range(1, max_id + 1))

    with tqdm(total=len(ids), desc="Encounters") as pbar:
        # Process in chunks to limit concurrency
        chunk_size = 50
        for start in range(0, len(ids), chunk_size):
            chunk = ids[start : start + chunk_size]
            tasks = {pid: client.get_encounters(pid) for pid in chunk}
            for pid, coro in tasks.items():
                try:
                    data = await coro
                    # Only store if there are encounters
                    if data:
                        results[pid] = data
                except Exception as e:
                    skipped += 1
                    logger.debug("Skipped encounters for %d: %s", pid, e)
                pbar.update(1)

    if skipped:
        logger.info(
            "Encounters: fetched %d (non-empty), skipped %d",
            len(results), skipped,
        )
    return results


async def fetch_all_data(client: PokeAPIClient, max_pokemon_id: int = 1025):
    """Fetch all data from PokeAPI."""
    print("=== Fetching all Pokemon data from PokeAPI ===\n")

    # Phase 1: Pokemon + Species
    pokemon_data = await fetch_all_pokemon(client, max_pokemon_id)
    species_data = await fetch_all_species(client, max_pokemon_id)

    # Phase 2: Evolution chains
    evo_chains = await fetch_all_evolution_chains(client, species_data)

    # Phase 3: Moves
    moves_data = await fetch_all_moves(client)

    # Phase 4: Types
    types_data = await fetch_all_types(client)

    # Phase 5: Abilities
    abilities_data = await fetch_all_abilities(client)

    # Phase 6: Items
    items_data = await fetch_all_items(client)

    # Phase 7: Natures
    natures_data = await fetch_all_natures(client)

    # Phase 8: Regional variants (Alola, Galar, Hisui, Paldea)
    regional_data = await fetch_regional_variants(client, species_data)

    # Phase 9: Encounters (location/version data)
    encounters_data = await fetch_all_encounters(client, max_pokemon_id)

    print("\n=== Fetch complete ===")
    print(f"  Pokemon: {len(pokemon_data)}")
    print(f"  Species: {len(species_data)}")
    print(f"  Evo Chains: {len(evo_chains)}")
    print(f"  Moves: {len(moves_data)}")
    print(f"  Types: {len(types_data)}")
    print(f"  Abilities: {len(abilities_data)}")
    print(f"  Items: {len(items_data)}")
    print(f"  Natures: {len(natures_data)}")
    print(f"  Regional variants: {len(regional_data)}")
    print(f"  Encounters: {len(encounters_data)} (non-empty)")

    return {
        "pokemon": pokemon_data,
        "species": species_data,
        "evolution_chains": evo_chains,
        "moves": moves_data,
        "types": types_data,
        "abilities": abilities_data,
        "items": items_data,
        "natures": natures_data,
        "regional_variants": regional_data,
        "encounters": encounters_data,
    }
