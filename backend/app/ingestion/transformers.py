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
        (e.get("flavor_text") or e.get("text", "")).replace("\n", " ").replace("\f", " ")
        for e in entries
        if e.get("language", {}).get("name") == lang
        and (e.get("flavor_text") or e.get("text"))
    ]
    return texts[-1] if texts else ""


def _get_stat(stats: list[dict], stat_name: str) -> int:
    for s in stats:
        if s["stat"]["name"] == stat_name:
            return s["base_stat"]
    return 0


def _format_evo_trigger(
    details: list[dict],
    item_name_lookup: dict[str, str] | None = None,
) -> str:
    """Formatta il metodo di evoluzione dal campo evolution_details di PokeAPI.

    Restituisce una descrizione breve in italiano del trigger.
    item_name_lookup mappa slug EN -> nome IT (es. "sun-stone" -> "Pietra Solare").
    """
    if not details:
        return ""

    lookup = item_name_lookup or {}

    # Prendi il primo dettaglio (di solito ce n'e' uno solo)
    d = details[0]
    trigger = d.get("trigger", {}).get("name", "")
    level = d.get("min_level")
    item = d.get("item")
    held_item = d.get("held_item")
    happiness = d.get("min_happiness")
    time_of_day = d.get("time_of_day", "")

    if trigger == "level-up":
        parts = []
        if level:
            parts.append(f"Lv.{level}")
        if happiness is not None:
            parts.append("felicita")
        if time_of_day:
            tod_it = {"day": "giorno", "night": "notte"}.get(time_of_day, time_of_day)
            parts.append(f"di {tod_it}")
        return f" ({', '.join(parts)})" if parts else ""
    elif trigger == "trade":
        if held_item:
            slug = held_item.get("name", "")
            item_name = lookup.get(slug, slug.replace("-", " ").title())
            return f" (scambio con {item_name})"
        return " (scambio)"
    elif trigger == "use-item":
        if item:
            slug = item.get("name", "")
            item_name = lookup.get(slug, slug.replace("-", " ").title())
            return f" ({item_name})"
        return " (strumento)"
    elif trigger == "shed":
        return " (slot vuoto + Poke Ball)"
    else:
        return ""


def _format_evolution_chain(
    chain: dict,
    species_data: dict[int, dict],
    generation: int,
    name_lookup: dict[str, str] | None = None,
    item_name_lookup: dict[str, str] | None = None,
) -> str:
    """Formatta la catena evolutiva con ramificazioni, metodi e filtro generazione.

    Risultato per Machop: ``Machop -> Machoke (Lv.28) -> Machamp (scambio)``
    Risultato per Eevee gen 1: ``Eevee -> Vaporeon (Pietra Idrica) / Jolteon (Pietratuono) / ...``
    """
    species_name = chain["species"]["name"]

    # Controlla se il Pokemon esiste nella generazione target
    sp_url = chain["species"].get("url", "")
    sp_id = int(sp_url.rstrip("/").split("/")[-1]) if sp_url else 0
    sp_data = species_data.get(sp_id)
    if sp_data:
        gen_introduced = int(
            sp_data.get("generation", {})
            .get("url", "/0/")
            .rstrip("/")
            .split("/")[-1]
        )
        if gen_introduced > generation:
            return ""

    display_name = (
        name_lookup.get(species_name, species_name.capitalize())
        if name_lookup
        else species_name.capitalize()
    )

    # Aggiungi il metodo di evoluzione (se presente)
    evo_details = chain.get("evolution_details", [])
    trigger_text = _format_evo_trigger(evo_details, item_name_lookup)

    # Raccoglie le evoluzioni valide per questa generazione
    branches: list[str] = []
    for evo in chain.get("evolves_to", []):
        branch_text = _format_evolution_chain(
            evo, species_data, generation, name_lookup, item_name_lookup,
        )
        if branch_text:
            branches.append(branch_text)

    current = f"{display_name}{trigger_text}"

    if not branches:
        return current
    elif len(branches) == 1:
        return f"{current} -> {branches[0]}"
    else:
        # Ramificazione: formato con barra
        return f"{current} -> {' / '.join(branches)}"


def _get_type_name_it(type_data: dict) -> str:
    return _get_localized(type_data.get("names", []), "it")


# Mapping nome generazione PokeAPI -> numero
_GEN_NAME_TO_NUM: dict[str, int] = {
    "generation-i": 1, "generation-ii": 2, "generation-iii": 3,
    "generation-iv": 4, "generation-v": 5, "generation-vi": 6,
    "generation-vii": 7, "generation-viii": 8, "generation-ix": 9,
}


def _get_pokemon_types_for_gen(poke: dict, target_gen: int) -> list[str]:
    """Ricostruisce i tipi del Pokemon per una generazione specifica.

    PokeAPI ``past_types``: ogni entry dice
    "prima di generation-X, questo Pokemon aveva questi tipi".
    """
    current_types = [t["type"]["name"] for t in poke["types"]]

    for pt in poke.get("past_types", []):
        gen_name = pt.get("generation", {}).get("name", "")
        gen_num = _GEN_NAME_TO_NUM.get(gen_name, 99)

        # Se la gen target e' precedente al cambio, usiamo i tipi passati
        if target_gen <= gen_num:
            current_types = [t["type"]["name"] for t in pt["types"]]

    return current_types


def _get_generation_for_move_version(version_group_name: str) -> int | None:
    return VERSION_GROUP_TO_GEN.get(version_group_name)


