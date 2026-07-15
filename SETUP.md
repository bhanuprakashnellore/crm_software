# Setup & Installation Guide — Field Copilot (HCP CRM)

End-to-end instructions to get the backend (FastAPI + LangGraph) and frontend (React + Redux) running locally.
Tested on Windows with Python 3.11 and Node 24, but any Python 3.10+ / Node 18+ environment should work.

---

## 1. Prerequisites

Install these before you start:

| Requirement | Version | Check with | Get it from |
|---|---|---|---|
| Python | 3.10+ | `python --version` | https://www.python.org/downloads/ |
| Node.js (includes npm) | 18+ | `node --version` | https://nodejs.org/ |
| PostgreSQL | 14+ (or Docker) | `psql --version` | https://www.postgresql.org/download/ |
| Docker Desktop (optional, easiest DB path) | any recent | `docker --version` | https://www.docker.com/products/docker-desktop/ |
| Git | any recent | `git --version` | https://git-scm.com/downloads |
| Groq API key | — | — | https://console.groq.com/keys (free account, create a new API key) |

You do **not** need to install LangChain/LangGraph/FastAPI/etc. globally — they're installed into a Python
virtual environment in Step 3.

---

## 2. Get the code

```bash
git clone <your-repo-url> hcp-crm
cd hcp-crm
```

(If you already have the folder locally, just `cd` into it.)

Project layout:

```
hcp-crm/
├── backend/          FastAPI + LangGraph app
├── frontend/          React + Redux app
├── docker-compose.yml Postgres for local dev
└── README.md
```

---

## 3. Database (PostgreSQL)

### Option A — Docker (recommended, fastest)

From the repo root:

```bash
docker compose up -d
```

This starts Postgres 16 on `localhost:5432` with:
- user: `crm_user`
- password: `crm_password`
- database: `hcp_crm`

Check it's running:

```bash
docker ps
```

### Option B — Local PostgreSQL install (no Docker)

If you'd rather use a Postgres you already have installed, create the database and user manually:

```sql
CREATE USER crm_user WITH PASSWORD 'crm_password';
CREATE DATABASE hcp_crm OWNER crm_user;
```

Either way, you'll end up with this connection string (already the default in `.env.example`):

```
postgresql+psycopg2://crm_user:crm_password@localhost:5432/hcp_crm
```

---

## 4. Backend setup (FastAPI + LangGraph)

```bash
cd backend
```

### 4.1 Create and activate a virtual environment

```bash
python -m venv .venv

# Windows (PowerShell / Git Bash)
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 4.2 Install dependencies

```bash
pip install -r requirements.txt
```

This installs FastAPI, Uvicorn, SQLAlchemy, psycopg2, LangGraph, langchain-groq, and supporting packages.

### 4.3 Configure environment variables

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` and fill in:

```
DATABASE_URL=postgresql+psycopg2://crm_user:crm_password@localhost:5432/hcp_crm
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxx      # <-- paste your real Groq key here
GROQ_MODEL=gemma2-9b-it
GROQ_FALLBACK_MODEL=llama-3.3-70b-versatile
CORS_ORIGINS=http://localhost:5173
```

To get a Groq API key: sign in at https://console.groq.com → **API Keys** → **Create API Key**.

### 4.4 Seed sample data (optional but recommended for the demo)

```bash
python seed.py
```

This adds 4 sample HCPs (Dr. Anika Rao, Dr. Vikram Sinha, Dr. Meera Iyer, Dr. Sanjay Kapoor) so there's data to
search, log against, and edit right away.

### 4.5 Run the backend

```bash
uvicorn app.main:app --reload --port 8000
```

- API base URL: `http://localhost:8000`
- Interactive API docs (Swagger UI): `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health` → should return `{"status": "ok"}`

Tables are created automatically on first startup (`Base.metadata.create_all`) — no separate migration step
needed.

Leave this terminal running.

---

## 5. Frontend setup (React + Redux)

Open a **new** terminal.

```bash
cd frontend
```

### 5.1 Install dependencies

```bash
npm install
```

### 5.2 Run the frontend dev server

```bash
npm run dev
```

- App URL: `http://localhost:5173`
- The Vite dev server automatically proxies any `/api/*` request to `http://localhost:8000` (configured in
  `vite.config.js`) — no frontend `.env` file is needed.

> If port 5173 is already in use on your machine, Vite will automatically pick the next free port (5174, 5175,
> …) and print the actual URL in the terminal — just use whatever URL it prints.

Open the printed URL in your browser. You should see the **Field Copilot** dashboard with the Inter font, a
sidebar (Dashboard / Log Interaction / HCP Directory), and — if you ran `seed.py` — 4 HCPs under **HCP
Directory**.

---

## 6. Verifying everything works

1. **HCP Directory** → confirm the 4 seeded HCPs appear.
2. **Log Interaction → Structured Form** → pick an HCP, fill in a few fields, submit → it should appear on the
   Dashboard's "Recent interactions" list.
3. **Log Interaction → Conversational** → type something like:
   > Log a visit with Dr. Anika Rao — discussed CardioMax dosing, left 10 samples, she was very positive.

   The agent should reply confirming the interaction was logged, with a `log_interaction` tool tag shown under
   its message. This requires a valid `GROQ_API_KEY` in `backend/.env` — if the key is missing/invalid you'll
   get an authentication error from Groq surfaced as a chat error message.
4. Try an edit through chat, e.g.:
   > Change the sentiment of that interaction to neutral.

   You should see the `edit_interaction` tool tag and the CRM data update accordingly.

---

## 7. Common issues

| Symptom | Likely cause / fix |
|---|---|
| Backend fails to start with a `psycopg2` connection error | Postgres isn't running, or `DATABASE_URL` in `.env` doesn't match your actual user/password/db name. Check `docker ps` (Option A) or your local Postgres service. |
| Chat replies with an error / 401 from Groq | `GROQ_API_KEY` is missing, invalid, or unset in `backend/.env`. Regenerate a key at console.groq.com. |
| Frontend shows blank page / network errors in console | Backend isn't running on port 8000, or CORS_ORIGINS in `.env` doesn't include the frontend's actual URL/port. |
| `npm install` fails on native deps | Make sure you're on Node 18+; delete `node_modules` and `package-lock.json` and retry. |
| Port 8000 or 5173 already in use | Something else on your machine is bound to that port. Run the backend with `--port 8010` (and update `vite.config.js`'s proxy target to match), or let Vite auto-pick a free port for the frontend. |

---

## 8. Stopping everything

- Frontend: `Ctrl+C` in its terminal.
- Backend: `Ctrl+C` in its terminal.
- Database (Docker): `docker compose down` (add `-v` to also delete the stored data).
