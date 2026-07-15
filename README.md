# Field Copilot — AI-First HCP CRM (Log Interaction Screen)

An AI-first CRM module for pharmaceutical field representatives to log, review, and manage their interactions
with Healthcare Professionals (HCPs). The centerpiece is the **Log Interaction Screen**, which lets a rep capture
a visit either through a traditional structured form or by simply talking to an AI agent the way they'd brief a
colleague.

## Tech stack

| Layer            | Choice                                                              |
|-------------------|---------------------------------------------------------------------|
| Frontend          | React 18 + Redux Toolkit + React Router, Vite, Google **Inter** font |
| Backend           | Python, FastAPI                                                     |
| AI agent framework| **LangGraph**                                                       |
| LLMs              | Groq — `gemma2-9b-it` (primary), `llama-3.3-70b-versatile` (fallback for tougher extraction) |
| Database          | PostgreSQL (SQLAlchemy ORM)                                          |

## Why a form *and* a chat interface

Field reps log interactions in very different contexts: a detailed post-visit debrief at a desk (structured form
is faster and more precise), versus a two-line note dictated between appointments (chat is faster and more
natural). The Log Interaction Screen exposes a toggle between the two, but they write to the **same** database
through the **same** underlying data model — the chat path just uses the LangGraph agent to turn free text into
that structured record instead of asking the rep to fill in fields by hand.

## Architecture

```
frontend (React + Redux)
   │  axios → /api/*  (Vite dev-server proxy → http://localhost:8000)
   ▼
backend (FastAPI)
   ├── /api/hcps           CRUD for HCP directory
   ├── /api/interactions   CRUD for the structured-form path (no LLM involved)
   └── /api/chat           Conversational path → LangGraph agent
                                │
                                ▼
                       LangGraph StateGraph (agent ⇄ tools loop)
                        ChatGroq(gemma2-9b-it) bound to 6 tools
                                │
                                ▼
                        PostgreSQL (hcps, interactions, follow_ups)
```

The structured form talks directly to plain CRUD REST endpoints. The chat interface sends the rep's message to
`/api/chat`, which runs a LangGraph agent loop (`agent` node ⇄ `tools` node) using `MemorySaver` so each chat
thread keeps conversational memory. The agent decides which tool(s) to call based on the message — the same tools
back both the "5 required tools" spec and the CRM's actual read/write logic, so there's only one source of truth
for what an "interaction" is.

## Role of the LangGraph agent

The agent (`backend/app/agent/graph.py`) is the reasoning layer that sits between a rep's natural language and the
CRM's structured data. Its job is to:

1. **Interpret intent** — decide whether the rep is logging a new interaction, editing one, asking for history,
   searching for an HCP, or requesting a follow-up reminder.
