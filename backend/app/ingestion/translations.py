"""Centralized Italian translation mappings for PokeAPI data.

All static translation dicts live here to keep transformers.py clean.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)


# ── Type name EN → IT (single source of truth) ───────────────────
TYPE_EN_TO_IT: dict[str, str] = {
    "Normal": "Normale", "Fire": "Fuoco", "Water": "Acqua",
    "Electric": "Elettro", "Grass": "Erba", "Ice": "Ghiaccio",
    "Fighting": "Lotta", "Poison": "Veleno", "Ground": "Terra",
    "Flying": "Volante", "Psychic": "Psico", "Bug": "Coleottero",
    "Rock": "Roccia", "Ghost": "Spettro", "Dragon": "Drago",
    "Dark": "Buio", "Steel": "Acciaio", "Fairy": "Folletto",
    "Mixed": "Misto",
}


# ── Regional form labels for display ─────────────────────────────
_REGION_LABEL_IT: dict[str, str] = {
    "alola": "di Alola",
    "galar": "di Galar",
    "hisui": "di Hisui",
    "paldea": "di Paldea",
}

_REGION_ADJ_EN: dict[str, str] = {
    "alola": "alolan",
    "galar": "galarian",
    "hisui": "hisuian",
    "paldea": "paldean",
}


def _normalize_key(name: str) -> str:
    """Lowercase and normalize curly apostrophes to straight."""
    return name.lower().replace("\u2019", "'")


def build_pokemon_name_lookup(
    species_data: dict[int, dict],
) -> dict[str, str]:
    """Build a shared EN display name → IT display name lookup.

    Maps lowercased English display names to Italian display names.
    Also generates regional form entries from species varieties.

    Returns a dict like::

        {"great tusk": "Grandizanne",
         "vulpix": "Vulpix",
         "vulpix-alola": "Vulpix di Alola",
         "alolan vulpix": "Vulpix di Alola", ...}
    """
    lookup: dict[str, str] = {}

    for sp in species_data.values():
        en_name = ""
        it_name = ""
        for entry in sp.get("names", []):
            lang = entry.get("language", {}).get("name")
            if lang == "en":
                en_name = entry.get("name", "")
            elif lang == "it":
                it_name = entry.get("name", "")

        if not en_name or not it_name:
            continue

        en_key = _normalize_key(en_name)
        lookup[en_key] = it_name

        # Generate regional form entries from varieties
        for variety in sp.get("varieties", []):
            if variety.get("is_default"):
                continue
            var_name = variety.get("pokemon", {}).get("name", "")
            for suffix, label in _REGION_LABEL_IT.items():
                if var_name.endswith(f"-{suffix}"):
                    regional_it = f"{it_name} {label}"
                    # "vulpix-alola" → "Vulpix di Alola"
                    lookup[var_name] = regional_it
                    # "alolan vulpix" → "Vulpix di Alola"
                    adj = _REGION_ADJ_EN.get(suffix, "")
                    if adj:
                        lookup[f"{adj} {en_key}"] = regional_it
                    break

    return lookup


def translate_pokemon_name(
    name: str,
    lookup: dict[str, str],
) -> str:
    """Translate a single Pokemon name EN → IT using the lookup.

    Handles: plain names, hyphenated regional forms (``Vulpix-Alola``),
    prefixed regional forms (``Alolan Dugtrio``), slash alternatives
    (``Pansage/Pansear/Panpour``), and partially-Italian form labels
    (``Lycanroc Forma Giorno``).

    Falls back to the original English name with a logged warning
    when no translation is found.
    """
    # Handle slash alternatives: translate each part separately
    if "/" in name:
        parts = [translate_pokemon_name(p.strip(), lookup) for p in name.split("/")]
        return "/".join(parts)

    key = _normalize_key(name)

    # Direct match (covers: plain names, hyphenated regionals, paradox)
    if key in lookup:
        return lookup[key]

    # Hyphenated regional not pre-computed: "Farfetch'd-Galar"
    for suffix, label in _REGION_LABEL_IT.items():
        tag = f"-{suffix}"
        if key.endswith(tag):
            base_key = key[: -len(tag)]
            base_it = lookup.get(base_key)
            if base_it:
                return f"{base_it} {label}"
            break

    # Already partially Italian: "Lycanroc Forma Giorno"
    if " forma " in key:
        base_word = name.split(" ", 1)[0]
        base_it = lookup.get(_normalize_key(base_word))
        if base_it:
            return f"{base_it} {name.split(' ', 1)[1]}"

    # No translation found
    logger.warning("No IT translation for Pokemon name: %s", name)
    return name


def substitute_pokemon_names_in_text(
    text: str,
    lookup: dict[str, str],
) -> str:
    """Replace English Pokemon names in prose text with Italian names.

    Only substitutes names that actually differ EN → IT.
    Processes longer names first to prevent partial matches
    (e.g. ``Iron Valiant`` before ``Iron``).
    """
    # Filter to only names that actually change
    replacements: dict[str, str] = {}
    for en_lower, it_name in lookup.items():
        if en_lower != it_name.lower():
            replacements[en_lower] = it_name

    if not replacements:
        return text

    # Longest first to avoid partial matches
    for en_lower in sorted(replacements, key=len, reverse=True):
        it_name = replacements[en_lower]
        pattern = r"\b" + re.escape(en_lower) + r"\b"
        text = re.sub(pattern, it_name, text, flags=re.IGNORECASE)

    return text

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

# Regional variant region slug to generation number
VARIANT_REGION_TO_GEN: dict[str, int] = {
    "alola": 7,
    "galar": 8,
    "hisui": 8,  # Legends: Arceus counts as gen 8
    "paldea": 9,
}

# Regional variant region slug to Italian display name
REGION_NAME_IT: dict[str, str] = {
    "alola": "Alola",
    "galar": "Galar",
    "hisui": "Hisui",
    "paldea": "Paldea",
}

# PokeAPI encounter method slug to Italian label
ENCOUNTER_METHOD_IT: dict[str, str] = {
    "walk": "erba alta",
    "old-rod": "Amo Vecchio",
    "good-rod": "Amo Buono",
    "super-rod": "Super Amo",
    "surf": "Surf",
    "rock-smash": "Spaccaroccia",
    "headbutt": "Bottintesta",
    "gift": "regalo",
    "gift-egg": "uovo regalo",
    "dark-grass": "erba scura",
    "grass-spots": "erba tremante",
    "cave-spots": "polvere nelle grotte",
    "bridge-spots": "ombre sui ponti",
    "surf-spots": "increspature nell'acqua",
    "super-rod-spots": "increspature (Super Amo)",
    "yellow-flowers": "fiori gialli",
    "purple-flowers": "fiori viola",
    "red-flowers": "fiori rossi",
    "rough-terrain": "terreno accidentato",
    "only-one": "evento unico",
    "pokeflute": "Pokeflauto",
    "squirt-bottle": "Annaffiatoio",
    "berry-piles": "cumuli di bacche",
    "roaming": "vagante",
    "radar": "Pokeradar",
    "honey-tree": "albero di Miele",
    "fishing": "pesca",
    "tall-grass": "erba altissima",
    "seaweed": "alghe",
    "bubble-spots": "bolle nell'acqua",
    "rock-smash-spots": "rocce fragili",
}

# PokeAPI location-area slug to Italian name.
# Fallback for slugs not in this dict: slug → Title Case.
LOCATION_NAME_IT: dict[str, str] = {
    # --- Gen 1: Kanto ---
    "kanto-route-1": "Percorso 1",
    "kanto-route-2-south-towards-viridian-city": "Percorso 2 (sud)",
    "kanto-route-2-north-towards-pewter-city": "Percorso 2 (nord)",
    "kanto-route-3": "Percorso 3",
    "kanto-route-4": "Percorso 4",
    "kanto-route-5": "Percorso 5",
    "kanto-route-6": "Percorso 6",
    "kanto-route-7": "Percorso 7",
    "kanto-route-8": "Percorso 8",
    "kanto-route-9": "Percorso 9",
    "kanto-route-10": "Percorso 10",
    "kanto-route-11": "Percorso 11",
    "kanto-route-12": "Percorso 12",
    "kanto-route-13": "Percorso 13",
    "kanto-route-14": "Percorso 14",
    "kanto-route-15": "Percorso 15",
    "kanto-route-16": "Percorso 16",
    "kanto-route-17": "Percorso 17 (Pista Ciclabile)",
    "kanto-route-18": "Percorso 18",
    "kanto-sea-route-19": "Percorso 19",
    "kanto-sea-route-20": "Percorso 20",
    "kanto-sea-route-21": "Percorso 21",
    "kanto-route-22": "Percorso 22",
    "kanto-route-23": "Percorso 23",
    "kanto-route-24": "Percorso 24",
    "kanto-route-25": "Percorso 25",
    "kanto-route-26": "Percorso 26",
    "kanto-route-27": "Percorso 27",
    "kanto-route-28": "Percorso 28",
    "viridian-forest": "Bosco Smeraldo",
    "mt-moon-1f": "Monte Luna (1P)",
    "mt-moon-2f": "Monte Luna (2P)",
    "mt-moon-b1f": "Monte Luna (S1)",
    "mt-moon-b2f": "Monte Luna (S2)",
    "rock-tunnel-1f": "Tunnel Roccioso (1P)",
    "rock-tunnel-b1f": "Tunnel Roccioso (S1)",
    "pokemon-tower-3f": "Torre Pokemon (3P)",
    "pokemon-tower-4f": "Torre Pokemon (4P)",
    "pokemon-tower-5f": "Torre Pokemon (5P)",
    "pokemon-tower-6f": "Torre Pokemon (6P)",
    "pokemon-tower-7f": "Torre Pokemon (7P)",
    "kanto-safari-zone-middle": "Zona Safari (centro)",
    "kanto-safari-zone-area-1-east": "Zona Safari (est)",
    "kanto-safari-zone-area-2-north": "Zona Safari (nord)",
    "kanto-safari-zone-area-3-west": "Zona Safari (ovest)",
    "seafoam-islands-1f": "Isole Spumarine (1P)",
    "seafoam-islands-b1f": "Isole Spumarine (S1)",
    "seafoam-islands-b2f": "Isole Spumarine (S2)",
    "seafoam-islands-b3f": "Isole Spumarine (S3)",
    "seafoam-islands-b4f": "Isole Spumarine (S4)",
    "kanto-victory-road-1-1f": "Via Vittoria (1P)",
    "kanto-victory-road-1-2f": "Via Vittoria (2P)",
    "kanto-victory-road-1-3f": "Via Vittoria (3P)",
    "cerulean-cave-1f": "Grotta Celeste (1P)",
    "cerulean-cave-2f": "Grotta Celeste (2P)",
    "cerulean-cave-b1f": "Grotta Celeste (S1)",
    "power-plant": "Centrale Elettrica",
    "digletts-cave": "Grotta Diglett",
    "pokemon-mansion-1f": "Villa Pokemon (1P)",
    "pokemon-mansion-2f": "Villa Pokemon (2P)",
    "pokemon-mansion-3f": "Villa Pokemon (3P)",
    "pokemon-mansion-b1f": "Villa Pokemon (S1)",
    "tohjo-falls": "Cascate Tohjo",
    # --- Gen 2: Johto ---
    "johto-route-29": "Percorso 29",
    "johto-route-30": "Percorso 30",
    "johto-route-31": "Percorso 31",
    "johto-route-32": "Percorso 32",
    "johto-route-33": "Percorso 33",
    "johto-route-34": "Percorso 34",
    "johto-route-35": "Percorso 35",
    "johto-route-36": "Percorso 36",
    "johto-route-37": "Percorso 37",
    "johto-route-38": "Percorso 38",
    "johto-route-39": "Percorso 39",
    "johto-sea-route-40": "Percorso 40",
    "johto-sea-route-41": "Percorso 41",
    "johto-route-42": "Percorso 42",
    "johto-route-43": "Percorso 43",
    "johto-route-44": "Percorso 44",
    "johto-route-45": "Percorso 45",
    "johto-route-46": "Percorso 46",
    "johto-route-47": "Percorso 47",
    "johto-route-48": "Percorso 48",
    "ilex-forest": "Bosco di Lecci",
    "union-cave-1f": "Grotta di Mezzo (1P)",
    "union-cave-b1f": "Grotta di Mezzo (S1)",
    "union-cave-b2f": "Grotta di Mezzo (S2)",
    "slowpoke-well-1f": "Pozzo Slowpoke (1P)",
    "slowpoke-well-b1f": "Pozzo Slowpoke (S1)",
    "national-park": "Parco Nazionale",
    "burned-tower-1f": "Torre Bruciata (1P)",
    "burned-tower-b1f": "Torre Bruciata (S1)",
    "bell-tower-2f": "Torre Campana (2P)",
    "bell-tower-3f": "Torre Campana (3P)",
    "bell-tower-4f": "Torre Campana (4P)",
    "bell-tower-5f": "Torre Campana (5P)",
    "whirl-islands-1f": "Isole Vorticose (1P)",
    "whirl-islands-b1f": "Isole Vorticose (S1)",
    "whirl-islands-b2f": "Isole Vorticose (S2)",
    "mt-mortar-1f": "Monte Scodella (1P)",
    "mt-mortar-lower-cave": "Monte Scodella (grotta inferiore)",
    "mt-mortar-upper-cave": "Monte Scodella (grotta superiore)",
    "lake-of-rage": "Lago d'Ira",
    "ice-path-1f": "Via Gelata (1P)",
    "ice-path-b1f": "Via Gelata (S1)",
    "ice-path-b2f": "Via Gelata (S2)",
    "ice-path-b3f": "Via Gelata (S3)",
    "dragons-den": "Tana del Drago",
    "dark-cave-violet-city-entrance": "Grotta Scura (ingresso Violapoli)",
    "dark-cave-blackthorn-city-entrance": "Grotta Scura (ingresso Ebanopoli)",
    "mt-silver-outside": "Monte Argento (esterno)",
    "mt-silver-1f": "Monte Argento (1P)",
    "mt-silver-2f": "Monte Argento (2P)",
    "mt-silver-3f": "Monte Argento (3P)",
    "mt-silver-4f": "Monte Argento (4P)",
    "ruins-of-alph-outside": "Rovine d'Alfa (esterno)",
    "sprout-tower-2f": "Torre Sprout (2P)",
    "sprout-tower-3f": "Torre Sprout (3P)",
    # --- Gen 3: Hoenn ---
    "hoenn-route-101": "Percorso 101",
    "hoenn-route-102": "Percorso 102",
    "hoenn-route-103": "Percorso 103",
    "hoenn-route-104": "Percorso 104",
    "hoenn-route-105": "Percorso 105",
    "hoenn-route-106": "Percorso 106",
    "hoenn-route-107": "Percorso 107",
    "hoenn-route-108": "Percorso 108",
    "hoenn-route-109": "Percorso 109",
    "hoenn-route-110": "Percorso 110",
    "hoenn-route-111": "Percorso 111",
    "hoenn-route-112": "Percorso 112",
    "hoenn-route-113": "Percorso 113",
    "hoenn-route-114": "Percorso 114",
    "hoenn-route-115": "Percorso 115",
    "hoenn-route-116": "Percorso 116",
    "hoenn-route-117": "Percorso 117",
    "hoenn-route-118": "Percorso 118",
    "hoenn-route-119": "Percorso 119",
    "hoenn-route-120": "Percorso 120",
    "hoenn-route-121": "Percorso 121",
    "hoenn-route-122": "Percorso 122",
    "hoenn-route-123": "Percorso 123",
    "hoenn-route-124": "Percorso 124",
    "hoenn-route-125": "Percorso 125",
    "hoenn-route-126": "Percorso 126",
    "hoenn-route-127": "Percorso 127",
    "hoenn-route-128": "Percorso 128",
    "hoenn-route-129": "Percorso 129",
    "hoenn-route-130": "Percorso 130",
    "hoenn-route-131": "Percorso 131",
    "hoenn-route-132": "Percorso 132",
    "hoenn-route-133": "Percorso 133",
    "hoenn-route-134": "Percorso 134",
    "petalburg-woods": "Bosco Petalo",
    "rusturf-tunnel": "Tunnel Menferro",
    "granite-cave-1f": "Grotta Pietrosa (1P)",
    "granite-cave-b1f": "Grotta Pietrosa (S1)",
    "granite-cave-b2f": "Grotta Pietrosa (S2)",
    "meteor-falls": "Cascate Meteora",
    "meteor-falls-back": "Cascate Meteora (fondo)",
    "meteor-falls-b1f": "Cascate Meteora (S1)",
    "fiery-path": "Cammino Ardente",
    "jagged-pass": "Passo Selvaggio",
    "mt-pyre-1f": "Monte Pira (1P)",
    "mt-pyre-2f": "Monte Pira (2P)",
    "mt-pyre-3f": "Monte Pira (3P)",
    "mt-pyre-4f": "Monte Pira (4P)",
    "mt-pyre-5f": "Monte Pira (5P)",
    "mt-pyre-6f": "Monte Pira (6P)",
    "mt-pyre-outside": "Monte Pira (esterno)",
    "mt-pyre-summit": "Monte Pira (vetta)",
    "shoal-cave-high-tide": "Grotta Ondosa (alta marea)",
    "shoal-cave-low-tide": "Grotta Ondosa (bassa marea)",
    "seafloor-cavern": "Antro Abissale",
    "cave-of-origin-1f": "Grotta dei Tempi (1P)",
    "hoenn-victory-road-1f": "Via Vittoria (1P)",
    "hoenn-victory-road-b1f": "Via Vittoria (S1)",
    "sky-pillar-1f": "Torre dei Cieli (1P)",
    "sky-pillar-3f": "Torre dei Cieli (3P)",
    "sky-pillar-5f": "Torre dei Cieli (5P)",
    "new-mauville": "Ciclanova",
    "abandoned-ship": "Vecchia Nave",
    "hoenn-safari-zone-sw": "Zona Safari (SO)",
    "hoenn-safari-zone-se": "Zona Safari (SE)",
    "terra-cave": "Grotta Terra",
    "marine-cave": "Grotta Mare",
    "southern-island": "Isola Remota",
    "sea-mauville": "Ciclamare",
    # --- Gen 4: Sinnoh ---
    "sinnoh-route-201": "Percorso 201",
    "sinnoh-route-202": "Percorso 202",
    "sinnoh-route-203": "Percorso 203",
    "sinnoh-route-204-south-towards-jubilife-city": "Percorso 204 (sud)",
    "sinnoh-route-204-north-towards-floaroma-town": "Percorso 204 (nord)",
    "sinnoh-route-205-south-towards-floaroma-town": "Percorso 205 (sud)",
    "sinnoh-route-205-east-towards-eterna-city": "Percorso 205 (est)",
    "sinnoh-route-206": "Percorso 206",
    "sinnoh-route-207": "Percorso 207",
    "sinnoh-route-208": "Percorso 208",
    "sinnoh-route-209": "Percorso 209",
    "sinnoh-route-210-south-towards-solaceon-town": "Percorso 210 (sud)",
    "sinnoh-route-210-west-towards-celestic-town": "Percorso 210 (ovest)",
    "sinnoh-route-211-west-towards-eterna-city": "Percorso 211 (ovest)",
    "sinnoh-route-211-east-towards-celestic-town": "Percorso 211 (est)",
    "sinnoh-route-212-north-towards-hearthome-city": "Percorso 212 (nord)",
    "sinnoh-route-212-east-towards-pastoria-city": "Percorso 212 (est)",
    "sinnoh-route-213": "Percorso 213",
    "sinnoh-route-214": "Percorso 214",
    "sinnoh-route-215": "Percorso 215",
    "sinnoh-route-216": "Percorso 216",
    "sinnoh-route-217": "Percorso 217",
    "sinnoh-route-218": "Percorso 218",
    "sinnoh-route-219": "Percorso 219",
    "sinnoh-sea-route-220": "Percorso 220",
    "sinnoh-route-221": "Percorso 221",
    "sinnoh-route-222": "Percorso 222",
    "sinnoh-sea-route-223": "Percorso 223",
    "sinnoh-route-224": "Percorso 224",
    "sinnoh-route-225": "Percorso 225",
    "sinnoh-sea-route-226": "Percorso 226",
    "sinnoh-route-227": "Percorso 227",
    "sinnoh-route-228": "Percorso 228",
    "sinnoh-route-229": "Percorso 229",
    "sinnoh-sea-route-230": "Percorso 230",
    "eterna-forest": "Bosco di Evopoli",
    "old-chateau-entrance": "Antico Chateau (ingresso)",
    "old-chateau-dining-room": "Antico Chateau (sala da pranzo)",
    "wayward-cave-1f": "Grotta Labirinto (1P)",
    "wayward-cave-b1f": "Grotta Labirinto (S1)",
    "mt-coronet-1f-route-207": "Monte Corona (1P, Percorso 207)",
    "mt-coronet-2f": "Monte Corona (2P)",
    "mt-coronet-3f": "Monte Corona (3P)",
    "mt-coronet-4f": "Monte Corona (4P)",
    "mt-coronet-5f": "Monte Corona (5P)",
    "mt-coronet-6f": "Monte Corona (6P)",
    "mt-coronet-exterior-snowfall": "Monte Corona (esterno, nevicata)",
    "mt-coronet-exterior-blizzard": "Monte Corona (esterno, bufera)",
    "mt-coronet-1f-from-exterior": "Monte Corona (1P, dall'esterno)",
    "mt-coronet-1f-route-216": "Monte Corona (1P, Percorso 216)",
    "mt-coronet-1f-route-211": "Monte Corona (1P, Percorso 211)",
    "mt-coronet-b1f": "Monte Corona (S1)",
    "great-marsh-area-1": "Gran Palude (zona 1)",
    "great-marsh-area-2": "Gran Palude (zona 2)",
    "great-marsh-area-3": "Gran Palude (zona 3)",
    "great-marsh-area-4": "Gran Palude (zona 4)",
    "great-marsh-area-5": "Gran Palude (zona 5)",
    "great-marsh-area-6": "Gran Palude (zona 6)",
    "fuego-ironworks": "Fonderie Fuego",
    "iron-island-1f": "Isola Ferrosa (1P)",
    "iron-island-b1f-left": "Isola Ferrosa (S1, sinistra)",
    "iron-island-b1f-right": "Isola Ferrosa (S1, destra)",
    "iron-island-b2f-right": "Isola Ferrosa (S2, destra)",
    "iron-island-b2f-left": "Isola Ferrosa (S2, sinistra)",
    "stark-mountain-entrance": "Monte Ostile (ingresso)",
    "stark-mountain-inside": "Monte Ostile (interno)",
    "snowpoint-temple-1f": "Tempio di Nevepoli (1P)",
    "snowpoint-temple-b1f": "Tempio di Nevepoli (S1)",
    "trophy-garden": "Giardino Trofeo",
    "oreburgh-mine-1f": "Cava di Mineropoli (1P)",
    "oreburgh-mine-b1f": "Cava di Mineropoli (S1)",
    "oreburgh-gate-1f": "Varco di Mineropoli (1P)",
    "oreburgh-gate-b1f": "Varco di Mineropoli (S1)",
    "valley-windworks": "Impianto Turbine",
    "lost-tower-3f": "Torre Memoria (3P)",
    "lost-tower-4f": "Torre Memoria (4P)",
    "lost-tower-5f": "Torre Memoria (5P)",
    "lake-verity-before-galactic-intervention": "Lago Verita",
    "lake-verity-after-galactic-intervention": "Lago Verita",
    "lake-valor": "Lago Valore",
    "lake-acuity": "Lago Arguzia",
    "spear-pillar": "Vetta Lancia",
    "turnback-cave-pillar-1": "Grotta Ritorno",
    "sinnoh-victory-road-1f": "Via Vittoria (1P)",
    "sinnoh-victory-road-2f": "Via Vittoria (2P)",
    "sinnoh-victory-road-b1f": "Via Vittoria (S1)",
    # --- Gen 5: Unova ---
    "unova-route-1": "Percorso 1",
    "unova-route-2": "Percorso 2",
    "unova-route-3": "Percorso 3",
    "unova-route-4": "Percorso 4",
    "unova-route-5": "Percorso 5",
    "unova-route-6": "Percorso 6",
    "unova-route-7": "Percorso 7",
    "unova-route-8": "Percorso 8",
    "unova-route-9": "Percorso 9",
    "unova-route-10": "Percorso 10",
    "unova-route-11": "Percorso 11",
    "unova-route-12": "Percorso 12",
    "unova-route-13": "Percorso 13",
    "unova-route-14": "Percorso 14",
    "unova-route-15": "Percorso 15",
    "unova-route-16": "Percorso 16",
    "unova-route-17": "Percorso 17",
    "unova-route-18": "Percorso 18",
    "unova-route-19": "Percorso 19",
    "unova-route-20": "Percorso 20",
    "unova-route-21": "Percorso 21",
    "unova-route-22": "Percorso 22",
    "unova-route-23": "Percorso 23",
    "pinwheel-forest-outside": "Bosco Girandola (esterno)",
    "pinwheel-forest-inside": "Bosco Girandola (interno)",
    "desert-resort-entrance": "Deserto della Quiete (ingresso)",
    "desert-resort": "Deserto della Quiete",
    "relic-castle-a": "Castello Sepolto",
    "relic-castle-b": "Castello Sepolto",
    "chargestone-cave-1f": "Cava Pietrelettrica (1P)",
    "chargestone-cave-b1f": "Cava Pietrelettrica (S1)",
    "chargestone-cave-b2f": "Cava Pietrelettrica (S2)",
    "twist-mountain-b1f-3f": "Monte Vite",
    "dragonspiral-tower-entrance": "Torre Dragospira (ingresso)",
    "giant-chasm-outside": "Fossa Gigante (esterno)",
    "giant-chasm": "Fossa Gigante",
    "giant-chasm-forest": "Fossa Gigante (foresta)",
    "unova-victory-road-outside": "Via Vittoria (esterno)",
    "wellspring-cave": "Falda Sotterranea",
    "mistralton-cave": "Cava Ponentopoli",
    "celestial-tower-2f": "Torre Cielo (2P)",
    "celestial-tower-3f": "Torre Cielo (3P)",
    "celestial-tower-4f": "Torre Cielo (4P)",
    "celestial-tower-5f": "Torre Cielo (5P)",
    "moor-of-icirrus": "Palude Mistralopoli",
    "abundant-shrine": "Tempio Abbondanza",
    "lostlorn-forest": "Bosco Smarrimento",
    "undella-bay": "Baia Spiraria",
    "dreamyard": "Cantiere dei Sogni",
    "castelia-sewers": "Fogne di Austropoli",
    "floccesy-ranch-outer": "Fattoria di Venturia (esterno)",
    "floccesy-ranch-inner": "Fattoria di Venturia (interno)",
    "strange-house-1f": "Casa Bizzarra (1P)",
    "nature-sanctuary": "Riserva Naturale",
    # --- Gen 6: Kalos ---
    "kalos-route-2": "Percorso 2",
    "kalos-route-3": "Percorso 3",
    "kalos-route-4": "Percorso 4",
    "kalos-route-5": "Percorso 5",
    "kalos-route-6": "Percorso 6",
    "kalos-route-7": "Percorso 7",
    "kalos-route-8": "Percorso 8",
    "kalos-route-9": "Percorso 9",
    "kalos-route-10": "Percorso 10",
    "kalos-route-11": "Percorso 11",
    "kalos-route-12": "Percorso 12",
    "kalos-route-13": "Percorso 13",
    "kalos-route-14": "Percorso 14",
    "kalos-route-15": "Percorso 15",
    "kalos-route-16": "Percorso 16",
    "kalos-route-17": "Percorso 17",
    "kalos-route-18": "Percorso 18",
    "kalos-route-19": "Percorso 19",
    "kalos-route-20": "Percorso 20",
    "kalos-route-21": "Percorso 21",
    "kalos-route-22": "Percorso 22",
    "santalune-forest": "Bosco Novartopoli",
    "pokemon-village": "Valle dei Pokemon",
    "connecting-cave": "Grotta Trait d'Union",
    "lost-hotel": "Albergo Diroccato",
    "azure-bay": "Baia Azzurra",
    # --- Gen 7: Alola ---
    "alola-route-1-east": "Percorso 1 (est)",
    "alola-route-1-hauoli-outskirts": "Percorso 1 (periferia Hau'oli)",
    "alola-route-1-south": "Percorso 1 (sud)",
    "alola-route-2-main": "Percorso 2",
    "alola-route-3-main": "Percorso 3",
    "alola-route-4": "Percorso 4",
    "alola-route-5": "Percorso 5",
    "alola-route-6-north": "Percorso 6 (nord)",
    "alola-route-6-south": "Percorso 6 (sud)",
    "alola-route-7": "Percorso 7",
    "alola-route-8-main": "Percorso 8",
    "alola-route-9-main": "Percorso 9",
    "alola-route-10": "Percorso 10",
    "alola-route-11": "Percorso 11",
    "alola-route-12": "Percorso 12",
    "alola-route-13": "Percorso 13",
    "alola-route-14": "Percorso 14",
    "alola-route-15-main": "Percorso 15",
    "alola-route-16-main": "Percorso 16",
    "alola-route-17-all-areas": "Percorso 17",
    "verdant-cavern-trial-site": "Grotta Sottobosco",
    "melemele-meadow": "Prato Mele Mele",
    "melemele-sea": "Mare di Mele Mele",
    "ten-carat-hill-farthest-hollow": "Collina Diecicarati (Caldera Recondita)",
    "ten-carat-hill-inside": "Collina Diecicarati (interno)",
    "seaward-cave": "Grotta Pratomare",
    "brooklet-hill-main": "Collina Scrosciante",
    "brooklet-hill-totems-den": "Collina Scrosciante (tana del dominante)",
    "wela-volcano-park": "Parco Vulcano Wela",
    "lush-jungle-north": "Giungla Ombrosa (nord)",
    "lush-jungle-south": "Giungla Ombrosa (sud)",
    "lush-jungle-west": "Giungla Ombrosa (ovest)",
    "digletts-tunnel": "Tunnel Diglett",
    "haina-desert": "Deserto Haina",
    "mount-hokulani-main": "Picco Hokulani",
    "mount-lanakila-base": "Monte Lanakila (base)",
    "mount-lanakila-cave": "Monte Lanakila (grotta)",
    "mount-lanakila-outside": "Monte Lanakila (esterno)",
    "vast-poni-canyon-inside": "Canyon di Poni (interno)",
    "vast-poni-canyon-outside": "Canyon di Poni (esterno)",
    "poni-grove": "Foresta di Poni",
    "poni-plains-center": "Pianura di Poni",
    "poni-meadow": "Prato Poni",
    "poni-gauntlet": "Erta di Poni",
    "poni-coast": "Costa di Poni",
    "resolution-cave": "Caverna Climax",
    "exeggutor-island": "Isola Exeggutor",
    "memorial-hill": "Colle della Memoria",
    "malie-garden": "Giardino di Malie",
    "thrifty-megamart-abandoned-site": "Villa Losca",
    # --- Gen 8: Galar ---
    "galar-route-1": "Percorso 1",
    "galar-route-2": "Percorso 2",
    "galar-route-3-main": "Percorso 3",
    "galar-route-4": "Percorso 4",
    "galar-route-5": "Percorso 5",
    "galar-route-6": "Percorso 6",
    "galar-route-7": "Percorso 7",
    "galar-route-8-main": "Percorso 8",
    "galar-route-9-main": "Percorso 9",
    "galar-route-9-circhester-bay": "Percorso 9 (Baia Circhester)",
    "galar-route-10-main": "Percorso 10",
    "slumbering-weald": "Bosco Assopito",
    "galar-mine": "Miniera di Galar",
    "galar-mine-no-2": "Miniera 2",
    "glimwood-tangle": "Bosco Brillabirinto",
    "rolling-fields-main": "Pianura Serena",
    "dappled-grove": "Boschetto Ombraluce",
    "watchtower-ruins": "Torre Diroccata",
    "east-lake-axewell": "Lago Axew (est)",
    "west-lake-axewell": "Lago Axew (ovest)",
    "axews-eye": "Occhio del Lago Axew",
    "south-lake-miloch-main": "Lago Milotic (sud)",
    "giants-seat": "Sedia del Gigante",
    "north-lake-miloch": "Lago Milotic (nord)",
    "motostoke-riverbank": "Fiume di Steamington",
    "bridge-field": "Piana dei Ponti",
    "stony-wilderness-main": "Landa delle Pietre",
    "dusty-bowl": "Conca delle Sabbie",
    "giants-mirror": "Specchio del Gigante",
    "hammerlocke-hills": "Colle Knuckleburgh",
    "giants-cap-main": "Berretto del Gigante",
    "lake-of-outrage": "Lago Dragofuria",
    "fields-of-honor-main": "Pianura Inchino",
    "soothing-wetlands": "Acquitrino Fresco",
    "forest-of-focus": "Bosco Concentrazione",
    "challenge-beach-main": "Spiaggia Sfida",
    "challenge-road": "Cammino Sfida",
    "training-lowlands-main": "Piana Addestramento",
    "potbottom-desert": "Deserto Paiolo",
    "workout-sea": "Mar Ginnico",
    "honeycalm-island": "Isola Quietarnia",
    "slippery-slope": "Nevi Primoscivolo",
    "frostpoint-field": "Campo Trivio",
    "giants-bed": "Letto del Gigante",
    "snowslide-slope": "Piana Sottozero",
    "giants-foot": "Suola del Gigante",
    "frigid-sea": "Mar Gelido",
    "ballimere-lake": "Riva del Lago Ball",
    "crown-shrine": "Tempio Corona",
    "max-lair": "Dynatana Max",
    # --- Gen 9: Paldea ---
    "south-province-area-one": "Area 1 Sud",
    "south-province-area-two": "Area 2 Sud",
    "south-province-area-three": "Area 3 Sud",
    "south-province-area-four": "Area 4 Sud",
    "south-province-area-five": "Area 5 Sud",
    "south-province-area-six": "Area 6 Sud",
    "west-province-area-one": "Area 1 Ovest",
    "west-province-area-two": "Area 2 Ovest",
    "west-province-area-three": "Area 3 Ovest",
    "east-province-area-one": "Area 1 Est",
    "east-province-area-two": "Area 2 Est",
    "east-province-area-three": "Area 3 Est",
    "north-province-area-one": "Area 1 Nord",
    "north-province-area-two": "Area 2 Nord",
    "north-province-area-three": "Area 3 Nord",
    "casseroya-lake": "Lago Gran Caldero",
    "dalizapa-passage": "Passaggio Mescadia",
    "glaseado-mountain": "Sierra Napada",
    "asado-desert": "Deserto Alasar",
    "tagtree-thicket": "Boschetto dei Segni",
    "socarrat-trail": "Sentiero di Dosilla",
    "alfornada-cavern": "Caverna di Las Brasas",
}
