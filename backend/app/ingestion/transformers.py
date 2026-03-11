"""Transform raw PokeAPI JSON into per-generation LangChain Documents."""

import logging

from langchain_core.documents import Document

from app.core.generation_mapper import (
    MAX_POKEMON_PER_GEN,
    VERSION_GROUP_TO_GEN,
)
from app.ingestion.smogon_client import fetch_smogon_sets
from app.ingestion.smogon_transformer import build_smogon_documents

logger = logging.getLogger(__name__)

# --- Egg group EN → IT mapping (15 groups) ---

EGG_GROUP_IT: dict[str, str] = {
    "monster": "Mostro",
    "dragon": "Drago",
    "ground": "Campestre",
    "bug": "Coleottero",
    "flying": "Volante",
    "fairy": "Fatato",
    "plant": "Vegetale",
    "humanshape": "Umanoide",
    "human-like": "Umanoide",
    "mineral": "Minerale",
    "indeterminate": "Amorfo",
    "water1": "Acqua 1",
    "water2": "Acqua 2",
    "water3": "Acqua 3",
    "ditto": "Ditto",
    "no-eggs": "Sconosciuto",
}

# --- Growth rate EN → IT mapping ---

GROWTH_RATE_IT: dict[str, str] = {
    "slow": "Lento (1.250.000 EXP)",
    "medium": "Medio-Veloce (1.000.000 EXP)",
    "medium-slow": "Medio-Lento (1.059.860 EXP)",
    "fast": "Veloce (800.000 EXP)",
    "slow-then-very-fast": "Erratico (600.000 EXP)",
    "fast-then-very-slow": "Fluttuante (1.640.000 EXP)",
}

# --- Move ailment EN → IT mapping ---

AILMENT_IT: dict[str, str] = {
    "none": "",
    "paralysis": "Paralisi",
    "sleep": "Sonno",
    "freeze": "Congelamento",
    "burn": "Scottatura",
    "poison": "Veleno",
    "confusion": "Confusione",
    "infatuation": "Infatuazione",
    "trap": "Trappola",
    "nightmare": "Incubo",
    "torment": "Provocazione",
    "disable": "Impedimento",
    "yawn": "Sonnolenza",
    "heal-block": "Anticura",
    "no-type-immunity": "Rimozione immunita",
    "leech-seed": "Parassiseme",
    "embargo": "Embargo",
    "perish-song": "Canto Perenne",
    "ingrain": "Radicamento",
    "tar-shot": "Colpo di Catrame",
    "unknown": "Sconosciuto",
}

# --- Move target EN → IT mapping ---

TARGET_IT: dict[str, str] = {
    "selected-pokemon": "Un Pokemon selezionato",
    "all-opponents": "Tutti gli avversari",
    "user": "Utilizzatore",
    "all-other-pokemon": "Tutti gli altri Pokemon",
    "all-allies": "Tutti gli alleati",
    "user-and-allies": "Utilizzatore e alleati",
    "entire-field": "Tutto il campo",
    "specific-move": "Mossa specifica",
    "random-opponent": "Avversario casuale",
    "users-field": "Campo alleato",
    "opponents-field": "Campo avversario",
    "ally": "Un alleato",
    "user-or-ally": "Utilizzatore o alleato",
    "all-pokemon": "Tutti i Pokemon",
    "fainting-pokemon": "Pokemon in difficolta",
}

# --- Regional Pokedex name mapping ---

POKEDEX_NAME_IT: dict[str, str] = {
    "national": "Nazionale",
    "kanto": "Kanto",
    "original-johto": "Johto",
    "updated-johto": "Johto (HGSS)",
    "hoenn": "Hoenn",
    "updated-hoenn": "Hoenn (ORAS)",
    "original-sinnoh": "Sinnoh",
    "extended-sinnoh": "Sinnoh (Platino)",
    "original-unova": "Unima",
    "updated-unova": "Unima (B2W2)",
    "kalos-central": "Kalos Centrale",
    "kalos-coastal": "Kalos Costiero",
    "kalos-mountain": "Kalos Montano",
    "original-alola": "Alola",
    "updated-alola": "Alola (USUM)",
    "letsgo-kanto": "Kanto (LGPE)",
    "galar": "Galar",
    "isle-of-armor": "Isola dell'Armatura",
    "crown-tundra": "Landa Corona",
    "hisui": "Hisui",
    "paldea": "Paldea",
    "kitakami": "Kitakami",
    "blueberry": "Mirtillo",
}

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
    move_name_lookup: dict[str, str] | None = None,
    species_name_lookup: dict[str, str] | None = None,
    type_name_lookup: dict[str, str] | None = None,
) -> str:
    """Formatta il metodo di evoluzione dal campo evolution_details di PokeAPI.

    Restituisce una descrizione breve in italiano del trigger.
    item_name_lookup mappa slug EN -> nome IT (es. "sun-stone" -> "Pietra Solare").
    move_name_lookup mappa slug EN -> nome IT mossa.
    species_name_lookup mappa slug EN -> nome IT specie.
    type_name_lookup mappa slug EN -> nome IT tipo.
    """
    if not details:
        return ""

    lookup = item_name_lookup or {}
    move_lookup = move_name_lookup or {}
    sp_lookup = species_name_lookup or {}
    tp_lookup = type_name_lookup or {}

    # Prendi il primo dettaglio (di solito ce n'e' uno solo)
    d = details[0]
    trigger = d.get("trigger", {}).get("name", "")
    level = d.get("min_level")
    item = d.get("item")
    held_item = d.get("held_item")
    happiness = d.get("min_happiness")
    time_of_day = d.get("time_of_day", "")
    known_move = d.get("known_move")
    known_move_type = d.get("known_move_type")
    location = d.get("location")
    party_species = d.get("party_species")
    party_type = d.get("party_type")
    trade_species = d.get("trade_species")
    min_affection = d.get("min_affection")
    min_beauty = d.get("min_beauty")
    relative_physical_stats = d.get("relative_physical_stats")
    needs_rain = d.get("needs_overworld_rain", False)
    turn_upside_down = d.get("turn_upside_down", False)

    if trigger == "level-up":
        parts = []
        if level:
            parts.append(f"Lv.{level}")
        if happiness is not None:
            parts.append("felicita")
        if min_affection is not None:
            parts.append("affetto")
        if min_beauty is not None:
            parts.append("bellezza")
        if time_of_day:
            tod_it = {"day": "giorno", "night": "notte"}.get(time_of_day, time_of_day)
            parts.append(f"di {tod_it}")
        if known_move:
            mv_slug = known_move.get("name", "")
            mv_name = move_lookup.get(mv_slug, mv_slug.replace("-", " ").title())
            parts.append(f"conoscendo {mv_name}")
        if known_move_type:
            tp_slug = known_move_type.get("name", "")
            tp_name = tp_lookup.get(tp_slug, tp_slug.capitalize())
            parts.append(f"con mossa tipo {tp_name}")
        if location:
            loc_name = location.get("name", "").replace("-", " ").title()
            parts.append(f"a {loc_name}")
        if party_species:
            ps_slug = party_species.get("name", "")
            ps_name = sp_lookup.get(ps_slug, ps_slug.capitalize())
            parts.append(f"con {ps_name} in squadra")
        if party_type:
            pt_slug = party_type.get("name", "")
            pt_name = tp_lookup.get(pt_slug, pt_slug.capitalize())
            parts.append(f"con Pokemon tipo {pt_name} in squadra")
        if needs_rain:
            parts.append("sotto la pioggia")
        if turn_upside_down:
            parts.append("console capovolta")
        if relative_physical_stats is not None:
            rps_map = {1: "Att > Dif", -1: "Att < Dif", 0: "Att = Dif"}
            parts.append(rps_map.get(relative_physical_stats, ""))
        if held_item:
            slug = held_item.get("name", "")
            item_name = lookup.get(slug, slug.replace("-", " ").title())
            parts.append(f"con {item_name}")
        return f" ({', '.join(p for p in parts if p)})" if parts else ""
    elif trigger == "trade":
        if trade_species:
            ts_slug = trade_species.get("name", "")
            ts_name = sp_lookup.get(ts_slug, ts_slug.capitalize())
            return f" (scambio con {ts_name})"
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
    elif trigger == "spin":
        return " (girare su se stessi)"
    elif trigger == "take-damage":
        return " (subire danno)"
    elif trigger == "tower-of-darkness":
        return " (Torre delle Tenebre)"
    elif trigger == "tower-of-waters":
        return " (Torre delle Acque)"
    elif trigger == "three-critical-hits":
        return " (3 colpi critici)"
    elif trigger == "agile-style-move":
        return " (mossa stile rapido)"
    elif trigger == "strong-style-move":
        return " (mossa stile potente)"
    elif trigger == "recoil-damage":
        return " (danno da contraccolpo)"
    else:
        return ""


