"""Transform raw PokeAPI JSON into per-generation LangChain Documents."""

from langchain_core.documents import Document

from app.core.generation_mapper import (
    MAX_POKEMON_PER_GEN,
    VERSION_GROUP_TO_GEN,
)

# --- Helpers ---


def _get_localized(entries: list[dict], lang: str, key: str = "name") -> str:
    """Extract a localized string from a list of name/language entries."""
    for entry in entries:
        if entry.get("language", {}).get("name") == lang:
            return entry.get(key, entry.get("name", ""))
    return ""


def _get_flavor_text(entries: list[dict], lang: str) -> str:
    """Get the most recent flavor text in the given language."""
    texts = [
        e["flavor_text"].replace("\n", " ").replace("\f", " ")
        for e in entries
        if e.get("language", {}).get("name") == lang
    ]
    return texts[-1] if texts else ""


def _get_stat(stats: list[dict], stat_name: str) -> int:
    for s in stats:
        if s["stat"]["name"] == stat_name:
            return s["base_stat"]
    return 0


def _parse_evolution_chain(chain: dict) -> list[str]:
    """Recursively extract species names from an evolution chain."""
    names = [chain["species"]["name"]]
    for evo in chain.get("evolves_to", []):
        names.extend(_parse_evolution_chain(evo))
    return names


def _get_type_name_it(type_data: dict) -> str:
    return _get_localized(type_data.get("names", []), "it")


def _get_generation_for_move_version(version_group_name: str) -> int | None:
    return VERSION_GROUP_TO_GEN.get(version_group_name)


# --- Type Effectiveness Calculation ---


def _build_type_effectiveness_table(
    types_data: dict[int, dict],
    generation: int,
) -> dict[str, dict[str, float]]:
    """Build a lookup: attacking_type -> defending_type -> multiplier.

    Uses generation-aware damage relations.
    """
    table: dict[str, dict[str, float]] = {}

    # Get all type names that exist in this generation
    existing_types: set[str] = set()
    for type_data in types_data.values():
        gen_introduced = int(
            type_data.get("generation", {})
            .get("url", "/0/")
            .rstrip("/")
            .split("/")[-1]
        )
        if gen_introduced <= generation:
            existing_types.add(type_data["name"])

    for type_data in types_data.values():
        atk_type = type_data["name"]
        if atk_type not in existing_types:
            continue

        relations = _reconstruct_type_matchups(type_data, generation)

        matchups: dict[str, float] = {}
        # Default everything to x1
        for def_type in existing_types:
            matchups[def_type] = 1.0

        for entry in relations.get("double_damage_to", []):
            if entry["name"] in existing_types:
                matchups[entry["name"]] = 2.0
        for entry in relations.get("half_damage_to", []):
            if entry["name"] in existing_types:
                matchups[entry["name"]] = 0.5
        for entry in relations.get("no_damage_to", []):
            if entry["name"] in existing_types:
                matchups[entry["name"]] = 0.0

        table[atk_type] = matchups

    return table


def _calculate_type_effectiveness(
    defending_types: list[str],
    type_table: dict[str, dict[str, float]],
    type_name_it: dict[str, str],
) -> str:
    """Calculate combined dual-type effectiveness and return formatted Italian text.

    For each attacking type, multiplies the individual matchups against
    each defending type to get the combined multiplier.
    """
    combined: dict[str, float] = {}

    for atk_type in type_table:
        multiplier = 1.0
        for def_type in defending_types:
            multiplier *= type_table.get(atk_type, {}).get(def_type, 1.0)
        combined[atk_type] = multiplier

    # Group by multiplier
    groups: dict[float, list[str]] = {}
    for atk_type, mult in combined.items():
        if mult == 1.0:
            continue  # Skip neutral — not interesting
        it_name = type_name_it.get(atk_type, atk_type)
        groups.setdefault(mult, []).append(it_name)

    lines = []

    # Weaknesses (descending)
    for mult in sorted([m for m in groups if m > 1.0], reverse=True):
        types_str = ", ".join(sorted(groups[mult]))
        lines.append(f"Debolezze (x{mult:g}): {types_str}")

    # Resistances (ascending)
    for mult in sorted([m for m in groups if 0 < m < 1.0]):
        types_str = ", ".join(sorted(groups[mult]))
        lines.append(f"Resistenze (x{mult:g}): {types_str}")

    # Immunities
    if 0.0 in groups:
        types_str = ", ".join(sorted(groups[0.0]))
        lines.append(f"Immunita (x0): {types_str}")

    return "\n".join(lines) if lines else "Nessuna debolezza o resistenza particolare"


