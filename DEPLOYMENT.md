# Deployment Guide

This project uses a Dockerized setup with a split-database architecture to ensure stability and separation of concerns.

## Architecture

-   **Frontend**: Next.js application.
-   **Backend**: FastAPI application.
-   **Database**: PostgreSQL with `pgvector` extension.
    -   `chat_db`: Stores application data (Users, Chats, etc.). Managed by **Alembic**.
    -   `cognee_db`: Stores Cognee internal data and vector embeddings. Managed by **Cognee**.

## Fresh Deployment (Reset)

To deploy the application from scratch (or to reset the environment completely), use the provided `clean_deploy.sh` script.

**⚠️ WARNING: This will delete all existing data in the databases!**

```bash
./clean_deploy.sh
```

This script performs the following:
1.  Stops all containers and removes volumes (`docker compose down -v`).
2.  Rebuilds the images.
3.  Starts the services.
4.  Waits for the database to become healthy.
5.  Ensures `chat_db` exists.
6.  Runs Alembic migrations to populate `chat_db`.

## Updating an Existing Deployment

To update the application without losing data:

1.  **Pull the latest changes**:
    ```bash
    git pull origin main
    ```

2.  **Rebuild and restart services**:
    ```bash
    docker compose -f docker-compose.prod.yml up -d --build
    ```

3.  **Run Migrations**:
    ```bash
    docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
    ```

## Troubleshooting

### Database Connection Issues
If you see errors like `database "chat_db" does not exist`, it means the initialization script didn't run (usually because the volume already existed). Run `./clean_deploy.sh` to fix this by starting fresh.

### Migration Conflicts
If Alembic reports conflicts (e.g., `DuplicateTableError`), it means the database schema is out of sync with the migration history. A fresh deployment (`./clean_deploy.sh`) is the recommended fix in development/testing environments.