def _get_pokemon_abilities_for_gen(
    poke: dict,
    target_gen: int,
    abilities_data: dict,
) -> tuple[list[str], str | None]:
    """Ricostruisce le abilita del Pokemon per una generazione specifica.

    Gestisce:
    - ``past_abilities`` (PokeAPI): storico delle abilita cambiate
    - Abilita nascoste: non esistevano prima di gen 5
    - Filtro per generazione di introduzione dell'abilita stessa

    Returns:
        (lista_slug_abilita_normali, slug_hidden_ability_o_None)
    """
    # Abilita non esistevano prima di gen 3
    if target_gen < 3:
        return [], None

    # Ricostruisce le abilita per la generazione target.
    # IMPORTANTE: past_abilities e' un DELTA per slot, non una lista
    # completa. Ogni entry indica solo gli slot che sono cambiati.
    # Bisogna fare merge per slot, non sostituzione totale.
    abilities_by_slot: dict[int, dict] = {}
    for a in poke.get("abilities", []):
        abilities_by_slot[a.get("slot", 0)] = a

    for pa in poke.get("past_abilities", []):
        gen_name = pa.get("generation", {}).get("name", "")
        gen_num = _GEN_NAME_TO_NUM.get(gen_name, 99)
        if target_gen <= gen_num:
            # Merge: sostituisci solo gli slot specificati
            for a in pa.get("abilities", []):
                abilities_by_slot[a.get("slot", 0)] = a

    raw_abilities = list(abilities_by_slot.values())

    # Indice rapido slug -> ability data
    ab_by_slug: dict[str, dict] = {}
    for ab in abilities_data.values():
        ab_by_slug[ab["name"]] = ab

    abilities: list[str] = []
    hidden: str | None = None

    for a in raw_abilities:
        # past_abilities puo' avere slot con ability=None
        if not a.get("ability"):
            continue
        ab_slug = a["ability"]["name"]

        # Filtra abilita non ancora introdotte nella gen target
        ab_data = ab_by_slug.get(ab_slug)
        if ab_data:
            ab_gen = int(
                ab_data.get("generation", {})
                .get("url", "/0/")
                .rstrip("/")
                .split("/")[-1]
            )
            if ab_gen > target_gen:
                continue

        # Le abilita nascoste non esistevano prima di gen 5
        if a.get("is_hidden") and target_gen < 5:
            continue

        if a.get("is_hidden"):
            hidden = ab_slug
        else:
            abilities.append(ab_slug)

    return abilities, hidden


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

    # Formato per-tipo: ogni tipo ha il moltiplicatore accanto.
    # Questo impedisce all'LLM di invertire i valori tra tipi diversi.
    weaknesses: list[tuple[float, str]] = []
    resistances: list[tuple[float, str]] = []
    immunities: list[str] = []

    for atk_type, mult in combined.items():
        if mult == 1.0:
            continue
        it_name = type_name_it.get(atk_type, atk_type)
        if mult > 1.0:
            weaknesses.append((mult, it_name))
        elif mult == 0.0:
            immunities.append(it_name)
        else:
            resistances.append((mult, it_name))

    # Ordina: debolezze decrescenti, resistenze crescenti
    weaknesses.sort(key=lambda x: (-x[0], x[1]))
    resistances.sort(key=lambda x: (x[0], x[1]))

    lines = []
    if weaknesses:
        lines.append("Debolezze: " + ", ".join(
            f"{name} x{mult:g}" for mult, name in weaknesses
        ))
    if resistances:
        lines.append("Resistenze: " + ", ".join(
            f"{name} x{mult:g}" for mult, name in resistances
        ))
    if immunities:
        lines.append("Immunita: " + ", ".join(sorted(immunities)))

    return "\n".join(lines) if lines else "Nessuna debolezza o resistenza particolare"


# --- Pokemon Documents ---