# --- Pokemon Documents ---


def build_pokemon_documents(
    pokemon_data: dict[int, dict],
    species_data: dict[int, dict],
    evo_chains: dict[int, dict],
    all_types: dict[int, dict],
    generation: int,
    type_table: dict[str, dict[str, float]] | None = None,
) -> list[Document]:
    """Build one Document per Pokemon for the given generation."""
    max_id = MAX_POKEMON_PER_GEN.get(generation, 1025)
    docs = []

    # Build type name lookup (EN -> IT)
    type_name_it: dict[str, str] = {}
    for t in all_types.values():
        en_name = t["name"]
        it_name = _get_localized(t.get("names", []), "it") or en_name
        type_name_it[en_name] = it_name

    # Build type effectiveness table if not provided
    if type_table is None:
        type_table = _build_type_effectiveness_table(all_types, generation)

    for pid in range(1, max_id + 1):
        poke = pokemon_data.get(pid)
        spec = species_data.get(pid)
        if not poke or not spec:
            continue

        # Names
        name_it = _get_localized(spec.get("names", []), "it") or poke["name"]
        name_en = poke["name"].capitalize()

        # Types
        types_en = [t["type"]["name"] for t in poke["types"]]
        types_it = [type_name_it.get(t, t) for t in types_en]

        # Stats
        hp = _get_stat(poke["stats"], "hp")
        atk = _get_stat(poke["stats"], "attack")
        defense = _get_stat(poke["stats"], "defense")
        sp_atk = _get_stat(poke["stats"], "special-attack")
        sp_def = _get_stat(poke["stats"], "special-defense")
        speed = _get_stat(poke["stats"], "speed")
        bst = hp + atk + defense + sp_atk + sp_def + speed

        # Abilities
        abilities = []
        hidden_ability = None
        for a in poke.get("abilities", []):
            ab_name = a["ability"]["name"].replace("-", " ").title()
            if a.get("is_hidden"):
                hidden_ability = ab_name
            else:
                abilities.append(ab_name)

        # Generation introduced
        gen_introduced = int(
            spec.get("generation", {})
            .get("url", "/0/")
            .rstrip("/")
            .split("/")[-1]
        )

        # Flavor text
        flavor = _get_flavor_text(spec.get("flavor_text_entries", []), "it")
        if not flavor:
            flavor = _get_flavor_text(spec.get("flavor_text_entries", []), "en")

        # Genus
        genus = _get_localized(spec.get("genera", []), "it", key="genus")

        # Evolution chain
        evo_chain_url = spec.get("evolution_chain", {}).get("url", "")
        evo_text = ""
        if evo_chain_url:
            chain_id = int(evo_chain_url.rstrip("/").split("/")[-1])
            chain_data = evo_chains.get(chain_id)
            if chain_data:
                evo_names = _parse_evolution_chain(chain_data["chain"])
                evo_text = " -> ".join(evo_names)

        # Learnset for this generation
        learnset_moves = []
        for m in poke.get("moves", []):
            for vgd in m.get("version_group_details", []):
                vg_name = vgd["version_group"]["name"]
                vg_gen = _get_generation_for_move_version(vg_name)
                if vg_gen == generation:
                    method = vgd["move_learn_method"]["name"]
                    level = vgd.get("level_learned_at", 0)
                    move_name = m["move"]["name"].replace("-", " ").title()
                    if method == "level-up" and level > 0:
                        learnset_moves.append(f"{move_name} (Lv.{level})")
                    elif method == "machine":
                        learnset_moves.append(f"{move_name} (MT)")
                    break

        # Height / Weight
        height_m = poke["height"] / 10
        weight_kg = poke["weight"] / 10

        is_legendary = spec.get("is_legendary", False)
        is_mythical = spec.get("is_mythical", False)

        # Calculate dual-type effectiveness
        type_eff_text = _calculate_type_effectiveness(
            types_en, type_table, type_name_it,
        )

        page_content = f"""\
Nome: {name_it} (#{pid})
Nome inglese: {name_en}
Categoria: {genus}
Tipi: {', '.join(types_it)}
Generazione di introduzione: {gen_introduced}

Statistiche base:
- HP: {hp}
- Attacco: {atk}
- Difesa: {defense}
- Attacco Speciale: {sp_atk}
- Difesa Speciale: {sp_def}
- Velocita: {speed}
- Totale: {bst}

Altezza: {height_m} m
Peso: {weight_kg} kg

Efficacia tipi (difesa):
{type_eff_text}

Abilita: {', '.join(abilities) if abilities else 'Nessuna'}
Abilita nascosta: {hidden_ability or 'Nessuna'}

Catena evolutiva: {evo_text or 'Nessuna evoluzione'}

Descrizione Pokedex:
{flavor}

Mosse apprendibili (Generazione {generation}):
{', '.join(learnset_moves[:30]) if learnset_moves else 'Dati non disponibili'}

Leggendario: {'Si' if is_legendary else 'No'}
Misterioso: {'Si' if is_mythical else 'No'}"""

        metadata = {
            "entity_type": "pokemon",
            "pokemon_id": pid,
            "name_en": name_en.lower(),
            "name_it": name_it.lower(),
            "types": types_en,
            "generation": generation,
            "gen_introduced": gen_introduced,
            "is_legendary": is_legendary,
            "is_mythical": is_mythical,
            "bst": bst,
        }

        docs.append(Document(page_content=page_content, metadata=metadata))

    return docs


