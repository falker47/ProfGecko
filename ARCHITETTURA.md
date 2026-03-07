# Prof. Gallade - Architettura e Concetti Teorici

Questo documento spiega i concetti teorici alla base del progetto Prof. Gallade: chatbot conversazionali, architettura Transformer, embedding vettoriali e Retrieval-Augmented Generation (RAG).

---

## 1. Chatbot Conversazionali

### Cos'e' un Chatbot

Un chatbot e' un sistema software che simula una conversazione in linguaggio naturale. Esistono due categorie principali:

- **Rule-based**: rispondono seguendo regole fisse (if/else, pattern matching). Semplici ma rigidi.
- **AI-based**: usano modelli di linguaggio (LLM) per generare risposte. Flessibili ma richiedono gestione accurata del contesto.

Prof. Gallade appartiene alla seconda categoria: usa un LLM (Gemini o Gemma) per generare risposte in italiano basandosi su dati Pokemon strutturati.

### Componenti di un Chatbot AI

```
Utente -> [Preprocessing] -> [Retrieval] -> [Generazione LLM] -> Risposta
              |                    |                |
         Pulizia input     Cerca contesto     Genera testo
         Detect intent     dal database       usando contesto
```

1. **Preprocessing**: analisi della domanda (lingua, intent, entita menzionate)
2. **Retrieval**: recupero di informazioni rilevanti da una base di conoscenza
3. **Generazione**: il modello di linguaggio produce la risposta usando il contesto

---

## 2. Architettura Transformer

### Il Problema: Sequenze Lunghe

Prima dei Transformer (2017), i modelli NLP usavano RNN (Recurrent Neural Networks) e LSTM che processavano il testo un token alla volta. Questo causava:
- Lentezza (non parallelizzabile)
- Perdita di informazione per sequenze lunghe
- Difficolta a catturare dipendenze tra parole distanti

### La Soluzione: Attention Mechanism

Il paper "Attention Is All You Need" (Vaswani et al., 2017) ha introdotto il meccanismo di **Self-Attention**: ogni token puo' "guardare" tutti gli altri token nella sequenza contemporaneamente, calcolando quanto ognuno e' rilevante.

```
Input: "Dragonite e' debole al Ghiaccio"

Self-Attention per "debole":
  Dragonite: 0.3  (chi e' debole?)
  e':        0.0  (irrilevante)
  debole:    0.1  (se stesso)
  al:        0.1  (preposizione)
  Ghiaccio:  0.5  (debole A COSA?)
```

### Struttura del Transformer

```
┌─────────────────────────────┐
│         Output              │
├─────────────────────────────┤
│    Linear + Softmax         │
├─────────────────────────────┤
│  ┌───────────────────────┐  │
│  │   Decoder Block (x N) │  │
│  │  ┌─────────────────┐  │  │
│  │  │ Feed-Forward     │  │  │
│  │  ├─────────────────┤  │  │
│  │  │ Cross-Attention  │  │  │
│  │  ├─────────────────┤  │  │
│  │  │ Masked Self-Attn │  │  │
│  │  └─────────────────┘  │  │
│  └───────────────────────┘  │
├─────────────────────────────┤
│  ┌───────────────────────┐  │
│  │   Encoder Block (x N) │  │
│  │  ┌─────────────────┐  │  │
│  │  │ Feed-Forward     │  │  │
│  │  ├─────────────────┤  │  │
│  │  │ Self-Attention   │  │  │
│  │  └─────────────────┘  │  │
│  └───────────────────────┘  │
├─────────────────────────────┤
│  Positional Encoding        │
├─────────────────────────────┤
│  Token Embedding            │
├─────────────────────────────┤
│         Input               │
└─────────────────────────────┘
```

**Componenti chiave:**