def build_pokemon_documents(
    pokemon_data: dict[int, dict],
    species_data: dict[int, dict],
    evo_chains: dict[int, dict],
    all_types: dict[int, dict],
    generation: int,
    type_table: dict[str, dict[str, float]] | None = None,
    type_name_it: dict[str, str] | None = None,
    moves_data: dict[int, dict] | None = None,
    abilities_data: dict[int, dict] | None = None,
    items_data: dict[int, dict] | None = None,
) -> list[Document]:
    """Build one Document per Pokemon for the given generation."""
    max_id = MAX_POKEMON_PER_GEN.get(generation, 1025)
    docs = []

    # Usa il lookup condiviso o costruiscilo se non fornito
    if type_name_it is None:
        type_name_it = _build_type_name_lookup(all_types)

    # Build move name lookup (EN slug -> IT name)
    move_name_it: dict[str, str] = {}
    if moves_data:
        for mv in moves_data.values():
            slug = mv["name"]  # e.g. "thunderbolt"
            it_name = _get_localized(mv.get("names", []), "it")
            move_name_it[slug] = it_name or slug.replace("-", " ").title()

    # Build ability name + effect lookup (EN slug -> IT name / effect)
    ability_name_it: dict[str, str] = {}
    ability_effect_it: dict[str, str] = {}
    if abilities_data:
        for ab in abilities_data.values():
            slug = ab["name"]  # e.g. "inner-focus"
            it_name = _get_localized(ab.get("names", []), "it")
            ability_name_it[slug] = it_name or slug.replace("-", " ").title()
            # Effect description: solo italiano (flavor_text IT → effect_entries IT)
            desc = _get_flavor_text(ab.get("flavor_text_entries", []), "it")
            if not desc:
                for ee in ab.get("effect_entries", []):
                    if ee.get("language", {}).get("name") == "it":
                        desc = ee.get("short_effect", ee.get("effect", ""))
                        break
            if desc:
                ability_effect_it[slug] = desc

    # Build species name lookup (slug -> IT name) for evolution chains
    species_name_it: dict[str, str] = {}
    for sp in species_data.values():
        slug = sp.get("name", "")
        it_name = _get_localized(sp.get("names", []), "it")
        if slug and it_name:
            species_name_it[slug] = it_name

    # Build item name lookup (EN slug -> IT name) for evolution triggers
    item_name_it: dict[str, str] = {}
    if items_data:
        for it in items_data.values():
            slug = it["name"]  # e.g. "sun-stone"
            it_name = _get_localized(it.get("names", []), "it")
            if it_name:
                item_name_it[slug] = it_name

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

        # Types (generation-aware: usa past_types per ricostruire i tipi storici)
        types_en = _get_pokemon_types_for_gen(poke, generation)
        types_it = [type_name_it.get(t, t) for t in types_en]

        # Stats
        hp = _get_stat(poke["stats"], "hp")
        atk = _get_stat(poke["stats"], "attack")
        defense = _get_stat(poke["stats"], "defense")
        sp_atk = _get_stat(poke["stats"], "special-attack")
        sp_def = _get_stat(poke["stats"], "special-defense")
        speed = _get_stat(poke["stats"], "speed")
        bst = hp + atk + defense + sp_atk + sp_def + speed

        # Abilities (generation-aware + Italian names + effect descriptions)
        ab_slugs, hidden_slug = _get_pokemon_abilities_for_gen(
            poke, generation, abilities_data or {},
        )
        abilities_with_desc: list[str] = []
        for s in ab_slugs:
            ab_name = ability_name_it.get(s, s.replace("-", " ").title())
            ab_eff = ability_effect_it.get(s, "")
            abilities_with_desc.append(
                f"{ab_name}: {ab_eff}" if ab_eff else ab_name
            )
        hidden_ability_desc = ""
        if hidden_slug:
            h_name = ability_name_it.get(
                hidden_slug, hidden_slug.replace("-", " ").title()
            )
            h_eff = ability_effect_it.get(hidden_slug, "")
            hidden_ability_desc = (
                f"{h_name}: {h_eff}" if h_eff else h_name
            )

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

        # Evolution chain (generation-aware + tree format)
        evo_chain_url = spec.get("evolution_chain", {}).get("url", "")
        evo_text = ""
        if evo_chain_url:
            chain_id = int(evo_chain_url.rstrip("/").split("/")[-1])
            chain_data = evo_chains.get(chain_id)
            if chain_data:
                evo_text = _format_evolution_chain(
                    chain_data["chain"],
                    species_data,
                    generation,
                    name_lookup=species_name_it,
                    item_name_lookup=item_name_it,
                )

        # Learnset for this generation (Italian move names)
        # Formato compatto: mosse per livello con "(Lv.X)", mosse MT solo nomi.
        # Manteniamo TUTTI i nomi (serve per query tipo "Charizard impara Terremoto?")
        # ma evitiamo di ripetere "(MT)" per ogni mossa.
        levelup_moves: list[tuple[int, str]] = []
        mt_moves: list[str] = []
        for m in poke.get("moves", []):
            for vgd in m.get("version_group_details", []):
                vg_name = vgd["version_group"]["name"]
                vg_gen = _get_generation_for_move_version(vg_name)
                if vg_gen == generation:
                    method = vgd["move_learn_method"]["name"]
                    level = vgd.get("level_learned_at", 0)
                    move_slug = m["move"]["name"]
                    move_name = move_name_it.get(
                        move_slug, move_slug.replace("-", " ").title()
                    )
                    if method == "level-up" and level > 0:
                        levelup_moves.append((level, f"{move_name} (Lv.{level})"))
                    elif method == "machine":
                        mt_moves.append(move_name)
                    break
        # Ordina mosse per livello
        levelup_moves.sort(key=lambda x: x[0])

        # Formatta sezione mosse compatta
        learnset_lines: list[str] = []
        if levelup_moves:
            learnset_lines.append(
                "Per livello: " + ", ".join(t[1] for t in levelup_moves)
            )
        if mt_moves:
            learnset_lines.append(
                "Via MT/MN: " + ", ".join(sorted(mt_moves))
            )
        learnset_text = "\n".join(learnset_lines) if learnset_lines else "Dati non disponibili"

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

Abilita:
{chr(10).join('- ' + a for a in abilities_with_desc) if abilities_with_desc else 'Nessuna'}
Abilita nascosta: {hidden_ability_desc or 'Nessuna'}

Catena evolutiva: {evo_text or 'Nessuna evoluzione'}

Descrizione Pokedex:
{flavor}

Mosse apprendibili (Generazione {generation}):
{learnset_text}

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


# --- Summary / Ranking Documents ---


