# FlowDay

**AI-powered daily planner for freelancers managing multiple client projects.**

FlowDay bridges the gap between calendar apps (time-only) and task managers (no time awareness). Users organize tasks by project, drag them onto a daily timeline, track time with an inline timer, and receive AI-generated weekly reviews that surface productivity patterns across all their engagements.

---

## Architecture

```mermaid
graph TB
    subgraph Frontend["Frontend — React 18 + TypeScript (Vite)"]
        UI[Dark-themed UI<br/>#111113]
        Pages[Pages: Login · Dashboard<br/>Planner · Review · WeeklyReview]
        State[Zustand Stores<br/>auth · planner · timer · ui]
        DnD[dnd-kit Drag & Drop]
        Charts[Recharts Visualizations]
    end

    subgraph Backend["Backend — FastAPI + Python 3.12"]
        API[REST API<br/>9 route modules]
        Services[Service Layer<br/>business logic]
        Models[SQLAlchemy 2.0<br/>async ORM models]
        Auth[OAuth 2.0 + JWT<br/>Google · GitHub]
    end

    subgraph AI["AI Pipeline — Pydantic AI"]
        direction TB
        subgraph GroupA["Group A — Parallel (asyncio.gather)"]
            TA[Time Analyst]
            MA[Meeting Analyst]
            CA[Code Analyst]
            TKA[Task Analyst]
        end
        PD[Group B — Pattern Detector]
        NW[Group C — Narrative Writer]
        Judge[Group D — Judge Agent<br/>different LLM provider]
    end

    subgraph Infra["Infrastructure"]
        PG[(PostgreSQL 16)]
        Redis[(Redis 7)]
        Sentry[Sentry Error Tracking]
        Prom[Prometheus Metrics]
        Grafana[Grafana Dashboards]
    end

    subgraph CICD["CI/CD — GitHub Actions (8 stages)"]
        Lint[1-2: Lint + Type-check]
        Tests[3: Unit + Integration Tests]
        E2E[4: E2E Playwright]
        Sec[5: Security Gates ×4]
        AIReview[6: Claude AI PR Review]
        Deploy[7-8: Vercel Deploy]
    end

    Frontend -->|HTTP + JWT| Backend
    Backend --> AI
    Backend --> PG
    Backend --> Redis
    Backend --> Sentry
    Backend --> Prom
    Prom --> Grafana

    GroupA --> PD --> NW --> Judge
    Judge -->|score < threshold| NW

    Auth -->|OAuth 2.0| ExtGoogle[Google Calendar API]
    Auth -->|OAuth 2.0| ExtGitHub[GitHub API]

    Lint --> Tests --> E2E --> Sec --> AIReview --> Deploy
```

### AI Weekly Review Pipeline

The core innovation is a multi-agent pipeline that generates weekly productivity reviews:

```mermaid
sequenceDiagram
    participant O as Orchestrator
    participant A as Group A (4 Analysts)
    participant B as Pattern Detector
    participant C as Narrative Writer
    participant D as Judge

    O->>A: Launch 4 analysts in parallel
    activate A
    Note over A: Time · Meeting · Code · Task<br/>run concurrently via asyncio.gather
    A-->>O: Structured typed outputs
    deactivate A

    O->>B: Pass all analyst outputs
    activate B
    B-->>O: Cross-source correlations<br/>with confidence scores
    deactivate B

    O->>C: Analyst outputs + patterns
    activate C
    C-->>O: Human-readable narrative
    deactivate C

    O->>D: Score narrative (different LLM)
    activate D
    alt Score ≥ threshold
        D-->>O: Pass — actionability, accuracy, coherence
    else Score < threshold (max 2 retries)
        D->>C: ModelRetry → regenerate
        C->>D: New narrative
        D-->>O: Re-score
    end
    deactivate D
```

Each agent uses Pydantic AI with typed `result_type` schemas and `RunContext` dependency injection, keeping agents testable and provider-agnostic.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript 5, Vite 5, Zustand, React Query, dnd-kit, Recharts |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic |
| AI | Pydantic AI (provider-agnostic agents with structured outputs) |
| Database | PostgreSQL 16 + asyncpg |
| Cache | Redis 7 |
| Auth | OAuth 2.0 (Google, GitHub) + JWT (access + refresh tokens) |
| Monitoring | Prometheus, Grafana, Sentry |
| CI/CD | GitHub Actions (8 stages), Docker, Vercel |
| Security | OWASP Top 10 compliance, Fernet encryption, 4 security gates |

---

## Data Model

```mermaid
erDiagram
    User ||--o{ Project : owns
    User ||--o{ WeeklyReview : receives
    User ||--o{ ExternalSync : connects
    Project ||--o{ Task : contains
    Task ||--o{ ScheduleBlock : "planned on"
    Task ||--o{ TimeEntry : "tracked by"

    User {
        uuid id PK
        string email UK
        string name
        text google_oauth_token "Fernet encrypted"
        text github_oauth_token "Fernet encrypted"
        jsonb settings_json
    }
    Project {
        uuid id PK
        uuid user_id FK
        string name
        string color "hex code"
        string client_name
        decimal hourly_rate
        enum status "active | archived"
    }
    Task {
        uuid id PK
        uuid project_id FK
        string title
        int estimate_minutes
        enum priority "low | medium | high | urgent"
        enum status "todo | in_progress | done"
        date due_date
    }
    ScheduleBlock {
        uuid id PK
        uuid task_id FK
        date date
        decimal start_hour
        decimal end_hour
        enum source "manual | google_calendar"
    }
    TimeEntry {
        uuid id PK
        uuid task_id FK
        timestamptz started_at
        timestamptz ended_at
        int duration_seconds
    }
    WeeklyReview {
        uuid id PK
        uuid user_id FK
        date week_start
        jsonb raw_data_json
        jsonb insights_json
        text narrative
        jsonb scores_json
        enum status "pending | generating | complete | failed"
    }
    ExternalSync {
        uuid id PK
        uuid user_id FK
        enum provider "google_calendar | github"
        timestamptz last_synced_at
        jsonb sync_config_json
    }
```

