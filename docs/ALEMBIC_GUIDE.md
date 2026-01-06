# Alembic Database Migrations Guide

This project uses **Alembic** to handle database schema changes (migrations). Alembic keeps your database table structure in sync with your Python SQLAlchemy models.

## 🔄 The Workflow

The general workflow for making database changes is:

1.  **Modify Python Models**: Change your code in `backend/app/models/models.py`.
2.  **Generate Migration**: Create a script that defines these changes.
3.  **Apply Migration**: Run the script to update the actual database.

---

## 🚀 Common Commands

### 1. Generating a Migration (Autogenerate)
After you verify your changes in `models.py`, generate a migration script. Alembic compares your code to the current database state.

**Command (Development):**
```bash
# Must be run from the backend directory
cd backend
alembic revision --autogenerate -m "describe your changes here"
```

**What this does:**
- Creates a new Python file in `backend/alembic/versions/`.
- This file contains `upgrade()` and `downgrade()` functions.
- **Always review this file** to ensure it captured your changes correctly.

### 2. Applying Migrations (Update DB)
To push the changes to your running database.

**Using our helper script (Recommended):**
```bash
./migrate.sh
```

**Or Manual Command:**
```bash
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

---

## 📂 Project Structure

- **`backend/app/models/`**: Where your data models live. This is the source of truth.
- **`backend/alembic/versions/`**: The history of all changes (migration scripts).
- **`migrate.sh`**: A utility script to run migrations inside the Docker container.

## 🛠 Troubleshooting

### "Target database is not up to date"
This means you have new migration scripts that haven't been applied to the DB yet.
- **Fix**: Run `./migrate.sh` (or `alembic upgrade head`).

### "Column ... does not exist"
This means your code expects a column that isn't in the database yet.
- **Fix**: You likely modified the model but forgot to generate or apply the migration. Follow the workflow steps above.

### Data Validation Errors (e.g. `ResponseValidationError`)
This often happens if you add a non-nullable column to a table that already has data.
- **Fix**: You might need to edit the generated migration script to "backfill" data (UPDATE existing rows) before applying the Not Null constraint.

---

## 📝 Example: Adding a new column

1.  Open `backend/app/models/models.py`.
2.  Add `new_col = Column(String)` to a class.
3.  Run `cd backend && alembic revision --autogenerate -m "add new_col"`.
4.  Run `./migrate.sh`.
5.  Done!