def _build_pokemon_stat_list(
    pokemon_data: dict[int, dict],
    species_data: dict[int, dict],
    all_types: dict[int, dict],
    generation: int,
    type_name_it: dict[str, str],
) -> list[dict]:
    """Build a list of stat dicts for all Pokemon available in a generation.

    Each dict has: pid, name_it, name_en, hp, atk, defense, sp_atk, sp_def,
    speed, bst, types_it, is_legendary, is_mythical.
    """
    max_id = MAX_POKEMON_PER_GEN.get(generation, 1025)
    result: list[dict] = []

    for pid in range(1, max_id + 1):
        poke = pokemon_data.get(pid)
        spec = species_data.get(pid)
        if not poke or not spec:
            continue

        name_it = _get_localized(spec.get("names", []), "it") or poke["name"]
        name_en = poke["name"].capitalize()

        types_en = _get_pokemon_types_for_gen(poke, generation)
        types_it = [type_name_it.get(t, t) for t in types_en]

        hp = _get_stat(poke["stats"], "hp")
        atk = _get_stat(poke["stats"], "attack")
        defense = _get_stat(poke["stats"], "defense")
        sp_atk = _get_stat(poke["stats"], "special-attack")
        sp_def = _get_stat(poke["stats"], "special-defense")
        speed = _get_stat(poke["stats"], "speed")
        bst = hp + atk + defense + sp_atk + sp_def + speed

        is_legendary = spec.get("is_legendary", False)
        is_mythical = spec.get("is_mythical", False)

        result.append({
            "pid": pid,
            "name_it": name_it,
            "name_en": name_en,
            "hp": hp,
            "atk": atk,
            "defense": defense,
            "sp_atk": sp_atk,
            "sp_def": sp_def,
            "speed": speed,
            "bst": bst,
            "types_it": types_it,
            "is_legendary": is_legendary,
            "is_mythical": is_mythical,
        })

    return result


def _format_stat_line(p: dict) -> str:
    """Format one Pokemon's stats for a ranking line."""
    tag = ""
    if p["is_legendary"]:
        tag = " [Leggendario]"
    elif p["is_mythical"]:
        tag = " [Misterioso]"
    types_str = "/".join(p["types_it"])
    return (
        f"{p['name_it']} - BST: {p['bst']} (Tipi: {types_str}){tag}\n"
        f"   HP: {p['hp']} | Attacco: {p['atk']} | Difesa: {p['defense']} "
        f"| Att.Sp: {p['sp_atk']} | Dif.Sp: {p['sp_def']} | Velocita: {p['speed']}"
    )


def _format_single_stat_line(p: dict, stat_name: str, stat_value: int) -> str:
    """Format one Pokemon's entry for a single-stat ranking."""
    tag = ""
    if p["is_legendary"]:
        tag = " [Leggendario]"
    elif p["is_mythical"]:
        tag = " [Misterioso]"
    types_str = "/".join(p["types_it"])
    return f"{p['name_it']} - {stat_name}: {stat_value} (BST: {p['bst']}, Tipi: {types_str}){tag}"


