# QueryMind Phases 6 and 7: API and Frontend

## Django REST API

Implemented in:
- [views.py](/Users/apple/querymind/backend/core/views.py)
- [urls.py](/Users/apple/querymind/backend/core/urls.py)
- [throttles.py](/Users/apple/querymind/backend/core/throttles.py)

Endpoints:
- `POST /api/query`
- `GET /api/schema`
- `GET /api/history`
- `GET /api/analytics/rollup`
- `POST /api/admin/etl/run`

Security provisions:
- read-only execution path in [nl2sql.py](/Users/apple/querymind/backend/core/nl2sql.py)
- SQL validation before execution
- rate limiting: 10 queries/minute per IP
- database-level `readonly_user` role created in [01_schema.sql](/Users/apple/querymind/db/sql/01_schema.sql)

## Angular Frontend

Implemented in:
- [app.component.ts](/Users/apple/querymind/frontend/src/app/app.component.ts)
- [app.component.html](/Users/apple/querymind/frontend/src/app/app.component.html)
- [app.component.css](/Users/apple/querymind/frontend/src/app/app.component.css)

Main UI features:
- collapsible-style schema browser structure
- natural-language input panel
- example queries
- results grid
- generated SQL panel
- explanation and execution metadata
- recent history list
- analytics tab with rollup bar chart and ETL trigger button

