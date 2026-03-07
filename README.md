# Prof. Gallade

Chatbot RAG (Retrieval-Augmented Generation) che risponde a domande sul mondo Pokemon in italiano, con dati storicizzati per ogni generazione (1-9).

## Architettura

```
Frontend (Next.js)  <-->  Backend (FastAPI)  <-->  ChromaDB (Vector Store)
     |                         |                         |
  React 19 + SSE          LangChain RAG            14.000+ documenti
  Tailwind CSS             Hybrid Retrieval         9 generazioni
  TypeScript               Generation-aware         5 entity types
```

### Stack Tecnologico

| Componente | Tecnologia |
|---|---|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS |
| Backend API | FastAPI, SSE (Server-Sent Events) per streaming |
| Framework RAG | LangChain |
| Vector Store | ChromaDB (persistente su disco) |
| Embedding | HuggingFace `paraphrase-multilingual-MiniLM-L12-v2` (locale) |
| LLM | Gemini 2.5 Flash (produzione) / Ollama gemma3 (sviluppo locale) |
| Dati | PokeAPI v2 (con cache locale su disco) |

## Funzionalita

- **Risposte in italiano** su qualsiasi Pokemon, mossa, tipo, abilita, strumento o natura
- **Storicizzazione per generazione**: dati corretti per ogni gen (tipi passati, abilita passate, matchup tipo storici, statistiche mosse passate)
- **Catene evolutive** con metodi di evoluzione in italiano (scambio, livello, pietre, felicita)
- **Efficacia tipi difensiva** pre-calcolata per ogni Pokemon (incluso dual-type)
- **Follow-up contestuali**: "Parlami di Dragonite" -> "che debolezze ha in quarta gen?"
- **Streaming SSE**: i token vengono inviati al frontend man mano che vengono generati
- **Retrieval ibrido**: name matching diretto + ricerca semantica

## Struttura Progetto

```
ProfGallade/
├── backend/
│   ├── app/
│   │   ├── api/            # Endpoint FastAPI (chat, health)
│   │   ├── core/           # RAG chain, LLM, embeddings, prompts
│   │   ├── ingestion/      # Pipeline dati: fetch -> transform -> index
│   │   └── models/         # Pydantic schemas
│   ├── data/
│   │   ├── raw/            # Cache JSON da PokeAPI
│   │   └── chroma_db/      # Database vettoriale ChromaDB
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── app/            # Pages Next.js
│   │   ├── components/     # Componenti React (chat, layout, ui)
│   │   ├── hooks/          # Custom hooks (useChat)
│   │   └── lib/            # API client, types, constants
│   └── package.json
├── docker-compose.yml
├── start_dev.bat           # Avvio rapido sviluppo (Windows)
└── run_ingestion.bat       # Re-ingestion dati (Windows)
```

## Setup

### Prerequisiti

- Python 3.11+
- Node.js 18+
- (Opzionale) Ollama per LLM locale
- (Opzionale) Google API Key per Gemini

### 1. Backend

```bash
cd backend

# Crea virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/Mac

# Installa dipendenze
pip install -r requirements.txt

# Configura environment
cp .env.example .env
# Modifica .env con la tua configurazione
```

### 2. Ingestion Dati

La prima volta bisogna scaricare i dati da PokeAPI e indicizzarli in ChromaDB:

```bash
cd backend
python -m app.ingestion.run_ingestion
```

Questo processo:
1. Scarica ~5000 risorse da PokeAPI (con cache locale in `data/raw/`)
2. Costruisce ~14.000 documenti per 9 generazioni
3. Genera embedding e li indicizza in ChromaDB

La prima esecuzione impiega ~30 minuti (download + embedding). Le successive usano la cache e richiedono solo il re-embedding (~10 minuti).

Opzioni:
```bash
# Forza re-ingestion (ricrea il database)
python -m app.ingestion.run_ingestion --force

# Solo alcune generazioni
python -m app.ingestion.run_ingestion --force --gens 1,4,9
```

### 3. Frontend

```bash
cd frontend
npm install
```

### 4. Avvio

**Windows (rapido):**
```
start_dev.bat
```

**Manuale:**
```bash
# Terminal 1 - Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

L'applicazione sara disponibile su:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Docs API: http://localhost:8000/docs

## API

### POST `/api/chat/stream`

Chat con streaming SSE.

```json
{
  "message": "Parlami di Dragonite",
  "chat_history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

Risposta SSE:
```
event: token
data: {"token": "Dragonite"}

event: token
data: {"token": " e' un Pokemon"}

event: done
data: {"generation_used": 9}
```

### POST `/api/chat`

Chat sincrona (risposta completa).

### GET `/api/health`

Health check con conteggio documenti.

## Configurazione LLM

### Gemini (Produzione)

```env
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
GOOGLE_API_KEY=your-api-key
```

### Ollama (Sviluppo Locale)

```bash
# Installa e avvia Ollama
ollama pull gemma3:12b
```

```env
LLM_PROVIDER=ollama
LLM_MODEL=gemma3:12b
```

## Pipeline Dati

### Entity Types

| Tipo | Documenti/Gen | Esempio |
|---|---|---|
| `pokemon` | ~1025 | Nome, tipi, stats, abilita, mosse, catena evolutiva |
| `move` | ~900 | Nome, tipo, potenza, precisione, PP, effetto |
| `type` | 18 | Matchup offensivi e difensivi |
| `ability` | ~300 | Nome, effetto, descrizione |
| `item` | ~2100 (solo gen 9) | Nome, categoria, effetto |
| `nature` | 25 (gen 3+) | Nome, stat modificate |

### Storicizzazione

I dati vengono ricostruiti per ogni generazione usando:
- `past_types`: tipi cambiati nel tempo (es. Clefairy era Normale prima di gen 6)
- `past_abilities`: abilita cambiate (merge per slot, non sostituzione)
- `past_damage_relations`: matchup tipo storici (es. Spettro non colpiva Psico in gen 1)
- `past_values` (mosse): potenza/precisione/PP cambiate nel tempo

### Retrieval Ibrido

Il sistema usa due fasi di retrieval per superare il problema dell'*embedding dilution*:

1. **Name matching** (Phase 1): cerca documenti il cui nome (IT o EN) nei metadata corrisponde a parole nella domanda
2. **Semantic search** (Phase 2): riempie i posti rimanenti con risultati semanticamente simili

Questo approccio e' necessario perche' i documenti Pokemon (~1400 chars) superano il limite di token del modello di embedding (~128 token), causando la perdita del nome nell'embedding.