def build_summary_documents(
    pokemon_data: dict[int, dict],
    species_data: dict[int, dict],
    all_types: dict[int, dict],
    generation: int,
    type_name_it: dict[str, str] | None = None,
) -> list[Document]:
    """Build pre-computed summary/ranking documents for a generation.

    These documents are indexed alongside per-Pokemon docs so that
    semantic search finds them for analytical queries like
    "qual e il pokemon piu forte in gen 4".
    """
    if type_name_it is None:
        type_name_it = _build_type_name_lookup(all_types)

    poke_list = _build_pokemon_stat_list(
        pokemon_data, species_data, all_types, generation, type_name_it,
    )
    if not poke_list:
        return []

    docs: list[Document] = []

    # --- 1. BST ranking overall (top 20) ---
    by_bst = sorted(poke_list, key=lambda p: p["bst"], reverse=True)
    top20 = by_bst[:20]
    lines = [f"{i+1}. {_format_stat_line(p)}" for i, p in enumerate(top20)]
    best_overall = top20[0]
    best_non_legend = next(
        (p for p in by_bst if not p["is_legendary"] and not p["is_mythical"]),
        None,
    )

    content = (
        f"Classifica Pokemon per Statistiche Base Totali (BST) - Generazione {generation}\n\n"
        f"I 20 Pokemon con il BST piu alto disponibili in Generazione {generation}:\n\n"
        + "\n".join(lines)
        + f"\n\nPokemon piu forte in assoluto: {best_overall['name_it']} (BST {best_overall['bst']})"
    )
    if best_non_legend:
        content += (
            f"\nPokemon non-leggendario piu forte: "
            f"{best_non_legend['name_it']} (BST {best_non_legend['bst']})"
        )

    docs.append(Document(
        page_content=content,
        metadata={
            "entity_type": "summary",
            "summary_category": "bst_ranking_overall",
            "name_en": "bst ranking overall",
            "name_it": "classifica pokemon piu forti",
            "generation": generation,
        },
    ))

    # --- 2. BST non-legendary (top 15) ---
    non_legends = [p for p in by_bst if not p["is_legendary"] and not p["is_mythical"]]
    top15_nl = non_legends[:15]
    lines_nl = [f"{i+1}. {_format_stat_line(p)}" for i, p in enumerate(top15_nl)]

    docs.append(Document(
        page_content=(
            f"Classifica Pokemon non leggendari per BST - Generazione {generation}\n\n"
            f"I 15 Pokemon non leggendari e non mitici con il BST piu alto "
            f"disponibili in Generazione {generation}:\n\n"
            + "\n".join(lines_nl)
        ),
        metadata={
            "entity_type": "summary",
            "summary_category": "bst_ranking_non_legendary",
            "name_en": "non legendary bst ranking",
            "name_it": "classifica pokemon non leggendari",
            "generation": generation,
        },
    ))

    # --- 3. Legendary & Mythical list ---
    legends = [p for p in by_bst if p["is_legendary"] or p["is_mythical"]]
    legend_lines = []
    for i, p in enumerate(legends):
        tag = "Leggendario" if p["is_legendary"] else "Misterioso"
        types_str = "/".join(p["types_it"])
        legend_lines.append(
            f"{i+1}. {p['name_it']} - BST: {p['bst']} (Tipi: {types_str}) [{tag}]"
        )

    leg_count = sum(1 for p in legends if p["is_legendary"])
    myth_count = sum(1 for p in legends if p["is_mythical"])

    docs.append(Document(
        page_content=(
            f"Pokemon Leggendari e Mitici - Generazione {generation}\n\n"
            f"Totale: {len(legends)} ({leg_count} leggendari, {myth_count} mitici)\n\n"
            + "\n".join(legend_lines)
        ),
        metadata={
            "entity_type": "summary",
            "summary_category": "legendary_mythical_list",
            "name_en": "legendary mythical pokemon list",
            "name_it": "pokemon leggendari e mitici",
            "generation": generation,
        },
    ))

    # --- 4-9. Individual stat rankings (top 15 each) ---
    stat_configs = [
        ("hp", "HP", "pokemon con piu hp punti salute"),
        ("atk", "Attacco", "pokemon con piu attacco fisico"),
        ("defense", "Difesa", "pokemon con piu difesa fisico"),
        ("sp_atk", "Attacco Speciale", "pokemon con piu attacco speciale"),
        ("sp_def", "Difesa Speciale", "pokemon con piu difesa speciale"),
        ("speed", "Velocita", "pokemon piu veloci"),
    ]

    for stat_key, stat_label, name_it_val in stat_configs:
        by_stat = sorted(poke_list, key=lambda p, k=stat_key: p[k], reverse=True)
        top15 = by_stat[:15]
        stat_lines = [
            f"{i+1}. {_format_single_stat_line(p, stat_label, p[stat_key])}"
            for i, p in enumerate(top15)
        ]
        best = top15[0]
        best_nl = next(
            (p for p in by_stat if not p["is_legendary"] and not p["is_mythical"]),
            None,
        )

        stat_content = (
            f"Classifica Pokemon per {stat_label} base - Generazione {generation}\n\n"
            f"I 15 Pokemon con la {stat_label} base piu alta "
            f"disponibili in Generazione {generation}:\n\n"
            + "\n".join(stat_lines)
            + f"\n\nPokemon con {stat_label} piu alta: {best['name_it']} ({best[stat_key]})"
        )
        if best_nl:
            stat_content += (
                f"\nNon-leggendario con {stat_label} piu alta: "
                f"{best_nl['name_it']} ({best_nl[stat_key]})"
            )

        cat_suffix = stat_key.replace("_", "")
        docs.append(Document(
            page_content=stat_content,
            metadata={
                "entity_type": "summary",
                "summary_category": f"stat_ranking_{cat_suffix}",
                "name_en": f"{stat_label.lower()} ranking",
                "name_it": name_it_val,
                "generation": generation,
            },
        ))

    # --- 10. Type distribution ---
    type_counts: dict[str, int] = {}
    for p in poke_list:
        for t in p["types_it"]:
            type_counts[t] = type_counts.get(t, 0) + 1

    sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
    type_lines = [f"- {tname}: {count} Pokemon" for tname, count in sorted_types]

    most_common = sorted_types[0] if sorted_types else ("?", 0)
    least_common = sorted_types[-1] if sorted_types else ("?", 0)

    legend_names = [p["name_it"] for p in legends if p["is_legendary"]]
    mythical_names = [p["name_it"] for p in legends if p["is_mythical"]]

    dist_content = (
        f"Distribuzione Pokemon per Tipo - Generazione {generation}\n\n"
        f"Totale Pokemon disponibili in Generazione {generation}: {len(poke_list)}\n\n"
        f"Pokemon per tipo (un Pokemon doppio tipo viene contato in entrambi):\n"
        + "\n".join(type_lines)
        + f"\n\nTipo piu comune: {most_common[0]} ({most_common[1]} Pokemon)"
        + f"\nTipo piu raro: {least_common[0]} ({least_common[1]} Pokemon)"
        + f"\n\nPokemon Leggendari ({leg_count}): {', '.join(legend_names) if legend_names else 'Nessuno'}"
        + f"\nPokemon Mitici ({myth_count}): {', '.join(mythical_names) if mythical_names else 'Nessuno'}"
    )

    docs.append(Document(
        page_content=dist_content,
        metadata={
            "entity_type": "summary",
            "summary_category": "type_distribution",
            "name_en": "type distribution",
            "name_it": "distribuzione pokemon per tipo",
            "generation": generation,
        },
    ))

    return docs


# --- Build / Strategy Documents ---

# Before Gen 4, physical/special was determined by type, not by move.
_PHYSICAL_TYPES_PRE_GEN4 = frozenset({
    "normal", "fighting", "poison", "ground", "flying",
    "bug", "rock", "ghost", "steel",
})

