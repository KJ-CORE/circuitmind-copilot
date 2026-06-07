# ⚡ CircuitMind Design Co-pilot

> A natural-language AI co-pilot for electronics circuit design — powered by NVIDIA Nemotron-3, LangGraph, FastAPI, and RAG.

Describe your electronics project in plain English and CircuitMind will generate:
- ✅ **System Requirements** — Microcontroller, sensors, actuators, communication, power specs
- ✅ **Bill of Materials (BOM)** — Recommended components with reasons and part numbers
- ✅ **Physical Pin Connections** — Complete wiring diagram table
- ✅ **Electrical Validation** — Detects voltage mismatches, GPIO conflicts, missing pull-ups (with self-healing loop)
- ✅ **Production Firmware** — Compilable Arduino/ESP32 C++ code
- ✅ **PDF + `.ino` Export** — Packaged under `project/<uuid>/`

---

## Architecture

```
User Prompt (CLI)
      │
      ▼
FastAPI Backend  ──►  LangGraph Workflow
                            │
              ┌─────────────▼─────────────┐
              │   1. Requirements Agent    │  ← Extracts structured specs
              │   2. Component Agent       │  ← Recommends parts
              │   3. Schematic Agent       │  ← Wires connections
              │   4. Validation Agent ─────┼── RAG (Qdrant vector DB)
              │   5. Firmware Agent        │  ← Generates C++ firmware
              │   6. Report Compiler       │  ← Markdown + PDF
              └────────────────────────────┘
                            │
                       SQLite / PostgreSQL
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | NVIDIA Nemotron-3 (via [NVIDIA Integrate API](https://integrate.api.nvidia.com)) |
| Agent Orchestration | LangGraph |
| Backend API | FastAPI + Uvicorn |
| Database | SQLite (default) / PostgreSQL (Docker) |
| Vector Store | Qdrant (in-memory default / Docker) |
| Embeddings | OpenAI `text-embedding-3-small` / FakeEmbeddings fallback |
| CLI Client | Python `requests` + `fpdf2` |

---

## Quickstart

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/circuitmind-copilot.git
cd circuitmind-copilot
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r backend/requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your **NVIDIA API key**:

```env
OPENAI_API_KEY=nvapi-YOUR_KEY_HERE
NVIDIA_MODEL=nvidia/nemotron-3-nano-30b-a3b
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
```

> Get a free API key at [https://integrate.api.nvidia.com](https://integrate.api.nvidia.com)

### 5. Start the backend server

```bash
# From the electronics-copilot/ root directory
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Run the CLI client (in a new terminal)

```bash
python client.py
```

---

## CLI Menu

```
============================================================
           CIRCUITMIND DESIGN CO-PILOT
============================================================
 [1] Check Backend Connection Status
 [2] Generate New Circuit Design
 [3] List All Saved Designs
 [4] View Specific Design Details
 [5] Upload & Ingest Datasheet (PDF RAG)
 [6] Exit
============================================================
```

### Example Prompt

```
Design an Arduino Nano board for temperature detection using a DHT11 sensor,
with Wi-Fi connectivity via ESP-01 and cloud logging to ThingSpeak.
```

### Export Options (inside View Design)

```
 [1] Export Design Package (PDF Report & Firmware Code to UUID folder)
 [2] Export Full Markdown Report (.md)
 [3] View Full Firmware Code in Console
 [4] View Full Markdown Report in Console
```

Exported files are saved to:
```
project/
└── <project-uuid>/
    ├── <project-uuid>.pdf     ← Full PDF design report
    └── <project-uuid>.ino     ← Compilable Arduino firmware
```

---

## Optional: Docker (PostgreSQL + Qdrant)

For persistent storage and a live Qdrant vector database:

```bash
cd docker
docker-compose up -d
```

Then update `.env`:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/circuitmind
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

---

## Running Tests

```bash
# From the electronics-copilot/ root directory
python -m pytest backend/tests/ -v
```

---

## Project Structure

```
electronics-copilot/
├── .env.example              # Config template (copy to .env)
├── .gitignore
├── client.py                 # Interactive CLI client
│
├── agents/                   # LangGraph agent nodes
│   ├── graph.py              # Workflow builder & routing logic
│   ├── llm_client.py         # NVIDIA API client + JSON extractor
│   ├── requirement_agent.py
│   ├── component_agent.py
│   ├── schematic_agent.py
│   ├── validation_agent.py
│   └── firmware_agent.py
│
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py           # FastAPI app entry point
│   │   ├── config.py         # Pydantic settings (.env loader)
│   │   ├── database.py       # SQLAlchemy engine (PG → SQLite fallback)
│   │   ├── models.py         # Project ORM model
│   │   ├── schemas.py        # Pydantic request/response schemas
│   │   └── routes.py         # API endpoints
│   └── tests/
│       ├── test_agents.py
│       ├── test_graph.py
│       └── ab_test_rag.py
│
├── rag/
│   ├── embeddings.py         # Embedding model factory
│   └── vector_db.py          # Qdrant vector store + PDF ingestion
│
└── docker/
    ├── docker-compose.yml    # PostgreSQL + Qdrant services
    └── postgres/
        └── init.sql          # DB schema initialization
```

---

## License

MIT License — free to use, modify, and distribute.

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first.
