#!/usr/bin/env bash
set -e

echo "Waiting for database (SQLAlchemy probe)..."
python - << 'PY'
import os, time, sys
try:
    import psycopg2
    print("psycopg2 imported successfully")
except ImportError as e:
    print(f"psycopg2 import error: {e}")
    sys.exit(1)

from sqlalchemy import create_engine, text

dsn = os.environ.get("SQLALCHEMY_DATABASE_URI") or "postgresql://postgres:postgres@core_db:5432/coredb"
for i in range(60):
    try:
        engine = create_engine(dsn, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("DB is ready.")
        break
    except Exception as e:
        print(f"DB not ready yet (attempt {i+1}/60):", e)
        print(f"Using DSN: {dsn}")
        time.sleep(2)
else:
    sys.exit("DB wait timeout")
PY

echo "Running Alembic migrations..."
cd /app
alembic upgrade head

echo "Starting FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