# Notable status moves to prioritize in build documents.
_PRIORITY_STATUS_SLUGS = frozenset({
    # Setup
    "swords-dance", "dragon-dance", "calm-mind", "nasty-plot",
    "bulk-up", "shell-smash", "quiver-dance", "iron-defense",
    "agility", "rock-polish", "shift-gear", "coil", "tail-glow",
    "cotton-guard", "cosmic-power", "amnesia", "barrier",
    "autotomize", "belly-drum", "curse", "growth", "hone-claws",
    "work-up", "no-retreat",
    # Recovery
    "recover", "roost", "soft-boiled", "slack-off",
    "synthesis", "morning-sun", "moonlight", "rest",
    "shore-up", "strength-sap", "wish",
    # Hazards
    "stealth-rock", "spikes", "toxic-spikes", "sticky-web",
    # Status inflicting
    "thunder-wave", "toxic", "will-o-wisp", "spore",
    "sleep-powder", "hypnosis", "stun-spore", "glare", "yawn",
    # Utility
    "taunt", "protect", "substitute", "encore",
    "defog", "heal-bell", "aromatherapy",
    "trick", "switcheroo",
    "whirlwind", "roar", "haze",
    "trick-room", "tailwind",
    "parting-shot", "memento",
})


def _get_effective_damage_class(
    move_data: dict, move_type_en: str, generation: int,
) -> str:
    """Get the effective damage class for a generation.

    Pre-Gen 4, damage class was determined by type:
    - Physical: Normal, Fighting, Poison, Ground, Flying, Bug, Rock, Ghost, Steel
    - Special: Fire, Water, Grass, Electric, Ice, Psychic, Dragon, Dark
    """
    base_class = move_data.get("damage_class", {}).get("name", "status")
    if base_class == "status":
        return "status"
    if generation < 4:
        return "physical" if move_type_en in _PHYSICAL_TYPES_PRE_GEN4 else "special"
    return base_class


def _classify_pokemon_role(
    atk: int, sp_atk: int, defense: int, sp_def: int,
    hp: int, speed: int,
) -> tuple[str, str]:
    """Classify a Pokemon's competitive role from base stats.

    Returns (role_label_it, dominant_attack_type).
    dominant_attack_type: "physical", "special", or "mixed".
    """
    if abs(atk - sp_atk) <= 15:
        atk_type, atk_label = "mixed", "Misto"
    elif atk > sp_atk:
        atk_type, atk_label = "physical", "Fisico"
    else:
        atk_type, atk_label = "special", "Speciale"

    best_off = max(atk, sp_atk)
    bulk = (hp + defense + sp_def) / 3

    if best_off >= 100 and speed >= 80:
        return f"Sweeper {atk_label}", atk_type
    if best_off >= 90 and bulk >= 90:
        return f"Attaccante Bulky {atk_label}", atk_type
    if bulk >= 100 and best_off < 80:
        if defense >= sp_def + 20:
            return "Wall Fisico", atk_type
        if sp_def >= defense + 20:
            return "Wall Speciale", atk_type
        return "Wall Misto", atk_type
    if best_off >= 80:
        return f"Attaccante {atk_label}", atk_type
    if speed >= 100:
        return "Supporto Veloce", atk_type
    return "Supporto", atk_type


def _rank_pokemon_moves(
    poke: dict,
    move_by_slug: dict[str, dict],
    generation: int,
    type_name_it: dict[str, str],
    move_name_it: dict[str, str],
    pokemon_types_en: list[str],
    dominant_atk: str,
) -> tuple[list[dict], list[dict], list[str]]:
    """Rank moves a Pokemon can learn in this generation.

    Returns (stab_moves, coverage_moves, status_move_names).
    stab/coverage sorted by effective_power = power * accuracy/100 * STAB_bonus.
    status is a list of notable status move names (Italian).
    """
    seen: set[str] = set()
    stab: list[dict] = []
    coverage: list[dict] = []
    status_names: list[str] = []

    ok_classes = (
        {"physical", "special"} if dominant_atk == "mixed"
        else {dominant_atk}
    )

    for m in poke.get("moves", []):
        slug = m["move"]["name"]
        if slug in seen:
            continue
        for vgd in m.get("version_group_details", []):
            vg = vgd["version_group"]["name"]
            if _get_generation_for_move_version(vg) != generation:
                continue
            seen.add(slug)

            md = move_by_slug.get(slug)
            if not md:
                break

            stats = _reconstruct_move_stats(md, generation)
            move_type = stats.get("type", "normal")
            dmg_class = _get_effective_damage_class(md, move_type, generation)

            if dmg_class == "status":
                if slug in _PRIORITY_STATUS_SLUGS and len(status_names) < 3:
                    it_name = move_name_it.get(
                        slug, slug.replace("-", " ").title(),
                    )
                    status_names.append(it_name)
                break

            power = stats.get("power") or 0
            accuracy = stats.get("accuracy") or 100
            if power <= 0 or dmg_class not in ok_classes:
                break

            is_stab = move_type in pokemon_types_en
            eff = power * (accuracy / 100) * (1.5 if is_stab else 1.0)

            info = {
                "name_it": move_name_it.get(
                    slug, slug.replace("-", " ").title(),
                ),
                "type_it": type_name_it.get(move_type, move_type),
                "power": power,
                "accuracy": accuracy,
                "effective": round(eff, 1),
            }
            if is_stab:
                stab.append(info)
            else:
                coverage.append(info)
            break

    stab.sort(key=lambda x: x["effective"], reverse=True)
    coverage.sort(key=lambda x: x["effective"], reverse=True)
    return stab[:4], coverage[:5], status_names