- **Token Embedding**: converte ogni parola in un vettore numerico (es. 768 dimensioni)
- **Positional Encoding**: aggiunge informazione sulla posizione del token nella sequenza
- **Self-Attention**: calcola le relazioni tra tutti i token (Q, K, V matrices)
- **Feed-Forward Network**: trasformazione non-lineare per ogni posizione
- **Layer Normalization + Residual Connections**: stabilizzano il training

### Varianti Moderne

| Modello | Tipo | Uso |
|---|---|---|
| BERT | Solo Encoder | Comprensione testo, embedding |
| GPT | Solo Decoder | Generazione testo |
| T5 | Encoder-Decoder | Traduzione, riassunti |
| Gemini, Gemma | Decoder (evoluto) | Chat, ragionamento, multimodale |

Prof. Gallade usa:
- **Gemini 2.5 Flash** o **Gemma 3** come LLM (decoder-only) per generare risposte
- **paraphrase-multilingual-MiniLM-L12-v2** come encoder per generare embedding

---

## 3. Embedding Vettoriali

### Cos'e' un Embedding

Un embedding e' una rappresentazione numerica densa di un testo in uno spazio vettoriale. Testi con significato simile hanno embedding vicini nello spazio.

```
"Pikachu e' un Pokemon elettrico"  ->  [0.23, -0.45, 0.12, ..., 0.67]  (768 dim)
"Raichu e' di tipo Elettro"       ->  [0.21, -0.43, 0.14, ..., 0.65]  (vicino!)
"La pizza margherita e' buona"     ->  [-0.78, 0.31, -0.55, ..., 0.02] (lontano!)
```

### Come Funziona la Similarity Search

1. La domanda dell'utente viene convertita in un vettore embedding
2. Questo vettore viene confrontato con tutti i vettori nel database
3. I documenti piu' "vicini" (cosine similarity o distanza L2) vengono restituiti

```
Query: "Debolezze di Garchomp"
  -> embedding: [0.15, -0.32, ...]

Documenti nel DB:
  Garchomp (pokemon):  dist = 0.23  <- PIU' VICINO
  Terremoto (mossa):   dist = 0.45
  Tipo Terra:          dist = 0.52
  Pikachu (pokemon):   dist = 0.89  <- LONTANO
```

### Il Problema dell'Embedding Dilution

Il modello di embedding usato (`paraphrase-multilingual-MiniLM-L12-v2`) ha un limite di ~128 token. I documenti Pokemon sono molto piu' lunghi (~1400 caratteri, ~350 token). Questo causa **embedding dilution**: il significato si "diluisce" nell'embedding perche' troppe informazioni vengono compresse in un unico vettore.

**Conseguenza pratica**: cercando "Dragonite", il sistema trova prima mosse o abilita con nomi simili (documenti corti, embedding concentrato) piuttosto che il documento Pokemon di Dragonite (documento lungo, embedding diluito).

**Soluzione adottata**: Retrieval ibrido (name matching + semantic search), descritto nella sezione RAG.

---

## 4. Retrieval-Augmented Generation (RAG)

### Il Problema dei LLM Puri

I Large Language Models hanno tre limiti fondamentali:

1. **Conoscenza statica**: sanno solo cio' che hanno appreso durante il training
2. **Allucinazioni**: inventano informazioni plausibili ma false
3. **Nessuna fonte**: non possono citare da dove viene un'informazione

### La Soluzione: RAG

RAG combina retrieval (recupero informazioni) con generation (generazione testo):

```
                    ┌──────────────────┐
                    │   Base di         │
                    │   Conoscenza      │
                    │   (ChromaDB)      │
                    └────────┬─────────┘
                             │
                      2. Retrieval
                             │
                             v
┌──────────┐    1. Query    ┌──────────────┐    3. Contesto    ┌──────────┐
│  Utente  │ ──────────────>│  RAG Chain   │ ────────────────> │   LLM    │
│          │                │              │                   │ (Gemini) │
│          │ <──────────────│              │ <──────────────── │          │
└──────────┘    5. Risposta └──────────────┘    4. Generazione └──────────┘
```

