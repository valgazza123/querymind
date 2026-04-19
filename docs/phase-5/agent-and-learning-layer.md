# QueryMind Phase 5: NL2SQL Agent and Learning Layer

Core implementation:
- schema serializer: [nl2sql.py](/Users/apple/querymind/backend/core/nl2sql.py)
- query history model: [models.py](/Users/apple/querymind/backend/core/models.py)
- history-backed retrieval: [nl2sql.py](/Users/apple/querymind/backend/core/nl2sql.py)

## Implemented Features

- PostgreSQL schema introspection using `information_schema`
- compact schema serialization including view definitions
- Anthropic Claude integration through `NL2SQLAgent`
- strict SQL validation using `sqlparse`
- rejection of dangerous SQL keywords
- read-only execution
- self-healing retry loop using prior execution error feedback
- retrieval of similar successful past queries using `difflib.SequenceMatcher`

## JSON Output Contract

The agent is instructed to return:
```json
{
  "sql": "SELECT ...",
  "explanation": "What the query does",
  "tables_used": ["student", "department"],
  "complexity_level": "basic"
}
```