def build_pokemon_build_documents(
    pokemon_data: dict[int, dict],
    species_data: dict[int, dict],
    moves_data: dict[int, dict],
    all_types: dict[int, dict],
    generation: int,
    type_name_it: dict[str, str] | None = None,
) -> list[Document]:
    """Build one 'build' Document per Pokemon with BST >= 400.

    Each document contains: role classification, top STAB moves,
    top coverage moves, and notable status moves with effective
    power calculations for team-building and build queries.
    """
    if type_name_it is None:
        type_name_it = _build_type_name_lookup(all_types)

    max_id = MAX_POKEMON_PER_GEN.get(generation, 1025)

    move_name_it: dict[str, str] = {}
    move_by_slug: dict[str, dict] = {}
    for mv in moves_data.values():
        slug = mv["name"]
        it_name = _get_localized(mv.get("names", []), "it")
        move_name_it[slug] = it_name or slug.replace("-", " ").title()
        move_by_slug[slug] = mv

    docs: list[Document] = []

    for pid in range(1, max_id + 1):
        poke = pokemon_data.get(pid)
        spec = species_data.get(pid)
        if not poke or not spec:
            continue

        hp = _get_stat(poke["stats"], "hp")
        atk = _get_stat(poke["stats"], "attack")
        defense = _get_stat(poke["stats"], "defense")
        sp_atk = _get_stat(poke["stats"], "special-attack")
        sp_def = _get_stat(poke["stats"], "special-defense")
        speed = _get_stat(poke["stats"], "speed")
        bst = hp + atk + defense + sp_atk + sp_def + speed

        if bst < 400:
            continue

        name_it = _get_localized(spec.get("names", []), "it") or poke["name"]
        name_en = poke["name"].capitalize()
        types_en = _get_pokemon_types_for_gen(poke, generation)
        types_it = [type_name_it.get(t, t) for t in types_en]
        is_legendary = spec.get("is_legendary", False)
        is_mythical = spec.get("is_mythical", False)

        role, dominant_atk = _classify_pokemon_role(
            atk, sp_atk, defense, sp_def, hp, speed,
        )
        stab, cov, status_names = _rank_pokemon_moves(
            poke, move_by_slug, generation, type_name_it,
            move_name_it, types_en, dominant_atk,
        )

        if dominant_atk == "special":
            stat_line = f"Att.Sp: {sp_atk} | Attacco: {atk} | Velocita: {speed}"
        else:
            stat_line = f"Attacco: {atk} | Att.Sp: {sp_atk} | Velocita: {speed}"

        sections = [
            f"Build consigliata: {name_it}",
            f"Generazione: {generation} | Ruolo: {role} | Tipi: {'/'.join(types_it)}",
            f"{stat_line} | BST: {bst}",
        ]

        if stab:
            cls = ""
            if dominant_atk == "physical":
                cls = " (fisiche)"
            elif dominant_atk == "special":
                cls = " (speciali)"
            sections.append("")
            sections.append(f"Migliori mosse STAB{cls}:")
            for mv in stab:
                sections.append(
                    f"- {mv['name_it']}: {mv['type_it']}, "
                    f"{mv['power']} pot, {mv['accuracy']}% "
                    f"(eff: {mv['effective']})"
                )

        if cov:
            sections.append("")
            sections.append("Migliori mosse copertura:")
            for mv in cov:
                sections.append(
                    f"- {mv['name_it']}: {mv['type_it']}, "
                    f"{mv['power']} pot, {mv['accuracy']}% "
                    f"(eff: {mv['effective']})"
                )

        if status_names:
            sections.append("")
            sections.append("Mosse stato utili:")
            for name in status_names:
                sections.append(f"- {name}")

        page_content = "\n".join(sections)

        metadata = {
            "entity_type": "build",
            "pokemon_id": pid,
            "name_en": name_en.lower(),
            "name_it": name_it.lower(),
            "generation": generation,
            "bst": bst,
            "role": role,
            "is_legendary": is_legendary,
            "is_mythical": is_mythical,
        }
        docs.append(Document(page_content=page_content, metadata=metadata))

    return docs