def _format_evolution_chain(
    chain: dict,
    species_data: dict[int, dict],
    generation: int,
    name_lookup: dict[str, str] | None = None,
    item_name_lookup: dict[str, str] | None = None,
    move_name_lookup: dict[str, str] | None = None,
    type_name_lookup: dict[str, str] | None = None,
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
    trigger_text = _format_evo_trigger(
        evo_details,
        item_name_lookup=item_name_lookup,
        move_name_lookup=move_name_lookup,
        species_name_lookup=name_lookup,
        type_name_lookup=type_name_lookup,
    )

    # Raccoglie le evoluzioni valide per questa generazione
    branches: list[str] = []
    for evo in chain.get("evolves_to", []):
        branch_text = _format_evolution_chain(
            evo, species_data, generation, name_lookup, item_name_lookup,
            move_name_lookup, type_name_lookup,
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


def _extract_learnset_for_gen(
    poke: dict,
    gen: int,
    move_name_it: dict[str, str],
) -> tuple[list[tuple[int, str]], list[str]]:
    """Extract level-up and TM/HM moves for a Pokemon in a specific generation.

    Returns (levelup_moves, mt_moves) where:
    - levelup_moves: sorted list of (level, "MoveName (Lv.X)") tuples
    - mt_moves: unsorted list of Italian move names learned via TM/HM
    """
    levelup_moves: list[tuple[int, str]] = []
    mt_moves: list[str] = []
    for m in poke.get("moves", []):
        for vgd in m.get("version_group_details", []):
            vg_name = vgd["version_group"]["name"]
            vg_gen = _get_generation_for_move_version(vg_name)
            if vg_gen == gen:
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
    levelup_moves.sort(key=lambda x: x[0])
    return levelup_moves, mt_moves


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
                    move_name_lookup=move_name_it,
                    type_name_lookup=type_name_it,
                )

        # Learnset for this generation (Italian move names)
        # Formato compatto: mosse per livello con "(Lv.X)", mosse MT solo nomi.
        # Manteniamo TUTTI i nomi (serve per query tipo "Charizard impara Terremoto?")
        # ma evitiamo di ripetere "(MT)" per ogni mossa.
        # Se il Pokemon non ha mosse in questa generazione (es. non presente
        # nel Pokedex regionale), cerca all'indietro la gen piu' recente con dati.
        levelup_moves, mt_moves = _extract_learnset_for_gen(
            poke, generation, move_name_it,
        )
        learnset_gen = generation
        if not levelup_moves and not mt_moves:
            for fb_gen in range(generation - 1, 0, -1):
                fb_lu, fb_mt = _extract_learnset_for_gen(
                    poke, fb_gen, move_name_it,
                )
                if fb_lu or fb_mt:
                    levelup_moves, mt_moves = fb_lu, fb_mt
                    learnset_gen = fb_gen
                    break

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

        # Egg groups (already in species data)
        egg_groups_en = [eg["name"] for eg in spec.get("egg_groups", [])]
        egg_groups_it = [EGG_GROUP_IT.get(eg, eg) for eg in egg_groups_en]

        # Species info: growth rate, capture rate, happiness, hatch counter
        growth_rate_en = spec.get("growth_rate", {}).get("name", "")
        growth_rate_it = GROWTH_RATE_IT.get(growth_rate_en, growth_rate_en)
        capture_rate = spec.get("capture_rate", 0)
        base_happiness = spec.get("base_happiness", 0)
        hatch_counter = spec.get("hatch_counter", 0)
        hatch_steps = hatch_counter * 256 if hatch_counter else 0
        is_baby = spec.get("is_baby", False)

        # Pokedex numbers (regional dex entries)
        pokedex_entries: list[str] = []
        for pdx in spec.get("pokedex_numbers", []):
            dex_name = pdx.get("pokedex", {}).get("name", "")
            dex_num = pdx.get("entry_number", 0)
            dex_name_it = POKEDEX_NAME_IT.get(dex_name)
            if dex_name_it and dex_name != "national":
                pokedex_entries.append(f"{dex_name_it}: #{dex_num}")

        # Held items (items found on wild Pokemon)
        held_items_text_parts: list[str] = []
        for hi in poke.get("held_items", []):
            hi_slug = hi.get("item", {}).get("name", "")
            hi_name = item_name_it.get(hi_slug, hi_slug.replace("-", " ").title())
            # Get version-specific rarities
            version_parts: list[str] = []
            for vd in hi.get("version_details", []):
                v_slug = vd.get("version", {}).get("name", "")
                v_gen = VERSION_TO_GEN.get(v_slug, 0)
                if v_gen == generation:
                    rarity = vd.get("rarity", 0)
                    v_name_it = VERSION_NAME_IT.get(v_slug, v_slug)
                    version_parts.append(f"{v_name_it} {rarity}%")
            if version_parts:
                held_items_text_parts.append(
                    f"{hi_name} ({', '.join(version_parts)})"
                )

        # Calculate dual-type effectiveness
        type_eff_text = _calculate_type_effectiveness(
            types_en, type_table, type_name_it,
        )

        # Build optional sections
        held_items_line = (
            "Strumenti tenuti (Pokemon selvatici): " + "; ".join(held_items_text_parts)
            if held_items_text_parts else ""
        )
        pokedex_line = (
            "Numeri Pokedex regionali: " + ", ".join(pokedex_entries)
            if pokedex_entries else ""
        )
        baby_line = "Pokemon Baby: Si" if is_baby else ""

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

Gruppo uova: {', '.join(egg_groups_it) if egg_groups_it else 'Sconosciuto'}
Tasso di crescita: {growth_rate_it}
Tasso di cattura: {capture_rate}
Felicita base: {base_happiness}
Passi per schiudersi: {hatch_steps}

Descrizione Pokedex:
{flavor}

Mosse apprendibili{f' (dalla Generazione {learnset_gen}, non presente in Gen {generation})' if learnset_gen != generation else f' (Generazione {generation})'}:
{learnset_text}

Leggendario: {'Si' if is_legendary else 'No'}
Misterioso: {'Si' if is_mythical else 'No'}"""

        # Append optional sections
        if baby_line:
            page_content += f"\n{baby_line}"
        if held_items_line:
            page_content += f"\n{held_items_line}"
        if pokedex_line:
            page_content += f"\n{pokedex_line}"

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
            "is_baby": is_baby,
            "bst": bst,
            "egg_groups": egg_groups_en or ["unknown"],
            "capture_rate": capture_rate,
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

        # Fallback: se nessuna mossa in questa gen, prova gens precedenti
        build_gen = generation
        if not stab and not cov:
            for fb_gen in range(generation - 1, 0, -1):
                fb_stab, fb_cov, fb_status = _rank_pokemon_moves(
                    poke, move_by_slug, fb_gen, type_name_it,
                    move_name_it, types_en, dominant_atk,
                )
                if fb_stab or fb_cov:
                    stab, cov, status_names = fb_stab, fb_cov, fb_status
                    build_gen = fb_gen
                    break

        if dominant_atk == "special":
            stat_line = f"Att.Sp: {sp_atk} | Attacco: {atk} | Velocita: {speed}"
        else:
            stat_line = f"Attacco: {atk} | Att.Sp: {sp_atk} | Velocita: {speed}"

        sections = [
            f"Build consigliata: {name_it}",
            f"Generazione: {generation} | Ruolo: {role} | Tipi: {'/'.join(types_it)}",
            f"{stat_line} | BST: {bst}",
        ]
        if build_gen != generation:
            sections.append(
                f"(Dati mosse dalla Generazione {build_gen},"
                f" non presente in Gen {generation})"
            )

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


def _build_reverse_learnset(
    pokemon_data: dict[int, dict],
    species_data: dict[int, dict],
    generation: int,
) -> dict[str, list[str]]:
    """Build reverse mapping: move_slug → sorted list of Pokemon IT names.

    For each move, collects all Pokemon that can learn it in the
    given generation (via any learn method in that gen's version groups).
    Only includes default-form Pokemon up to the generation's dex cap.
    """
    max_id = MAX_POKEMON_PER_GEN.get(generation, 1025)
    mapping: dict[str, set[str]] = {}

    for pid, poke in pokemon_data.items():
        if pid > max_id:
            continue
        sp = species_data.get(pid)
        if not sp:
            continue
        name_it = (
            _get_localized(sp.get("names", []), "it")
            or poke["name"].replace("-", " ").title()
        )

        for m in poke.get("moves", []):
            move_slug = m["move"]["name"]
            for vgd in m.get("version_group_details", []):
                vg_name = vgd["version_group"]["name"]
                if _get_generation_for_move_version(vg_name) == generation:
                    mapping.setdefault(move_slug, set()).add(name_it)
                    break  # found match for this gen, skip other version groups

    return {slug: sorted(names) for slug, names in mapping.items()}


def build_move_documents(
    moves_data: dict[int, dict],
    generation: int,
    type_name_it: dict[str, str] | None = None,
    all_types: dict[int, dict] | None = None,
    reverse_learnset: dict[str, list[str]] | None = None,
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

        # Priority
        priority = move.get("priority", 0)
        priority_str = ""
        if priority != 0:
            priority_str = f"\nPriorita: {'+' if priority > 0 else ''}{priority}"

        # Meta fields (ailment, flinch, drain, crit, healing)
        meta = move.get("meta") or {}
        meta_lines: list[str] = []

        ailment_slug = meta.get("ailment", {}).get("name", "none")
        ailment_chance = meta.get("ailment_chance", 0)
        ailment_it = AILMENT_IT.get(ailment_slug, ailment_slug)
        if ailment_it and ailment_slug != "none":
            meta_lines.append(
                f"Stato inflitto: {ailment_it}"
                + (f" ({ailment_chance}%)" if ailment_chance and ailment_chance < 100 else "")
            )

        flinch_chance = meta.get("flinch_chance", 0)
        if flinch_chance:
            meta_lines.append(f"Tentennamento: {flinch_chance}%")

        drain = meta.get("drain", 0)
        if drain > 0:
            meta_lines.append(f"Assorbimento: {drain}% del danno inflitto")
        elif drain < 0:
            meta_lines.append(f"Contraccolpo: {abs(drain)}% del danno inflitto")

        healing = meta.get("healing", 0)
        if healing > 0:
            meta_lines.append(f"Cura: {healing}% degli HP massimi")

        crit_rate = meta.get("crit_rate", 0)
        if crit_rate > 0:
            meta_lines.append(f"Tasso critico aumentato: +{crit_rate}")

        # Stat changes (top-level field)
        stat_changes = move.get("stat_changes", [])
        if stat_changes:
            stat_it_map = {
                "attack": "Attacco", "defense": "Difesa",
                "special-attack": "Att.Sp", "special-defense": "Dif.Sp",
                "speed": "Velocita", "accuracy": "Precisione",
                "evasion": "Elusione", "hp": "HP",
            }
            sc_parts = []
            for sc in stat_changes:
                sc_name = stat_it_map.get(
                    sc.get("stat", {}).get("name", ""), "?"
                )
                sc_change = sc.get("change", 0)
                sc_parts.append(
                    f"{sc_name} {'+' if sc_change > 0 else ''}{sc_change}"
                )
            stat_chance = meta.get("stat_chance", 0)
            if sc_parts:
                sc_text = "Modifica statistiche: " + ", ".join(sc_parts)
                if stat_chance and stat_chance < 100:
                    sc_text += f" ({stat_chance}%)"
                meta_lines.append(sc_text)

        meta_text = "\n".join(meta_lines)

        # Target
        target_slug = move.get("target", {}).get("name", "")
        target_it = TARGET_IT.get(target_slug, target_slug.replace("-", " "))

        page_content = f"""\
Mossa: {name_it}
Nome inglese: {name_en}
Tipo: {type_it}
Categoria: {damage_class_it}
Potenza: {power_str}
Precisione: {accuracy_str}
PP: {pp_str}{priority_str}
Bersaglio: {target_it}
Effetto: {stats['effect']}"""

        if meta_text:
            page_content += f"\n{meta_text}"

        # Reverse learnset: which Pokemon learn this move
        if reverse_learnset:
            learners = reverse_learnset.get(move["name"], [])
            if learners:
                count = len(learners)
                _MAX_LISTED = 40
                if count <= _MAX_LISTED:
                    learner_str = ", ".join(learners)
                else:
                    learner_str = (
                        ", ".join(learners[:_MAX_LISTED])
                        + f" e altri {count - _MAX_LISTED}"
                    )
                page_content += (
                    f"\nPokemon che imparano questa mossa ({count}): "
                    f"{learner_str}"
                )

        metadata = {
            "entity_type": "move",
            "move_id": mid,
            "name_en": name_en.lower(),
            "name_it": name_it.lower(),
            "type": type_en,
            "generation": generation,
            "damage_class": damage_class,
            "priority": priority,
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
    species_data: dict[int, dict] | None = None,
    pokemon_data: dict[int, dict] | None = None,
) -> list[Document]:
    """Build one Document per type for the given generation."""
    if type_name_it is None:
        type_name_it = _build_type_name_lookup(types_data)

    # Build species name lookup for Pokemon list
    sp_name_it: dict[str, str] = {}
    if species_data:
        for sp in species_data.values():
            slug = sp.get("name", "")
            it = _get_localized(sp.get("names", []), "it")
            if slug and it:
                sp_name_it[slug] = it

    max_id = MAX_POKEMON_PER_GEN.get(generation, 1025) if pokemon_data else 0

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

        # Build Pokemon list for this type (filtered by generation)
        type_pokemon_names: list[str] = []
        if pokemon_data and species_data:
            for entry in type_data.get("pokemon", []):
                poke_name = entry.get("pokemon", {}).get("name", "")
                poke_url = entry.get("pokemon", {}).get("url", "")
                poke_id = int(poke_url.rstrip("/").split("/")[-1]) if poke_url else 0
                if poke_id < 1 or poke_id > max_id:
                    continue
                if poke_id not in pokemon_data:
                    continue
                it_name = sp_name_it.get(poke_name, poke_name.capitalize())
                type_pokemon_names.append(it_name)

        pokemon_list_text = ""
        if type_pokemon_names:
            pokemon_list_text = (
                f"\n\nPokemon di tipo {name_it} ({len(type_pokemon_names)}):\n"
                + ", ".join(sorted(type_pokemon_names))
            )

        page_content = f"""\
Tipo: {name_it}

Attacco - Super efficace (x2) contro: {', '.join(super_eff) or 'Nessuno'}
Attacco - Poco efficace (x0.5) contro: {', '.join(not_very) or 'Nessuno'}
Attacco - Nessun effetto (x0) su: {', '.join(no_damage_to) or 'Nessuno'}

Difesa - Debole (x2) a: {', '.join(weak_to) or 'Nessuno'}
Difesa - Resiste (x0.5) a: {', '.join(resists) or 'Nessuno'}
Difesa - Immune (x0) a: {', '.join(immune_to) or 'Nessuno'}

Nota: per Pokemon doppio tipo, moltiplicare i fattori di ciascun tipo."""

        if pokemon_list_text:
            page_content += pokemon_list_text

        metadata = {
            "entity_type": "type",
            "type_id": tid,
            "name_en": name_en,
            "name_it": name_it.lower(),
            "generation": generation,
            "pokemon_count": len(type_pokemon_names),
        }

        docs.append(Document(page_content=page_content, metadata=metadata))

    return docs


# --- Ability Documents ---


def build_ability_documents(
    abilities_data: dict[int, dict],
    generation: int,
    species_data: dict[int, dict] | None = None,
    pokemon_data: dict[int, dict] | None = None,
) -> list[Document]:
    """Build one Document per ability for the given generation."""
    # Build species name lookup for Pokemon list
    sp_name_it: dict[str, str] = {}
    if species_data:
        for sp in species_data.values():
            slug = sp.get("name", "")
            it = _get_localized(sp.get("names", []), "it")
            if slug and it:
                sp_name_it[slug] = it

    max_id = MAX_POKEMON_PER_GEN.get(generation, 1025) if pokemon_data else 0

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

        # Build Pokemon list for this ability (filtered by generation)
        ab_pokemon_normal: list[str] = []
        ab_pokemon_hidden: list[str] = []
        if pokemon_data and species_data:
            for entry in ability.get("pokemon", []):
                poke_name = entry.get("pokemon", {}).get("name", "")
                poke_url = entry.get("pokemon", {}).get("url", "")
                poke_id = int(poke_url.rstrip("/").split("/")[-1]) if poke_url else 0
                if poke_id < 1 or poke_id > max_id:
                    continue
                if poke_id not in pokemon_data:
                    continue
                it_name = sp_name_it.get(poke_name, poke_name.capitalize())
                if entry.get("is_hidden"):
                    ab_pokemon_hidden.append(it_name)
                else:
                    ab_pokemon_normal.append(it_name)

        pokemon_text_parts: list[str] = []
        if ab_pokemon_normal:
            pokemon_text_parts.append(
                f"Pokemon con questa abilita ({len(ab_pokemon_normal)}): "
                + ", ".join(sorted(ab_pokemon_normal))
            )
        if ab_pokemon_hidden:
            pokemon_text_parts.append(
                f"Pokemon con questa abilita nascosta ({len(ab_pokemon_hidden)}): "
                + ", ".join(sorted(ab_pokemon_hidden))
            )

        page_content = f"""\
Abilita: {name_it}
Nome inglese: {name_en}
Effetto: {effect}
Descrizione: {flavor}"""

        if pokemon_text_parts:
            page_content += "\n" + "\n".join(pokemon_text_parts)

        metadata = {
            "entity_type": "ability",
            "ability_id": aid,
            "name_en": name_en.lower(),
            "name_it": name_it.lower(),
            "generation": generation,
            "pokemon_count": len(ab_pokemon_normal) + len(ab_pokemon_hidden),
        }

        docs.append(Document(page_content=page_content, metadata=metadata))

    return docs


# --- Item Documents ---


def _build_reverse_item_usage(
    generation: int,
    species_data: dict[int, dict],
) -> dict[str, list[str]]:
    """Build reverse mapping: item_slug → sorted list of Pokemon IT names.

    Uses Smogon competitive sets across all tiers to determine which
    Pokemon competitively use which items.  Item slugs use PokeAPI format
    (lowercase, hyphens) to match ``item["name"]`` in ``items_data``.
    """
    from app.ingestion.smogon_transformer import _to_slug

    # Build species display name (EN) → Italian name lookup
    sp_en_to_it: dict[str, str] = {}
    for sp in species_data.values():
        en_name = ""
        for entry in sp.get("names", []):
            if entry.get("language", {}).get("name") == "en":
                en_name = entry.get("name", "")
                break
        it_name = _get_localized(sp.get("names", []), "it")
        if en_name and it_name:
            sp_en_to_it[en_name.lower()] = it_name

    mapping: dict[str, set[str]] = {}

    _TIERS = ["ou", "uu", "ubers", "ru", "nu"]
    for tier in _TIERS:
        try:
            sets = fetch_smogon_sets(generation, tier)
        except Exception:
            continue
        for pokemon_en, pokemon_sets in sets.items():
            pokemon_it = sp_en_to_it.get(pokemon_en.lower(), pokemon_en)
            for set_data in pokemon_sets.values():
                items_raw = set_data.get("item", [])
                if isinstance(items_raw, str):
                    items_raw = [items_raw]
                for item_name in items_raw:
                    item_slug = _to_slug(item_name)
                    mapping.setdefault(item_slug, set()).add(pokemon_it)

    return {slug: sorted(names) for slug, names in mapping.items()}


def build_item_documents(
    items_data: dict[int, dict],
    generation: int,
    reverse_item_usage: dict[str, list[str]] | None = None,
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

        # Reverse item usage: which Pokemon use this item competitively
        if reverse_item_usage:
            item_slug = item["name"]  # PokeAPI slug, e.g. "life-orb"
            users = reverse_item_usage.get(item_slug, [])
            if users:
                count = len(users)
                _MAX_LISTED = 30
                if count <= _MAX_LISTED:
                    user_str = ", ".join(users)
                else:
                    user_str = (
                        ", ".join(users[:_MAX_LISTED])
                        + f" e altri {count - _MAX_LISTED}"
                    )
                page_content += (
                    f"\nPokemon che usano questo strumento"
                    f" in competitivo ({count}): {user_str}"
                )

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


def build_trainer_documents(generation: int) -> list[Document]:
    """Build documents for gym leaders, Elite Four and champions.

    Uses static data from trainer_data.py (PokeAPI doesn't expose NPC
    trainer data). Produces one document per game version that falls
    under the given generation, listing all notable trainers and their
    teams so the LLM can reason about type matchups.
    """
    from app.ingestion.trainer_data import TRAINER_DATA, _t

    docs: list[Document] = []
    for slug, data in TRAINER_DATA.items():
        if data["generation"] != generation:
            continue

        lines: list[str] = []
        game_it = data["game_it"]
        region = data["region_it"]
        lines.append(
            f"Capipalestra, Superquattro e Campione in {game_it} "
            f"(Generazione {generation}, regione {region}):"
        )

        # Gym leaders (or Kahunas for Gen 7)
        has_gyms = data.get("has_gyms", True)
        if has_gyms and data.get("gym_leaders"):
            lines.append("")
            lines.append("Capipalestra:")
            for i, gl in enumerate(data["gym_leaders"], 1):
                name_it = gl["name"]
                name_en = gl.get("name_en", "")
                name_display = (
                    f"{name_it} ({name_en})" if name_en and name_en != name_it
                    else name_it
                )
                type_it = _t(gl["type"])
                city = gl.get("city_it", "")
                team_str = ", ".join(gl["team"])
                version_note = f" [solo {gl['version']}]" if gl.get("version") else ""
                lines.append(
                    f"{i}. {name_display} - {city} - Tipo: {type_it} "
                    f"- Squadra: {team_str}{version_note}"
                )
        elif not has_gyms:
            # Gen 7 — Kahunas + Trial Captains
            if data.get("kahunas"):
                lines.append("")
                lines.append("Kahuna delle isole:")
                for kh in data["kahunas"]:
                    name = kh["name"]
                    type_it = _t(kh["type"])
                    island = kh.get("island_it", "")
                    team_str = ", ".join(kh.get("team", []))
                    lines.append(
                        f"- {name} - {island} - Tipo: {type_it} - Squadra: {team_str}"
                    )
            if data.get("trial_captains"):
                lines.append("")
                lines.append("Capitani delle prove:")
                for tc in data["trial_captains"]:
                    name = tc["name"]
                    type_it = _t(tc["type"])
                    team_str = ", ".join(tc.get("team", []))
                    if team_str:
                        lines.append(f"- {name} - Tipo: {type_it} - Squadra: {team_str}")
                    else:
                        lines.append(f"- {name} - Tipo: {type_it}")

        # Elite Four
        if data.get("elite_four"):
            lines.append("")
            lines.append("Superquattro:")
            for j, e4 in enumerate(data["elite_four"], 1):
                name_it = e4["name"]
                name_en = e4.get("name_en", "")
                name_display = (
                    f"{name_it} ({name_en})" if name_en and name_en != name_it
                    else name_it
                )
                type_it = _t(e4["type"])
                team_str = ", ".join(e4["team"])
                lines.append(f"{j}. {name_display} - Tipo: {type_it} - Squadra: {team_str}")

        # Champion
        champ = data.get("champion")
        if champ:
            lines.append("")
            name_it = champ["name"]
            name_en = champ.get("name_en", "")
            name_display = (
                f"{name_it} ({name_en})" if name_en and name_en != name_it
                else name_it
            )
            type_it = _t(champ["type"])
            team_str = ", ".join(champ["team"])
            note = f"\nNota: {champ['note']}" if champ.get("note") else ""
            lines.append(
                f"Campione: {name_display} - Tipo: {type_it} - Squadra: {team_str}{note}"
            )

        content = "\n".join(lines)
        docs.append(Document(
            page_content=content,
            metadata={
                "entity_type": "trainer_info",
                "generation": generation,
                "game_slug": slug,
                "game_it": game_it,
                "region": region,
            },
        ))

    return docs


# --- Game Static Data Documents (starters, exclusives, legendaries) ---


def build_game_data_documents(generation: int) -> list[Document]:
    """Build documents for starters, version exclusives and legendaries.

    Uses static data from game_data.py. Produces up to 3 documents per game
    slug that matches the given generation.
    """
    from app.ingestion.game_data import GAME_STATIC_DATA

    docs: list[Document] = []
    for slug, data in GAME_STATIC_DATA.items():
        if data["generation"] != generation:
            continue

        game_it = data["game_it"]
        region = data["region_it"]

        # --- Starters document ---
        starters = data.get("starters", [])
        if starters:
            lines = [
                f"Starter Pokemon in {game_it} "
                f"(Generazione {generation}, regione {region}):",
                "",
            ]
            for s in starters:
                lines.append(f"- {s['name']} ({s['type_it']})")
            lines.append("")
            lines.append(
                "Nota: lo starter scelto all'inizio del gioco non preclude "
                "la cattura di nessun altro Pokemon."
            )
            docs.append(Document(
                page_content="\n".join(lines),
                metadata={
                    "entity_type": "game_info",
                    "info_category": "starters",
                    "generation": generation,
                    "game_slug": slug,
                    "game_it": game_it,
                    "region": region,
                },
            ))

        # --- Version exclusives document ---
        exclusives = data.get("version_exclusives", {})
        if exclusives:
            lines = [
                f"Pokemon esclusivi per versione - {game_it} "
                f"(Generazione {generation}):",
                "",
            ]
            for version, poke_list in exclusives.items():
                lines.append(
                    f"Esclusivi di {version}: {', '.join(poke_list)}"
                )
            lines.append("")
            lines.append(
                "Per completare il Pokedex e necessario scambiare "
                "con l'altra versione."
            )
            docs.append(Document(
                page_content="\n".join(lines),
                metadata={
                    "entity_type": "game_info",
                    "info_category": "version_exclusives",
                    "generation": generation,
                    "game_slug": slug,
                    "game_it": game_it,
                    "region": region,
                },
            ))

        # --- Legendaries document ---
        legendaries = data.get("legendaries", [])
        if legendaries:
            lines = [
                f"Pokemon Leggendari in {game_it} "
                f"(Generazione {generation}, regione {region}):",
                "",
            ]
            for leg in legendaries:
                lines.append(
                    f"- {leg['name']} ({leg['type_it']}) - {leg['location']}"
                )
            docs.append(Document(
                page_content="\n".join(lines),
                metadata={
                    "entity_type": "game_info",
                    "info_category": "legendaries",
                    "generation": generation,
                    "game_slug": slug,
                    "game_it": game_it,
                    "region": region,
                },
            ))

        # --- Best starter document ---
        best_starter = data.get("best_starter")
        if best_starter:
            starter_names = ", ".join(s["name"] for s in data.get("starters", []))
            text = (
                f"Miglior starter in {game_it} "
                f"(Generazione {generation}, regione {region}):\n"
                f"Gli starter disponibili sono: {starter_names}.\n\n"
                f"{best_starter}"
            )
            docs.append(Document(
                page_content=text,
                metadata={
                    "entity_type": "game_info",
                    "info_category": "best_starter",
                    "generation": generation,
                    "game_slug": slug,
                    "game_it": game_it,
                    "region": region,
                },
            ))

        # --- Best team document ---
        best_team = data.get("best_team")
        if best_team:
            text = (
                f"Miglior squadra consigliata per {game_it} "
                f"(Generazione {generation}, regione {region}):\n\n"
                f"{best_team}"
            )
            docs.append(Document(
                page_content=text,
                metadata={
                    "entity_type": "game_info",
                    "info_category": "best_team",
                    "generation": generation,
                    "game_slug": slug,
                    "game_it": game_it,
                    "region": region,
                },
            ))

    return docs


# --- Regional Variant Documents ---

# Maps regional suffix to the generation that introduced the form
_VARIANT_REGION_TO_GEN: dict[str, int] = {
    "alola": 7,
    "galar": 8,
    "hisui": 8,  # Legends: Arceus counts as gen 8
    "paldea": 9,
}

_REGION_NAME_IT: dict[str, str] = {
    "alola": "Alola",
    "galar": "Galar",
    "hisui": "Hisui",
    "paldea": "Paldea",
}


def build_regional_variant_documents(
    regional_data: dict[str, dict],
    pokemon_data: dict[int, dict],
    species_data: dict[int, dict],
    all_types: dict[int, dict],
    generation: int,
    type_name_it: dict[str, str] | None = None,
    abilities_data: dict[int, dict] | None = None,
) -> list[Document]:
    """Build one Document per regional variant available in this generation.

    Regional variants use entity_type='pokemon' so existing retrieval
    (name matching) works seamlessly.
    """
    if type_name_it is None:
        type_name_it = _build_type_name_lookup(all_types)

    # Build ability name lookup
    ability_name_it: dict[str, str] = {}
    if abilities_data:
        for ab in abilities_data.values():
            slug = ab["name"]
            it_name = _get_localized(ab.get("names", []), "it")
            ability_name_it[slug] = it_name or slug.replace("-", " ").title()

    docs: list[Document] = []

    for variant_name, vdata in regional_data.items():
        # Determine region from name suffix
        region_key = ""
        for suffix in _VARIANT_REGION_TO_GEN:
            if variant_name.endswith(f"-{suffix}"):
                region_key = suffix
                break
        if not region_key:
            continue

        # Only include if this generation >= the introduction generation
        intro_gen = _VARIANT_REGION_TO_GEN[region_key]
        if generation < intro_gen:
            continue

        region_it = _REGION_NAME_IT.get(region_key, region_key.title())

        # Base Pokemon name (e.g. "raichu" from "raichu-alola")
        base_name = variant_name.rsplit(f"-{region_key}", 1)[0]

        # Get species data for the base form (for Italian name, egg groups)
        base_spec = None
        for sp in species_data.values():
            if sp.get("name") == base_name:
                base_spec = sp
                break

        base_name_it = ""
        if base_spec:
            base_name_it = _get_localized(base_spec.get("names", []), "it") or base_name.title()
        else:
            base_name_it = base_name.title()

        variant_name_it = f"{base_name_it} di {region_it}"

        # Types
        types_en = [t["type"]["name"] for t in vdata.get("types", [])]
        types_it = [type_name_it.get(t, t) for t in types_en]

        # Stats
        hp = _get_stat(vdata["stats"], "hp")
        atk = _get_stat(vdata["stats"], "attack")
        defense = _get_stat(vdata["stats"], "defense")
        sp_atk = _get_stat(vdata["stats"], "special-attack")
        sp_def = _get_stat(vdata["stats"], "special-defense")
        speed = _get_stat(vdata["stats"], "speed")
        bst = hp + atk + defense + sp_atk + sp_def + speed

        # Abilities
        abilities_list: list[str] = []
        hidden_ab = ""
        for ab_entry in vdata.get("abilities", []):
            slug = ab_entry["ability"]["name"]
            ab_it = ability_name_it.get(slug, slug.replace("-", " ").title())
            if ab_entry.get("is_hidden"):
                hidden_ab = ab_it
            else:
                abilities_list.append(ab_it)

        # Variant ID
        variant_id = vdata.get("id", 0)

        # Compare with base form
        base_poke = None
        for pid, p in pokemon_data.items():
            if p.get("name") == base_name:
                base_poke = p
                break

        diff_lines: list[str] = []
        if base_poke:
            base_types_en = [t["type"]["name"] for t in base_poke.get("types", [])]
            base_types_it = [type_name_it.get(t, t) for t in base_types_en]
            if types_it != base_types_it:
                diff_lines.append(
                    f"- Tipo: {', '.join(types_it)} (base: {', '.join(base_types_it)})"
                )
            base_bst = sum(
                _get_stat(base_poke["stats"], s)
                for s in ("hp", "attack", "defense", "special-attack",
                          "special-defense", "speed")
            )
            if bst != base_bst:
                diff_lines.append(f"- BST: {bst} (base: {base_bst})")

        diff_text = "\n".join(diff_lines) if diff_lines else "Nessuna differenza significativa"

        # Egg groups from base species
        egg_groups_en = []
        egg_groups_it_str = "Sconosciuto"
        if base_spec:
            egg_groups_en = [eg["name"] for eg in base_spec.get("egg_groups", [])]
            egg_groups_it = [EGG_GROUP_IT.get(eg, eg) for eg in egg_groups_en]
            egg_groups_it_str = ", ".join(egg_groups_it) if egg_groups_it else "Sconosciuto"

        page_content = f"""\
Nome: {variant_name_it} (Forma Regionale)
Nome inglese: {variant_name.replace('-', ' ').title()}
Forma base: {base_name_it}
Regione: {region_it} (Generazione {intro_gen})
Tipi: {', '.join(types_it)}

Statistiche base:
- HP: {hp}
- Attacco: {atk}
- Difesa: {defense}
- Attacco Speciale: {sp_atk}
- Difesa Speciale: {sp_def}
- Velocita: {speed}
- Totale: {bst}

Differenze dalla forma base:
{diff_text}

Abilita: {', '.join(abilities_list) if abilities_list else 'Nessuna'}
Abilita nascosta: {hidden_ab or 'Nessuna'}

Gruppo uova: {egg_groups_it_str}"""

        metadata = {
            "entity_type": "pokemon",
            "pokemon_id": variant_id,
            "name_en": variant_name,
            "name_it": variant_name_it.lower(),
            "types": types_en,
            "generation": generation,
            "gen_introduced": intro_gen,
            "is_legendary": False,
            "is_mythical": False,
            "bst": bst,
            "egg_groups": egg_groups_en or ["unknown"],
            "is_regional_variant": True,
            "variant_region": region_key,
            "base_pokemon_name": base_name,
        }

        docs.append(Document(page_content=page_content, metadata=metadata))

    return docs


# --- Encounter / Location Documents ---

# Maps PokeAPI version slug to Italian name
VERSION_NAME_IT: dict[str, str] = {
    "red": "Rosso", "blue": "Blu", "yellow": "Giallo",
    "gold": "Oro", "silver": "Argento", "crystal": "Cristallo",
    "ruby": "Rubino", "sapphire": "Zaffiro", "emerald": "Smeraldo",
    "firered": "Rosso Fuoco", "leafgreen": "Verde Foglia",
    "diamond": "Diamante", "pearl": "Perla", "platinum": "Platino",
    "heartgold": "Oro HeartGold", "soulsilver": "Argento SoulSilver",
    "black": "Nero", "white": "Bianco",
    "black-2": "Nero 2", "white-2": "Bianco 2",
    "x": "X", "y": "Y",
    "omega-ruby": "Rubino Omega", "alpha-sapphire": "Zaffiro Alpha",
    "sun": "Sole", "moon": "Luna",
    "ultra-sun": "Ultrasole", "ultra-moon": "Ultraluna",
    "lets-go-pikachu": "Let's Go Pikachu",
    "lets-go-eevee": "Let's Go Eevee",
    "sword": "Spada", "shield": "Scudo",
    "brilliant-diamond": "Diamante Lucente",
    "shining-pearl": "Perla Splendente",
    "legends-arceus": "Leggende Arceus",
    "scarlet": "Scarlatto", "violet": "Violetto",
}

# Maps PokeAPI version slug to generation number
VERSION_TO_GEN: dict[str, int] = {
    "red": 1, "blue": 1, "yellow": 1,
    "gold": 2, "silver": 2, "crystal": 2,
    "ruby": 3, "sapphire": 3, "emerald": 3,
    "firered": 3, "leafgreen": 3,
    "diamond": 4, "pearl": 4, "platinum": 4,
    "heartgold": 4, "soulsilver": 4,
    "black": 5, "white": 5, "black-2": 5, "white-2": 5,
    "x": 6, "y": 6, "omega-ruby": 6, "alpha-sapphire": 6,
    "sun": 7, "moon": 7, "ultra-sun": 7, "ultra-moon": 7,
    "lets-go-pikachu": 7, "lets-go-eevee": 7,
    "sword": 8, "shield": 8,
    "brilliant-diamond": 8, "shining-pearl": 8,
    "legends-arceus": 8,
    "scarlet": 9, "violet": 9,
}


def _format_location_name(slug: str) -> str:
    """Convert PokeAPI location area slug to readable name.

    'viridian-forest-area' -> 'Viridian Forest'
    'kanto-route-2-area' -> 'Kanto Route 2'
    """
    name = slug.replace("-", " ").title()
    # Remove trailing "Area" if present
    if name.endswith(" Area"):
        name = name[:-5].rstrip()
    return name


def _format_encounter_method(method_slug: str) -> str:
    """Translate encounter method to short Italian label."""
    methods = {
        "walk": "erba", "old-rod": "Amo Vecchio",
        "good-rod": "Amo Buono", "super-rod": "Super Amo",
        "surf": "surf", "rock-smash": "spaccaroccia",
        "headbutt": "Colpoditesta", "gift": "regalo",
        "gift-egg": "uovo regalo",
    }
    return methods.get(method_slug, method_slug.replace("-", " "))


def build_encounter_documents(
    encounters_data: dict[int, list],
    species_data: dict[int, dict],
    generation: int,
) -> list[Document]:
    """Build one encounter Document per Pokemon per generation.

    Groups all locations and versions for a Pokemon within a single
    generation into one document. Skips Pokemon with no encounters
    in the target generation.
    """
    docs: list[Document] = []

    for pid, encounter_list in encounters_data.items():
        spec = species_data.get(pid)
        if not spec:
            continue

        name_en = spec.get("name", f"pokemon-{pid}").capitalize()
        name_it = _get_localized(spec.get("names", []), "it") or name_en

        # Group encounters by version for this generation
        # Structure: {version_it: [(location, method, min_lv, max_lv, chance), ...]}
        version_encounters: dict[str, list[tuple[str, str, int, int, int]]] = {}

        for loc_entry in encounter_list:
            location = _format_location_name(
                loc_entry.get("location_area", {}).get("name", "unknown")
            )
            for vd in loc_entry.get("version_details", []):
                version_slug = vd.get("version", {}).get("name", "")
                vgen = VERSION_TO_GEN.get(version_slug)
                if vgen != generation:
                    continue

                version_it = VERSION_NAME_IT.get(version_slug, version_slug)

                for enc in vd.get("encounter_details", []):
                    method = _format_encounter_method(
                        enc.get("method", {}).get("name", "walk")
                    )
                    min_lv = enc.get("min_level", 0)
                    max_lv = enc.get("max_level", 0)
                    chance = enc.get("chance", 0)

                    if version_it not in version_encounters:
                        version_encounters[version_it] = []
                    version_encounters[version_it].append(
                        (location, method, min_lv, max_lv, chance)
                    )

        if not version_encounters:
            continue

        # Build document text
        lines = [f"Dove trovare {name_it} (Generazione {generation}):", ""]

        for version_it, encounters in sorted(version_encounters.items()):
            lines.append(f"Pokemon {version_it}:")

            # Deduplicate and aggregate by location
            loc_data: dict[str, list[str]] = {}
            for loc, method, min_lv, max_lv, chance in encounters:
                if loc not in loc_data:
                    loc_data[loc] = []
                if min_lv == max_lv:
                    detail = f"{method}, Lv.{min_lv}, {chance}%"
                else:
                    detail = f"{method}, Lv.{min_lv}-{max_lv}, {chance}%"
                if detail not in loc_data[loc]:
                    loc_data[loc].append(detail)

            for loc, details in loc_data.items():
                # Truncate details if too many
                if len(details) > 3:
                    details = details[:3] + ["..."]
                lines.append(f"- {loc} ({'; '.join(details)})")

            lines.append("")

        content = "\n".join(lines).rstrip()

        # Truncate if document is too long (keep under ~1500 chars)
        if len(content) > 1500:
            content = content[:1450] + "\n\n[dati aggiuntivi troncati]"

        docs.append(Document(
            page_content=content,
            metadata={
                "entity_type": "encounter",
                "pokemon_id": pid,
                "name_en": name_en.lower(),
                "name_it": name_it.lower(),
                "generation": generation,
            },
        ))

    return docs


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

    reverse_learnset = _build_reverse_learnset(
        all_data["pokemon"], all_data["species"], generation,
    )
    docs.extend(build_move_documents(
        all_data["moves"],
        generation,
        type_name_it=type_name_it,
        reverse_learnset=reverse_learnset,
    ))

    docs.extend(build_type_documents(
        all_data["types"],
        generation,
        type_name_it=type_name_it,
        species_data=all_data.get("species"),
        pokemon_data=all_data.get("pokemon"),
    ))

    docs.extend(build_ability_documents(
        all_data["abilities"],
        generation,
        species_data=all_data.get("species"),
        pokemon_data=all_data.get("pokemon"),
    ))

    # Items only for the latest gen (no historical tracking available)
    if generation == max(MAX_POKEMON_PER_GEN.keys()):
        reverse_item_usage = _build_reverse_item_usage(
            generation, all_data["species"],
        )
        docs.extend(build_item_documents(
            all_data["items"],
            generation,
            reverse_item_usage=reverse_item_usage,
        ))

    docs.extend(build_nature_documents(
        all_data["natures"],
        generation,
    ))

    docs.extend(build_trainer_documents(generation))

    docs.extend(build_game_data_documents(generation))

    # Regional variants (if fetched)
    if all_data.get("regional_variants"):
        docs.extend(build_regional_variant_documents(
            all_data["regional_variants"],
            all_data["pokemon"],
            all_data["species"],
            all_data["types"],
            generation,
            type_name_it=type_name_it,
            abilities_data=all_data.get("abilities"),
        ))

    # Encounters (if fetched)
    if all_data.get("encounters"):
        docs.extend(build_encounter_documents(
            all_data["encounters"],
            all_data["species"],
            generation,
        ))

    # Smogon competitive sets (multiple tiers)
    _SMOGON_TIERS = ["ou", "uu", "ubers", "ru", "nu"]
    for tier in _SMOGON_TIERS:
        try:
            smogon_sets = fetch_smogon_sets(generation, tier)
            if smogon_sets:
                smogon_docs = build_smogon_documents(
                    smogon_sets, all_data, generation, tier=tier,
                )
                docs.extend(smogon_docs)
                logger.info(
                    "Gen %d: %d Smogon %s documents built",
                    generation, len(smogon_docs), tier.upper(),
                )
        except Exception as exc:
            logger.warning(
                "Gen %d: Smogon %s fetch/build failed, skipping: %s",
                generation, tier.upper(), exc,
            )

    return docs
