"""Static game data: starters, legendaries and version exclusives per game.

PokeAPI does not expose these as structured endpoints, so this is a curated
static dataset mirroring the games covered by ``trainer_data.py``.

Sources:
- Bulbapedia, Serebii, PokemonDB
- Italian names from official localisation
"""

from __future__ import annotations

# ── Type name mapping EN → IT ────────────────────────────────────
_TYPE_IT = {
    "Normal": "Normale", "Fire": "Fuoco", "Water": "Acqua",
    "Electric": "Elettro", "Grass": "Erba", "Ice": "Ghiaccio",
    "Fighting": "Lotta", "Poison": "Veleno", "Ground": "Terra",
    "Flying": "Volante", "Psychic": "Psico", "Bug": "Coleottero",
    "Rock": "Roccia", "Ghost": "Spettro", "Dragon": "Drago",
    "Dark": "Buio", "Steel": "Acciaio", "Fairy": "Folletto",
}


def _t(en: str) -> str:
    return _TYPE_IT.get(en, en)


# ── Game static data ─────────────────────────────────────────────

GAME_STATIC_DATA: dict[str, dict] = {

    # ═══════════════════════════════════════════════════════════════
    # GENERATION 1 — Kanto
    # ═══════════════════════════════════════════════════════════════

    "red_blue": {
        "game_it": "Pokemon Rosso e Blu",
        "game_en": "Pokemon Red & Blue",
        "generation": 1,
        "region_it": "Kanto",
        "versions": ["Rosso", "Blu"],
        "starters": [
            {"name": "Bulbasaur", "type_it": f"{_t('Grass')}/{_t('Poison')}"},
            {"name": "Charmander", "type_it": _t("Fire")},
            {"name": "Squirtle", "type_it": _t("Water")},
        ],
        "legendaries": [
            {"name": "Articuno", "type_it": f"{_t('Ice')}/{_t('Flying')}",
             "location": "Isole Spumarine"},
            {"name": "Zapdos", "type_it": f"{_t('Electric')}/{_t('Flying')}",
             "location": "Centrale Elettrica"},
            {"name": "Moltres", "type_it": f"{_t('Fire')}/{_t('Flying')}",
             "location": "Strada Vittoria"},
            {"name": "Mewtwo", "type_it": _t("Psychic"),
             "location": "Grotta Cerulean (dopo la Lega)"},
        ],
        "version_exclusives": {
            "Rosso": [
                "Ekans", "Arbok", "Oddish", "Gloom", "Vileplume",
                "Mankey", "Primeape", "Growlithe", "Arcanine",
                "Scyther", "Electabuzz",
            ],
            "Blu": [
                "Sandshrew", "Sandslash", "Vulpix", "Ninetales",
                "Meowth", "Persian", "Bellsprout", "Weepinbell",
                "Victreebel", "Magmar", "Pinsir",
            ],
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # GENERATION 2 — Johto
    # ═══════════════════════════════════════════════════════════════

    "gold_silver": {
        "game_it": "Pokemon Oro e Argento",
        "game_en": "Pokemon Gold & Silver",
        "generation": 2,
        "region_it": "Johto",
        "versions": ["Oro", "Argento"],
        "starters": [
            {"name": "Chikorita", "type_it": _t("Grass")},
            {"name": "Cyndaquil", "type_it": _t("Fire")},
            {"name": "Totodile", "type_it": _t("Water")},
        ],
        "legendaries": [
            {"name": "Raikou", "type_it": _t("Electric"),
             "location": "Vagante per Johto (dopo Torre Bruciata)"},
            {"name": "Entei", "type_it": _t("Fire"),
             "location": "Vagante per Johto (dopo Torre Bruciata)"},
            {"name": "Suicune", "type_it": _t("Water"),
             "location": "Vagante per Johto (dopo Torre Bruciata)"},
            {"name": "Lugia", "type_it": f"{_t('Psychic')}/{_t('Flying')}",
             "location": "Isole Turbine (Argento) / evento (Oro)"},
            {"name": "Ho-Oh", "type_it": f"{_t('Fire')}/{_t('Flying')}",
             "location": "Torre Campanaria (Oro) / evento (Argento)"},
            {"name": "Celebi", "type_it": f"{_t('Psychic')}/{_t('Grass')}",
             "location": "Evento speciale (Bosco di Lecci)"},
        ],
        "version_exclusives": {
            "Oro": [
                "Mankey", "Primeape", "Growlithe", "Arcanine",
                "Spinarak", "Ariados", "Gligar", "Teddiursa", "Ursaring",
                "Mantine",
            ],
            "Argento": [
                "Vulpix", "Ninetales", "Meowth", "Persian",
                "Ledyba", "Ledian", "Delibird", "Skarmory",
                "Phanpy", "Donphan",
            ],
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # GENERATION 3 — Hoenn
    # ═══════════════════════════════════════════════════════════════

    "emerald": {
        "game_it": "Pokemon Smeraldo",
        "game_en": "Pokemon Emerald",
        "generation": 3,
        "region_it": "Hoenn",
        "versions": ["Rubino", "Zaffiro", "Smeraldo"],
        "starters": [
            {"name": "Treecko", "type_it": _t("Grass")},
            {"name": "Torchic", "type_it": _t("Fire")},
            {"name": "Mudkip", "type_it": _t("Water")},
        ],
        "legendaries": [
            {"name": "Groudon", "type_it": _t("Ground"),
             "location": "Grotta dei Tempi (Rubino/Smeraldo)"},
            {"name": "Kyogre", "type_it": _t("Water"),
             "location": "Grotta dei Tempi (Zaffiro/Smeraldo)"},
            {"name": "Rayquaza", "type_it": f"{_t('Dragon')}/{_t('Flying')}",
             "location": "Pilastro del Cielo"},
            {"name": "Latias", "type_it": f"{_t('Dragon')}/{_t('Psychic')}",
             "location": "Vagante per Hoenn (Zaffiro/Smeraldo)"},
            {"name": "Latios", "type_it": f"{_t('Dragon')}/{_t('Psychic')}",
             "location": "Vagante per Hoenn (Rubino/Smeraldo)"},
            {"name": "Regirock", "type_it": _t("Rock"),
             "location": "Grotta nel Deserto"},
            {"name": "Regice", "type_it": _t("Ice"),
             "location": "Grotta dell'Isola"},
            {"name": "Registeel", "type_it": _t("Steel"),
             "location": "Rovine Antiche"},
            {"name": "Jirachi", "type_it": f"{_t('Steel')}/{_t('Psychic')}",
             "location": "Evento speciale"},
            {"name": "Deoxys", "type_it": _t("Psychic"),
             "location": "Evento speciale"},
        ],
        "version_exclusives": {
            "Rubino": [
                "Seedot", "Nuzleaf", "Shiftry", "Mawile",
                "Zangoose", "Solrock", "Groudon",
            ],
            "Zaffiro": [
                "Lotad", "Lombre", "Ludicolo", "Sableye",
                "Seviper", "Lunatone", "Kyogre",
            ],
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # GENERATION 4 — Sinnoh
    # ═══════════════════════════════════════════════════════════════

    "platinum": {
        "game_it": "Pokemon Platino",
        "game_en": "Pokemon Platinum",
        "generation": 4,
        "region_it": "Sinnoh",
        "versions": ["Diamante", "Perla", "Platino"],
        "starters": [
            {"name": "Turtwig", "type_it": _t("Grass")},
            {"name": "Chimchar", "type_it": _t("Fire")},
            {"name": "Piplup", "type_it": _t("Water")},
        ],
        "legendaries": [
            {"name": "Dialga", "type_it": f"{_t('Steel')}/{_t('Dragon')}",
             "location": "Vetta Lancia (Diamante/Platino)"},
            {"name": "Palkia", "type_it": f"{_t('Water')}/{_t('Dragon')}",
             "location": "Vetta Lancia (Perla/Platino)"},
            {"name": "Giratina", "type_it": f"{_t('Ghost')}/{_t('Dragon')}",
             "location": "Mondo Distorto (Platino) / Fonte Ritorno"},
            {"name": "Uxie", "type_it": _t("Psychic"),
             "location": "Lago Sapienza"},
            {"name": "Mesprit", "type_it": _t("Psychic"),
             "location": "Vagante (dopo Lago Valore)"},
            {"name": "Azelf", "type_it": _t("Psychic"),
             "location": "Lago Coraggio"},
            {"name": "Heatran", "type_it": f"{_t('Fire')}/{_t('Steel')}",
             "location": "Monte Ostile"},
            {"name": "Regigigas", "type_it": _t("Normal"),
             "location": "Tempio Nevepoli (con i 3 Regi)"},
            {"name": "Cresselia", "type_it": _t("Psychic"),
             "location": "Isola Lunapiena (vagante)"},
        ],
        "version_exclusives": {
            "Diamante": [
                "Seel", "Dewgong", "Scyther", "Murkrow", "Honchkrow",
                "Larvitar", "Pupitar", "Tyranitar", "Cranidos", "Rampardos",
                "Stunky", "Skuntank", "Dialga",
            ],
            "Perla": [
                "Slowpoke", "Slowbro", "Pinsir", "Misdreavus", "Mismagius",
                "Bagon", "Shelgon", "Salamence", "Shieldon", "Bastiodon",
                "Glameow", "Purugly", "Palkia",
            ],
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # GENERATION 5 — Unova
    # ═══════════════════════════════════════════════════════════════

    "black_white": {
        "game_it": "Pokemon Nero e Bianco",
        "game_en": "Pokemon Black & White",
        "generation": 5,
        "region_it": "Unima",
        "versions": ["Nero", "Bianco"],
        "starters": [
            {"name": "Snivy", "type_it": _t("Grass")},
            {"name": "Tepig", "type_it": _t("Fire")},
            {"name": "Oshawott", "type_it": _t("Water")},
        ],
        "legendaries": [
            {"name": "Reshiram", "type_it": f"{_t('Dragon')}/{_t('Fire')}",
             "location": "Lega Pokemon (Nero)"},
            {"name": "Zekrom", "type_it": f"{_t('Dragon')}/{_t('Electric')}",
             "location": "Lega Pokemon (Bianco)"},
            {"name": "Kyurem", "type_it": f"{_t('Dragon')}/{_t('Ice')}",
             "location": "Fossa Gigante"},
            {"name": "Cobalion", "type_it": f"{_t('Steel')}/{_t('Fighting')}",
             "location": "Grotta Misteriosa"},
            {"name": "Terrakion", "type_it": f"{_t('Rock')}/{_t('Fighting')}",
             "location": "Grotta della Trappola"},
            {"name": "Virizion", "type_it": f"{_t('Grass')}/{_t('Fighting')}",
             "location": "Bosco Mirco"},
            {"name": "Tornadus", "type_it": _t("Flying"),
             "location": "Vagante per Unima (Nero)"},
            {"name": "Thundurus", "type_it": f"{_t('Electric')}/{_t('Flying')}",
             "location": "Vagante per Unima (Bianco)"},
            {"name": "Landorus", "type_it": f"{_t('Ground')}/{_t('Flying')}",
             "location": "Santuario Abbondanza (con Tornadus e Thundurus)"},
        ],
        "version_exclusives": {
            "Nero": [
                "Cottonee", "Whimsicott", "Gothita", "Gothorita", "Gothitelle",
                "Vullaby", "Mandibuzz", "Tornadus", "Reshiram",
            ],
            "Bianco": [
                "Petilil", "Lilligant", "Solosis", "Duosion", "Reuniclus",
                "Rufflet", "Braviary", "Thundurus", "Zekrom",
            ],
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # GENERATION 6 — Kalos
    # ═══════════════════════════════════════════════════════════════

    "x_y": {
        "game_it": "Pokemon X e Y",
        "game_en": "Pokemon X & Y",
        "generation": 6,
        "region_it": "Kalos",
        "versions": ["X", "Y"],
        "starters": [
            {"name": "Chespin", "type_it": _t("Grass")},
            {"name": "Fennekin", "type_it": _t("Fire")},
            {"name": "Froakie", "type_it": _t("Water")},
        ],
        "legendaries": [
            {"name": "Xerneas", "type_it": _t("Fairy"),
             "location": "Grotta Climax (X)"},
            {"name": "Yveltal", "type_it": f"{_t('Dark')}/{_t('Flying')}",
             "location": "Grotta Climax (Y)"},
            {"name": "Zygarde", "type_it": f"{_t('Dragon')}/{_t('Ground')}",
             "location": "Grotta Climax (postgame)"},
            {"name": "Mewtwo", "type_it": _t("Psychic"),
             "location": "Villaggio Pokemon (postgame)"},
        ],
        "version_exclusives": {
            "X": [
                "Staryu", "Starmie", "Pinsir", "Houndour", "Houndoom",
                "Poochyena", "Mightyena", "Aron", "Lairon", "Aggron",
                "Swirlix", "Slurpuff", "Clauncher", "Clawitzer", "Xerneas",
            ],
            "Y": [
                "Shellder", "Cloyster", "Heracross", "Larvitar", "Pupitar",
                "Tyranitar", "Electrike", "Manectric", "Purrloin", "Liepard",
                "Spritzee", "Aromatisse", "Skrelp", "Dragalge", "Yveltal",
            ],
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # GENERATION 7 — Alola
    # ═══════════════════════════════════════════════════════════════

    "sun_moon": {
        "game_it": "Pokemon Sole e Luna",
        "game_en": "Pokemon Sun & Moon",
        "generation": 7,
        "region_it": "Alola",
        "versions": ["Sole", "Luna"],
        "starters": [
            {"name": "Rowlet", "type_it": f"{_t('Grass')}/{_t('Flying')}"},
            {"name": "Litten", "type_it": _t("Fire")},
            {"name": "Popplio", "type_it": _t("Water")},
        ],
        "legendaries": [
            {"name": "Solgaleo", "type_it": f"{_t('Psychic')}/{_t('Steel')}",
             "location": "Altare del Sole (Sole)"},
            {"name": "Lunala", "type_it": f"{_t('Psychic')}/{_t('Ghost')}",
             "location": "Altare della Luna (Luna)"},
            {"name": "Necrozma", "type_it": _t("Psychic"),
             "location": "Prato Tenkarat (postgame)"},
            {"name": "Tapu Koko", "type_it": f"{_t('Electric')}/{_t('Fairy')}",
             "location": "Rovine del Conflitto (Mele Mele)"},
            {"name": "Tapu Lele", "type_it": f"{_t('Psychic')}/{_t('Fairy')}",
             "location": "Rovine della Vita (Akala)"},
            {"name": "Tapu Bulu", "type_it": f"{_t('Grass')}/{_t('Fairy')}",
             "location": "Rovine dell'Abbondanza (Ula Ula)"},
            {"name": "Tapu Fini", "type_it": f"{_t('Water')}/{_t('Fairy')}",
             "location": "Rovine della Speranza (Poni)"},
        ],
        "version_exclusives": {
            "Sole": [
                "Vulpix-Alola", "Ninetales-Alola", "Cranidos", "Rampardos",
                "Tirtouga", "Carracosta", "Cottonee", "Whimsicott",
                "Rufflet", "Braviary", "Passimian", "Lycanroc Forma Giorno",
                "Turtonator", "Solgaleo",
            ],
            "Luna": [
                "Sandshrew-Alola", "Sandslash-Alola", "Shieldon", "Bastiodon",
                "Archen", "Archeops", "Petilil", "Lilligant",
                "Vullaby", "Mandibuzz", "Oranguru", "Lycanroc Forma Notte",
                "Drampa", "Lunala",
            ],
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # GENERATION 8 — Galar
    # ═══════════════════════════════════════════════════════════════

    "sword_shield": {
        "game_it": "Pokemon Spada e Scudo",
        "game_en": "Pokemon Sword & Shield",
        "generation": 8,
        "region_it": "Galar",
        "versions": ["Spada", "Scudo"],
        "starters": [
            {"name": "Grookey", "type_it": _t("Grass")},
            {"name": "Scorbunny", "type_it": _t("Fire")},
            {"name": "Sobble", "type_it": _t("Water")},
        ],
        "legendaries": [
            {"name": "Zacian", "type_it": _t("Fairy"),
             "location": "Torre Energia (Spada)"},
            {"name": "Zamazenta", "type_it": _t("Fighting"),
             "location": "Torre Energia (Scudo)"},
            {"name": "Eternatus", "type_it": f"{_t('Poison')}/{_t('Dragon')}",
             "location": "Torre Energia (storia principale)"},
        ],
        "version_exclusives": {
            "Spada": [
                "Farfetch'd-Galar", "Sirfetch'd", "Seedot", "Nuzleaf",
                "Shiftry", "Mawile", "Solrock", "Darumaka-Galar",
                "Darmanitan-Galar", "Scraggy", "Scrafty", "Gothita",
                "Gothorita", "Gothitelle", "Rufflet", "Braviary",
                "Deino", "Zweilous", "Hydreigon", "Swirlix", "Slurpuff",
                "Passimian", "Turtonator", "Jangmo-o", "Hakamo-o",
                "Kommo-o", "Flapple", "Stonjourner", "Zacian",
            ],
            "Scudo": [
                "Ponyta-Galar", "Rapidash-Galar", "Lotad", "Lombre",
                "Ludicolo", "Sableye", "Lunatone", "Corsola-Galar",
                "Cursola", "Croagunk", "Toxicroak", "Solosis", "Duosion",
                "Reuniclus", "Vullaby", "Mandibuzz", "Larvitar", "Pupitar",
                "Tyranitar", "Spritzee", "Aromatisse", "Oranguru",
                "Drampa", "Goomy", "Sliggoo", "Goodra", "Appletun",
                "Eiscue", "Zamazenta",
            ],
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # GENERATION 9 — Paldea
    # ═══════════════════════════════════════════════════════════════

    "scarlet_violet": {
        "game_it": "Pokemon Scarlatto e Violetto",
        "game_en": "Pokemon Scarlet & Violet",
        "generation": 9,
        "region_it": "Paldea",
        "versions": ["Scarlatto", "Violetto"],
        "starters": [
            {"name": "Sprigatito", "type_it": _t("Grass")},
            {"name": "Fuecoco", "type_it": _t("Fire")},
            {"name": "Quaxly", "type_it": _t("Water")},
        ],
        "legendaries": [
            {"name": "Koraidon", "type_it": f"{_t('Fighting')}/{_t('Dragon')}",
             "location": "Fondo del Grande Cratere (Scarlatto)"},
            {"name": "Miraidon", "type_it": f"{_t('Electric')}/{_t('Dragon')}",
             "location": "Fondo del Grande Cratere (Violetto)"},
            {"name": "Wo-Chien", "type_it": f"{_t('Dark')}/{_t('Grass')}",
             "location": "Santuario della Calamita (rimuovi paletti)"},
            {"name": "Chien-Pao", "type_it": f"{_t('Dark')}/{_t('Ice')}",
             "location": "Santuario della Calamita (rimuovi paletti)"},
            {"name": "Ting-Lu", "type_it": f"{_t('Dark')}/{_t('Ground')}",
             "location": "Santuario della Calamita (rimuovi paletti)"},
            {"name": "Chi-Yu", "type_it": f"{_t('Dark')}/{_t('Fire')}",
             "location": "Santuario della Calamita (rimuovi paletti)"},
        ],
        "version_exclusives": {
            "Scarlatto": [
                "Larvitar", "Pupitar", "Tyranitar", "Drifloon", "Drifblim",
                "Stunky", "Skuntank", "Deino", "Zweilous", "Hydreigon",
                "Skrelp", "Dragalge", "Oranguru", "Stonjourner",
                "Armarouge", "Great Tusk", "Scream Tail", "Brute Bonnet",
                "Flutter Mane", "Slither Wing", "Sandy Shocks", "Roaring Moon",
                "Koraidon",
            ],
            "Violetto": [
                "Bagon", "Shelgon", "Salamence", "Misdreavus", "Mismagius",
                "Gulpin", "Swalot", "Clauncher", "Clawitzer", "Passimian",
                "Eiscue", "Dreepy", "Drakloak", "Dragapult",
                "Ceruledge", "Iron Treads", "Iron Bundle", "Iron Hands",
                "Iron Jugulis", "Iron Moth", "Iron Thorns", "Iron Valiant",
                "Miraidon",
            ],
        },
    },
}
