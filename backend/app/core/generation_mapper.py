GAME_TO_GENERATION: dict[str, int] = {
    # Gen 1
    "rosso": 1, "blu": 1, "giallo": 1,
    "red": 1, "blue": 1, "yellow": 1,
    # Gen 2
    "oro": 2, "argento": 2, "cristallo": 2,
    "gold": 2, "silver": 2, "crystal": 2,
    # Gen 3
    "rubino": 3, "zaffiro": 3, "smeraldo": 3,
    "rossofuoco": 3, "rosso fuoco": 3, "verdefoglia": 3, "verde foglia": 3,
    "ruby": 3, "sapphire": 3, "emerald": 3,
    "firered": 3, "fire red": 3, "leafgreen": 3, "leaf green": 3,
    # Gen 4
    "diamante": 4, "perla": 4, "platino": 4,
    "heartgold": 4, "heart gold": 4, "soulsilver": 4, "soul silver": 4,
    "diamond": 4, "pearl": 4, "platinum": 4,
    # Gen 5
    "nero": 5, "bianco": 5, "nero 2": 5, "bianco 2": 5,
    "nero2": 5, "bianco2": 5,
    "black": 5, "white": 5, "black 2": 5, "white 2": 5,
    # Gen 6
    "x": 6, "y": 6,
    "rubino omega": 6, "zaffiro alpha": 6,
    "omega ruby": 6, "alpha sapphire": 6,
    # Gen 7
    "sole": 7, "luna": 7, "ultrasole": 7, "ultraluna": 7,
    "sun": 7, "moon": 7, "ultra sun": 7, "ultra moon": 7,
    "let's go pikachu": 7, "let's go eevee": 7,
    "lets go pikachu": 7, "lets go eevee": 7,
    "let's go": 7,
    # Gen 8
    "spada": 8, "scudo": 8,
    "sword": 8, "shield": 8,
    "diamante lucente": 8, "perla splendente": 8,
    "brilliant diamond": 8, "shining pearl": 8,
    "leggende arceus": 8, "legends arceus": 8,
    # Gen 9
    "scarlatto": 9, "violetto": 9,
    "scarlet": 9, "violet": 9,
}

# Explicit gen references
GEN_KEYWORDS: dict[str, int] = {
    "gen 1": 1, "gen1": 1, "generazione 1": 1, "prima generazione": 1,
    "gen 2": 2, "gen2": 2, "generazione 2": 2, "seconda generazione": 2,
    "gen 3": 3, "gen3": 3, "generazione 3": 3, "terza generazione": 3,
    "gen 4": 4, "gen4": 4, "generazione 4": 4, "quarta generazione": 4,
    "gen 5": 5, "gen5": 5, "generazione 5": 5, "quinta generazione": 5,
    "gen 6": 6, "gen6": 6, "generazione 6": 6, "sesta generazione": 6,
    "gen 7": 7, "gen7": 7, "generazione 7": 7, "settima generazione": 7,
    "gen 8": 8, "gen8": 8, "generazione 8": 8, "ottava generazione": 8,
    "gen 9": 9, "gen9": 9, "generazione 9": 9, "nona generazione": 9,
}

# Max Pokemon national dex number per generation
MAX_POKEMON_PER_GEN: dict[int, int] = {
    1: 151,
    2: 251,
    3: 386,
    4: 493,
    5: 649,
    6: 721,
    7: 809,
    8: 905,
    9: 1025,
}

LATEST_GENERATION = 9

# PokeAPI version groups mapped to generations
VERSION_GROUP_TO_GEN: dict[str, int] = {
    "red-blue": 1, "yellow": 1,
    "gold-silver": 2, "crystal": 2,
    "ruby-sapphire": 3, "emerald": 3, "firered-leafgreen": 3,
    "colosseum": 3, "xd": 3,
    "diamond-pearl": 4, "platinum": 4, "heartgold-soulsilver": 4,
    "black-white": 5, "black-2-white-2": 5,
    "x-y": 6, "omega-ruby-alpha-sapphire": 6,
    "sun-moon": 7, "ultra-sun-ultra-moon": 7, "lets-go-pikachu-lets-go-eevee": 7,
    "sword-shield": 8, "brilliant-diamond-and-shining-pearl": 8,
    "legends-arceus": 8,
    "scarlet-violet": 9,
}


def detect_generation(query: str) -> int | None:
    """Detect the target generation from a user query.

    Returns the generation number if found, or None to use the latest.
    Checks explicit gen references first, then game names.
    """
    query_lower = query.lower()

    # Check explicit gen references first (most specific)
    for keyword, gen in sorted(GEN_KEYWORDS.items(), key=lambda x: -len(x[0])):
        if keyword in query_lower:
            return gen

    # Check game names (longest match first to avoid partial matches)
    for game, gen in sorted(GAME_TO_GENERATION.items(), key=lambda x: -len(x[0])):
        if game in query_lower:
            return gen

    return None