1. L'utente fa una domanda
2. Il sistema recupera documenti rilevanti dal database vettoriale
3. I documenti vengono passati al LLM come "contesto"
4. Il LLM genera una risposta basata SOLO sul contesto fornito
5. La risposta viene restituita all'utente

### Vantaggi di RAG vs LLM Puro

| Aspetto | LLM Puro | RAG |
|---|---|---|
| Accuratezza | Puo' allucinare | Vincolato ai dati reali |
| Aggiornamento | Richiede re-training | Basta aggiornare il DB |
| Trasparenza | "Black box" | Fonti tracciabili |
| Costo | Modelli enormi | Modelli piccoli + DB |
| Dominio specifico | Conoscenza generica | Esperto del dominio |

---

## 5. Architettura Prof. Gallade

### Pipeline Completa

```
┌─────────────────────────────────────────────────────────────────────┐
│                      INGESTION PIPELINE (offline)                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PokeAPI ──> Fetcher ──> Transformers ──> Indexer ──> ChromaDB      │
│  (v2 REST)   (async,     (per-gen docs,   (batch,    (14K+ docs,   │
│              cache)      IT locale)       embed)     persistente)   │
│                                                                     │
│  Dati scaricati:                                                    │
│  - 1025 Pokemon + Species                                           │
│  - 500+ Evolution Chains                                            │
│  - 919 Mosse                                                        │
│  - 18 Tipi (con past_damage_relations)                              │
│  - 307 Abilita (con past_abilities)                                 │
│  - 2100+ Strumenti                                                  │
│  - 25 Nature                                                        │
│                                                                     │
│  Per ogni generazione (1-9), i dati vengono ricostruiti             │
│  storicamente usando i campi past_* di PokeAPI.                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                       QUERY PIPELINE (runtime)                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. PREPROCESSING                                                   │
│     ├─ detect_generation("in Pokemon Nero") -> gen 5                │
│     ├─ _build_retrieval_query (arricchisce follow-up con history)   │
│     └─ _detect_excluded_types (escludi item/nature di default)      │
│                                                                     │
│  2. HYBRID RETRIEVAL                                                │
│     ├─ Phase 1: Name Matching                                       │
│     │   └─ _find_by_name: cerca name_it/name_en nei metadata        │
│     │      ChromaDB (bypassa embedding dilution)                    │
│     └─ Phase 2: Semantic Search                                     │
│         └─ similarity search con filtro generazione                 │
│            (riempie i posti rimanenti fino a k=12)                  │
│                                                                     │
│  3. PROMPT ASSEMBLY                                                 │
│     ├─ System prompt: "Sei il Professor Gallade..."                │
│     ├─ Context: documenti recuperati (separati da ---)              │
│     ├─ Chat history: messaggi precedenti                            │
│     └─ Question: domanda corrente                                   │
│                                                                     │
│  4. LLM GENERATION                                                  │
│     ├─ Gemini 2.5 Flash (produzione)                                │
│     │   oppure Gemma 3 12B via Ollama (sviluppo)                    │
│     └─ Streaming SSE al frontend                                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Storicizzazione dei Dati

Il cuore del progetto e' la capacita di rispondere con dati corretti per ogni generazione. Esempio:

| Pokemon | Gen 1-5 | Gen 6+ |
|---|---|---|
| Clefairy | Tipo: Normale | Tipo: Folletto |
| Magnemite | Tipo: Elettro | Tipo: Elettro/Acciaio |

| Abilita | Gen 3-6 | Gen 7+ |
|---|---|---|
| Gengar | Levitazione | Corpofunesto |

Questo e' implementato nel modulo `transformers.py` che ricostruisce lo stato di ogni entita per ogni generazione usando i campi `past_types`, `past_abilities` e `past_damage_relations` dell'API.

### Retrieval Ibrido: Perche' e Come

**Il problema**: i documenti Pokemon (~1400 caratteri) contengono nome, tipi, statistiche, abilita, mosse, catena evolutiva e descrizione Pokedex. Il modello di embedding (`MiniLM-L12-v2`, max ~128 token) non riesce a catturare tutto questo contenuto in un unico vettore. Il nome del Pokemon si "perde" nell'embedding.

**Conseguenza**: cercando "Parlami di Dragonite", il retriever semantico trova prima l'abilita "Dragomascelle" (documento corto, embedding concentrato, distanza 8.49) piuttosto che il Pokemon Dragonite (documento lungo, embedding diluito, distanza 11.48).

**La soluzione**: retrieval in due fasi:

```
Phase 1: Name Matching (diretto, deterministico)
  - Estrai parole candidate dalla domanda ("dragonite")
  - Cerca nei metadata ChromaDB: name_it="dragonite" OR name_en="dragonite"
  - Risultato: documento Pokemon Dragonite trovato con certezza

