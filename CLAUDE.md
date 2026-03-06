# ProduckAI — Claude Memory

## What This Project Is

**ProduckAI** is an open-source, local-first **Product Management Copilot**. It ingests unstructured customer feedback from multiple sources, clusters it into themes using ML, and surfaces prioritized insights through a web UI, REST API, and Chrome extension.

---

## Monorepo Structure

```
produckai/
├── apps/api/        # Python FastAPI backend (main service)
├── apps/web/        # Next.js 14 frontend
├── apps/worker/     # Celery async task workers
├── apps/extension/  # Chrome MV3 extension (Jira integration)
├── packages/shared/ # Shared utilities (VOC scoring logic)
└── infra/           # Alembic DB migrations, init SQL
```

---

## Tech Stack

| Layer       | Technology                                                               |
| ----------- | ------------------------------------------------------------------------ |
| Backend     | Python 3.11, FastAPI, SQLAlchemy 2.0, Alembic                            |
| Database    | PostgreSQL 16 + pgvector                                                 |
| Queue/Cache | Redis + Celery                                                           |
| ML          | sentence-transformers (all-MiniLM-L6-v2), HDBSCAN/KMeans, KeyBERT, VADER |
| Frontend    | Next.js 14 (App Router), TypeScript, Tailwind CSS, SWR                   |
| Infra       | Docker Compose (6 services)                                              |
| LLM         | Anthropic Claude (required), OpenAI GPT-4 (optional)                     |

---

## Core Data Flow

```
Feedback Sources → API Ingest → PostgreSQL
                                    ↓
                     Celery Worker: Embeddings (384-dim) → pgvector
                                    ↓
                     HDBSCAN Clustering → Themes
                                    ↓
                     6-Component VOC Score → Insights
                                    ↓
                     Next.js UI / Chrome Extension
```

---

## Data Sources (Ingestion)

- **Slack** — OAuth, live channel sync (`apps/api/ingestion/ingest_slack.py`)
- **Jira** — API token auth (`apps/api/api/jira.py`)
- **Google Docs/Drive** — OAuth, chunking, PII redaction (`apps/api/ingestion/ingest_gdocs.py`)
- **Zoom** — Cloud recordings, VTT transcript parsing (`apps/api/ingestion/ingest_zoom.py`)
- **CSV** — File upload endpoint with template support
- **Manual/Conversational** — Direct API or MCP tool capture
- **Linear** — Stub, planned for v2

---

## ML Pipeline

1. **Embeddings** — `sentence-transformers/all-MiniLM-L6-v2` → 384-dim vectors stored in pgvector
2. **Clustering** — HDBSCAN (density-based, no need to pre-specify cluster count) with KMeans fallback
3. **Labeling** — KeyBERT keyword extraction + optional LLM refinement
4. **Sentiment** — VADER (negative sentiment = higher urgency)

---

## VOC Scoring Formula (6-component, configurable)

```
Score = 0.35 × Frequency_norm
      + 0.30 × ACV_norm
      + 0.15 × Segment_priority   (Enterprise=1.0, MM=0.7, SMB=0.5)
      + 0.10 × Sentiment_lift
      + 0.10 × Trend_momentum
      - 0.10 × Duplicate_penalty
```

Weights are configurable via environment variables, API (`POST /admin/weights`), or the web UI sliders.

---

## API Structure

50+ REST endpoints across 16 route modules in `apps/api/api/`:

| Module                 | Purpose                             |
| ---------------------- | ----------------------------------- |
| `/themes`              | List, detail, filter, sort themes   |
| `/search`              | Full-text feedback and theme search |
| `/cluster/run`         | Trigger ML clustering pipeline      |
| `/ingest/*`            | Data ingestion endpoints            |
| `/upload`              | File upload (CSV)                   |
| `/tickets/{key}/score` | Jira VOC scoring                    |
| `/integrations`        | OAuth/connection management         |
| `/admin/weights`       | Scoring weight configuration        |
| `/competitive`         | Competitive intelligence            |
| `/chat`                | Chat/agent interaction (Claude)     |

Interactive docs at `http://localhost:8000/docs` when running.

---

## Database Models

Located in `apps/api/models/`:

1. `Feedback` — Raw feedback with embeddings, source, metadata
2. `Theme` — Clustered themes with centroids and metrics
3. `FeedbackTheme` — Many-to-many with confidence scores
4. `Customer` — Account data (ACV, segment, domain)
5. `Artifact` — Tickets, PRDs, roadmap items
6. `ArtifactTheme` — Artifact-theme relationships
7. `Insight` — AI-generated insights from themes
8. `JiraTicket` / `VOCScore` — Jira-specific scoring data
9. `OAuthToken` — Integration credentials