# --- Move Documents ---


def _reconstruct_move_stats(move: dict, target_gen: int) -> dict:
    """Reconstruct a move's stats as they were in a specific generation.

    PokeAPI's past_values lists changes in REVERSE chronological order.
    Each entry says: "before version group X, this move had these values."
    """
    current = {
        "power": move.get("power"),
        "accuracy": move.get("accuracy"),
        "pp": move.get("pp"),
        "type": move.get("type", {}).get("name"),
        "effect": "",
    }
    # Effect entries
    for ee in move.get("effect_entries", []):
        if ee.get("language", {}).get("name") == "en":
            current["effect"] = ee.get("short_effect", "")
            break

    # Apply past_values: each entry means "before this version group,
    # the move had these values"
    past = move.get("past_values", [])
    for pv in past:
        vg_name = pv.get("version_group", {}).get("name", "")
        change_gen = VERSION_GROUP_TO_GEN.get(vg_name, 99)

        if target_gen < change_gen:
            # We're looking at a gen before this change, so apply the old values
            if pv.get("power") is not None:
                current["power"] = pv["power"]
            if pv.get("accuracy") is not None:
                current["accuracy"] = pv["accuracy"]
            if pv.get("pp") is not None:
                current["pp"] = pv["pp"]
            if pv.get("type") is not None:
                current["type"] = pv["type"]["name"]

    return current


def build_move_documents(
    moves_data: dict[int, dict],
    all_types: dict[int, dict],
    generation: int,
) -> list[Document]:
    """Build one Document per move for the given generation."""
    type_name_it: dict[str, str] = {}
    for t in all_types.values():
        en_name = t["name"]
        it_name = _get_localized(t.get("names", []), "it") or en_name
        type_name_it[en_name] = it_name

    docs = []

    for mid, move in moves_data.items():
        # Check if this move existed in this generation
        gen_introduced = int(
            move.get("generation", {})
            .get("url", "/0/")
            .rstrip("/")
            .split("/")[-1]
        )
        if gen_introduced > generation:
            continue

        stats = _reconstruct_move_stats(move, generation)

        name_en = move["name"].replace("-", " ").title()
        name_it = _get_localized(move.get("names", []), "it") or name_en
        type_en = stats["type"] or "normal"
        type_it = type_name_it.get(type_en, type_en)

        damage_class = move.get("damage_class", {}).get("name", "status")
        damage_class_it = {
            "physical": "Fisico",
            "special": "Speciale",
            "status": "Stato",
        }.get(damage_class, damage_class)

        power_str = str(stats["power"]) if stats["power"] else "-"
        accuracy_str = f"{stats['accuracy']}%" if stats["accuracy"] else "-"
        pp_str = str(stats["pp"]) if stats["pp"] else "-"

        page_content = f"""\
Mossa: {name_it}
Nome inglese: {name_en}
Tipo: {type_it}
Categoria: {damage_class_it}
Potenza: {power_str}
Precisione: {accuracy_str}
PP: {pp_str}
Effetto: {stats['effect']}"""

        metadata = {
            "entity_type": "move",
            "move_id": mid,
            "name_en": name_en.lower(),
            "name_it": name_it.lower(),
            "type": type_en,
            "generation": generation,
            "damage_class": damage_class,
        }

        docs.append(Document(page_content=page_content, metadata=metadata))

    return docs