def build_team_roster_documents(
    pokemon_data: dict[int, dict],
    species_data: dict[int, dict],
    all_types: dict[int, dict],
    generation: int,
    type_name_it: dict[str, str] | None = None,
) -> list[Document]:
    """Build team roster summary document per generation.

    Lists top Pokemon per role (Sweeper, Wall, Attaccante Bulky,
    Supporto) for team-building queries.
    """
    if type_name_it is None:
        type_name_it = _build_type_name_lookup(all_types)

    poke_list = _build_pokemon_stat_list(
        pokemon_data, species_data, all_types, generation, type_name_it,
    )

    viable: list[dict] = []
    for p in poke_list:
        if p["bst"] < 400:
            continue
        role, _ = _classify_pokemon_role(
            p["atk"], p["sp_atk"], p["defense"], p["sp_def"],
            p["hp"], p["speed"],
        )
        p["role"] = role
        viable.append(p)

    role_order = [
        "Sweeper Fisico", "Sweeper Speciale", "Sweeper Misto",
        "Attaccante Bulky", "Wall / Tank", "Supporto",
    ]
    role_groups: dict[str, list[dict]] = {r: [] for r in role_order}

    for p in viable:
        r = p["role"]
        if "Sweeper" in r and "Fisico" in r:
            role_groups["Sweeper Fisico"].append(p)
        elif "Sweeper" in r and "Speciale" in r:
            role_groups["Sweeper Speciale"].append(p)
        elif "Sweeper" in r and "Misto" in r:
            role_groups["Sweeper Misto"].append(p)
        elif "Attaccante" in r:
            role_groups["Attaccante Bulky"].append(p)
        elif "Wall" in r:
            role_groups["Wall / Tank"].append(p)
        else:
            role_groups["Supporto"].append(p)

    for group in role_groups.values():
        group.sort(key=lambda p: p["bst"], reverse=True)

    sections = [
        f"Pokemon consigliati per ruolo - Generazione {generation}",
        "",
    ]

    for role_name in role_order:
        pokes = role_groups[role_name]
        non_legends = [
            p for p in pokes
            if not p["is_legendary"] and not p["is_mythical"]
        ]
        if not non_legends:
            continue
        sections.append(f"{role_name} (non leggendari):")
        for p in non_legends[:5]:
            types_str = "/".join(p["types_it"])
            if "Speciale" in role_name:
                sections.append(
                    f"- {p['name_it']}: {types_str}, Att.Sp {p['sp_atk']}, "
                    f"Vel {p['speed']}, BST {p['bst']}"
                )
            elif "Wall" in role_name or "Supporto" in role_name:
                sections.append(
                    f"- {p['name_it']}: {types_str}, Dif {p['defense']}, "
                    f"Dif.Sp {p['sp_def']}, HP {p['hp']}, BST {p['bst']}"
                )
            else:
                sections.append(
                    f"- {p['name_it']}: {types_str}, Atk {p['atk']}, "
                    f"Vel {p['speed']}, BST {p['bst']}"
                )
        sections.append("")

    legends = [p for p in viable if p["is_legendary"] or p["is_mythical"]]
    legends.sort(key=lambda p: p["bst"], reverse=True)
    if legends:
        sections.append("Leggendari / Mitici disponibili:")
        for p in legends[:10]:
            types_str = "/".join(p["types_it"])
            tag = "Leggendario" if p["is_legendary"] else "Misterioso"
            sections.append(
                f"- {p['name_it']}: {types_str}, BST {p['bst']}, "
                f"{p['role']} [{tag}]"
            )

    return [Document(
        page_content="\n".join(sections),
        metadata={
            "entity_type": "summary",
            "summary_category": "team_roster_by_role",
            "name_en": "team roster by role",
            "name_it": "pokemon consigliati per ruolo squadra",
            "generation": generation,
        },
    )]


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
    # Effect entries: preferisci italiano, fallback inglese
    for ee in move.get("effect_entries", []):
        if ee.get("language", {}).get("name") == "it":
            current["effect"] = ee.get("short_effect", "")
            break
    if not current["effect"]:
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
    generation: int,
    type_name_it: dict[str, str] | None = None,
    all_types: dict[int, dict] | None = None,
) -> list[Document]:
    """Build one Document per move for the given generation."""
    if type_name_it is None and all_types is not None:
        type_name_it = _build_type_name_lookup(all_types)
    elif type_name_it is None:
        type_name_it = {}

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
        gen_num = _GEN_NAME_TO_NUM.get(vg_name, 99)

        if target_gen <= gen_num:
            current = pdr.get("damage_relations", current)
            break  # Prima corrispondenza = quella giusta (ordine cronologico)

    return current


def build_type_documents(
    types_data: dict[int, dict],
    generation: int,
    type_name_it: dict[str, str] | None = None,
) -> list[Document]:
    """Build one Document per type for the given generation."""
    if type_name_it is None:
        type_name_it = _build_type_name_lookup(types_data)

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


def _build_type_name_lookup(all_types: dict[int, dict]) -> dict[str, str]:
    """Build shared type name lookup (EN slug -> IT name).

    Costruito una volta sola e riutilizzato da tutti i builder nella
    stessa generazione, evitando di ricostruirlo N volte.
    """
    type_name_it: dict[str, str] = {}
    for t in all_types.values():
        en_name = t["name"]
        it_name = _get_localized(t.get("names", []), "it") or en_name
        type_name_it[en_name] = it_name
    return type_name_it


def build_all_documents_for_generation(
    all_data: dict,
    generation: int,
) -> list[Document]:
    """Build all documents for a specific generation."""
    docs = []

    # Pre-build shared lookups (una volta sola per generazione)
    type_name_it = _build_type_name_lookup(all_data["types"])
    type_table = _build_type_effectiveness_table(all_data["types"], generation)

    docs.extend(build_pokemon_documents(
        all_data["pokemon"],
        all_data["species"],
        all_data["evolution_chains"],
        all_data["types"],
        generation,
        type_table=type_table,
        type_name_it=type_name_it,
        moves_data=all_data.get("moves"),
        abilities_data=all_data.get("abilities"),
        items_data=all_data.get("items"),
    ))

    docs.extend(build_summary_documents(
        all_data["pokemon"],
        all_data["species"],
        all_data["types"],
        generation,
        type_name_it=type_name_it,
    ))

    docs.extend(build_pokemon_build_documents(
        all_data["pokemon"],
        all_data["species"],
        all_data["moves"],
        all_data["types"],
        generation,
        type_name_it=type_name_it,
    ))

    docs.extend(build_team_roster_documents(
        all_data["pokemon"],
        all_data["species"],
        all_data["types"],
        generation,
        type_name_it=type_name_it,
    ))

    docs.extend(build_move_documents(
        all_data["moves"],
        generation,
        type_name_it=type_name_it,
    ))

    docs.extend(build_type_documents(
        all_data["types"],
        generation,
        type_name_it=type_name_it,
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
