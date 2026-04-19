# QueryMind

**Schema-aware Natural Language to SQL engine** built around a University Management System demo database. Type a question in plain English, get validated SQL, results, and explanations -- powered by Claude AI.

> DBMS syllabus end-to-end: ER modeling, relational conversion, normalization, SQL, joins, indexing, ACID transactions, OLAP, ETL, and a Claude-backed NL2SQL layer.

---

## Features

### Core NL2SQL Engine
- **Natural language to SQL** -- ask questions like *"Show top 10 students by GPA"* and get validated, read-only SQL
- **Schema-aware prompts** -- introspects PostgreSQL `information_schema`, builds compact context for Claude
- **SQL validation** -- `sqlparse`-based validation, rejects destructive statements
- **Query history** -- every attempt logged with execution time, row count, success/failure
- **SSE streaming** -- real-time token-by-token SQL generation with typewriter effect

### Smart / AI Features
- **Confidence scoring** -- each query returns a confidence level and reasoning
- **EXPLAIN plan visualization** -- D3-powered tree rendering of PostgreSQL `EXPLAIN (FORMAT JSON)` output
- **Auto SQL repair** -- Claude-powered fix-it that takes failing SQL + error message and returns corrected SQL
- **Conversational follow-ups** -- multi-turn chat with prior SQL context
- **Voice input** -- Web Speech API dictation for hands-free querying
- **Text-to-speech** -- speak explanations aloud with SpeechSynthesis

### Visual / UX
- **Three.js particle landing** -- animated 3D particle field on the landing page
- **GSAP transitions** -- sequenced, interruptible timeline animations throughout the UI
- **Monaco SQL editor** -- VS Code-quality editor with schema-aware autocomplete (tables, columns, SQL keywords)
- **D3 result charts** -- bar, line, pie, and scatter charts from query results
- **4 themes** -- Dark, Light, OLED Black, and Sepia with CSS custom properties
- **Cursor halo** -- radial gradient blob that follows the mouse
- **Matrix rain mode** -- canvas-based Matrix digital rain easter egg
- **Reduced motion** -- respects `prefers-reduced-motion` and manual toggle
- **Metrics strip** -- live dashboard showing total queries, success rate, avg/p95 latency, rows returned

### Productivity
- **Export results** -- CSV, JSON, Markdown table, and Pandas DataFrame formats
- **Saved queries** -- bookmark queries to localStorage for quick re-use
- **Share links** -- generate shareable URLs that hydrate query results
- **Schema browser** -- sidebar with expandable tables, columns, types, and constraints
- **Achievement system** -- unlock badges for milestones (first query, speed demon, 10 queries, etc.)

### Backend / Database
- **Normalized OLTP schema** -- Person -> Student/Faculty/Staff ISA hierarchy, weak entities, proper indexes
- **Analytics star schema** -- `fact_enrollments` with student, course, faculty, department, time dimensions
- **Incremental ETL** -- Django management command for warehouse loading
- **OLAP queries** -- ROLLUP, CUBE, GROUPING SETS analytics
- **ACID transactions** -- proper transaction isolation for concurrent operations
- **Metrics API** -- aggregated stats (total/today/success rate/avg/p95/fastest/slowest/rows/unique tables)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Angular 18, TypeScript, GSAP, Three.js, D3.js v7, Monaco Editor |
| **Backend** | Python 3.11+, Django 5, Django REST Framework, Gunicorn |
| **Database** | PostgreSQL 16 (OLTP + OLAP star schema) |
| **AI/LLM** | Anthropic Claude SDK (`claude-sonnet-4-20250514`), schema-aware prompts |
| **DevOps** | Docker Compose, Nginx reverse proxy, GitHub Actions CI/CD |
| **Cloud** | AWS ECS Fargate, RDS, S3, CloudFront, Route 53, ACM |

---

## Project Structure