# --- Type Matchup Documents ---


def _reconstruct_type_matchups(type_data: dict, target_gen: int) -> dict:
    """Reconstruct type damage relations for a specific generation."""
    current = type_data.get("damage_relations", {})

    for pdr in type_data.get("past_damage_relations", []):
        vg_name = pdr.get("generation", {}).get("name", "")
        # past_damage_relations uses generation name, not version group
        gen_num = {
            "generation-i": 1, "generation-ii": 2, "generation-iii": 3,
            "generation-iv": 4, "generation-v": 5, "generation-vi": 6,
            "generation-vii": 7, "generation-viii": 8, "generation-ix": 9,
        }.get(vg_name, 99)

        if target_gen <= gen_num:
            current = pdr.get("damage_relations", current)

    return current


def build_type_documents(
    types_data: dict[int, dict],
    generation: int,
) -> list[Document]:
    """Build one Document per type for the given generation."""
    type_name_it: dict[str, str] = {}
    for t in types_data.values():
        en_name = t["name"]
        it_name = _get_localized(t.get("names", []), "it") or en_name
        type_name_it[en_name] = it_name

    docs = []

    for tid, type_data in types_data.items():
        # Skip fairy before gen 6
        gen_introduced = int(
            type_data.get("generation", {})
            .get("url", "/0/")
            .rstrip("/")
            .split("/")[-1]
        )
        if gen_introduced > generation:
            continue

        name_en = type_data["name"]
        name_it = type_name_it.get(name_en, name_en)
        relations = _reconstruct_type_matchups(type_data, generation)

        def names_it(rel_list):
            return [type_name_it.get(r["name"], r["name"]) for r in rel_list]

        super_eff = names_it(relations.get("double_damage_to", []))
        not_very = names_it(relations.get("half_damage_to", []))
        no_damage_to = names_it(relations.get("no_damage_to", []))
        weak_to = names_it(relations.get("double_damage_from", []))
        resists = names_it(relations.get("half_damage_from", []))
        immune_to = names_it(relations.get("no_damage_from", []))

        page_content = f"""\
Tipo: {name_it}

Attacco - Super efficace (x2) contro: {', '.join(super_eff) or 'Nessuno'}
Attacco - Poco efficace (x0.5) contro: {', '.join(not_very) or 'Nessuno'}
Attacco - Nessun effetto (x0) su: {', '.join(no_damage_to) or 'Nessuno'}

Difesa - Debole (x2) a: {', '.join(weak_to) or 'Nessuno'}
Difesa - Resiste (x0.5) a: {', '.join(resists) or 'Nessuno'}
Difesa - Immune (x0) a: {', '.join(immune_to) or 'Nessuno'}

Nota: per Pokemon doppio tipo, moltiplicare i fattori di ciascun tipo."""

        metadata = {
            "entity_type": "type",
            "type_id": tid,
            "name_en": name_en,
            "name_it": name_it.lower(),
            "generation": generation,
        }

        docs.append(Document(page_content=page_content, metadata=metadata))

    return docs


# --- Ability Documents ---


def build_ability_documents(
    abilities_data: dict[int, dict],
    generation: int,
) -> list[Document]:
    """Build one Document per ability for the given generation."""
    docs = []

    for aid, ability in abilities_data.items():
        gen_introduced = int(
            ability.get("generation", {})
            .get("url", "/0/")
            .rstrip("/")
            .split("/")[-1]
        )
        if gen_introduced > generation:
            continue

        name_en = ability["name"].replace("-", " ").title()
        name_it = _get_localized(ability.get("names", []), "it") or name_en

        effect = ""
        for ee in ability.get("effect_entries", []):
            if ee.get("language", {}).get("name") == "it":
                effect = ee.get("short_effect", ee.get("effect", ""))
                break
        if not effect:
            for ee in ability.get("effect_entries", []):
                if ee.get("language", {}).get("name") == "en":
                    effect = ee.get("short_effect", ee.get("effect", ""))
                    break

        flavor = _get_flavor_text(
            ability.get("flavor_text_entries", []), "it"
        )
        if not flavor:
            flavor = _get_flavor_text(
                ability.get("flavor_text_entries", []), "en"
            )

        page_content = f"""\
Abilita: {name_it}
Nome inglese: {name_en}
Effetto: {effect}
Descrizione: {flavor}"""

        metadata = {
            "entity_type": "ability",
            "ability_id": aid,
            "name_en": name_en.lower(),
            "name_it": name_it.lower(),
            "generation": generation,
        }

        docs.append(Document(page_content=page_content, metadata=metadata))

    return docs