---

## Services Layer

Business logic in `apps/api/services/` (14 modules), including:

- `clustering.py` — HDBSCAN/KMeans pipeline
- `embeddings.py` — Sentence-transformer inference
- `scoring.py` — VOC score computation (also in `packages/shared/scoring.py`)
- `insights.py` — AI insight generation

---

## Background Jobs (Celery)

- **Worker**: `apps/worker/tasks.py` — embedding generation, clustering
- **Beat Schedule**: `apps/worker/celery_app.py`
  - Daily clustering at 2 AM
  - OAuth token refresh every 10 minutes

---

## Chrome Extension

Located in `apps/extension/` (MV3):

- Overlays VOC score on Jira ticket pages (`content.js`)
- Side panel shows related themes and customer quotes
- One-click PRD generation
- Background service worker (`background.js`)

---

## Docker Compose Services

| Service  | Port | Role                          |
| -------- | ---- | ----------------------------- |
| postgres | 5432 | PostgreSQL + pgvector         |
| redis    | 6379 | Cache + task broker           |
| api      | 8000 | FastAPI (hot reload)          |
| worker   | —    | Celery worker (concurrency=2) |
| beat     | —    | Celery scheduler              |
| web      | 3000 | Next.js dev server            |

---

## Key Environment Variables

```bash
DEMO_MODE=true              # Full features with sample data, no API keys needed
DATABASE_URL=...            # PostgreSQL connection string
REDIS_URL=...               # Redis connection string
ANTHROPIC_API_KEY=...       # Required (for insights, competitive intel, chat)
OPENAI_API_KEY=...          # Optional (LLM label refinement)
EMBEDDING_MODEL=...         # Swap sentence-transformer model
PII_REDACTION_ENABLED=true  # Email/phone/URL scrubbing
```

---

## Common Make Commands

```bash
make up           # Start all services (docker-compose up)
make seed         # Load demo data
make cluster      # Run ML clustering
make test         # Run pytest suite
make lint         # Run Ruff + mypy
make migrate      # Run Alembic migrations
make ingest-slack # Manual Slack ingestion
make logs-api     # Tail API logs
```

---

## Entry Points

| App         | Entry Point                          |
| ----------- | ------------------------------------ |
| API         | `apps/api/main.py`                   |
| Worker      | `apps/worker/celery_app.py`          |
| Web         | `apps/web/src/app/page.tsx`          |
| Seed CLI    | `apps/api/scripts/seed_demo.py`      |
| Cluster CLI | `apps/api/scripts/run_clustering.py` |

---

## Key Design Decisions

- **Demo mode**: Complete feature set testable with bundled sample data and no external API keys
- **pgvector**: Vector similarity in native Postgres — no separate vector DB required
- **HDBSCAN**: Density-based clustering — cluster count is discovered, not specified
- **Service layer pattern**: Route handlers are thin; business logic lives in `services/`
- **Async throughout**: FastAPI async endpoints + Celery for heavy ML tasks
- **Configurable scoring**: All 6 VOC weights overridable at runtime
- **Read-only OAuth**: Connectors only read data, never write or delete

---

## Frontend Pages (Next.js App Router)

Located in `apps/web/src/app/`:

- Themes board — cards with score visualization and filters
- Theme detail — quotes, customer breakdowns, related artifacts
- Competitive intelligence dashboard
- Integration management (OAuth setup)
- CSV upload

---

## MCP Tools Available

This project includes a ProduckAI MCP server (`mcp__produckai__*`) with tools for:

- Capturing and searching feedback
- Running clustering and generating embeddings
- Searching themes and insights
- Calculating VOC scores
- Generating PRDs
- Syncing Slack, Google Drive, Zoom, Jira

---

## Documentation Files

| File              | Contents                                   |
| ----------------- | ------------------------------------------ |
| `README.md`       | Overview, quick start, API reference       |
| `Architecture.md` | Detailed system design, data flow, scaling |
| `QUICKSTART.md`   | 5-minute setup guide                       |
| `INSTALLATION.md` | Docker + manual installation steps         |
| `CONTRIBUTING.md` | Contribution guidelines                    |
| `SECURITY.md`     | Security policy, vulnerability reporting   |
