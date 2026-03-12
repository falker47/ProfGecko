"""Supplemental obtainment methods not covered by PokeAPI encounters.

PokeAPI only provides wild encounter data (grass, caves, fishing, etc.).
This module covers alternative obtainment methods such as:
- Game Corner purchases (Casino)
- NPC gifts (story gifts, fossils)
- In-game trades
- Special events (Togepi egg, etc.)

Keyed by lowercase PokeAPI species name. Each entry lists the generation,
game versions (Italian names), method, and details.

Sources: Bulbapedia, Serebii, PokemonDB
"""

from __future__ import annotations

SUPPLEMENTAL_OBTAINMENT: dict[str, list[dict]] = {
    # ── Game Corner / Casino purchases ─────────────────────────────
    "abra": [
        {"generation": 1, "versions": ["Rosso", "Blu"],
         "method_it": "Sala Giochi di Azzurropoli",
         "details_it": "Acquisto per 200 gettoni (Blu) o 120 (Rosso)"},
        {"generation": 1, "versions": ["Giallo"],
         "method_it": "Sala Giochi di Azzurropoli",
         "details_it": "Acquisto per 230 gettoni"},
        {"generation": 3, "versions": ["Rosso Fuoco", "Verde Foglia"],
         "method_it": "Sala Giochi di Azzurropoli",
         "details_it": "Acquisto per 120 gettoni (RF) o 180 (VF)"},
    ],
    "clefairy": [
        {"generation": 1, "versions": ["Rosso", "Blu"],
         "method_it": "Sala Giochi di Azzurropoli",
         "details_it": "Acquisto per 500 gettoni (Rosso) o 750 (Blu)"},
        {"generation": 3, "versions": ["Rosso Fuoco", "Verde Foglia"],
         "method_it": "Sala Giochi di Azzurropoli",
         "details_it": "Acquisto per 500 gettoni (RF) o 750 (VF)"},
    ],
    "dratini": [
        {"generation": 1, "versions": ["Rosso", "Blu"],
         "method_it": "Sala Giochi di Azzurropoli",
         "details_it": "Acquisto per 2800 gettoni"},
        {"generation": 1, "versions": ["Giallo"],
         "method_it": "Sala Giochi di Azzurropoli",
         "details_it": "Acquisto per 4600 gettoni"},
        {"generation": 3, "versions": ["Rosso Fuoco", "Verde Foglia"],
         "method_it": "Sala Giochi di Azzurropoli",
         "details_it": "Acquisto per 2800 gettoni"},
        {"generation": 4, "versions": ["HeartGold", "SoulSilver"],
         "method_it": "Tana del Drago",
         "details_it": "Dono dal Capo degli Anziani dopo il test nella Tana del Drago"},
    ],
    "porygon": [
        {"generation": 1, "versions": ["Rosso", "Blu"],
         "method_it": "Sala Giochi di Azzurropoli",
         "details_it": "Acquisto per 9999 gettoni (R) o 6500 (B)"},
        {"generation": 1, "versions": ["Giallo"],
         "method_it": "Sala Giochi di Azzurropoli",
         "details_it": "Acquisto per 6500 gettoni"},
        {"generation": 3, "versions": ["Rosso Fuoco", "Verde Foglia"],
         "method_it": "Sala Giochi di Azzurropoli",
         "details_it": "Acquisto per 9999 gettoni"},
    ],
    "scyther": [
        {"generation": 1, "versions": ["Rosso"],
         "method_it": "Sala Giochi di Azzurropoli",
         "details_it": "Acquisto per 5500 gettoni"},
        {"generation": 3, "versions": ["Rosso Fuoco"],
         "method_it": "Sala Giochi di Azzurropoli",
         "details_it": "Acquisto per 5500 gettoni"},
    ],
    "pinsir": [
        {"generation": 1, "versions": ["Blu"],
         "method_it": "Sala Giochi di Azzurropoli",
         "details_it": "Acquisto per 2500 gettoni"},
        {"generation": 3, "versions": ["Verde Foglia"],
         "method_it": "Sala Giochi di Azzurropoli",
         "details_it": "Acquisto per 2500 gettoni"},
    ],
    # Gen 2 Casino
    "mr. mime": [
        {"generation": 1, "versions": ["Rosso", "Blu", "Giallo"],
         "method_it": "Scambio in-game",
         "details_it": "Scambia un Abra con una ragazza nel Percorso 2 (unico modo)"},
        {"generation": 3, "versions": ["Rosso Fuoco", "Verde Foglia"],
         "method_it": "Scambio in-game",
         "details_it": "Scambia un Abra con una ragazza nel Percorso 2"},
    ],

    # ── NPC Gifts (story Pokemon) ─────────────────────────────────
    "bulbasaur": [
        {"generation": 6, "versions": ["X", "Y"],
         "method_it": "Dono NPC",
         "details_it": "Ricevuto dal Prof. Platan a Luminopoli come secondo starter di Gen 1"},
    ],
    "charmander": [
        {"generation": 6, "versions": ["X", "Y"],
         "method_it": "Dono NPC",
         "details_it": "Ricevuto dal Prof. Platan a Luminopoli come secondo starter di Gen 1"},
    ],
    "squirtle": [
        {"generation": 6, "versions": ["X", "Y"],
         "method_it": "Dono NPC",
         "details_it": "Ricevuto dal Prof. Platan a Luminopoli come secondo starter di Gen 1"},
    ],
    "eevee": [
        {"generation": 1, "versions": ["Rosso", "Blu", "Giallo"],
         "method_it": "Dono",
         "details_it": "Trovato sul tetto del Condominio Pokemon di Azzurropoli"},
        {"generation": 2, "versions": ["Oro", "Argento", "Cristallo"],
         "method_it": "Dono NPC",
         "details_it": "Ricevuto da Bill ad Amarantopoli"},
        {"generation": 3, "versions": ["Rosso Fuoco", "Verde Foglia"],
         "method_it": "Dono",
         "details_it": "Trovato sul tetto del Condominio Pokemon di Azzurropoli"},
        {"generation": 4, "versions": ["HeartGold", "SoulSilver"],
         "method_it": "Dono NPC",
         "details_it": "Ricevuto da Bill ad Amarantopoli"},
        {"generation": 4, "versions": ["Diamante", "Perla", "Platino"],
         "method_it": "Dono NPC",
         "details_it": "Ricevuto da Narciso a Cuoripoli (dopo Pokedex Nazionale)"},
        {"generation": 6, "versions": ["X", "Y"],
         "method_it": "Dono NPC",
         "details_it": "Ricevuto da un NPC nel Percorso 10"},
    ],
    "lapras": [
        {"generation": 1, "versions": ["Rosso", "Blu", "Giallo"],
         "method_it": "Dono NPC",
         "details_it": "Ricevuto da un dipendente Silph al 7o piano della Silph S.p.A. a Zafferanopoli"},
        {"generation": 2, "versions": ["Oro", "Argento", "Cristallo"],
         "method_it": "Incontro speciale",
         "details_it": "Appare nelle Grotte di Ghiaccio ogni venerdi (seminterrato)"},
        {"generation": 3, "versions": ["Rosso Fuoco", "Verde Foglia"],
         "method_it": "Dono NPC",
         "details_it": "Ricevuto da un dipendente Silph al 7o piano della Silph S.p.A."},
        {"generation": 4, "versions": ["HeartGold", "SoulSilver"],
         "method_it": "Incontro speciale",
         "details_it": "Appare nelle Grotte di Ghiaccio ogni venerdi"},
    ],
    "hitmonlee": [
        {"generation": 1, "versions": ["Rosso", "Blu", "Giallo"],
         "method_it": "Dono NPC",
         "details_it": "Scegli uno tra Hitmonlee e Hitmonchan al Dojo di Zafferanopoli"},
        {"generation": 3, "versions": ["Rosso Fuoco", "Verde Foglia"],
         "method_it": "Dono NPC",
         "details_it": "Scegli uno tra Hitmonlee e Hitmonchan al Dojo di Zafferanopoli"},
    ],
    "hitmonchan": [
        {"generation": 1, "versions": ["Rosso", "Blu", "Giallo"],
         "method_it": "Dono NPC",
         "details_it": "Scegli uno tra Hitmonlee e Hitmonchan al Dojo di Zafferanopoli"},
        {"generation": 3, "versions": ["Rosso Fuoco", "Verde Foglia"],
         "method_it": "Dono NPC",
         "details_it": "Scegli uno tra Hitmonlee e Hitmonchan al Dojo di Zafferanopoli"},
    ],
    "togepi": [
        {"generation": 2, "versions": ["Oro", "Argento", "Cristallo"],
         "method_it": "Uovo dono",
         "details_it": "Uovo ricevuto dall'Assistente del Prof. Elm al Centro Pokemon dopo il primo badge"},
        {"generation": 4, "versions": ["HeartGold", "SoulSilver"],
         "method_it": "Uovo dono",
         "details_it": "Uovo ricevuto dall'Assistente del Prof. Elm al Centro Pokemon"},
        {"generation": 4, "versions": ["Diamante", "Perla", "Platino"],
         "method_it": "Uovo dono",
         "details_it": "Uovo ricevuto da Camilla a Cuoripoli"},
    ],
    "riolu": [
        {"generation": 4, "versions": ["Diamante", "Perla", "Platino"],
         "method_it": "Uovo dono",
         "details_it": "Uovo ricevuto da Marisio sull'Isola Ferrosa (poi evolve in Lucario con amicizia)"},
        {"generation": 4, "versions": ["HeartGold", "SoulSilver"],
         "method_it": "Uovo dono",
         "details_it": "Uovo ricevuto al Percorso Camminata dopo la Hall of Fame"},
    ],
    "lucario": [
        {"generation": 6, "versions": ["X", "Y"],
         "method_it": "Dono NPC",
         "details_it": "Ricevuto dal Guru della Lotta a Shalour City con la sua Lucarionite"},
    ],
    "castform": [
        {"generation": 3, "versions": ["Rubino", "Zaffiro", "Smeraldo"],
         "method_it": "Dono NPC",
         "details_it": "Ricevuto al Centro Meteorologico sul Percorso 119 dopo aver sconfitto il Team"},
        {"generation": 6, "versions": ["Rubino Omega", "Zaffiro Alpha"],
         "method_it": "Dono NPC",
         "details_it": "Ricevuto al Centro Meteorologico sul Percorso 119"},
    ],
    "beldum": [
        {"generation": 3, "versions": ["Rubino", "Zaffiro", "Smeraldo"],
         "method_it": "Dono NPC",
         "details_it": "Pokeball sulla scrivania di Rocco Petri (casa postgame a Porto Alghepoli)"},
        {"generation": 6, "versions": ["Rubino Omega", "Zaffiro Alpha"],
         "method_it": "Dono NPC",
         "details_it": "Ricevuto da Rocco Petri dopo la Lega"},
    ],
    "wynaut": [
        {"generation": 3, "versions": ["Rubino", "Zaffiro", "Smeraldo"],
         "method_it": "Uovo dono",
         "details_it": "Uovo ricevuto da una signora alle Terme Ardenti"},
    ],
    "zorua": [
        {"generation": 5, "versions": ["Nero", "Bianco"],
         "method_it": "Dono NPC",
         "details_it": "Ricevuto come Zorua travestito a Castelia City (richiede evento Celebi)"},
    ],
    "larvesta": [
        {"generation": 5, "versions": ["Nero", "Bianco"],
         "method_it": "Uovo dono",
         "details_it": "Uovo ricevuto da un Ranger sul Percorso 18"},
    ],
    "toxel": [
        {"generation": 8, "versions": ["Spada", "Scudo"],
         "method_it": "Dono NPC",
         "details_it": "Ricevuto dall'allevatrice nel Vivaio del Percorso 5"},
    ],
    "type-null": [
        {"generation": 7, "versions": ["Sole", "Luna", "Ultrasole", "Ultraluna"],
         "method_it": "Dono NPC",
         "details_it": "Ricevuto da Iridio al Paradiso Aether (postgame)"},
        {"generation": 8, "versions": ["Spada", "Scudo"],
         "method_it": "Dono NPC",
         "details_it": "Ricevuto nella Torre Lotta (postgame)"},
    ],

    # ── Fossil Pokemon (choice) ───────────────────────────────────
    "omanyte": [
        {"generation": 1, "versions": ["Rosso", "Blu", "Giallo"],
         "method_it": "Fossile",
         "details_it": "Rigenera il Fossile Conchiglia al Laboratorio di Isola Cannella (scegli tra Omanyte e Kabuto)"},
        {"generation": 3, "versions": ["Rosso Fuoco", "Verde Foglia"],
         "method_it": "Fossile",
         "details_it": "Fossile Conchiglia nel Monte Luna (scegli tra Omanyte e Kabuto)"},
    ],
    "kabuto": [
        {"generation": 1, "versions": ["Rosso", "Blu", "Giallo"],
         "method_it": "Fossile",
         "details_it": "Rigenera il Fossile Cupola al Laboratorio di Isola Cannella (scegli tra Omanyte e Kabuto)"},
        {"generation": 3, "versions": ["Rosso Fuoco", "Verde Foglia"],
         "method_it": "Fossile",
         "details_it": "Fossile Cupola nel Monte Luna (scegli tra Omanyte e Kabuto)"},
    ],
    "aerodactyl": [
        {"generation": 1, "versions": ["Rosso", "Blu", "Giallo"],
         "method_it": "Fossile",
         "details_it": "Rigenera l'Ambra Antica (ricevuta da uno scienziato al Museo di Plumbeopoli)"},
        {"generation": 3, "versions": ["Rosso Fuoco", "Verde Foglia"],
         "method_it": "Fossile",
         "details_it": "Ambra Antica dal Museo di Plumbeopoli"},
    ],
    "lileep": [
        {"generation": 3, "versions": ["Rubino", "Zaffiro", "Smeraldo"],
         "method_it": "Fossile",
         "details_it": "Fossile Radice nel Deserto (scegli tra Lileep e Anorith)"},
    ],
    "anorith": [
        {"generation": 3, "versions": ["Rubino", "Zaffiro", "Smeraldo"],
         "method_it": "Fossile",
         "details_it": "Fossilartiglio nel Deserto (scegli tra Lileep e Anorith)"},
    ],
    "cranidos": [
        {"generation": 4, "versions": ["Diamante", "Platino"],
         "method_it": "Fossile",
         "details_it": "Fossile Cranio scavato nel Sotterraneo"},
        {"generation": 8, "versions": ["Diamante Lucente"],
         "method_it": "Fossile",
         "details_it": "Fossile Cranio scavato nel Grand Underground"},
    ],
    "shieldon": [
        {"generation": 4, "versions": ["Perla", "Platino"],
         "method_it": "Fossile",
         "details_it": "Fossile Armatura scavato nel Sotterraneo"},
        {"generation": 8, "versions": ["Perla Splendente"],
         "method_it": "Fossile",
         "details_it": "Fossile Armatura scavato nel Grand Underground"},
    ],
    "tirtouga": [
        {"generation": 5, "versions": ["Nero", "Bianco", "Nero 2", "Bianco 2"],
         "method_it": "Fossile",
         "details_it": "Fossile Coperchio ricevuto a Nacrene City"},
    ],
    "archen": [
        {"generation": 5, "versions": ["Nero", "Bianco", "Nero 2", "Bianco 2"],
         "method_it": "Fossile",
         "details_it": "Fossile Piuma ricevuto a Nacrene City"},
    ],
    "tyrunt": [
        {"generation": 6, "versions": ["X", "Y"],
         "method_it": "Fossile",
         "details_it": "Fossile Mascella (scegli tra Tyrunt e Amaura)"},
    ],
    "amaura": [
        {"generation": 6, "versions": ["X", "Y"],
         "method_it": "Fossile",
         "details_it": "Fossile Pinna (scegli tra Tyrunt e Amaura)"},
    ],

    # ── Notable in-game trades ─────────────────────────────────────
    "jynx": [
        {"generation": 1, "versions": ["Rosso", "Blu"],
         "method_it": "Scambio in-game",
         "details_it": "Scambia un Poliwhirl con un NPC al Percorso 18"},
    ],
    "farfetchd": [
        {"generation": 1, "versions": ["Rosso", "Blu"],
         "method_it": "Scambio in-game",
         "details_it": "Scambia uno Spearow con un NPC a Vermilion City"},
    ],
    "steelix": [
        {"generation": 4, "versions": ["Diamante", "Perla", "Platino"],
         "method_it": "Scambio in-game",
         "details_it": "Scambia un Medicham con Mindy sul Percorso 226 (postgame, NON evolve perche' tiene Pietrasempre)"},
    ],
    "haunter": [
        {"generation": 4, "versions": ["Diamante", "Perla", "Platino"],
         "method_it": "Scambio in-game",
         "details_it": "Scambia con Mindy a Nevepoli — attenzione: tiene Pietrasempre, quindi NON evolve in Gengar"},
    ],

    # ── Gen 4 special: Spiritomb ───────────────────────────────────
    "spiritomb": [
        {"generation": 4, "versions": ["Diamante", "Perla", "Platino"],
         "method_it": "Evento speciale",
         "details_it": "Inserisci la Pietra Chiave nella Torre Sgretolata (Percorso 209) dopo 32 interazioni nel Sotterraneo"},
    ],

    # ── Gen 5: Gift N's Pokemon ────────────────────────────────────
    "darmanitan": [
        {"generation": 5, "versions": ["Nero", "Bianco"],
         "method_it": "Dono speciale",
         "details_it": "Darmanitan con abilita' Forma Zen davanti al Resort Deserto (usa Acqua sulle statue)"},
    ],

    # ── Snorlax (blocking) ─────────────────────────────────────────
    "snorlax": [
        {"generation": 1, "versions": ["Rosso", "Blu", "Giallo"],
         "method_it": "Incontro statico",
         "details_it": "Due Snorlax bloccano i Percorsi 12 e 16, svegliabili con il Pokeflauto"},
        {"generation": 3, "versions": ["Rosso Fuoco", "Verde Foglia"],
         "method_it": "Incontro statico",
         "details_it": "Due Snorlax bloccano i Percorsi 12 e 16, svegliabili con il Pokeflauto"},
        {"generation": 4, "versions": ["HeartGold", "SoulSilver"],
         "method_it": "Incontro statico",
         "details_it": "Snorlax blocca l'ingresso della Grotta Diglett, svegliabile con il Pokeradio"},
    ],

    # ── Rotom ──────────────────────────────────────────────────────
    "rotom": [
        {"generation": 4, "versions": ["Diamante", "Perla", "Platino"],
         "method_it": "Incontro statico",
         "details_it": "TV nella Villa Chateau (notte, postgame in DP; pre-Lega in Platino)"},
    ],

    # ── Magikarp (notable purchase) ────────────────────────────────
    "magikarp": [
        {"generation": 1, "versions": ["Rosso", "Blu", "Giallo"],
         "method_it": "Acquisto NPC",
         "details_it": "Acquistabile per 500 Pokedollari dal venditore nel Centro Pokemon del Monte Luna"},
        {"generation": 3, "versions": ["Rosso Fuoco", "Verde Foglia"],
         "method_it": "Acquisto NPC",
         "details_it": "Acquistabile per 500 Pokedollari dal venditore nel Centro Pokemon del Monte Luna"},
        {"generation": 4, "versions": ["HeartGold", "SoulSilver"],
         "method_it": "Incontro speciale",
         "details_it": "Red Gyarados (shiny) al Lago Collera (evento storia)"},
    ],
}
