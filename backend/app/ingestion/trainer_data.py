"""Static data for gym leaders, Elite Four and Champions per game.

PokeAPI does not expose NPC trainer data, so this is a curated static
dataset covering the main-series games. Each entry is keyed by a slug
that maps to a generation (via ``generation`` field).

Sources:
- PokemonDB (pokemondb.net) gym leaders / elite four pages
- Italian names from official localisation

The ``type_it`` field uses the Italian type name that matches
our ChromaDB documents (e.g. "Roccia", "Acqua", "Fuoco").
"""

from __future__ import annotations

from app.ingestion.translations import TYPE_EN_TO_IT


def _t(en_type: str) -> str:
    """Translate type name EN → IT."""
    return TYPE_EN_TO_IT.get(en_type, en_type)


# ── Trainer data per game ────────────────────────────────────────

TRAINER_DATA: dict[str, dict] = {

    # ═══════════════════════════════════════════════════════════════
    # GENERATION 1 — Kanto
    # ═══════════════════════════════════════════════════════════════

    "red_blue": {
        "game_it": "Pokemon Rosso e Blu",
        "game_en": "Pokemon Red & Blue",
        "generation": 1,
        "region_it": "Kanto",
        "gym_leaders": [
            {"name": "Brock", "city_it": "Plumbeopoli", "type": "Rock",
             "team": ["Geodude", "Onix"]},
            {"name": "Misty", "city_it": "Celestopoli", "type": "Water",
             "team": ["Staryu", "Starmie"]},
            {"name": "Lt. Surge", "city_it": "Aranciopoli", "type": "Electric",
             "team": ["Voltorb", "Pikachu", "Raichu"]},
            {"name": "Erika", "city_it": "Azzurropoli", "type": "Grass",
             "team": ["Victreebel", "Tangela", "Vileplume"]},
            {"name": "Koga", "city_it": "Fucsinapoli", "type": "Poison",
             "team": ["Koffing", "Muk", "Koffing", "Weezing"]},
            {"name": "Sabrina", "city_it": "Zafferanopoli", "type": "Psychic",
             "team": ["Kadabra", "Mr. Mime", "Venomoth", "Alakazam"]},
            {"name": "Blaine", "city_it": "Isola Cannella", "type": "Fire",
             "team": ["Growlithe", "Ponyta", "Rapidash", "Arcanine"]},
            {"name": "Giovanni", "city_it": "Smeraldopoli", "type": "Ground",
             "team": ["Rhyhorn", "Dugtrio", "Nidoqueen", "Nidoking", "Rhydon"]},
        ],
        "elite_four": [
            {"name": "Lorelei", "type": "Ice",
             "team": ["Dewgong", "Cloyster", "Slowbro", "Jynx", "Lapras"]},
            {"name": "Bruno", "type": "Fighting",
             "team": ["Onix", "Hitmonchan", "Hitmonlee", "Onix", "Machamp"]},
            {"name": "Agatha", "type": "Ghost",
             "team": ["Gengar", "Golbat", "Haunter", "Arbok", "Gengar"]},
            {"name": "Lance", "type": "Dragon",
             "team": ["Gyarados", "Dragonair", "Dragonair", "Aerodactyl", "Dragonite"]},
        ],
        "champion": {
            "name": "Blu", "name_en": "Blue", "type": "Mixed",
            "team": ["Pidgeot", "Alakazam", "Rhydon", "Exeggutor", "Gyarados", "Arcanine"],
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
        "gym_leaders": [
            {"name": "Valerio", "name_en": "Falkner", "city_it": "Violapoli",
             "type": "Flying", "team": ["Pidgey", "Pidgeotto"]},
            {"name": "Raffaello", "name_en": "Bugsy", "city_it": "Azalina",
             "type": "Bug", "team": ["Metapod", "Kakuna", "Scyther"]},
            {"name": "Chiara", "name_en": "Whitney", "city_it": "Fiordoropoli",
             "type": "Normal", "team": ["Clefairy", "Miltank"]},
            {"name": "Angelo", "name_en": "Morty", "city_it": "Amarantopoli",
             "type": "Ghost", "team": ["Gastly", "Haunter", "Haunter", "Gengar"]},
            {"name": "Furio", "name_en": "Chuck", "city_it": "Fiorpescopoli",
             "type": "Fighting", "team": ["Primeape", "Poliwrath"]},
            {"name": "Jasmine", "city_it": "Olivinopoli",
             "type": "Steel", "team": ["Magnemite", "Magnemite", "Steelix"]},
            {"name": "Alfredo", "name_en": "Pryce", "city_it": "Mogania",
             "type": "Ice", "team": ["Seel", "Dewgong", "Piloswine"]},
            {"name": "Sandra", "name_en": "Clair", "city_it": "Ebanopoli",
             "type": "Dragon", "team": ["Dragonair", "Dragonair", "Dragonair", "Kingdra"]},
        ],
        "elite_four": [
            {"name": "Will", "type": "Psychic",
             "team": ["Xatu", "Jynx", "Slowbro", "Exeggutor", "Xatu"]},
            {"name": "Koga", "type": "Poison",
             "team": ["Ariados", "Venomoth", "Forretress", "Muk", "Crobat"]},
            {"name": "Bruno", "type": "Fighting",
             "team": ["Hitmontop", "Hitmonlee", "Hitmonchan", "Onix", "Machamp"]},
            {"name": "Karen", "type": "Dark",
             "team": ["Umbreon", "Vileplume", "Murkrow", "Gengar", "Houndoom"]},
        ],
        "champion": {
            "name": "Lance", "type": "Dragon",
            "team": ["Gyarados", "Dragonite", "Charizard", "Aerodactyl", "Dragonite", "Dragonite"],
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # GENERATION 3 — Hoenn (Emerald)
    # ═══════════════════════════════════════════════════════════════

    "emerald": {
        "game_it": "Pokemon Smeraldo",
        "game_en": "Pokemon Emerald",
        "generation": 3,
        "region_it": "Hoenn",
        "gym_leaders": [
            {"name": "Petra", "name_en": "Roxanne", "city_it": "Ferrugipoli",
             "type": "Rock", "team": ["Geodude", "Geodude", "Nosepass"]},
            {"name": "Rudi", "name_en": "Brawly", "city_it": "Alboripoli",
             "type": "Fighting", "team": ["Machop", "Meditite", "Makuhita"]},
            {"name": "Walter", "name_en": "Wattson", "city_it": "Ciclamipoli",
             "type": "Electric", "team": ["Voltorb", "Magneton", "Electrike", "Manectric"]},
            {"name": "Fiammetta", "name_en": "Flannery", "city_it": "Thermopoli",
             "type": "Fire", "team": ["Numel", "Slugma", "Camerupt", "Torkoal"]},
            {"name": "Norman", "city_it": "Petalipoli",
             "type": "Normal", "team": ["Spinda", "Vigoroth", "Linoone", "Slaking"]},
            {"name": "Alice", "name_en": "Winona", "city_it": "Forestopoli",
             "type": "Flying", "team": ["Swablu", "Tropius", "Pelipper", "Skarmory", "Altaria"]},
            {"name": "Tell e Lara", "name_en": "Tate & Liza", "city_it": "Algatopoli",
             "type": "Psychic", "team": ["Claydol", "Xatu", "Lunatone", "Solrock"]},
            {"name": "Adriano", "name_en": "Juan", "city_it": "Ceneride",
             "type": "Water", "team": ["Luvdisc", "Whiscash", "Sealeo", "Crawdaunt", "Kingdra"]},
        ],
        "elite_four": [
            {"name": "Sidney", "type": "Dark",
             "team": ["Mightyena", "Cacturne", "Shiftry", "Crawdaunt", "Absol"]},
            {"name": "Phoebe", "type": "Ghost",
             "team": ["Dusclops", "Banette", "Banette", "Sableye", "Dusclops"]},
            {"name": "Glacia", "type": "Ice",
             "team": ["Glalie", "Sealeo", "Glalie", "Sealeo", "Walrein"]},
            {"name": "Drake", "type": "Dragon",
             "team": ["Shelgon", "Altaria", "Kingdra", "Flygon", "Salamence"]},
        ],
        "champion": {
            "name": "Wallace", "type": "Water",
            "team": ["Wailord", "Tentacruel", "Whiscash", "Ludicolo", "Gyarados", "Milotic"],
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # GENERATION 4 — Sinnoh (Platinum)
    # ═══════════════════════════════════════════════════════════════

    "platinum": {
        "game_it": "Pokemon Platino",
        "game_en": "Pokemon Platinum",
        "generation": 4,
        "region_it": "Sinnoh",
        "gym_leaders": [
            {"name": "Roark", "city_it": "Carboburgo",
             "type": "Rock", "team": ["Geodude", "Onix", "Cranidos"]},
            {"name": "Gardenia", "city_it": "Evopoli",
             "type": "Grass", "team": ["Turtwig", "Cherrim", "Roserade"]},
            {"name": "Fantin", "name_en": "Fantina", "city_it": "Cuoripoli",
             "type": "Ghost", "team": ["Duskull", "Haunter", "Mismagius"]},
            {"name": "Marzia", "name_en": "Maylene", "city_it": "Rupepoli",
             "type": "Fighting", "team": ["Meditite", "Machoke", "Lucario"]},
            {"name": "Omar", "name_en": "Crasher Wake", "city_it": "Pratopoli",
             "type": "Water", "team": ["Gyarados", "Quagsire", "Floatzel"]},
            {"name": "Ferruccio", "name_en": "Byron", "city_it": "Mineropoli",
             "type": "Steel", "team": ["Magneton", "Steelix", "Bastiodon"]},
            {"name": "Bianca", "name_en": "Candice", "city_it": "Nevepoli",
             "type": "Ice", "team": ["Sneasel", "Piloswine", "Abomasnow", "Froslass"]},
            {"name": "Corrado", "name_en": "Volkner", "city_it": "Arenipoli",
             "type": "Electric", "team": ["Jolteon", "Raichu", "Luxray", "Electivire"]},
        ],
        "elite_four": [
            {"name": "Aaron", "type": "Bug",
             "team": ["Yanmega", "Scizor", "Vespiquen", "Heracross", "Drapion"]},
            {"name": "Terrie", "name_en": "Bertha", "type": "Ground",
             "team": ["Whiscash", "Gliscor", "Golem", "Rhyperior", "Hippowdon"]},
            {"name": "Vulcano", "name_en": "Flint", "type": "Fire",
             "team": ["Houndoom", "Flareon", "Rapidash", "Infernape", "Magmortar"]},
            {"name": "Luciano", "name_en": "Lucian", "type": "Psychic",
             "team": ["Mr. Mime", "Espeon", "Bronzong", "Alakazam", "Gallade"]},
        ],
        "champion": {
            "name": "Cynthia", "type": "Mixed",
            "team": ["Spiritomb", "Roserade", "Togekiss", "Lucario", "Milotic", "Garchomp"],
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # GENERATION 5 — Unova (Black & White)
    # ═══════════════════════════════════════════════════════════════

    "black_white": {
        "game_it": "Pokemon Nero e Bianco",
        "game_en": "Pokemon Black & White",
        "generation": 5,
        "region_it": "Unima",
        "gym_leaders": [
            {"name": "Spighetto/Chicco/Maisello", "name_en": "Cilan/Chili/Cress",
             "city_it": "Levantopoli", "type": "Grass/Fire/Water",
             "team": ["Lillipup", "Pansage/Pansear/Panpour"]},
            {"name": "Aloé", "name_en": "Lenora", "city_it": "Aloepoli",
             "type": "Normal", "team": ["Herdier", "Watchog"]},
            {"name": "Artemisio", "name_en": "Burgh", "city_it": "Austropoli",
             "type": "Bug", "team": ["Whirlipede", "Dwebble", "Leavanny"]},
            {"name": "Camelia", "name_en": "Elesa", "city_it": "Sciroccopoli",
             "type": "Electric", "team": ["Emolga", "Emolga", "Zebstrika"]},
            {"name": "Rafan", "name_en": "Clay", "city_it": "Libecciopoli",
             "type": "Ground", "team": ["Krokorok", "Palpitoad", "Excadrill"]},
            {"name": "Anemone", "name_en": "Skyla", "city_it": "Ponentopoli",
             "type": "Flying", "team": ["Swoobat", "Unfezant", "Swanna"]},
            {"name": "Silvestro", "name_en": "Brycen", "city_it": "Boreopoli",
             "type": "Ice", "team": ["Vanillish", "Cryogonal", "Beartic"]},
            {"name": "Aristide/Iris", "name_en": "Drayden/Iris", "city_it": "Spongopoli",
             "type": "Dragon", "team": ["Fraxure", "Druddigon", "Haxorus"]},
        ],
        "elite_four": [
            {"name": "Antemia", "name_en": "Shauntal", "type": "Ghost",
             "team": ["Cofagrigus", "Jellicent", "Golurk", "Chandelure"]},
            {"name": "Mirton", "name_en": "Grimsley", "type": "Dark",
             "team": ["Scrafty", "Liepard", "Krookodile", "Bisharp"]},
            {"name": "Catlina", "name_en": "Caitlin", "type": "Psychic",
             "team": ["Reuniclus", "Musharna", "Sigilyph", "Gothitelle"]},
            {"name": "Marzio", "name_en": "Marshal", "type": "Fighting",
             "team": ["Throh", "Sawk", "Conkeldurr", "Mienshao"]},
        ],
        "champion": {
            "name": "Nardo", "name_en": "Alder", "type": "Mixed",
            "team": ["Accelgor", "Bouffalant", "Druddigon", "Vanilluxe", "Escavalier", "Volcarona"],
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # GENERATION 6 — Kalos (X & Y)
    # ═══════════════════════════════════════════════════════════════

    "x_y": {
        "game_it": "Pokemon X e Y",
        "game_en": "Pokemon X & Y",
        "generation": 6,
        "region_it": "Kalos",
        "gym_leaders": [
            {"name": "Viola", "city_it": "Novartopoli",
             "type": "Bug", "team": ["Surskit", "Vivillon"]},
            {"name": "Lino", "name_en": "Grant", "city_it": "Temperopoli",
             "type": "Rock", "team": ["Amaura", "Tyrunt"]},
            {"name": "Ornella", "name_en": "Korrina", "city_it": "Yantaropoli",
             "type": "Fighting", "team": ["Mienfoo", "Machoke", "Hawlucha"]},
            {"name": "Amur", "name_en": "Ramos", "city_it": "Romanticopoli",
             "type": "Grass", "team": ["Jumpluff", "Weepinbell", "Gogoat"]},
            {"name": "Lem", "name_en": "Clemont", "city_it": "Luminopoli",
             "type": "Electric", "team": ["Emolga", "Magneton", "Heliolisk"]},
            {"name": "Valérie", "name_en": "Valerie", "city_it": "Romanticopoli",
             "type": "Fairy", "team": ["Mr. Mime", "Mawile", "Sylveon"]},
            {"name": "Astra", "name_en": "Olympia", "city_it": "Fluxopoli",
             "type": "Psychic", "team": ["Sigilyph", "Slowking", "Meowstic"]},
            {"name": "Edel", "name_en": "Wulfric", "city_it": "Fractalopoli",
             "type": "Ice", "team": ["Abomasnow", "Avalugg", "Cryogonal"]},
        ],
        "elite_four": [
            {"name": "Timeo", "name_en": "Wikstrom", "type": "Steel",
             "team": ["Klefki", "Probopass", "Aegislash", "Scizor"]},
            {"name": "Malva", "type": "Fire",
             "team": ["Pyroar", "Talonflame", "Torkoal", "Chandelure"]},
            {"name": "Lulù", "name_en": "Drasna", "type": "Dragon",
             "team": ["Dragalge", "Altaria", "Noivern", "Druddigon"]},
            {"name": "Narciso", "name_en": "Siebold", "type": "Water",
             "team": ["Clawitzer", "Starmie", "Gyarados", "Barbaracle"]},
        ],
        "champion": {
            "name": "Diantha", "type": "Mixed",
            "team": ["Hawlucha", "Aurorus", "Tyrantrum", "Goodra", "Gourgeist", "Gardevoir"],
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # GENERATION 7 — Alola (Sun & Moon)
    # Note: no gyms — uses Trial Captains and Island Kahunas
    # ═══════════════════════════════════════════════════════════════

    "sun_moon": {
        "game_it": "Pokemon Sole e Luna",
        "game_en": "Pokemon Sun & Moon",
        "generation": 7,
        "region_it": "Alola",
        "has_gyms": False,
        "kahunas": [
            {"name": "Hala", "island_it": "Isola Mele Mele",
             "type": "Fighting", "team": ["Mankey", "Makuhita", "Crabrawler"]},
            {"name": "Olivia", "island_it": "Isola Akala",
             "type": "Rock", "team": ["Nosepass", "Boldore", "Lycanroc"]},
            {"name": "Nanu", "island_it": "Isola Ula Ula",
             "type": "Dark", "team": ["Sableye", "Krokorok", "Persian"]},
            {"name": "Hapu", "island_it": "Isola Poni",
             "type": "Ground", "team": ["Alolan Dugtrio", "Gastrodon", "Flygon", "Mudsdale"]},
        ],
        "trial_captains": [
            {"name": "Ilima", "type": "Normal", "team": ["Gumshoos", "Smeargle"]},
            {"name": "Lana", "type": "Water", "team": ["Chinchou", "Shellder", "Araquanid"]},
            {"name": "Kiawe", "type": "Fire", "team": ["Growlithe", "Fletchinder", "Marowak"]},
            {"name": "Mallow", "type": "Grass", "team": ["Phantump", "Shiinotic", "Steenee"]},
            {"name": "Acerola", "type": "Ghost"},
            {"name": "Mina", "type": "Fairy",
             "team": ["Klefki", "Granbull", "Shiinotic", "Wigglytuff", "Ribombee"]},
        ],
        "elite_four": [
            {"name": "Hala", "type": "Fighting",
             "team": ["Hariyama", "Primeape", "Bewear", "Poliwrath", "Crabominable"]},
            {"name": "Olivia", "type": "Rock",
             "team": ["Relicanth", "Carbink", "Alolan Golem", "Probopass", "Lycanroc"]},
            {"name": "Acerola", "type": "Ghost",
             "team": ["Sableye", "Drifblim", "Dhelmise", "Froslass", "Palossand"]},
            {"name": "Kahili", "type": "Flying",
             "team": ["Skarmory", "Crobat", "Oricorio", "Mandibuzz", "Toucannon"]},
        ],
        "champion": {
            "name": "Kukui", "type": "Mixed",
            "team": ["Lycanroc", "Alolan Ninetales", "Braviary", "Magnezone", "Snorlax"],
            "note": "Lo starter forte contro il tuo viene aggiunto alla sua squadra.",
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # GENERATION 8 — Galar (Sword & Shield)
    # ═══════════════════════════════════════════════════════════════

    "sword_shield": {
        "game_it": "Pokemon Spada e Scudo",
        "game_en": "Pokemon Sword & Shield",
        "generation": 8,
        "region_it": "Galar",
        "gym_leaders": [
            {"name": "Yarrow", "name_en": "Milo", "city_it": "Turffield",
             "type": "Grass", "team": ["Gossifleur", "Eldegoss"]},
            {"name": "Nessa", "city_it": "Hulbury",
             "type": "Water", "team": ["Goldeen", "Arrokuda", "Drednaw"]},
            {"name": "Kabu", "city_it": "Motostoke",
             "type": "Fire", "team": ["Ninetales", "Arcanine", "Centiskorch"]},
            {"name": "Bea", "city_it": "Stow-on-Side",
             "type": "Fighting", "team": ["Hitmontop", "Pangoro", "Sirfetch'd", "Machamp"],
             "version": "Sword"},
            {"name": "Allister", "city_it": "Stow-on-Side",
             "type": "Ghost", "team": ["Yamask", "Mimikyu", "Cursola", "Gengar"],
             "version": "Shield"},
            {"name": "Opal", "city_it": "Ballonlea",
             "type": "Fairy", "team": ["Weezing", "Mawile", "Togekiss", "Alcremie"]},
            {"name": "Gordie", "city_it": "Circhester",
             "type": "Rock", "team": ["Barbaracle", "Shuckle", "Stonjourner", "Coalossal"],
             "version": "Sword"},
            {"name": "Melony", "city_it": "Circhester",
             "type": "Ice", "team": ["Frosmoth", "Darmanitan", "Eiscue", "Lapras"],
             "version": "Shield"},
            {"name": "Nepe", "name_en": "Piers", "city_it": "Spikemuth",
             "type": "Dark", "team": ["Scrafty", "Malamar", "Skuntank", "Obstagoon"]},
            {"name": "Raihan", "city_it": "Hammerlocke",
             "type": "Dragon", "team": ["Gigalith", "Flygon", "Sandaconda", "Duraludon"]},
        ],
        "elite_four": [],  # Sword/Shield has Champion Cup, no traditional E4
        "champion": {
            "name": "Leon", "type": "Mixed",
            "team": ["Aegislash", "Haxorus", "Seismitoad", "Dragapult", "Mr. Rime", "Charizard"],
            "note": "La sua squadra varia leggermente in base allo starter scelto.",
        },
    },

    # ═══════════════════════════════════════════════════════════════
    # GENERATION 9 — Paldea (Scarlet & Violet)
    # ═══════════════════════════════════════════════════════════════

    "scarlet_violet": {
        "game_it": "Pokemon Scarlatto e Violetto",
        "game_en": "Pokemon Scarlet & Violet",
        "generation": 9,
        "region_it": "Paldea",
        "gym_leaders": [
            {"name": "Katy", "city_it": "Cortondo",
             "type": "Bug", "team": ["Nymble", "Tarountula", "Teddiursa"]},
            {"name": "Brassius", "city_it": "Artazon",
             "type": "Grass", "team": ["Petilil", "Smoliv", "Sudowoodo"]},
            {"name": "Iono", "city_it": "Levincia",
             "type": "Electric", "team": ["Wattrel", "Bellibolt", "Luxio", "Mismagius"]},
            {"name": "Kofu", "city_it": "Cascarrafa",
             "type": "Water", "team": ["Veluza", "Wugtrio", "Crabominable"]},
            {"name": "Larry", "city_it": "Medali",
             "type": "Normal", "team": ["Komala", "Dudunsparce", "Staraptor"]},
            {"name": "Ryme", "city_it": "Montenevera",
             "type": "Ghost", "team": ["Banette", "Mimikyu", "Houndstone", "Toxtricity"]},
            {"name": "Tulip", "city_it": "Alfornada",
             "type": "Psychic", "team": ["Farigiraf", "Gardevoir", "Espathra", "Florges"]},
            {"name": "Grusha", "city_it": "Montagna Glaseado",
             "type": "Ice", "team": ["Frosmoth", "Beartic", "Cetitan", "Altaria"]},
        ],
        "elite_four": [
            {"name": "Rika", "type": "Ground",
             "team": ["Whiscash", "Camerupt", "Donphan", "Dugtrio", "Clodsire"]},
            {"name": "Poppy", "type": "Steel",
             "team": ["Copperajah", "Magnezone", "Bronzong", "Corviknight", "Tinkaton"]},
            {"name": "Larry", "type": "Flying",
             "team": ["Tropius", "Oricorio", "Altaria", "Staraptor", "Flamigo"]},
            {"name": "Hassel", "type": "Dragon",
             "team": ["Noivern", "Haxorus", "Dragalge", "Flapple", "Baxcalibur"]},
        ],
        "champion": {
            "name": "Geeta", "type": "Mixed",
            "team": ["Espathra", "Gogoat", "Veluza", "Avalugg", "Kingambit", "Glimmora"],
        },
    },
}
