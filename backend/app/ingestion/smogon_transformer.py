"""Transform Smogon JSON sets into per-Pokemon LangChain Documents.

All translations come from PokeAPI official Italian names (never literal).
The conversion chain is:
    Smogon display name  ->  PokeAPI slug  ->  Italian official name

Slug convention: lowercase, spaces -> hyphens  (e.g. "Swords Dance" -> "swords-dance")
"""

import logging
import re
from typing import Any

from langchain_core.documents import Document

logger = logging.getLogger(__name__)

# Smogon EV stat keys -> Italian stat names
_STAT_IT = {
    "hp": "PS",
    "atk": "Attacco",
    "def": "Difesa",
    "spa": "Att.Sp",
    "spd": "Dif.Sp",
    "spe": "Velocita",
}

# Nature stat modifiers (PokeAPI slug -> short Italian label)
_NATURE_STAT_SHORT = {
    "attack": "Attacco",
    "defense": "Difesa",
    "special-attack": "Att.Sp",
    "special-defense": "Dif.Sp",
    "speed": "Velocita",
}

# Max chars per document (avoids overly long documents for ChromaDB)
_MAX_DOC_CHARS = 2500


# ---------------------------------------------------------------------------
# Slug helpers
# ---------------------------------------------------------------------------

def _to_slug(display_name: str) -> str:
    """Convert a Smogon display name to a PokeAPI-style slug.

    "Swords Dance"  -> "swords-dance"
    "King's Rock"   -> "kings-rock"
    "Mr. Mime"      -> "mr-mime"
    """
    s = display_name.lower()
    s = s.replace("'", "").replace("'", "")  # king's -> kings
    s = s.replace(". ", "-").replace(".", "")  # mr. mime -> mr-mime
    s = re.sub(r"[^a-z0-9]+", "-", s)         # spaces/special -> hyphens
    return s.strip("-")


# ---------------------------------------------------------------------------
# Lookup builders
# ---------------------------------------------------------------------------

def _get_localized(entries: list[dict], lang: str) -> str:
    """Extract a localized name from a list of name/language entries."""
    for entry in entries:
        if entry.get("language", {}).get("name") == lang:
            return entry.get("name", "")
    return ""


def _build_en_slug_to_it(data: dict[int, dict]) -> dict[str, str]:
    """Build {en_slug: it_name} from any PokeAPI resource with 'name' + 'names'.

    Works for moves, abilities, items, species, natures.
    """
    lookup: dict[str, str] = {}
    for entry in data.values():
        slug = entry.get("name", "")
        it_name = _get_localized(entry.get("names", []), "it")
        if slug and it_name:
            lookup[slug] = it_name
    return lookup


def _build_en_display_to_it(
    data: dict[int, dict],
) -> dict[str, str]:
    """Build {en_display_lowercase: it_name} from PokeAPI resource.

    This allows direct lookup from Smogon display names (e.g. "Swords Dance")
    without going through slug first, as a fallback/complement.
    """
    lookup: dict[str, str] = {}
    for entry in data.values():
        en_name = _get_localized(entry.get("names", []), "en")
        it_name = _get_localized(entry.get("names", []), "it")
        if en_name and it_name:
            lookup[en_name.lower()] = it_name
    return lookup


def _build_nature_lookup(
    natures_data: dict[int, dict],
) -> dict[str, dict]:
    """Build {en_slug: {name_it, increased, decreased}} for natures."""
    lookup: dict[str, dict] = {}
    for nature in natures_data.values():
        slug = nature.get("name", "")
        it_name = _get_localized(nature.get("names", []), "it")
        if not slug:
            continue
        increased = nature.get("increased_stat")
        decreased = nature.get("decreased_stat")
        info: dict[str, Any] = {"name_it": it_name or slug.capitalize()}
        if increased and decreased:
            inc = _NATURE_STAT_SHORT.get(increased["name"], increased["name"])
            dec = _NATURE_STAT_SHORT.get(decreased["name"], decreased["name"])
            info["label"] = f"+{inc}, -{dec}"
        else:
            info["label"] = "Neutra"
        lookup[slug] = info
    return lookup