2. **Call the right tool(s)** with the right arguments, potentially chaining several in one turn (e.g. look up an
   HCP's history before confirming which interaction to edit).
3. **Delegate structured extraction to the LLM** inside each tool — turning messy free text into the same typed
   fields (topics, products, sentiment, samples, follow-ups) the structured form produces, plus a compliance
   check that a plain form doesn't do automatically.
4. **Report back conversationally**, confirming what was logged/changed so the rep can catch and correct mistakes
   immediately (a second `edit_interaction` call in the same thread).

State is a single running message list (`MessagesState`) checkpointed per `thread_id`, so a rep can say "Dr. Rao"
once and refer to "her" or "that interaction" in later turns.

## The 6 LangGraph tools

| # | Tool | Purpose |
|---|------|---------|
| 1 | **`log_interaction`** | See below |
| 2 | **`edit_interaction`** | See below |
| 3 | `search_hcp` | Fuzzy-searches HCPs by name/specialty/institution so the agent (or rep) can confirm who a conversation is about, or the frontend can look someone up before starting a chat. |
| 4 | `get_interaction_history` | Pulls the N most recent interactions for a named HCP — used when a rep asks "what did we discuss with Dr. X last time?" or to give the agent context before logging a follow-up visit. |
| 5 | `schedule_followup` | Turns a natural-language timing phrase ("in two weeks", "next Monday") into a concrete due date via the LLM and creates a `follow_ups` record linked to the HCP (and optionally the interaction). |
| 6 | `flag_compliance_review` | Standalone compliance scan of interaction notes for off-label promotion, unsubstantiated claims, competitor disparagement, or inducements — usable independently of logging, e.g. to vet a note before it's saved. |

### 1. Log Interaction — how it captures data

`log_interaction(raw_notes: str)`:

1. Sends the rep's free text to `gemma2-9b-it` with a prompt that extracts a strict JSON object: HCP name,
   channel, purpose, topics discussed, products discussed, materials shared, samples distributed (as a
   `{product: qty}` map), sentiment, a 1–3 sentence summary, and whether a follow-up is implied. If the primary
   model returns unparsable JSON, it retries once against the `llama-3.3-70b-versatile` fallback.
2. Runs the same raw text through a second, separate LLM call that acts as a **compliance reviewer**, flagging
   off-label/unsubstantiated-claim/competitor-disparagement language — a life-sciences-specific check a generic
   CRM form wouldn't have.
3. Resolves the HCP by fuzzy name match, creating a new HCP record if none exists yet (so a rep can mention a new
   contact mid-conversation without a separate "add HCP" step).
4. Persists an `Interaction` row (`source="chat"`) with all extracted fields plus the compliance flag/reason, and
   returns a structured confirmation the agent uses to reply to the rep.

### 2. Edit Interaction — how it modifies logged data

`edit_interaction(interaction_id: int, edit_instruction: str)`:

1. Loads the current interaction row and serializes its editable fields (topics, products, samples, sentiment,
   summary, follow-up info, etc.) as JSON.
2. Sends that current-state JSON plus the rep's plain-English instruction (e.g. *"change the sentiment to
   positive and note 20 more samples of CardioMax were requested"*) to the LLM, asking it to return a **JSON
   patch** containing only the fields that should change.
3. Applies the patch to the SQLAlchemy row (validating enum values, parsing the follow-up date) and commits.
4. Returns the updated fields so the agent can confirm exactly what changed — avoiding silent, unreviewable edits.

The structured-form side of editing is a plain `PATCH /api/interactions/{id}` with explicit fields (no LLM
involved) — both paths converge on the same table, so an interaction logged via chat can be corrected via the
form and vice versa.

## Database schema (simplified)

- **`hcps`** — name, specialty, institution, NPI, contact info, engagement tier, notes.
- **`interactions`** — FK to `hcps`, date/channel/purpose, topics/products/materials/samples (JSON), sentiment,
  summary, raw notes, follow-up fields, compliance flag/notes, `source` (`form` or `chat`).
- **`follow_ups`** — FK to `hcps`/`interactions`, due date, notes, status — created by `schedule_followup`.

## Running it locally

### 1. Database

```bash
docker compose up -d          # starts Postgres on localhost:5432
```

### 2. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate         # Windows (use `source .venv/bin/activate` on macOS/Linux)
pip install -r requirements.txt

copy .env.example .env         # Windows (`cp .env.example .env` on macOS/Linux)
# then edit .env and set GROQ_API_KEY (create one at https://console.groq.com/keys)

python seed.py                 # optional: seeds 4 sample HCPs so there's data to demo against
uvicorn app.main:app --reload --port 8000
```

The API is now at `http://localhost:8000` (interactive docs at `/docs`).

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The Vite dev server proxies `/api/*` to the backend, so no frontend env config is
needed.

## Project structure

```
backend/
  app/
    agent/
      llm.py          # ChatGroq clients (primary + fallback)
      extraction.py    # robust JSON-from-LLM helper
      tools.py         # the 6 LangGraph tools
      graph.py         # LangGraph StateGraph wiring (agent ⇄ tools)
    routers/
      hcps.py          # HCP CRUD
      interactions.py  # Interaction CRUD (structured-form path) + follow-ups list
      chat.py          # /api/chat → invokes the LangGraph agent
    models.py          # SQLAlchemy models
    schemas.py         # Pydantic request/response models
    database.py, config.py, main.py
  seed.py
frontend/
  src/
    features/          # Redux slices: hcps, interactions, chat
    components/         # Navbar, InteractionForm, ChatPanel, InteractionList
    pages/              # Dashboard, HCPList, HCPProfile, LogInteraction
    api/client.js        # axios instance
docker-compose.yml       # Postgres for local dev
```

## Design notes / scope

This is an assignment-scope build: no auth (a single hardcoded "Demo Rep"), no DB migrations tool (tables are
created via `Base.metadata.create_all` on startup — fine for a demo, would move to Alembic for production), and
the compliance check is a single LLM call rather than a maintained rules engine. These are deliberate corners cut
to keep the two required LangGraph tools (`log_interaction`, `edit_interaction`) and the three supporting tools
fully working end-to-end within the assignment's time box.
