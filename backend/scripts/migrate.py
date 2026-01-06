import os
import sys
import subprocess
from pathlib import Path

def run_migrations():
    """Run Alembic migrations to head."""
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)
    
    print("Running database migrations...")
    try:
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
        print("Migrations applied successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error applying migrations: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migrations()
