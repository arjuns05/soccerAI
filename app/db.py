from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase 
from app.config import settings 

DATABASE_URL = (
    f"postgresql+pyscopg3://{settings.pg_user}:{settings.pg_password}"
    f"@{settings.pg_host}:{settings.pg_port}/{settings.pg_db}"
)
engine = create_engine(DATABASE_URL, pool_pre_ping = True)
SessionLocal = sessionmaker(bind = engine, autoflush = False, autocommit = False)
class Base(DeclarativeBase):
    pass