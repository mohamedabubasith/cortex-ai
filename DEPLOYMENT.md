# Deployment Guide

This project uses a Dockerized setup with a split-database architecture to ensure stability and separation of concerns.

## Architecture

-   **Frontend**: Next.js application.
-   **Backend**: FastAPI application.
-   **Database**: PostgreSQL (application data: users, chats, KB metadata, etc.). Managed by **Alembic**.
-   **Knowledge base vectors**: **Qdrant** (document chunks and embeddings from the Haystack ingestion pipeline). Configure `QDRANT_URL` (include `:80` if REST is behind a proxy on port 80), `QDRANT_COLLECTION`, and `QDRANT_API_KEY` when the instance is secured.

## 1. Wipe and Recreate (Fresh Start)

To **delete everything** (data, containers, images) and start fresh:

```bash
./wipe_and_run.sh
```

**⚠️ WARNING: This will delete all existing data in the databases!**

## 2. Update and Rerun (Safe Update)

To **update the code** and restart containers **without losing data**:

```bash
./update.sh
```

## Troubleshooting

### Database Connection Issues
If you see errors like `database "chat_db" does not exist`, it means the initialization script didn't run. Run `./wipe_and_run.sh` to fix this by starting fresh.

### Migration Conflicts
If Alembic reports conflicts (e.g., `DuplicateTableError`), it means the database schema is out of sync. A fresh deployment (`./wipe_and_run.sh`) is the recommended fix in development/testing environments.
