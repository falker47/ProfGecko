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

    print(f"\n=== Fetch complete ===")
    print(f"  Pokemon: {len(pokemon_data)}")
    print(f"  Species: {len(species_data)}")
    print(f"  Evo Chains: {len(evo_chains)}")
    print(f"  Moves: {len(moves_data)}")
    print(f"  Types: {len(types_data)}")
    print(f"  Abilities: {len(abilities_data)}")
    print(f"  Items: {len(items_data)}")
    print(f"  Natures: {len(natures_data)}")

    return {
        "pokemon": pokemon_data,
        "species": species_data,
        "evolution_chains": evo_chains,
        "moves": moves_data,
        "types": types_data,
        "abilities": abilities_data,
        "items": items_data,
        "natures": natures_data,
    }
