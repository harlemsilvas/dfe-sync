from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.settings import settings

Base = declarative_base()

engine = create_engine(settings.DB_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