def _build_type_name_lookup(all_types: dict[int, dict]) -> dict[str, str]:
    """Build {en_slug: it_name} for types (for tera types)."""
    lookup: dict[str, str] = {}
    for t in all_types.values():
        en = t.get("name", "")
        it = _get_localized(t.get("names", []), "it")
        if en and it:
            lookup[en] = it
    return lookup


# ---------------------------------------------------------------------------
# Translation helpers
# ---------------------------------------------------------------------------

def _translate(
    display_name: str,
    slug_lookup: dict[str, str],
    display_lookup: dict[str, str],
) -> str:
    """Translate a Smogon display name to Italian, with fallback to English.

    1. Try slug lookup:   "Swords Dance" -> slug "swords-dance" -> lookup
    2. Try display lookup: lowercase display name -> lookup
    3. Fallback: return original English name
    """
    slug = _to_slug(display_name)
    it = slug_lookup.get(slug)
    if it:
        return it
    it = display_lookup.get(display_name.lower())
    if it:
        return it
    return display_name  # fallback EN


def _translate_option(
    value: str | list[str],
    slug_lookup: dict[str, str],
    display_lookup: dict[str, str],
) -> str:
    """Translate a single value or a list of alternatives.

    "Life Orb"              -> "Assorbisfera"
    ["Life Orb", "Lum Berry"] -> "Assorbisfera / Baccalanguo"
    """
    if isinstance(value, list):
        parts = [_translate(v, slug_lookup, display_lookup) for v in value]
        return " / ".join(parts)
    return _translate(value, slug_lookup, display_lookup)


# ---------------------------------------------------------------------------
# Document builder
# ---------------------------------------------------------------------------

