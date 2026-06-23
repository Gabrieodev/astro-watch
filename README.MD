<div align="center">

# AstroWatch — Near-Earth Asteroid Observatory & Risk Scoring

**A zero-cost, fully local data pipeline that monitors near-Earth asteroids, scores their risk with a custom algorithm, and explains them in plain language through a local AI assistant.**

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Ollama](https://img.shields.io/badge/Ollama-000000?style=for-the-badge&logo=ollama&logoColor=white)](https://ollama.com/)
[![Power BI](https://img.shields.io/badge/Power_BI-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)](https://powerbi.microsoft.com/)
[![NASA API](https://img.shields.io/badge/NASA_API-0B3D91?style=for-the-badge&logo=nasa&logoColor=white)](https://api.nasa.gov/)

</div>

---

## Overview

**AstroWatch** is an end-to-end data pipeline built around a simple premise: take a real-world astronomy data feed, turn it into a quantified risk signal, and make that signal understandable to a non-technical audience — all without spending a single dollar on infrastructure or APIs.

The system collects near-Earth object (NEO) data from NASA's public API, persists it in a relational database with idempotency guarantees, scores each asteroid's risk through a custom-built algorithm, generates plain-language explanations via a fully local LLM, and exports the result to a Power BI dashboard refreshed weekly.

Every architectural decision in this project was constrained by design: **zero cost, fully local execution, no distributed infrastructure.** Apache Spark and cloud services were deliberately left out of scope for v1 — not because they weren't considered, but because the project's goal was to build deep understanding of each pipeline stage from first principles before reaching for heavier tools.

---

## Why This Project Exists

This project was built while transitioning from a frontend/backend development background into Data Analytics, Business Intelligence and Data Engineering. The goal was never to have "something that works" — it was to understand *why* each piece works the way it does: why a primary key prevents duplicate inserts, why Min-Max normalisation is needed before combining metrics of different scales, why a heap is more efficient than a full sort for a top-N query, and how a local LLM can be constrained through prompt design rather than fine-tuning.

Each component was tested in isolation — collector, then database, then scoring, then AI assistant, then the full pipeline — with a defined success criterion at every step, before integrating the next.

---

## Architecture

The pipeline runs in five sequential phases, each independently testable and each owning a single responsibility.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Phase 1    │     │   Phase 2    │     │   Phase 3    │     │   Phase 4    │     │   Phase 5    │
│  Collection  │ ──▶ │   Storage    │ ──▶ │   Scoring    │ ──▶ │  Local AI    │ ──▶ │ Orchestration│
│              │     │              │     │              │     │              │     │ & Export     │
│  NASA NeoWs  │     │   SQLite +   │     │  Min-Max +   │     │   Ollama /   │     │  Pipeline +  │
│     API      │     │    Docker    │     │  Heap top-N  │     │   Llama 3    │     │   Power BI   │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

---

## Folder Structure

```plaintext
astrowatch/
│
├── src/
│   ├── coletor.py          # Phase 1 — NASA API collection
│   ├── banco.py            # Phase 2 — SQLite persistence
│   ├── processador.py      # Phase 3 — scoring algorithm
│   ├── assistente.py       # Phase 4 — Ollama / local AI
│   └── pipeline.py         # Phase 5 — orchestration
│
├── sql/
│   └── schema.sql          # Table definitions
│
├── data/
│   ├── asteroides.db              # SQLite database (auto-generated, not versioned)
│   └── asteroides_export.csv      # Power BI source file (auto-generated)
│
├── notebooks/
│   └── exploracao.ipynb    # Exploratory analysis in Jupyter
│
├── .env                     # NASA_API_KEY (not versioned)
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Phase 1 — Collection (NASA NeoWs API)

**Stack:** Python, `requests`, `python-dotenv`

Consumes NASA's free [NeoWs API](https://api.nasa.gov/) (`/neo/rest/v1/feed`), which returns near-Earth objects within a window of up to 7 days.

The core function, `buscar_asteroides(data_inicio, data_fim)`, accepts start and end dates as parameters and returns a list of normalised dictionaries — flattening NASA's nested JSON into direct fields: id, name, approach date, min/max diameter, velocity, distance in kilometres and in lunar distances, and a hazard flag.

> **Design decision:** dates are passed as parameters rather than hardcoded, enabling isolated testing and reuse across different time windows. HTTP errors are handled idiomatically via `raise_for_status()` rather than silently swallowed.

---

## Phase 2 — Storage (SQLite + Docker)

**Stack:** SQLite3 (Python standard library), Docker, Docker Compose

Two tables defined in `sql/schema.sql`:

| Table | Purpose |
|---|---|
| `asteroides` | Per-object data, including `score_risco` — populated in Phase 3, `NULL` until then |
| `coletas` | Pipeline execution history — run timestamps, record counts, failures (audit trail) |

Core functions in `banco.py`: `conectar()`, `criar_schema()`, `inserir_asteroides()`, `buscar_todos()`.

> **Design decision:** `INSERT OR IGNORE` combined with a `PRIMARY KEY` on `id` guarantees idempotency — running the pipeline multiple times never duplicates data. This was tested and validated explicitly: a second execution inserts zero new records when the data already exists.

The Dockerfile is based on `python:3.12-slim`. `docker-compose.yml` maps a volume (`./data:/app/data`) so the SQLite database persists outside the container, and injects the `.env` file for the API key.

---

## Phase 3 — Processing & Risk Scoring Algorithm

**Stack:** Python, Pandas, `heapq` (standard library)

A risk-scoring algorithm built from scratch — no third-party "risk scoring" library was used, because the goal was to understand the mathematics, not just produce a number.

The algorithm combines three factors — **distance, velocity and average diameter** — using **Min-Max normalisation** to bring metrics of vastly different scales onto a comparable 0–1 basis. These normalised values are then combined with defined weights (**distance 50%, velocity 30%, size 20%**) into a final score from 0 to 100.

The `top_perigosos(n)` function extracts the N most dangerous asteroids using a **max-heap** — implemented via `heapq` (natively a min-heap, so scores are inverted) — avoiding the cost of sorting the entire dataset just to retrieve the top N.

**Validated:**
- Heap ranking and Pandas `sort_values()` agree on the resulting order
- All scores fall strictly within the 0–100 range
- The asteroid with lowest distance and highest velocity consistently appears among the top-ranked

---

## Phase 4 — Local AI Assistant (Ollama)

**Stack:** Ollama (100% local LLM, free, `llama3` model)

The `gerar_ficha_asteroide(asteroid_id)` function builds a prompt from real asteroid data — name, distance, velocity, diameter, risk score — and asks the local model to generate an accessible explanation, a scientific fact, and a scale analogy, entirely in Brazilian Portuguese.

`chat_interativo()` provides a free-form conversation loop about the monitored asteroids.

> **Design decision:** all natural language processing runs locally via Ollama — no calls to paid AI APIs (OpenAI, Anthropic, or otherwise), in direct alignment with the project's zero-cost constraint. The system prompt was carefully engineered to control tone (accessible, non-technical), format (3 paragraphs) and language (Portuguese).

---

## Phase 5 — Orchestration & Visualisation

`pipeline.py` chains the previous four phases in sequence: **collection → storage → scoring → CSV export.**

- Weekly automatic scheduling via the `schedule` library (every Monday at 08:00)
- Export to `data/asteroides_export.csv`, consumed by Power BI
- Power BI dashboard with three planned pages:
  1. **Weekly overview** — KPI cards and a risk traffic-light table
  2. **Risk analysis** — scatter plot (distance × velocity, bubble size = asteroid diameter)
  3. **Temporal history** of monitored NEOs

---

## Architectural Decisions

**Idempotency as a first-class requirement, not an afterthought** — The `INSERT OR IGNORE` + primary key pattern was chosen specifically so the pipeline can be re-run safely — by a scheduler, by a manual retry, or during debugging — without ever corrupting the dataset with duplicates. This was explicitly tested rather than assumed.

**A custom scoring algorithm over a pre-built library** — Risk scoring could have used an off-the-shelf normalisation utility. It didn't, intentionally. Building the Min-Max normalisation and weighted combination from scratch forces an understanding of *why* distance, velocity and size cannot be averaged directly without first putting them on the same scale — a foundational data science concept that's easy to skip when a library hides it.

**A heap instead of a full sort for top-N retrieval** — Sorting the entire dataset to extract the 10 most dangerous asteroids is wasteful when N is small relative to the dataset size. Using `heapq` reflects a conscious choice to apply the right data structure for the access pattern, not just the most familiar one.

**Local LLM over a paid AI API** — Ollama with Llama 3 was chosen specifically to keep the entire pipeline at zero marginal cost, while still exploring real prompt engineering — controlling tone, structure and language through the system prompt rather than through model fine-tuning or paid API parameters.

**Docker as a portability layer, not a production requirement** — Containerisation here isn't about scaling — it's about guaranteeing that the pipeline runs identically regardless of the host machine's Python version or installed packages, and that the SQLite volume persists correctly outside the container lifecycle.

**Spark deliberately excluded from v1** — Apache Spark was considered for processing NASA's full historical NEO dataset (back to the 1990s), but excluded from this version. The dataset size at this stage doesn't justify distributed processing, and introducing Spark prematurely would have added infrastructure complexity without a corresponding learning or performance benefit. It remains a defined, scoped extension — not a missing feature.

---

## Testing & Validation

Each component was validated in isolation before integration, in this order:

| Component | Validation performed |
|---|---|
| Collector | Returns fully populated asteroid records; handles invalid API key, rate limit exceeded, and connection failure |
| Database | Verified via `sqlite3` CLI and DB Browser for SQLite; idempotency confirmed — second run inserts 0 new records |
| Processor | All scores confirmed within 0–100; heap ranking confirmed to match Pandas `sort_values()`; Min-Max normalisation logic validated |
| AI Assistant | Confirmed responses in Portuguese, grounded in the real data passed via prompt, following the defined 3-paragraph format |
| Full pipeline | Validated via `python src/pipeline.py` — collection → insertion → scoring → CSV export executes end-to-end without errors; re-validated inside Docker (`docker compose up`), confirming the volume persists data correctly outside the container |

---

## What This Project Taught Me

- Consuming a real REST API with proper error handling — not just the happy path
- Designing a relational schema from scratch, including primary key and idempotency decisions
- Implementing a custom scoring algorithm with Min-Max normalisation, understanding the math instead of relying on a packaged solution
- Using a heap (`heapq`) as an efficient data structure for top-N retrieval instead of sorting the full dataset
- Integrating a 100% local LLM (Ollama), including prompt engineering to control tone, format and language
- Containerising an application with Docker and Docker Compose, including volume management for data persistence
- Orchestrating a complete pipeline with automatic scheduling
- The discipline of testing each component in isolation, with a defined success criterion, before integrating the next

---

## Roadmap

- [x] NASA NeoWs API collection with error handling
- [x] SQLite persistence with idempotency guarantees
- [x] Custom risk-scoring algorithm with Min-Max normalisation
- [x] Heap-based top-N extraction
- [x] Local AI assistant via Ollama / Llama 3
- [x] Full pipeline orchestration with weekly scheduling
- [x] Docker containerisation with persistent volumes
- [x] CSV export for Power BI
- [ ] Apache Spark processing for the full historical NEO dataset (since the 1990s) — planned bonus phase
- [ ] Published Power BI dashboard (currently local only)
- [ ] Automated tests (currently validated manually, phase by phase)
- [ ] Basic CI/CD via GitHub Actions

---

## How to Run

### Prerequisites

- Python 3.12 or higher
- Docker and Docker Compose (optional — for containerised execution)
- [Ollama](https://ollama.com/) installed, with the `llama3` model pulled
- A free [NASA API key](https://api.nasa.gov/)

### Option A — Local (virtual environment)

**1. Clone the repository**

```bash
git clone https://github.com/gabrieodev/astrowatch.git
cd astrowatch
```

**2. Create a virtual environment and install dependencies**

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**3. Configure your API key**

Create a `.env` file in the project root:

```env
NASA_API_KEY=your_api_key_here
```

**4. Initialise the database schema**

```bash
python -c "from src.banco import criar_schema; criar_schema()"
```

**5. Pull the local LLM model**

```bash
ollama pull llama3
ollama serve
```

**6. Run the full pipeline**

```bash
python src/pipeline.py
```

This runs collection → storage → scoring → CSV export in sequence. The resulting file is available at `data/asteroides_export.csv`, ready to be connected to Power BI.

---

### Option B — Docker

```bash
docker compose up
```

The container runs the full pipeline with the SQLite volume persisted at `./data` on the host machine.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

**AstroWatch** — Real astronomy data, a transparent risk algorithm, and an AI that explains it all in plain language.

Python · SQLite · Docker · Ollama · Power BI · Zero cost, fully local.

</div>