---

## Features

**Project-based task management** — Color-coded projects per client with tasks that have time estimates, priority levels, and due dates.

**Daily planner** — Drag tasks from the project pool onto a time-axis timeline to create schedule blocks.

**Inline timer** — Start/stop time tracking per task; automatically creates TimeEntry records for planned-vs-actual analysis.

**Planned vs Actual view** — Side-by-side daily comparison (planned schedule vs what actually happened) with status tags (done/partial/skipped/unplanned) and weekly bar charts showing estimation accuracy per project.

**Google Calendar integration** — OAuth read-only sync; meetings appear as fixed blocks on the timeline.

**GitHub integration** — OAuth sync of commit activity and PR history for code productivity analysis in weekly reviews.

**AI weekly review** — Multi-agent system generating descriptive and diagnostic insights about your work week.

**LLM-as-Judge evaluation** — A separate model scores each review on actionability, accuracy, and coherence. Low scores trigger automatic regeneration.

---

## Getting Started

### Prerequisites

- Python 3.12 (conda: `conda activate vibing`)
- Node.js 20+
- Docker & Docker Compose
- PostgreSQL 16, Redis 7 (via Docker)

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/<your-org>/FlowDay.git
cd FlowDay

# 2. Start infrastructure
docker compose -f docker/docker-compose.yml up -d    # PostgreSQL + Redis + Prometheus + Grafana

# 3. Backend
cd backend
cp .env.example .env                                  # Configure your secrets
pip install -e ".[dev]"
alembic upgrade head                                  # Apply migrations
uvicorn app.main:app --reload --port 5060

# 4. Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Access Points

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:5060 |
| API Docs (Swagger) | http://localhost:5060/docs |
| Grafana | http://localhost:3001 |
| Prometheus | http://localhost:9090 |

---

## CI/CD Pipeline

The GitHub Actions pipeline runs 8 stages on every push and PR:

```
Stage 1-2: Lint + Type-check (backend & frontend, parallel)
    ↓
Stage 3: Unit + Integration Tests (real PostgreSQL, not mocked)
    ↓
Stage 4: E2E Tests (Playwright)
    ↓
Stage 5: Security Gates
    ├── Gate 1: pip-audit (Python CVEs)
    ├── Gate 2: npm audit (Node CVEs)
    ├── Gate 3: Gitleaks (secret detection)
    └── Gate 4: Bandit SAST (Python security)
    ↓
Stage 6: Claude AI PR Review (PRs only)
    ↓
Stage 7: Vercel Preview Deploy (PRs)
Stage 8: Vercel Production Deploy (main)
```

---

## Security

FlowDay implements OWASP Top 10 (2021) mitigations:

- **Auth:** OAuth 2.0 (Google, GitHub) + JWT with short-lived access tokens and refresh rotation
- **Encryption:** OAuth tokens encrypted at rest with Fernet; secrets via environment variables
- **Injection defense:** SQLAlchemy parameterized queries, Pydantic input validation, PII anonymization before LLM calls
- **CI enforcement:** 4 security gates must pass before merge
- **Monitoring:** Sentry error tracking, Grafana dashboards, audit logging for auth events

---

## Monitoring

Custom AI metrics tracked via Prometheus and visualized in Grafana:

| Metric | Description |
|--------|-------------|
| `agent_latency_seconds` | Time spent in each AI agent call |
| `token_cost_total` | Cumulative token cost by agent and model |
| `judge_score` | Judge agent scores (0–100) |
| `http_request_duration_seconds` | API request latency (p50/p95/p99) |

---

## Development Workflow

This project follows a strict 4-phase workflow for every issue:

1. **Explore** — Read existing code, understand impact (no file changes)
2. **Plan** — Write implementation plan with acceptance criteria
3. **Implement** — Strict TDD cycles: RED (failing test) → GREEN (minimum code) → REFACTOR
4. **Commit** — Feature branch with `[#N][RED|GREEN|REFACTOR]` prefix format

All development was done with Claude Code as the AI pair-programming partner, using custom slash commands (`/explore-issue`, `/plan-issue`, `/tdd`) to enforce discipline at each phase.

---

## Project Structure

```
FlowDay/
├── backend/
│   ├── app/
│   │   ├── agents/          # 7 AI agents + orchestrator
│   │   ├── api/             # 9 FastAPI route modules
│   │   ├── core/            # Config, DB, Redis, JWT, metrics
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   └── services/        # Business logic + OAuth sync
│   ├── tests/
│   ├── alembic/             # Database migrations
│   └── Dockerfile
├── frontend/
│   └── src/
│       ├── components/      # TaskCard, TimelineGrid, TimerButton, JudgeScoreCard...
│       ├── pages/           # Login, Dashboard, Planner, Review...
│       ├── stores/          # Zustand state management
│       ├── types/           # TypeScript interfaces
│       └── utils/           # Planner logic, validation, OAuth
├── docker/                  # Docker Compose + Grafana provisioning
├── docs/                    # Architecture docs & implementation plans
└── .github/workflows/       # 8-stage CI/CD pipeline
```

---

## License

This project was built as part of CS 7180 (Special Topics in AI) at Northeastern University, Spring 2026.