# --- Item Documents ---


def build_item_documents(
    items_data: dict[int, dict],
    generation: int,
) -> list[Document]:
    """Build one Document per item for the given generation.

    Note: PokeAPI doesn't track item generation introduction precisely.
    We include all items and tag them with the current generation.
    """
    docs = []

    for iid, item in items_data.items():
        name_en = item["name"].replace("-", " ").title()
        name_it = _get_localized(item.get("names", []), "it") or name_en

        effect = ""
        for ee in item.get("effect_entries", []):
            if ee.get("language", {}).get("name") == "it":
                effect = ee.get("short_effect", ee.get("effect", ""))
                break
        if not effect:
            for ee in item.get("effect_entries", []):
                if ee.get("language", {}).get("name") == "en":
                    effect = ee.get("short_effect", ee.get("effect", ""))
                    break

        category = item.get("category", {}).get("name", "").replace("-", " ")

        flavor = _get_flavor_text(
            item.get("flavor_text_entries", []), "it"
        )
        if not flavor:
            flavor = _get_flavor_text(
                item.get("flavor_text_entries", []), "en"
            )

        page_content = f"""\
Strumento: {name_it}
Nome inglese: {name_en}
Categoria: {category}
Effetto: {effect}
Descrizione: {flavor}"""

        metadata = {
            "entity_type": "item",
            "item_id": iid,
            "name_en": name_en.lower(),
            "name_it": name_it.lower(),
            "generation": generation,
        }

        docs.append(Document(page_content=page_content, metadata=metadata))

    return docs


# --- Nature Documents ---


def build_nature_documents(
    natures_data: dict[int, dict],
    generation: int,
) -> list[Document]:
    """Build one Document per nature (only for gen >= 3)."""
    if generation < 3:
        return []

    stat_name_it = {
        "attack": "Attacco",
        "defense": "Difesa",
        "special-attack": "Attacco Speciale",
        "special-defense": "Difesa Speciale",
        "speed": "Velocita",
    }

    docs = []

    for nid, nature in natures_data.items():
        name_en = nature["name"].capitalize()
        name_it = _get_localized(nature.get("names", []), "it") or name_en

        increased = nature.get("increased_stat")
        decreased = nature.get("decreased_stat")

        if increased and decreased:
            inc_name = stat_name_it.get(increased["name"], increased["name"])
            dec_name = stat_name_it.get(decreased["name"], decreased["name"])
            effect = f"+{inc_name}, -{dec_name}"
        else:
            effect = "Neutra (nessun modificatore)"

        page_content = f"""\
Natura: {name_it}
Nome inglese: {name_en}
Effetto: {effect}"""

        metadata = {
            "entity_type": "nature",
            "nature_id": nid,
            "name_en": name_en.lower(),
            "name_it": name_it.lower(),
            "generation": generation,
        }

        docs.append(Document(page_content=page_content, metadata=metadata))

    return docs


# --- Main builder ---


def build_all_documents_for_generation(
    all_data: dict,
    generation: int,
) -> list[Document]:
    """Build all documents for a specific generation."""
    docs = []

    # Pre-build type effectiveness table for this generation (shared)
    type_table = _build_type_effectiveness_table(all_data["types"], generation)

    docs.extend(build_pokemon_documents(
        all_data["pokemon"],
        all_data["species"],
        all_data["evolution_chains"],
        all_data["types"],
        generation,
        type_table=type_table,
    ))

    docs.extend(build_move_documents(
        all_data["moves"],
        all_data["types"],
        generation,
    ))

    docs.extend(build_type_documents(
        all_data["types"],
        generation,
    ))

    docs.extend(build_ability_documents(
        all_data["abilities"],
        generation,
    ))

    # Items only for the latest gen (no historical tracking available)
    if generation == max(MAX_POKEMON_PER_GEN.keys()):
        docs.extend(build_item_documents(
            all_data["items"],
            generation,
        ))

    docs.extend(build_nature_documents(
        all_data["natures"],
        generation,
    ))

    return docs