def build_smogon_documents(
    smogon_sets: dict[str, dict],
    all_data: dict,
    generation: int,
    tier: str = "ou",
) -> list[Document]:
    """Build one Document per Pokemon from Smogon sets.

    Args:
        smogon_sets: parsed Smogon JSON {PokemonName: {SetName: {...}}}
        all_data: full PokeAPI data dict (for translations)
        generation: generation number (1-9)
        tier: tier label (e.g. "ou")

    Returns:
        List of Documents with entity_type="smogon_set"
    """
    if not smogon_sets:
        return []

    # Build all translation lookups from PokeAPI data
    move_slug = _build_en_slug_to_it(all_data.get("moves", {}))
    move_disp = _build_en_display_to_it(all_data.get("moves", {}))

    ability_slug = _build_en_slug_to_it(all_data.get("abilities", {}))
    ability_disp = _build_en_display_to_it(all_data.get("abilities", {}))

    item_slug = _build_en_slug_to_it(all_data.get("items", {}))
    item_disp = _build_en_display_to_it(all_data.get("items", {}))

    nature_lookup = _build_nature_lookup(all_data.get("natures", {}))

    species_slug = _build_en_slug_to_it(all_data.get("species", {}))
    species_disp = _build_en_display_to_it(all_data.get("species", {}))

    type_lookup = _build_type_name_lookup(all_data.get("types", {}))

    docs: list[Document] = []

    for pokemon_en, sets in smogon_sets.items():
        # Translate Pokemon name
        pokemon_it = _translate(pokemon_en, species_slug, species_disp)

        # Build all sets for this Pokemon
        set_blocks: list[str] = []

        for set_name_en, set_data in sets.items():
            lines: list[str] = []

            # Set name = first move or a label — translate it
            set_name_it = _translate(set_name_en, move_slug, move_disp)
            # Fallback: if not a move, try ability/item translations
            if set_name_it == set_name_en:
                set_name_it = _translate(set_name_en, ability_slug, ability_disp)
            if set_name_it == set_name_en:
                set_name_it = _translate(set_name_en, item_slug, item_disp)
            lines.append(f"Set: {set_name_it}")

            # Ability
            if "ability" in set_data:
                ab = _translate_option(set_data["ability"], ability_slug, ability_disp)
                lines.append(f"Abilita: {ab}")

            # Item
            if "item" in set_data:
                itm = _translate_option(set_data["item"], item_slug, item_disp)
                lines.append(f"Strumento: {itm}")

            # Nature
            if "nature" in set_data:
                nat_val = set_data["nature"]
                if isinstance(nat_val, list):
                    nat_parts = []
                    for n in nat_val:
                        info = nature_lookup.get(n.lower(), {})
                        name = info.get("name_it", n)
                        label = info.get("label", "")
                        nat_parts.append(f"{name} ({label})" if label else name)
                    lines.append(f"Natura: {' / '.join(nat_parts)}")
                else:
                    info = nature_lookup.get(nat_val.lower(), {})
                    name = info.get("name_it", nat_val)
                    label = info.get("label", "")
                    lines.append(f"Natura: {name} ({label})" if label else f"Natura: {name}")

            # EVs (can be a dict or a list of alternative dicts)
            if "evs" in set_data:
                evs_raw = set_data["evs"]
                if isinstance(evs_raw, dict):
                    evs_list = [evs_raw]
                else:
                    evs_list = evs_raw  # list of dicts
                ev_strs = []
                for ev_dict in evs_list:
                    parts = []
                    for stat_key, val in ev_dict.items():
                        stat_it = _STAT_IT.get(stat_key, stat_key)
                        parts.append(f"{stat_it} {val}")
                    ev_strs.append(" / ".join(parts))
                if len(ev_strs) == 1:
                    lines.append(f"EV: {ev_strs[0]}")
                else:
                    lines.append(f"EV: {' oppure '.join(ev_strs)}")

            # IVs (only if non-standard; can be dict or list of dicts)
            if "ivs" in set_data:
                ivs_raw = set_data["ivs"]
                if isinstance(ivs_raw, dict):
                    ivs_list = [ivs_raw]
                else:
                    ivs_list = ivs_raw
                iv_strs = []
                for iv_dict in ivs_list:
                    parts = []
                    for stat_key, val in iv_dict.items():
                        stat_it = _STAT_IT.get(stat_key, stat_key)
                        parts.append(f"{stat_it} {val}")
                    iv_strs.append(" / ".join(parts))
                if len(iv_strs) == 1:
                    lines.append(f"IV: {iv_strs[0]}")
                else:
                    lines.append(f"IV: {' oppure '.join(iv_strs)}")

            # Moves
            if "moves" in set_data:
                move_parts = []
                for move_entry in set_data["moves"]:
                    if isinstance(move_entry, list):
                        # Alternatives: ["Scale Shot", "Stone Edge"]
                        alts = [_translate(m, move_slug, move_disp) for m in move_entry]
                        move_parts.append(" / ".join(alts))
                    else:
                        move_parts.append(_translate(move_entry, move_slug, move_disp))
                lines.append(f"Mosse: {', '.join(move_parts)}")

            # Tera types (gen 9 only)
            if "teratypes" in set_data:
                tera_parts = []
                for tt in set_data["teratypes"]:
                    tera_it = type_lookup.get(tt.lower(), tt)
                    tera_parts.append(tera_it)
                lines.append(f"Tera tipo: {' / '.join(tera_parts)}")

            set_blocks.append("\n".join(lines))

        # Build full document
        header = f"Build Smogon per {pokemon_it} - {tier.upper()} (Generazione {generation}):"

        # Truncate if too many sets
        full_content = header + "\n\n" + "\n\n".join(set_blocks)
        if len(full_content) > _MAX_DOC_CHARS and len(set_blocks) > 3:
            # Keep first 3 sets + truncation note
            truncated = header + "\n\n" + "\n\n".join(set_blocks[:3])
            remaining = len(set_blocks) - 3
            truncated += f"\n\n(... altri {remaining} set disponibili su Smogon)"
            full_content = truncated

        metadata = {
            "entity_type": "smogon_set",
            "name_it": pokemon_it.lower(),
            "name_en": pokemon_en.lower(),
            "tier": tier,
            "generation": generation,
        }

        docs.append(Document(page_content=full_content, metadata=metadata))

    return docs
