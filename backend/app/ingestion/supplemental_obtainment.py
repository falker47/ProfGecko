"""Supplemental obtainment methods not covered by PokeAPI encounters.

PokeAPI only provides wild encounter data (grass, caves, fishing, etc.).
This module covers alternative obtainment methods such as:
- Game Corner purchases (Casino)
- NPC gifts (story gifts, fossils)
- In-game trades
- Special events (Togepi egg, etc.)

Keyed by lowercase PokeAPI species name. Each entry lists the generation,
game versions (Italian names), method, and details.

Sources verified via Perplexity (Bulbapedia, Pokemon Central Wiki) — 2026-03-12
NPC names, location names, item names: official Italian game translations.
"""

from __future__ import annotations

SUPPLEMENTAL_OBTAINMENT: dict[str, list[dict]] = {
    # ── Game Corner / Casino purchases ─────────────────────────────
    "abra": [
        # Perplexity: Rosso=180, Blu=120, Giallo=230
        {"generation": 1, "versions": ["Rosso", "Blu"],
         "method_it": "Sala Giochi di Azzurropoli",
         "details_it": "Acquisto per 180 gettoni (Rosso) o 120 (Blu)"},
        {"generation": 1, "versions": ["Giallo"],
         "method_it": "Sala Giochi di Azzurropoli",
         "details_it": "Acquisto per 230 gettoni"},
        # Perplexity: RF=180, VF=120
        {"generation": 3, "versions": ["Rosso Fuoco", "Verde Foglia"],
         "method_it": "Sala Giochi di Azzurropoli",
         "details_it": "Acquisto per 180 gettoni (RF) o 120 (VF)"},
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
        # Perplexity: Rosso=2800, Blu=4600. Giallo: NON disponibile alla Sala Giochi
        {"generation": 1, "versions": ["Rosso"],
         "method_it": "Sala Giochi di Azzurropoli",
         "details_it": "Acquisto per 2800 gettoni"},
        {"generation": 1, "versions": ["Blu"],
         "method_it": "Sala Giochi di Azzurropoli",
         "details_it": "Acquisto per 4600 gettoni"},
        {"generation": 3, "versions": ["Rosso Fuoco", "Verde Foglia"],
         "method_it": "Sala Giochi di Azzurropoli",
         "details_it": "Acquisto per 2800 gettoni"},
        {"generation": 4, "versions": ["Oro HeartGold", "Argento SoulSilver"],
         "method_it": "Tana del Drago",
         "details_it": "Dono dal Capo degli Anziani dopo il test nella Tana del Drago"},
    ],
    "porygon": [
        # Perplexity: Rosso=9999, Blu=6500, Giallo=9999
        {"generation": 1, "versions": ["Rosso", "Blu"],
         "method_it": "Sala Giochi di Azzurropoli",
         "details_it": "Acquisto per 9999 gettoni (Rosso) o 6500 (Blu)"},
        {"generation": 1, "versions": ["Giallo"],
         "method_it": "Sala Giochi di Azzurropoli",
         "details_it": "Acquisto per 9999 gettoni"},
        {"generation": 3, "versions": ["Rosso Fuoco", "Verde Foglia"],
         "method_it": "Sala Giochi di Azzurropoli",
         "details_it": "Acquisto per 9999 gettoni (RF) o 6500 (VF)"},
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

    # ── In-game trades ───────────────────────────────────────────
    "mr. mime": [
        {"generation": 1, "versions": ["Rosso", "Blu"],
         "method_it": "Scambio in-game",
         "details_it": "Scambia un Abra con una ragazza nel Percorso 2 (unico modo per ottenerlo)"},
        {"generation": 1, "versions": ["Giallo"],
         "method_it": "Scambio in-game",
         "details_it": "Scambia un Clefairy con una ragazza nel Percorso 2 (unico modo per ottenerlo)"},
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
         "details_it": "Trovato sul tetto del Condominio di Azzurropoli"},
        # Perplexity: Oro e Cristallo da Bill; Argento dalla Sala Giochi
        {"generation": 2, "versions": ["Oro", "Cristallo"],
         "method_it": "Dono NPC",
         "details_it": "Ricevuto da Bill a Fiordoropoli"},
        {"generation": 2, "versions": ["Argento"],
         "method_it": "Sala Giochi di Fiordoropoli",
         "details_it": "Acquisto per 6666 gettoni alla Sala Giochi di Fiordoropoli"},
        {"generation": 3, "versions": ["Rosso Fuoco", "Verde Foglia"],
         "method_it": "Dono",
         "details_it": "Trovato sul tetto del Condominio di Azzurropoli"},
        {"generation": 4, "versions": ["Oro HeartGold", "Argento SoulSilver"],
         "method_it": "Dono NPC",
         "details_it": "Ricevuto da Bill a Fiordoropoli"},
        {"generation": 4, "versions": ["Diamante", "Perla"],
         "method_it": "Dono NPC",
         "details_it": "Ricevuto da Bebe (amministratrice PC) a Cuoripoli (dopo Pokedex Nazionale)"},
        {"generation": 4, "versions": ["Platino"],
         "method_it": "Dono NPC",
         "details_it": "Ricevuto da Bebe (amministratrice PC) a Cuoripoli (disponibile senza Pokedex Nazionale)"},
        {"generation": 6, "versions": ["X", "Y"],
         "method_it": "Dono NPC",
         "details_it": "Ricevuto da un NPC nel Percorso 10"},
    ],
    "lapras": [
        {"generation": 1, "versions": ["Rosso", "Blu", "Giallo"],
         "method_it": "Dono NPC",
         "details_it": "Ricevuto da un dipendente Silph al 7° piano della Silph S.p.A. a Zafferanopoli"},
        # Lapras appare ogni venerdi nella Grotta di Mezzo (tra Percorso 32 e 33)
        {"generation": 2, "versions": ["Oro", "Argento", "Cristallo"],
         "method_it": "Incontro speciale",
         "details_it": "Appare ogni venerdi nella Grotta di Mezzo (piano inferiore, serve Surf)"},
        {"generation": 3, "versions": ["Rosso Fuoco", "Verde Foglia"],
         "method_it": "Dono NPC",
         "details_it": "Ricevuto da un dipendente Silph al 7° piano della Silph S.p.A."},
        {"generation": 4, "versions": ["Oro HeartGold", "Argento SoulSilver"],
         "method_it": "Incontro speciale",
         "details_it": "Appare ogni venerdi nella Grotta di Mezzo (piano inferiore, serve Surf)"},
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
        {"generation": 4, "versions": ["Oro HeartGold", "Argento SoulSilver"],
         "method_it": "Uovo dono",
         "details_it": "Uovo ricevuto dall'Assistente del Prof. Elm al Centro Pokemon"},
        # Perplexity: solo Platino da Camilla, NON in Diamante/Perla
        {"generation": 4, "versions": ["Platino"],
         "method_it": "Uovo dono",
         "details_it": "Uovo ricevuto da Camilla a Evopoli"},
    ],
    "riolu": [
        {"generation": 4, "versions": ["Diamante", "Perla", "Platino"],
         "method_it": "Uovo dono",
         "details_it": "Uovo ricevuto da Marisio sull'Isola Ferrosa (poi evolve in Lucario con amicizia)"},
        {"generation": 4, "versions": ["Oro HeartGold", "Argento SoulSilver"],
         "method_it": "Pokewalker",
         "details_it": "Disponibile nella rotta Pokewalker 'Percorso Camminata' (accessorio esterno richiesto)"},
    ],
    "lucario": [
        # Perplexity: da Ornella (non "Guru della Lotta") alla Torre della Maestria
        {"generation": 6, "versions": ["X", "Y"],
         "method_it": "Dono NPC",
         "details_it": "Ricevuto da Ornella alla Torre della Maestria di Yantaropoli con la sua Lucarite"},
    ],
    "castform": [
        # Perplexity: "Istituto Meteo" e' il nome ufficiale italiano
        {"generation": 3, "versions": ["Rubino", "Zaffiro", "Smeraldo"],
         "method_it": "Dono NPC",
         "details_it": "Ricevuto all'Istituto Meteo sul Percorso 119 dopo aver sconfitto il Team"},
        {"generation": 6, "versions": ["Rubino Omega", "Zaffiro Alpha"],
         "method_it": "Dono NPC",
         "details_it": "Ricevuto all'Istituto Meteo sul Percorso 119"},
    ],
    "beldum": [
        {"generation": 3, "versions": ["Rubino", "Zaffiro", "Smeraldo"],
         "method_it": "Dono NPC",
         "details_it": "Pokeball sulla scrivania di Rocco Petri (casa postgame a Verdeazzupoli)"},
        {"generation": 6, "versions": ["Rubino Omega", "Zaffiro Alpha"],
         "method_it": "Dono NPC",
         "details_it": "Ricevuto da Rocco Petri dopo la Lega"},
    ],
    "wynaut": [
        {"generation": 3, "versions": ["Rubino", "Zaffiro", "Smeraldo"],
         "method_it": "Uovo dono",
         "details_it": "Uovo ricevuto da una signora alle terme di Cuordilava"},
    ],
    "zorua": [
        # Perplexity confermato: richiede Celebi da evento
        {"generation": 5, "versions": ["Nero", "Bianco"],
         "method_it": "Dono speciale",
         "details_it": "Ricevuto a Austropoli trasferendo un Celebi da evento speciale tramite Relocator"},
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
    # Nomi fossili italiani ufficiali da Pokemon Central Wiki:
    # Helix Fossil = Helixfossile, Dome Fossil = Domofossile,
    # Old Amber = Ambra Antica, Root Fossil = Radifossile,
    # Claw Fossil = Fossilunghia, Skull Fossil = Fossilcranio,
    # Armor Fossil = Fossilscudo, Cover Fossil = Fossiltappo,
    # Plume Fossil = Fossilpiuma, Jaw Fossil = Fossilmascella,
    # Sail Fossil = Fossilpinna
    "omanyte": [
        {"generation": 1, "versions": ["Rosso", "Blu", "Giallo"],
         "method_it": "Fossile",
         "details_it": "Rigenera l'Helixfossile al Laboratorio di Isola Cannella (scegli tra Omanyte e Kabuto)"},
        {"generation": 3, "versions": ["Rosso Fuoco", "Verde Foglia"],
         "method_it": "Fossile",
         "details_it": "Helixfossile nel Monte Luna (scegli tra Omanyte e Kabuto)"},
    ],
    "kabuto": [
        {"generation": 1, "versions": ["Rosso", "Blu", "Giallo"],
         "method_it": "Fossile",
         "details_it": "Rigenera il Domofossile al Laboratorio di Isola Cannella (scegli tra Omanyte e Kabuto)"},
        {"generation": 3, "versions": ["Rosso Fuoco", "Verde Foglia"],
         "method_it": "Fossile",
         "details_it": "Domofossile nel Monte Luna (scegli tra Omanyte e Kabuto)"},
    ],
    "aerodactyl": [
        {"generation": 1, "versions": ["Rosso", "Blu", "Giallo"],
         "method_it": "Fossile",
         "details_it": "Rigenera l'Ambra Antica (ricevuta nella sezione segreta del Museo di Plumbeopoli con HM Taglio)"},
        {"generation": 3, "versions": ["Rosso Fuoco", "Verde Foglia"],
         "method_it": "Fossile",
         "details_it": "Ambra Antica dal Museo di Plumbeopoli"},
    ],
    "lileep": [
        {"generation": 3, "versions": ["Rubino", "Zaffiro", "Smeraldo"],
         "method_it": "Fossile",
         "details_it": "Radifossile nel Deserto del Percorso 111 (scegli tra Lileep e Anorith)"},
    ],
    "anorith": [
        {"generation": 3, "versions": ["Rubino", "Zaffiro", "Smeraldo"],
         "method_it": "Fossile",
         "details_it": "Fossilunghia nel Deserto del Percorso 111 (scegli tra Lileep e Anorith)"},
    ],
    "cranidos": [
        # Perplexity: Fossilcranio. In Platino entrambi disponibili
        {"generation": 4, "versions": ["Diamante"],
         "method_it": "Fossile",
         "details_it": "Fossilcranio scavato nel Sotterraneo (esclusivo Diamante)"},
        {"generation": 4, "versions": ["Platino"],
         "method_it": "Fossile",
         "details_it": "Fossilcranio scavato nel Sotterraneo"},
        {"generation": 8, "versions": ["Diamante Lucente"],
         "method_it": "Fossile",
         "details_it": "Fossilcranio scavato nel Grand Underground"},
    ],
    "shieldon": [
        # Perplexity: Fossilscudo. In Platino entrambi disponibili
        {"generation": 4, "versions": ["Perla"],
         "method_it": "Fossile",
         "details_it": "Fossilscudo scavato nel Sotterraneo (esclusivo Perla)"},
        {"generation": 4, "versions": ["Platino"],
         "method_it": "Fossile",
         "details_it": "Fossilscudo scavato nel Sotterraneo"},
        {"generation": 8, "versions": ["Perla Splendente"],
         "method_it": "Fossile",
         "details_it": "Fossilscudo scavato nel Grand Underground"},
    ],
    "tirtouga": [
        # Perplexity: fossili scelti al Castello Sepolto, rigenerati al Museo di Zefiropoli
        {"generation": 5, "versions": ["Nero", "Bianco", "Nero 2", "Bianco 2"],
         "method_it": "Fossile",
         "details_it": "Fossiltappo ottenuto al Castello Sepolto, rigenerato al Museo di Zefiropoli"},
    ],
    "archen": [
        {"generation": 5, "versions": ["Nero", "Bianco", "Nero 2", "Bianco 2"],
         "method_it": "Fossile",
         "details_it": "Fossilpiuma ottenuto al Castello Sepolto, rigenerato al Museo di Zefiropoli"},
    ],
    "tyrunt": [
        {"generation": 6, "versions": ["X", "Y"],
         "method_it": "Fossile",
         "details_it": "Fossilmascella (scegli tra Tyrunt e Amaura)"},
    ],
    "amaura": [
        {"generation": 6, "versions": ["X", "Y"],
         "method_it": "Fossile",
         "details_it": "Fossilpinna (scegli tra Tyrunt e Amaura)"},
    ],

    # ── Notable in-game trades ─────────────────────────────────────
    "jynx": [
        {"generation": 1, "versions": ["Rosso", "Blu"],
         "method_it": "Scambio in-game",
         "details_it": "Scambia un Poliwhirl con un NPC a Celestopoli"},
    ],
    "farfetchd": [
        {"generation": 1, "versions": ["Rosso", "Blu"],
         "method_it": "Scambio in-game",
         "details_it": "Scambia uno Spearow con un NPC ad Aranciopoli"},
    ],
    "steelix": [
        {"generation": 4, "versions": ["Diamante", "Perla", "Platino"],
         "method_it": "Scambio in-game",
         "details_it": "Scambio in-game disponibile sul Percorso 226 (postgame)"},
    ],
    "haunter": [
        {"generation": 4, "versions": ["Diamante", "Perla", "Platino"],
         "method_it": "Scambio in-game",
         "details_it": "Scambia un Medicham con Mindy a Nevepoli — attenzione: Haunter tiene Pietrastante, quindi NON evolve in Gengar"},
    ],

    # ── Gen 4 special: Spiritomb ───────────────────────────────────
    "spiritomb": [
        # Perplexity: "Torre Memoria" per Hallowed Tower
        {"generation": 4, "versions": ["Diamante", "Perla", "Platino"],
         "method_it": "Evento speciale",
         "details_it": "Inserisci la Pietra Chiave nella Torre Memoria (Percorso 209) dopo 32 interazioni nel Sotterraneo"},
    ],

    # ── Gen 5: Darmanitan Forma Zen ───────────────────────────────
    "darmanitan": [
        # Perplexity: serve RageCandyBar, NON acqua
        {"generation": 5, "versions": ["Nero", "Bianco"],
         "method_it": "Dono speciale",
         "details_it": "Darmanitan con abilita' Forma Zen davanti al Deserto della Quiete "
                       "(usa una RageCandyBar sulle statue, acquistabile a Mistralopoli)"},
    ],

    # ── Snorlax (blocking) ─────────────────────────────────────────
    "snorlax": [
        {"generation": 1, "versions": ["Rosso", "Blu", "Giallo"],
         "method_it": "Incontro statico",
         "details_it": "Due Snorlax bloccano i Percorsi 12 e 16, svegliabili con il Pokeflauto"},
        {"generation": 3, "versions": ["Rosso Fuoco", "Verde Foglia"],
         "method_it": "Incontro statico",
         "details_it": "Due Snorlax bloccano i Percorsi 12 e 16, svegliabili con il Pokeflauto"},
        # Perplexity: serve sintonizzare Pokegear su frequenza Pokeflauto (scheda EXPN da Lavender Town)
        {"generation": 4, "versions": ["Oro HeartGold", "Argento SoulSilver"],
         "method_it": "Incontro statico",
         "details_it": "Snorlax blocca l'ingresso della Grotta Diglett, svegliabile con il Pokegear "
                       "sintonizzato sulla frequenza del Pokeflauto (richiede scheda EXPN)"},
    ],

    # ── Rotom ──────────────────────────────────────────────────────
    "rotom": [
        # Perplexity: NON e' postgame, accessibile appena si raggiunge Antico Chateau
        {"generation": 4, "versions": ["Diamante", "Perla", "Platino"],
         "method_it": "Incontro statico",
         "details_it": "TV nell'Antico Chateau di notte (richiede HM Taglio, accessibile prima della Lega)"},
    ],

    # ── Magikarp (notable purchase) + Red Gyarados ────────────────
    "magikarp": [
        {"generation": 1, "versions": ["Rosso", "Blu", "Giallo"],
         "method_it": "Acquisto NPC",
         "details_it": "Acquistabile per 500 Pokedollari dal venditore nel Centro Pokemon del Monte Luna"},
        {"generation": 3, "versions": ["Rosso Fuoco", "Verde Foglia"],
         "method_it": "Acquisto NPC",
         "details_it": "Acquistabile per 500 Pokedollari dal venditore nel Centro Pokemon del Monte Luna"},
        {"generation": 4, "versions": ["Oro HeartGold", "Argento SoulSilver"],
         "method_it": "Incontro speciale",
         "details_it": "Red Gyarados (shiny) al Lago d'Ira (evento storia)"},
    ],
}
