"""
ETSAI Database Backup
- PostgreSQL: exports to SQL dump file
- SQLite: uses SQLite backup API for safe copy
Run manually or via cron: python backup.py
"""
import os
import subprocess
import sqlite3
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL", "")
DB_PATH = os.environ.get("ETSAI_DB", "etsai.db")
BACKUP_DIR = os.environ.get("ETSAI_BACKUP_DIR", "backups")


def backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if DATABASE_URL:
        backup_postgres(timestamp)
    else:
        backup_sqlite(timestamp)

    clean_old_backups()


def backup_postgres(timestamp):
    """Dump PostgreSQL database using pg_dump."""
    backup_path = os.path.join(BACKUP_DIR, f"etsai_{timestamp}.sql")
    try:
        result = subprocess.run(
            ["pg_dump", DATABASE_URL, "--no-owner", "--no-privileges"],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            with open(backup_path, "w") as f:
                f.write(result.stdout)
            print(f"Postgres backup created: {backup_path}")
        else:
            print(f"pg_dump error: {result.stderr}")
    except FileNotFoundError:
        print("pg_dump not found. Install postgresql-client or use Railway's built-in backups.")
    except subprocess.TimeoutExpired:
        print("pg_dump timed out after 120s")


def backup_sqlite(timestamp):
    """Use SQLite's backup API for a safe, consistent copy."""
    if not os.path.exists(DB_PATH):
        print(f"Database not found: {DB_PATH}")
        return

    backup_path = os.path.join(BACKUP_DIR, f"etsai_{timestamp}.db")
    source = sqlite3.connect(DB_PATH)
    dest = sqlite3.connect(backup_path)
    try:
        source.backup(dest)
        print(f"SQLite backup created: {backup_path}")
    finally:
        dest.close()
        source.close()


def clean_old_backups():
    """Keep last 30 backups, remove older ones."""
    backups = sorted([
        f for f in os.listdir(BACKUP_DIR) if f.startswith("etsai_")
    ])
    while len(backups) > 30:
        old = backups.pop(0)
        os.remove(os.path.join(BACKUP_DIR, old))
        print(f"Removed old backup: {old}")


if __name__ == "__main__":
    backup()
