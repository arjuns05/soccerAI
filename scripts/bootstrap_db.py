from sqlalchemy import text, create_engine
from app.config import settings
from app.db import engine, Base
from app import models

def admin_engine():
    url = (
        f"postgresql+psycopg://{settings.pg_user}:{settings.pg_password}"
        f"@{settings.pg_host}:{settings.pg_port}/postgres"
    )
    return create_engine(url, isolation_level="AUTOCOMMIT", pool_pre_ping=True)

def ensure_db():
    eng = admin_engine()
    with eng.connect() as c:
        exists = c.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :d"),
            {"d": settings.pg_db},
        ).scalar()
        if not exists:
            c.execute(text(f'CREATE DATABASE "{settings.pg_db}"'))
            print(f"Created database {settings.pg_db}")

def main():
    ensure_db()
    Base.metadata.create_all(bind=engine)
    print("Tables created.")

if __name__ == "__main__":
    main()