Phase 2: Semantic Search (embedding, probabilistico)
  - Cerca per similarita semantica i documenti rimanenti
  - Filtra per generazione + escludi item/nature
  - Risultato: mosse, tipi, abilita correlate

Combinazione:
  - Phase 1 PRIMA (documenti garantiti)
  - Phase 2 DOPO (contesto aggiuntivo, senza duplicati)
  - Totale: fino a k=12 documenti
```

### Gestione Follow-up

Le domande di follow-up come "e le mosse?" o "che debolezze ha in quarta gen?" non contengono il nome del Pokemon. Il sistema:

1. Rileva che la domanda e' breve (< 6 parole) e c'e' una chat history
2. Arricchisce la query aggiungendo l'ultima domanda dell'utente dalla history
3. Esempio: "che debolezze ha?" + history "Parlami di Dragonite" -> "che debolezze ha? Parlami di Dragonite"
4. Il name matching trova "dragonite" nella query arricchita
5. La generazione viene rilevata dalla domanda corrente ("quarta gen" -> gen 4)

### System Prompt

Il system prompt e' progettato per minimizzare le allucinazioni:

```
Regole FONDAMENTALI:
1. Usa ESCLUSIVAMENTE i dati forniti nel contesto
2. Se il contesto non contiene l'informazione, dillo
3. COPIA i dati di efficacia tipi, NON ricalcolarli
```

La regola 3 e' cruciale: l'efficacia tipi e' pre-calcolata nel documento (incluso dual-type), quindi il LLM deve solo copiarla. Questo evita errori di calcolo che anche modelli avanzati commettono.

---

## 6. Tecnologie Chiave

### ChromaDB

Database vettoriale open-source che memorizza documenti con i loro embedding. Supporta:
- **Persistenza su disco**: i dati sopravvivono al riavvio
- **Filtri metadata**: `{"generation": 5, "entity_type": "pokemon"}`
- **Similarity search**: trova i documenti piu' simili a una query

### LangChain

Framework Python per costruire applicazioni con LLM. Prof. Gallade usa:
- `ChatPromptTemplate`: template per il prompt con variabili
- `Chroma` (langchain-chroma): integrazione con ChromaDB
- `StrOutputParser`: estrae il testo dalla risposta del LLM
- Chain LCEL: `prompt | llm | output_parser`

### SSE (Server-Sent Events)

Protocollo HTTP per streaming unidirezionale server->client. Il backend invia token man mano che il LLM li genera, dando all'utente una sensazione di risposta immediata.

```
Client                    Server
  |--- POST /chat/stream -->|
  |                          | (LLM genera token)
  |<-- event: token ---------|  {"token": "Drago"}
  |<-- event: token ---------|  {"token": "nite"}
  |<-- event: token ---------|  {"token": " e'"}
  |<-- event: done ----------|  {"generation_used": 9}
```
