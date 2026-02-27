# scripts/migrate_db.py
import sqlite3
from pathlib import Path
import pandas as pd
from backend.config import settings

DB_PATH = Path(settings.DATABASE_URL.replace("sqlite+aiosqlite:///", ""))

def migrate_csv_to_db():
    """One-time migration: CSV → SQLite"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create tables from schema.sql (optional if you run schema manually)
    with open("data/schema.sql", "r") as f:
        cursor.executescript(f.read())

    # Migrate telemetry_log.csv
    telemetry_path = Path("data/telemetry_log.csv")
    if telemetry_path.exists():
        df = pd.read_csv(telemetry_path)
        df.to_sql("telemetry", conn, if_exists="append", index=False)
        print(f"Migrated {len(df)} telemetry rows")

    # Migrate users.csv (if exists - assumes columns username,password_hash,role)
    users_path = Path("data/users.csv")
    if users_path.exists():
        df_users = pd.read_csv(users_path)
        df_users.to_sql("users", conn, if_exists="append", index=False)
        print(f"Migrated {len(df_users)} users")

    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate_csv_to_db()