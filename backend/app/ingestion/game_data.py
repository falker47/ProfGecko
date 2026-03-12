"""Static game data: starters, legendaries and version exclusives per game.

PokeAPI does not expose these as structured endpoints, so this is a curated
static dataset mirroring the games covered by ``trainer_data.py``.

Sources:
- Bulbapedia, Serebii, PokemonDB
- Italian names from official localisation
"""

from __future__ import annotations

from app.ingestion.translations import translate_type as _t

# ── Game static data ─────────────────────────────────────────────

GAME_STATIC_DATA: dict[str, dict] = {

    # ═══════════════════════════════════════════════════════════════
    # GENERATION 1 — Kanto
    # ═══════════════════════════════════════════════════════════════

    "red_blue": {
        "game_it": "Pokemon Rosso, Blu e Giallo",
        "game_en": "Pokemon Red, Blue & Yellow",
        "generation": 1,
        "region_it": "Kanto",
        "versions": ["Rosso", "Blu", "Giallo"],
        "starters": [
            {"name": "Bulbasaur", "type_it": f"{_t('Grass')}/{_t('Poison')}"},
            {"name": "Charmander", "type_it": _t("Fire")},
            {"name": "Squirtle", "type_it": _t("Water")},
        ],
        "best_starter": (
            "Bulbasaur e' la scelta piu' efficiente. E' superefficace contro "
            "le prime due palestre (Brock Roccia, Misty Acqua), resiste la terza "
            "(Lt. Surge Elettro) e ha vantaggio sulla quarta (Erika Erba e' neutro "
            "grazie al tipo Veleno). Impara anche Sonnifero e Parassiseme che aiutano "
            "nelle catture. Squirtle e' il secondo migliore: batte Brock facilmente e ha "
            "buone statistiche difensive. Charmander e' la scelta piu' difficile: debole "
            "contro le prime due palestre, ma diventa molto forte nel mid-late game."
        ),
        "best_team": (
            "Una squadra bilanciata per Kanto:\n"
            "- Venusaur (Erba/Veleno) - starter, copre Acqua e Roccia\n"
            "- Alakazam (Psico) - devastante in Gen 1 dove Psico non ha veri counter\n"
            "- Snorlax (Normale) - bulk enorme, Corposcontro e Riposo\n"
            "- Lapras (Acqua/Ghiaccio) - ottenuto gratis a Zafferanopoli, copre Drago e Volante\n"
            "- Jolteon (Elettro) - velocissimo, copre i tipi Acqua e Volante\n"
            "- Nidoking (Veleno/Terra) - movepool vastissimo, Terremoto e Gelopugno\n"
            "Alternative valide: Gyarados, Starmie, Gengar (difficile da ottenere senza scambi), "
            "Arcanine (solo Rosso) o Ninetales (solo Blu)."
        ),
        "legendaries": [
            {"name": "Articuno", "type_it": f"{_t('Ice')}/{_t('Flying')}",
             "location": "Isole Spumarine"},
            {"name": "Zapdos", "type_it": f"{_t('Electric')}/{_t('Flying')}",
             "location": "Centrale Elettrica"},
            {"name": "Moltres", "type_it": f"{_t('Fire')}/{_t('Flying')}",
             "location": "Via Vittoria"},
            {"name": "Mewtwo", "type_it": _t("Psychic"),
             "location": "Grotta Celeste (dopo la Lega)"},
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
        "game_it": "Pokemon Oro, Argento e Cristallo",
        "game_en": "Pokemon Gold, Silver & Crystal",
        "generation": 2,
        "region_it": "Johto",
        "versions": ["Oro", "Argento", "Cristallo"],
        "starters": [
            {"name": "Chikorita", "type_it": _t("Grass")},
            {"name": "Cyndaquil", "type_it": _t("Fire")},
            {"name": "Totodile", "type_it": _t("Water")},
        ],
        "best_starter": (
            "Cyndaquil e' generalmente la scelta migliore. Evolve in Typhlosion che ha "
            "ottime statistiche speciali. I tipi Fuoco sono rari in Johto e ha vantaggio "
            "contro Jasmine (Acciaio) e Pryce (Ghiaccio). Totodile e' altrettanto valido: "
            "Feraligatr ha statistiche di Attacco eccellenti e impara Surf e Cascata "
            "per le MN. Chikorita e' la scelta piu' difficile: debole contro le prime "
            "palestre (Falkner Volante, Bugsy Coleottero) e ha pochi matchup favorevoli."
        ),
        "best_team": (
            "Una squadra bilanciata per Johto:\n"
            "- Typhlosion (Fuoco) - starter, copre Acciaio e Ghiaccio\n"
            "- Espeon (Psico) - l'Eevee di Citta' Amarantopoli fatto evolvere di giorno, potentissimo\n"
            "- Heracross (Coleottero/Lotta) - catturabile con Bottintesta, enorme Attacco\n"
            "- Ampharos (Elettro) - cattura Mareep presto, copre Acqua e Volante\n"
            "- Gyarados (Acqua/Volante) - il Magikarp Rosso al Lago Collera, o qualsiasi Magikarp\n"
            "- Mamoswine non esiste ancora, quindi Lapras (Acqua/Ghiaccio) - ottenibile di venerdi' in Grotte di Ghiaccio\n"
            "Alternative valide: Ursaring, Red Gyarados, Dragonite (tardi ma devastante), "
            "Gengar (scambi), Scizor (scambi)."
        ),
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
        "game_it": "Pokemon Rubino, Zaffiro e Smeraldo",
        "game_en": "Pokemon Ruby, Sapphire & Emerald",
        "generation": 3,
        "region_it": "Hoenn",
        "versions": ["Rubino", "Zaffiro", "Smeraldo"],
        "starters": [
            {"name": "Treecko", "type_it": _t("Grass")},
            {"name": "Torchic", "type_it": _t("Fire")},
            {"name": "Mudkip", "type_it": _t("Water")},
        ],
        "best_starter": (
            "Mudkip e' ampiamente considerato il miglior starter di Gen 3. Evolve in "
            "Swampert (Acqua/Terra) che ha una sola debolezza (Erba 4x) ed e' superefficace "
            "contro moltissimi tipi. Batte le palestre di Roxanne (Roccia), Wattson (Elettro, "
            "grazie al tipo Terra immune), e Flannery (Fuoco). Torchic e' ottimo: Blaziken "
            "e' il primo starter Fuoco/Lotta, devastante con Calciardente e Sdoppiatore. "
            "Treecko e' il piu' debole: Sceptile e' veloce ma fragile, e Hoenn ha tanti "
            "tipi che lo contrastano."
        ),
        "best_team": (
            "Una squadra bilanciata per Hoenn:\n"
            "- Swampert (Acqua/Terra) - starter, quasi nessuna debolezza pratica\n"
            "- Gardevoir (Psico/Folletto in remake, Psico in originali) - cattura Ralts nel Percorso 102\n"
            "- Breloom (Erba/Lotta) - Spora + Semitraglia, cattura Shroomish nella Foresta di Petali\n"
            "- Flygon (Terra/Drago) - cattura Trapinch nel Deserto, ottima copertura\n"
            "- Aggron (Acciaio/Roccia) - cattura Aron nella Grotta Granito, tank fisico\n"
            "- Manectric (Elettro) - cattura Electrike sul Percorso 110, copre Acqua e Volante\n"
            "Alternative valide: Salamence (tardi), Milotic (difficile da ottenere), "
            "Swellow (disponibile presto), Camerupt."
        ),
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
        "game_it": "Pokemon Diamante, Perla e Platino",
        "game_en": "Pokemon Diamond, Pearl & Platinum",
        "generation": 4,
        "region_it": "Sinnoh",
        "versions": ["Diamante", "Perla", "Platino"],
        "starters": [
            {"name": "Turtwig", "type_it": _t("Grass")},
            {"name": "Chimchar", "type_it": _t("Fire")},
            {"name": "Piplup", "type_it": _t("Water")},
        ],
        "best_starter": (
            "Chimchar e' la scelta piu' consigliata per Sinnoh. Evolve in Infernape "
            "(Fuoco/Lotta), uno dei migliori starter in assoluto. I tipi Fuoco sono "
            "rarissimi in Sinnoh (in Diamante/Perla Chimchar e Ponyta sono gli unici "
            "due prima della Lega!) e serve per le palestre di Gardenia (Erba), "
            "Candice (Ghiaccio), Byron (Acciaio) e contro il campione Cynthia. "
            "Piplup e' secondo: Empoleon (Acqua/Acciaio) ha una tipizzazione unica con "
            "molte resistenze. Turtwig e' buono: Torterra (Erba/Terra) colpisce forte "
            "ma ha molte debolezze (Ghiaccio 4x)."
        ),
        "best_team": (
            "Una squadra bilanciata per Sinnoh:\n"
            "- Infernape (Fuoco/Lotta) - starter, Fuoco raro in Sinnoh\n"
            "- Staraptor (Normale/Volante) - cattura Starly subito, Prepotenza + Zuffa\n"
            "- Luxray (Elettro) - cattura Shinx presto, Prepotenza + Fulmindenti\n"
            "- Garchomp (Drago/Terra) - cattura Gible nella Grotta Nascosta, uno dei Pokemon piu' forti\n"
            "- Lucario (Lotta/Acciaio) - uovo da Marisio nella citta' di Ferruccio, ottima copertura\n"
            "- Gyarados (Acqua/Volante) o Floatzel (Acqua) - per Surf e copertura Acqua\n"
            "Alternative valide: Roserade (Veleno/Erba, forte speciale), Togekiss (con "
            "Leggiadro), Weavile (Buio/Ghiaccio), Gastrodon."
        ),
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
        "best_starter": (
            "Oshawott e' leggermente avvantaggiato per la run completa. Samurott impara "
            "una buona varieta' di mosse e ha statistiche bilanciate. Ha vantaggio "
            "contro la prima palestra solo se si sceglie Tepig. Tepig e' altrettanto "
            "forte: Emboar (Fuoco/Lotta) colpisce durissimo, anche se e' il terzo starter "
            "Fuoco/Lotta consecutivo. Snivy e' lo starter piu' debole della Gen 5: Serperior "
            "ha poche mosse di copertura e statistiche offensive basse (diventa molto forte "
            "solo con l'abilita' nascosta Inversione, non disponibile normalmente in-game)."
        ),
        "best_team": (
            "Una squadra bilanciata per Unima:\n"
            "- Samurott (Acqua) o Emboar (Fuoco/Lotta) - starter\n"
            "- Darmanitan (Fuoco) - cattura Darumaka nel Deserto Resort, Attacco mostruoso\n"
            "- Excadrill (Terra/Acciaio) - cattura Drilbur nelle grotte, veloce e potente\n"
            "- Krookodile (Terra/Buio) - cattura Sandile nel Deserto, Prepotenza + Terremoto\n"
            "- Reuniclus (Psico) - cattura Solosis (Bianco) o Gothita (Nero), ottimo speciale\n"
            "- Archeops (Roccia/Volante) - dal fossile, Attacco e Velocita' altissimi (ma Abilita' Sconforto)\n"
            "Alternative valide: Haxorus (Drago, Oltraggio devastante), Galvantula "
            "(Coleottero/Elettro, Elettrotela), Chandelure (Spettro/Fuoco), Eelektross "
            "(Elettro, nessuna debolezza grazie a Levitazione)."
        ),
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
        "best_starter": (
            "Froakie e' il migliore senza dubbio. Greninja (Acqua/Buio) e' velocissimo, "
            "ha un movepool eccellente e con l'abilita' Mutatipo (abilita' nascosta, "
            "disponibile solo con particolari metodi) diventa uno dei Pokemon piu' forti "
            "di sempre. Anche senza Mutatipo, Greninja e' eccellente in-game. "
            "Fennekin e' solido: Delphox (Fuoco/Psico) ha buone statistiche speciali. "
            "Chespin e' il meno forte: Chesnaught (Erba/Lotta) ha buon Attacco e Difesa "
            "ma troppe debolezze (Volante, Fuoco, Ghiaccio, Psico, Veleno, Folletto). "
            "Nota: in XY ricevi anche un secondo starter di Gen 1 (Bulbasaur/Charmander/Squirtle) "
            "poco dopo l'inizio."
        ),
        "best_team": (
            "Una squadra bilanciata per Kalos:\n"
            "- Greninja (Acqua/Buio) - starter, copertura enorme\n"
            "- Charizard (Fuoco/Volante) - secondo starter di Gen 1, Mega Evoluzione X o Y\n"
            "- Lucario (Lotta/Acciaio) - ricevuto nella storia a Shalour, Mega Evoluzione\n"
            "- Aegislash (Acciaio/Spettro) - cattura Honedge nel Percorso 6, forma offensiva/difensiva unica\n"
            "- Sylveon (Folletto) - evolvi l'Eevee ricevuto, devastante contro i Draghi\n"
            "- Talonflame (Fuoco/Volante) - cattura Fletchling subito, Aliraffica prioritaria\n"
            "Alternative valide: Gardevoir (Mega), Tyrantrum (fossile Drago/Roccia), "
            "Goodra (Drago), Florges (Folletto), Pangoro (Lotta/Buio)."
        ),
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
        "best_starter": (
            "Tutti e tre gli starter di Alola sono validi, ma Popplio ha un leggero "
            "vantaggio. Primarina (Acqua/Folletto) ha una tipizzazione eccellente con poche "
            "debolezze e colpisce forte con Canto della Sirena. Ha vantaggio contro molte "
            "sfide della storia. Litten e' altrettanto forte: Incineroar (Fuoco/Buio) "
            "ha Prepotenza, statistiche solide e buona copertura. Rowlet e' buono ma "
            "Decidueye (Erba/Spettro) e' piu' fragile e ha una tipizzazione con piu' debolezze."
        ),
        "best_team": (
            "Una squadra bilanciata per Alola:\n"
            "- Primarina (Acqua/Folletto) - starter, copre Drago, Buio e Lotta\n"
            "- Alolan Raichu (Elettro/Psico) - evolvi Pichu con la Pietratuono ad Alola\n"
            "- Mudsdale (Terra) - cattura Mudbray presto, Sopportazione + enorme Difesa\n"
            "- Salazzle (Veleno/Fuoco) - cattura Salandit femmina (12.5% chance), Corrosione unica\n"
            "- Mimikyu (Spettro/Folletto) - cattura nel Megamarket Abbandonato, Fantasmanto e' fantastico\n"
            "- Lycanroc (Roccia) - cattura Rockruff presto, Forma Giorno o Notte in base alla versione\n"
            "Alternative valide: Toxapex (tank incredibile), Araquanid (Acqua/Coleottero, "
            "Bolladacqua), Kommo-o (Drago/Lotta), Golisopod (Coleottero/Acqua), Alolan Ninetales (Ghiaccio/Folletto)."
        ),
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
        "best_starter": (
            "Scorbunny e' la scelta piu' forte. Cinderace (Fuoco) ha Velocita' e Attacco "
            "eccellenti, e con l'abilita' nascosta Libero (simile a Mutatipo di Greninja) "
            "cambia tipo ad ogni mossa. Anche senza abilita' nascosta, e' il piu' efficiente "
            "contro le palestre. Grookey e' secondo: Rillaboom (Erba) e' molto solido con "
            "Erbogenesi da abilita' nascosta e ottimo Attacco. Sobble e' il piu' debole "
            "dei tre: Inteleon (Acqua) e' un glass cannon veloce con buon Att.Sp ma fragile."
        ),
        "best_team": (
            "Una squadra bilanciata per Galar:\n"
            "- Cinderace (Fuoco) - starter, veloce e versatile\n"
            "- Corviknight (Volante/Acciaio) - cattura Rookidee subito, tank con Blindospecchio\n"
            "- Toxtricity (Elettro/Veleno) - evolvi Toxel (ricevuto nel Percorso 5), Forma Acuta o Bassa\n"
            "- Excadrill (Terra/Acciaio) - cattura nella Terra Selvaggia, potentissimo\n"
            "- Dragapult (Drago/Spettro) - cattura Dreepy nel Lago dell'Ira (tardi), uno dei piu' forti\n"
            "- Grimmsnarl (Buio/Folletto) - cattura Impidimp nella Foresta Sonnocchiuta, Schermoluce/Riflesso di supporto\n"
            "Alternative valide: Gyarados (Terra Selvaggia, Dynamax devastante), Dracovish "
            "(fossile, Branchiomorso distruttivo), Hatterene (Psico/Folletto), Darmanitan-Galar."
        ),
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
        "best_starter": (
            "Fuecoco e' generalmente il piu' consigliato. Skeledirge (Fuoco/Spettro) "
            "ha una tipizzazione unica eccellente, solo 4 debolezze e 6 resistenze + 1 immunita'. "
            "La mossa firma Canzone Ardente e' fortissima. Ha matchup favorevoli contro molte "
            "sfide della storia. Quaxly e' altrettanto valido: Quaquaval (Acqua/Lotta) e' "
            "veloce e forte fisicamente con Idroballetto. Sprigatito e' buono: "
            "Meowscarada (Erba/Buio) e' velocissimo e colpisce forte con Prestigiafiore, "
            "ma e' il piu' fragile dei tre."
        ),
        "best_team": (
            "Una squadra bilanciata per Paldea:\n"
            "- Skeledirge (Fuoco/Spettro) - starter, Canzone Ardente devastante\n"
            "- Pawmot (Elettro/Lotta) - cattura Pawmi nel Percorso 1, Preghiera Vitale per cure\n"
            "- Clodsire (Veleno/Terra) - cattura Wooper-Paldea presto, Assorbacqua + grande bulk\n"
            "- Garganacl (Roccia) - cattura Nacli presto, Sale Purificante lo rende quasi immortale\n"
            "- Tinkaton (Folletto/Acciaio) - cattura Tinkatink, tipizzazione difensiva eccellente\n"
            "- Baxcalibur (Drago/Ghiaccio) - cattura Frigibax nella Provincia Guancia (3), potente attaccante\n"
            "Alternative valide: Ceruledge o Armarouge (esclusivi di versione), Kingambit "
            "(Buio/Acciaio, Generale Supremo), Garchomp (tardi), Annihilape (Lotta/Spettro), "
            "Palafin (Acqua, forma Eroe fortissima)."
        ),
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

    # ═══════════════════════════════════════════════════════════════
    # REMAKES — Entries separate per giochi con regione diversa
    # ═══════════════════════════════════════════════════════════════

    "firered_leafgreen": {
        "game_it": "Pokemon Rosso Fuoco e Verde Foglia",
        "game_en": "Pokemon FireRed & LeafGreen",
        "generation": 3,
        "region_it": "Kanto",
        "versions": ["Rosso Fuoco", "Verde Foglia"],
        "starters": [
            {"name": "Bulbasaur", "type_it": f"{_t('Grass')}/{_t('Poison')}"},
            {"name": "Charmander", "type_it": _t("Fire")},
            {"name": "Squirtle", "type_it": _t("Water")},
        ],
        "best_starter": (
            "Bulbasaur resta la scelta piu' efficiente anche in FRLG. Vantaggio contro "
            "Brock e Misty, resiste Lt. Surge, e con le abilita' introdotte in Gen 3 "
            "(Crescita) diventa ancora piu' versatile. Squirtle e' secondo: Blastoise "
            "e' un tank affidabile. Charmander e' la sfida: debole alle prime palestre "
            "ma Charizard domina il mid-late game."
        ),
        "best_team": (
            "Una squadra bilanciata per Kanto (FRLG):\n"
            "- Venusaur (Erba/Veleno) - starter, copre Acqua e Roccia\n"
            "- Alakazam (Psico) - cattura Abra al Percorso 24, potentissimo speciale\n"
            "- Snorlax (Normale) - cattura con Pokeflauto, bulk enorme e Riposo\n"
            "- Lapras (Acqua/Ghiaccio) - ricevuto gratis alla Silph S.p.A., copre Drago e Volante\n"
            "- Jolteon (Elettro) - evolvi l'Eevee di Azzurropoli, velocissimo\n"
            "- Nidoking (Veleno/Terra) - cattura Nidoran presto, movepool vastissimo\n"
            "Alternative valide: Arcanine (solo Rosso Fuoco), Starmie, Heracross "
            "(Isole Spumarine postgame), Dragonite (tardi)."
        ),
        "legendaries": [
            {"name": "Articuno", "type_it": f"{_t('Ice')}/{_t('Flying')}",
             "location": "Isole Spumarine"},
            {"name": "Zapdos", "type_it": f"{_t('Electric')}/{_t('Flying')}",
             "location": "Centrale Elettrica"},
            {"name": "Moltres", "type_it": f"{_t('Fire')}/{_t('Flying')}",
             "location": "Monte Brace (Isola Uno)"},
            {"name": "Mewtwo", "type_it": _t("Psychic"),
             "location": "Grotta Celeste (dopo la Lega)"},
        ],
        "version_exclusives": {
            "Rosso Fuoco": [
                "Oddish", "Gloom", "Vileplume", "Psyduck", "Golduck",
                "Growlithe", "Arcanine", "Shellder", "Cloyster",
                "Elekid", "Electabuzz", "Scyther", "Wooper", "Quagsire",
            ],
            "Verde Foglia": [
                "Bellsprout", "Weepinbell", "Victreebel", "Slowpoke", "Slowbro",
                "Staryu", "Starmie", "Vulpix", "Ninetales",
                "Magby", "Magmar", "Pinsir", "Marill", "Azumarill",
            ],
        },
    },

    "heartgold_soulsilver": {
        "game_it": "Pokemon HeartGold e SoulSilver",
        "game_en": "Pokemon HeartGold & SoulSilver",
        "generation": 4,
        "region_it": "Johto",
        "versions": ["HeartGold", "SoulSilver"],
        "starters": [
            {"name": "Chikorita", "type_it": _t("Grass")},
            {"name": "Cyndaquil", "type_it": _t("Fire")},
            {"name": "Totodile", "type_it": _t("Water")},
        ],
        "best_starter": (
            "Cyndaquil e' la scelta migliore anche in HGSS. Typhlosion e' potente e i tipi "
            "Fuoco sono rari in Johto. Totodile e' altrettanto valido: Feraligatr con "
            "Danzaspada e Cascata (ora fisico in Gen 4) e' devastante. Chikorita resta "
            "la scelta piu' difficile: matchup sfavorevoli contro le prime palestre."
        ),
        "best_team": (
            "Una squadra bilanciata per Johto (HGSS):\n"
            "- Typhlosion (Fuoco) - starter, copre Acciaio e Ghiaccio\n"
            "- Espeon (Psico) - l'Eevee ricevuto da Bill ad Amarantopoli, evolvi con amicizia di giorno\n"
            "- Heracross (Coleottero/Lotta) - cattura con Bottintesta agli alberi, Attacco enorme\n"
            "- Ampharos (Elettro) - cattura Mareep presto al Percorso 32, copre Acqua e Volante\n"
            "- Red Gyarados (Acqua/Volante) - cattura obbligatoria al Lago Collera, Surf e Cascata\n"
            "- Mamoswine (Ghiaccio/Terra) - cattura Swinub nelle Grotte di Ghiaccio, evolvi con Forzantica\n"
            "Alternative valide: Dragonite (Tana del Drago, tardi ma devastante), "
            "Crobat (amicizia da Zubat), Machamp (scambi), Ursaring, Togekiss (uovo Togepi)."
        ),
        "legendaries": [
            {"name": "Ho-Oh", "type_it": f"{_t('Fire')}/{_t('Flying')}",
             "location": "Torre Campanaria (HeartGold, prima della Lega)"},
            {"name": "Lugia", "type_it": f"{_t('Psychic')}/{_t('Flying')}",
             "location": "Isole Turbine (SoulSilver, prima della Lega)"},
            {"name": "Raikou", "type_it": _t("Electric"),
             "location": "Vagante per Johto (dopo Torre Bruciata)"},
            {"name": "Entei", "type_it": _t("Fire"),
             "location": "Vagante per Johto (dopo Torre Bruciata)"},
            {"name": "Suicune", "type_it": _t("Water"),
             "location": "Percorso 25 (dopo gli eventi di Kanto)"},
            {"name": "Latias", "type_it": f"{_t('Dragon')}/{_t('Psychic')}",
             "location": "Vagante per Kanto (HeartGold, postgame)"},
            {"name": "Latios", "type_it": f"{_t('Dragon')}/{_t('Psychic')}",
             "location": "Vagante per Kanto (SoulSilver, postgame)"},
            {"name": "Groudon", "type_it": _t("Ground"),
             "location": "Grotta Incastonata (HeartGold, con Rossa Sfera)"},
            {"name": "Kyogre", "type_it": _t("Water"),
             "location": "Grotta Incastonata (SoulSilver, con Blu Sfera)"},
            {"name": "Rayquaza", "type_it": f"{_t('Dragon')}/{_t('Flying')}",
             "location": "Grotta Incastonata (con Groudon e Kyogre)"},
            {"name": "Mewtwo", "type_it": _t("Psychic"),
             "location": "Grotta Celeste (Kanto postgame)"},
        ],
        "version_exclusives": {
            "HeartGold": [
                "Mankey", "Primeape", "Growlithe", "Arcanine",
                "Spinarak", "Ariados", "Gligar", "Mantine",
                "Phanpy", "Donphan", "Sableye", "Baltoy", "Claydol",
                "Kyogre",
            ],
            "SoulSilver": [
                "Vulpix", "Ninetales", "Meowth", "Persian",
                "Ledyba", "Ledian", "Teddiursa", "Ursaring",
                "Delibird", "Skarmory", "Mawile", "Gulpin", "Swalot",
                "Groudon",
            ],
        },
    },

    "omega_ruby_alpha_sapphire": {
        "game_it": "Pokemon Rubino Omega e Zaffiro Alpha",
        "game_en": "Pokemon Omega Ruby & Alpha Sapphire",
        "generation": 6,
        "region_it": "Hoenn",
        "versions": ["Rubino Omega", "Zaffiro Alpha"],
        "starters": [
            {"name": "Treecko", "type_it": _t("Grass")},
            {"name": "Torchic", "type_it": _t("Fire")},
            {"name": "Mudkip", "type_it": _t("Water")},
        ],
        "best_starter": (
            "Mudkip e' la scelta migliore anche in ORAS. Swampert (Acqua/Terra) con la "
            "Mega Evoluzione guadagna Nuotovelox e diventa devastante sotto la pioggia. "
            "Solo una debolezza (Erba 4x). Torchic e' secondo: Blaziken con Mega Evoluzione "
            "e Boostvelox e' uno dei Pokemon piu' forti di sempre. Treecko e' il piu' debole: "
            "Sceptile Mega diventa Erba/Drago, interessante ma fragile."
        ),
        "best_team": (
            "Una squadra bilanciata per Hoenn (ORAS):\n"
            "- Mega Swampert (Acqua/Terra) - starter, Nuotovelox sotto pioggia\n"
            "- Gardevoir (Psico/Folletto) - cattura Ralts al Percorso 102, Mega Evoluzione disponibile\n"
            "- Breloom (Erba/Lotta) - cattura Shroomish nel Bosco di Petali, Sporeffetto + Tecnico\n"
            "- Flygon (Terra/Drago) - cattura Trapinch nel Deserto, Levitazione utile\n"
            "- Mega Aggron (Acciaio) - cattura Aron nella Grotta Pietrosa, Solidroccia pura da tank\n"
            "- Manectric (Elettro) - cattura Electrike al Percorso 110, Mega Evoluzione disponibile\n"
            "Alternative valide: Mega Altaria (Drago/Folletto), Mega Camerupt, Milotic, "
            "Latios/Latias (ottenibili nella storia, Mega Evoluzione con Eon Ticket)."
        ),
        "legendaries": [
            {"name": "Primal Groudon", "type_it": f"{_t('Ground')}/{_t('Fire')}",
             "location": "Antro Abissale (Rubino Omega)"},
            {"name": "Primal Kyogre", "type_it": _t("Water"),
             "location": "Grotta dei Fondali (Zaffiro Alpha)"},
            {"name": "Mega Rayquaza", "type_it": f"{_t('Dragon')}/{_t('Flying')}",
             "location": "Torre dei Cieli (Episodio Delta)"},
            {"name": "Deoxys", "type_it": _t("Psychic"),
             "location": "Spazio (Episodio Delta)"},
            {"name": "Latios", "type_it": f"{_t('Dragon')}/{_t('Psychic')}",
             "location": "Rubino Omega (storia Eon)"},
            {"name": "Latias", "type_it": f"{_t('Dragon')}/{_t('Psychic')}",
             "location": "Zaffiro Alpha (storia Eon)"},
        ],
        "version_exclusives": {
            "Rubino Omega": [
                "Seedot", "Nuzleaf", "Shiftry", "Mawile",
                "Zangoose", "Solrock", "Ho-Oh", "Palkia",
                "Tornadus", "Reshiram",
            ],
            "Zaffiro Alpha": [
                "Lotad", "Lombre", "Ludicolo", "Sableye",
                "Seviper", "Lunatone", "Lugia", "Dialga",
                "Thundurus", "Zekrom",
            ],
        },
    },

    "lets_go": {
        "game_it": "Pokemon Let's Go, Pikachu! e Let's Go, Eevee!",
        "game_en": "Pokemon Let's Go, Pikachu! & Let's Go, Eevee!",
        "generation": 7,
        "region_it": "Kanto",
        "versions": ["Let's Go Pikachu", "Let's Go Eevee"],
        "starters": [
            {"name": "Pikachu", "type_it": _t("Electric")},
            {"name": "Eevee", "type_it": _t("Normal")},
        ],
        "best_starter": (
            "Il partner iniziale NON puo' evolversi, ma impara mosse esclusive potentissime. "
            "Pikachu impara Fulmischianto (Elettro), Surfaschianto (Acqua), Ciclonaschianto "
            "(Volante). Eevee impara mosse di 8 tipi diversi (Splendibolla, Botta Ardente, "
            "ecc.), rendendolo incredibilmente versatile. Eevee e' leggermente superiore "
            "per la varieta' di copertura tipo."
        ),
        "best_team": (
            "Una squadra bilanciata per Kanto (Let's Go):\n"
            "- Pikachu/Eevee partner - mosse esclusive potentissime, non evolve\n"
            "- Venusaur, Charizard o Blastoise - ricevuto come dono nella storia\n"
            "- Snorlax (Normale) - Pokeflauto sul Percorso 12/16, tank imbattibile\n"
            "- Alolan Raichu o Alolan Ninetales - scambia con NPC le forme di Alola\n"
            "- Lapras (Acqua/Ghiaccio) - ricevuto gratis alla Silph S.p.A.\n"
            "- Aerodactyl (Roccia/Volante) - fossile dall'Ambra Antica, Velocita' altissima\n"
            "Note: solo i 151 Pokemon originali + Meltan/Melmetal. "
            "Niente abilita', niente strumenti tenuti, catture stile Pokemon GO."
        ),
        "legendaries": [
            {"name": "Articuno", "type_it": f"{_t('Ice')}/{_t('Flying')}",
             "location": "Isole Spumarine"},
            {"name": "Zapdos", "type_it": f"{_t('Electric')}/{_t('Flying')}",
             "location": "Centrale Elettrica"},
            {"name": "Moltres", "type_it": f"{_t('Fire')}/{_t('Flying')}",
             "location": "Via Vittoria"},
            {"name": "Mewtwo", "type_it": _t("Psychic"),
             "location": "Grotta Celeste (dopo la Lega)"},
        ],
        "version_exclusives": {
            "Let's Go Pikachu": [
                "Oddish", "Gloom", "Vileplume", "Sandshrew", "Sandslash",
                "Growlithe", "Arcanine", "Grimer", "Muk", "Scyther", "Mankey", "Primeape",
            ],
            "Let's Go Eevee": [
                "Bellsprout", "Weepinbell", "Victreebel", "Vulpix", "Ninetales",
                "Meowth", "Persian", "Koffing", "Weezing", "Pinsir", "Ekans", "Arbok",
            ],
        },
    },

    "brilliant_diamond_shining_pearl": {
        "game_it": "Pokemon Diamante Lucente e Perla Splendente",
        "game_en": "Pokemon Brilliant Diamond & Shining Pearl",
        "generation": 8,
        "region_it": "Sinnoh",
        "versions": ["Diamante Lucente", "Perla Splendente"],
        "starters": [
            {"name": "Turtwig", "type_it": _t("Grass")},
            {"name": "Chimchar", "type_it": _t("Fire")},
            {"name": "Piplup", "type_it": _t("Water")},
        ],
        "best_starter": (
            "Chimchar resta la scelta migliore anche in BDSP. I tipi Fuoco sono rarissimi "
            "in Sinnoh. Infernape (Fuoco/Lotta) domina le palestre e la Lega. "
            "Piplup e' secondo: Empoleon (Acqua/Acciaio) ha una tipizzazione unica. "
            "Il Grand Underground di BDSP rende piu' facile ottenere tipi Fuoco alternativi "
            "(Houndoom, Magmar), ma Chimchar resta il migliore."
        ),
        "best_team": (
            "Una squadra bilanciata per Sinnoh (BDSP):\n"
            "- Infernape (Fuoco/Lotta) - starter, tipo Fuoco raro in Sinnoh\n"
            "- Staraptor (Normale/Volante) - cattura Starly subito, Prepotenza + Zuffa\n"
            "- Luxray (Elettro) - cattura Shinx presto, Prepotenza + Fulmindenti\n"
            "- Garchomp (Drago/Terra) - cattura Gible nella Grotta Nascosta o Grand Underground\n"
            "- Lucario (Lotta/Acciaio) - dall'uovo di Marisio, ottima copertura\n"
            "- Gyarados (Acqua/Volante) - facile da ottenere, Intimidazione + Cascata\n"
            "Alternative valide: Roserade (Veleno/Erba), Togekiss (Leggiadro), "
            "Weavile (Buio/Ghiaccio), Gastrodon, Houndoom (Grand Underground)."
        ),
        "legendaries": [
            {"name": "Dialga", "type_it": f"{_t('Steel')}/{_t('Dragon')}",
             "location": "Vetta Lancia (Diamante Lucente)"},
            {"name": "Palkia", "type_it": f"{_t('Water')}/{_t('Dragon')}",
             "location": "Vetta Lancia (Perla Splendente)"},
            {"name": "Giratina", "type_it": f"{_t('Ghost')}/{_t('Dragon')}",
             "location": "Fonte Ritorno (postgame)"},
            {"name": "Uxie", "type_it": _t("Psychic"),
             "location": "Lago Sapienza"},
            {"name": "Mesprit", "type_it": _t("Psychic"),
             "location": "Vagante (dopo Lago Valore)"},
            {"name": "Azelf", "type_it": _t("Psychic"),
             "location": "Lago Coraggio"},
        ],
        "version_exclusives": {
            "Diamante Lucente": [
                "Caterpie", "Metapod", "Butterfree", "Ekans", "Arbok",
                "Growlithe", "Arcanine", "Seel", "Dewgong", "Scyther",
                "Murkrow", "Honchkrow", "Gligar", "Gliscor",
                "Larvitar", "Pupitar", "Tyranitar", "Seedot", "Nuzleaf",
                "Shiftry", "Mawile", "Cranidos", "Rampardos",
                "Stunky", "Skuntank", "Dialga",
            ],
            "Perla Splendente": [
                "Weedle", "Kakuna", "Beedrill", "Sandshrew", "Sandslash",
                "Vulpix", "Ninetales", "Slowpoke", "Slowbro",
                "Pinsir", "Misdreavus", "Mismagius", "Teddiursa", "Ursaring",
                "Stantler", "Bagon", "Shelgon", "Salamence", "Lotad",
                "Lombre", "Ludicolo", "Sableye", "Shieldon", "Bastiodon",
                "Glameow", "Purugly", "Palkia",
            ],
        },
    },

    "legends_arceus": {
        "game_it": "Pokemon Leggende: Arceus",
        "game_en": "Pokemon Legends: Arceus",
        "generation": 8,
        "region_it": "Hisui",
        "versions": ["Leggende Arceus"],
        "starters": [
            {"name": "Rowlet", "type_it": f"{_t('Grass')}/{_t('Flying')}"},
            {"name": "Cyndaquil", "type_it": _t("Fire")},
            {"name": "Oshawott", "type_it": _t("Water")},
        ],
        "best_starter": (
            "Tutti e tre sono validi grazie alle loro evoluzioni Hisuiane uniche. "
            "Cyndaquil e' leggermente consigliato: Typhlosion-Hisui (Fuoco/Spettro) "
            "ha una tipizzazione unica e potente. Oshawott e' secondo: Samurott-Hisui "
            "(Acqua/Buio) colpisce forte. Rowlet e' buono: Decidueye-Hisui (Erba/Lotta) "
            "ma ha piu' debolezze."
        ),
        "best_team": (
            "Una squadra bilanciata per Hisui:\n"
            "- Typhlosion-Hisui (Fuoco/Spettro) - starter, tipizzazione unica\n"
            "- Ursaluna (Terra/Normale) - evolvi Teddiursa con Blocco di Torba durante luna piena\n"
            "- Kleavor (Coleottero/Roccia) - forma Hisuiana di Scyther, Lord e Custode\n"
            "- Zoroark-Hisui (Normale/Spettro) - cattura nelle Distese Innevate, 3 immunita'\n"
            "- Goodra-Hisui (Acciaio/Drago) - evolvi Goomy, tank con copertura eccellente\n"
            "- Gardevoir (Psico/Folletto) o Lucario (Lotta/Acciaio) - disponibili nei Campi Cremisi\n"
            "Note: gameplay completamente diverso dai giochi tradizionali. Niente strumenti "
            "tenuti, niente abilita' in lotta. Sistema Agile/Potente per le mosse."
        ),
        "legendaries": [
            {"name": "Dialga (Origine)", "type_it": f"{_t('Steel')}/{_t('Dragon')}",
             "location": "Tempio di Sinnoh (storia principale)"},
            {"name": "Palkia (Origine)", "type_it": f"{_t('Water')}/{_t('Dragon')}",
             "location": "Tempio di Sinnoh (storia principale)"},
            {"name": "Giratina (Origine)", "type_it": f"{_t('Ghost')}/{_t('Dragon')}",
             "location": "Fonte Ritorno (postgame)"},
            {"name": "Arceus", "type_it": _t("Normal"),
             "location": "Tempio di Sinnoh (dopo aver catturato tutti i Pokemon)"},
            {"name": "Enamorus", "type_it": f"{_t('Fairy')}/{_t('Flying')}",
             "location": "Campi Cremisi (dopo le Forze della Natura)"},
        ],
        "version_exclusives": {},
    },
}
