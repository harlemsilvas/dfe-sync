from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.settings import settings
engine = create_engine(settings.DB_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)