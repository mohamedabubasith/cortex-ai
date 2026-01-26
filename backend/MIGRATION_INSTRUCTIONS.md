# Database Migration Instructions

## Run Migration

When you're ready to deploy, run the following commands:

```bash
cd backend

# Create migration
uv run alembic revision --autogenerate -m "Add agent audit logs table"

# Apply migration
uv run alembic upgrade head
```

## What the Migration Does

Creates the `agent_audit_logs` table with the following schema:

- `id` (String, PK)
- `user_id` (String, FK to users)
- `agent_id` (String, FK to agents)
- `session_id` (String)
- `model_name` (String)
- `prompt_tokens` (Integer)
- `completion_tokens` (Integer)
- `total_tokens` (Integer)
- `latency_ms` (Integer)
- `user_message` (Text)
- `llm_response` (Text)
- `tool_calls` (JSON)
- `rag_context` (JSON)
- `ip_address` (String)
- `status` (String)
- `error_message` (Text)
- `created_at` (DateTime)

## Note

The database must be running for the migration to work. If you see connection errors, make sure your PostgreSQL database is running.