```
querymind/
├── backend/
│   ├── core/               # Django app: views, services, serializers, NL2SQL
│   │   ├── services.py     # NL2SQL engine, EXPLAIN, repair, metrics, SSE streaming
│   │   ├── views.py        # REST API endpoints
│   │   ├── serializers.py  # DRF serializers
│   │   ├── urls.py         # URL routing
│   │   ├── nl2sql.py       # NL2SQL agent logic
│   │   ├── transactions.py # ACID transaction demos
│   │   └── analytics.py    # Analytics/OLAP views
│   ├── sql/
│   │   ├── ddl/            # Schema DDL, views, indexes
│   │   ├── seeds/          # Seed data generator
│   │   ├── queries/        # Demo SQL queries
│   │   └── warehouse/      # Star schema + OLAP queries
│   ├── requirements.txt
│   └── manage.py
├── frontend/
│   └── src/app/
│       ├── app.component.ts    # Main Angular component (~2400 lines)
│       ├── app.component.html  # Template with all UI features
│       └── app.component.css   # Styles, animations, themes
├── docs/                   # DBMS phase documentation
│   ├── phase-1/            # ER diagram, relational schema, normalization, DDL, seeds
│   ├── phase-2/            # Demo queries
│   └── ...                 # Additional phases
├── infrastructure/         # AWS setup/teardown scripts, IAM policies
├── scripts/                # Local validation scripts
├── docker-compose.yml
└── .env.example
```

---

## Quick Start

### With Docker (recommended)

```bash
git clone https://github.com/sanjeettuteja11-de/querymind.git
cd querymind
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
docker compose up --build
```

Then open:
- **App**: http://localhost
- **API**: http://localhost/api/
- **pgAdmin**: http://localhost:5050

Seed the database:
```bash
docker compose --profile seed run --rm seed
```

### Without Docker

**Backend:**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

**Frontend:**
```bash
cd frontend
npm install
npx ng serve --host 0.0.0.0 --port 4200
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/query` | NL2SQL query execution |
| `GET` | `/api/query/stream` | SSE streaming for typewriter effect |
| `POST` | `/api/query/explain` | PostgreSQL EXPLAIN plan |
| `POST` | `/api/query/fixit` | AI-powered SQL repair |
| `GET` | `/api/schema` | Database schema for frontend |
| `GET` | `/api/history` | Paginated query history |
| `GET` | `/api/history/<id>` | Single query detail (share links) |
| `GET` | `/api/metrics` | Aggregated query metrics |
| `GET` | `/api/analytics/rollup` | OLAP rollup chart data |
| `POST` | `/api/admin/etl/run` | Manual incremental ETL |
| `GET` | `/api/health` | Health check |

---

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | **Required** -- your Anthropic API key |
| `DJANGO_SECRET_KEY` | Django secret key |
| `DJANGO_DEBUG` | Debug mode (1/0) |
| `POSTGRES_*` | PostgreSQL connection settings |
| `SENTRY_DSN` | Optional Sentry error tracking |

---

## DBMS Deliverables

| Phase | Document |
|-------|----------|
| ER Diagram | [docs/phase-1/step-1.1-er-diagram.md](docs/phase-1/step-1.1-er-diagram.md) |
| Relational Schema | [docs/phase-1/step-1.2-relational-schema.md](docs/phase-1/step-1.2-relational-schema.md) |
| Normalization Audit | [docs/phase-1/step-1.3-normalization-audit.md](docs/phase-1/step-1.3-normalization-audit.md) |
| DDL Scripts | [backend/sql/ddl/](backend/sql/ddl/) |
| Seed Data | [backend/sql/seeds/](backend/sql/seeds/) |
| Demo Queries | [backend/sql/queries/](backend/sql/queries/) |
| Star Schema & OLAP | [backend/sql/warehouse/](backend/sql/warehouse/) |
| Transactions | [backend/core/transactions.py](backend/core/transactions.py) |
| NL2SQL Agent | [backend/core/nl2sql.py](backend/core/nl2sql.py) |

---

## License

This project is for educational and portfolio purposes.
