# QueryMind Phase 1.5: Seed Data Script

## Output File

The canonical seed script is:

- `backend/sql/seeds/seed_data.py`

It uses SQLAlchemy Core and Faker to insert realistic Indian university demo data.

## Seed Targets

The script creates:

- 5 departments.
- 20 faculty members.
- 200 students.
- 30 courses.
- 2 semesters.
- Sections for each course and semester.
- Enrollment and grade data.
- Exam and exam-result rows.
- Hostel and hostel-allotment rows.
- Fee invoice and fee payment rows.

## Environment Variables

The script reads database connection details from environment variables:

- `POSTGRES_DB`, default `querymind`
- `POSTGRES_USER`, default `querymind`
- `POSTGRES_PASSWORD`, default `querymind`
- `POSTGRES_HOST`, default `localhost`
- `POSTGRES_PORT`, default `5432`

For production, these values must come from the deployment environment or AWS Secrets Manager. They should not be committed as real credentials.

## Execution

Apply the schema first:

```bash
psql "$DATABASE_URL" -f backend/sql/ddl/01_schema.sql
psql "$DATABASE_URL" -f backend/sql/ddl/02_views.sql
psql "$DATABASE_URL" -f backend/sql/ddl/03_indexes.sql
```

Then run the seed script:

```bash
python backend/sql/seeds/seed_data.py
```

## Design Notes

The script uses deterministic random seeds so demo data is repeatable across local machines and deployments. It intentionally creates enough rows to support joins, grouping, rankings, recursive prerequisite demos, break-even style analytics, and OLAP queries in later phases.
