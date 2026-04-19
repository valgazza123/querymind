# Resume Bullet Points

- Built QueryMind, an NLP-to-SQL platform using Python, Django REST, PostgreSQL, and Angular that translated natural-language questions into validated SQL with query history, indexing strategy, and schema-aware prompt context.
- Designed a normalized university OLTP schema through 3NF, implemented transactional enrollment, grading, and fee workflows, and added query optimization primitives including composite and partial indexes plus read-only SQL execution safeguards.
- Engineered an OLAP-ready analytics layer with a star schema, incremental ETL pipeline, ROLLUP/CUBE reporting queries, and a REST API that exposed structured results for dashboards and portfolio demos.

## 2-Minute Interview Explanation

QueryMind solves the gap between natural language and relational databases. A user asks a question like "show students who scored above 80 in Math last semester", and the system understands the university schema, generates a safe SQL query, executes it on PostgreSQL, and returns both the result table and an explanation of the SQL. I built it as a DBMS project, but also as a portfolio piece to show full-stack engineering plus database fundamentals.

The first key decision was separating the system into an OLTP schema and an analytics schema. The OLTP side is normalized to 3NF so transactions like enrollment, grading, and fee payment stay correct. The analytics side uses a star schema because dashboards and OLAP queries are much faster when dimensions are denormalized. The second key decision was making the NL2SQL layer schema-aware. Instead of asking the model to guess, I introspect tables, keys, and views, serialize that into a compact prompt, validate generated SQL with `sqlparse`, and only allow safe read-oriented execution.

One interesting challenge was balancing correctness and usability. LLMs can generate plausible SQL that is still wrong for a real schema, especially with joins and derived attributes. I handled that with a small self-healing loop: if execution fails, the error message and schema context go back into the model for one or two retries. If I had more time, I would add stronger semantic validation, chart-rich analytics, and a benchmark suite comparing generated SQL accuracy against a labeled question set.

