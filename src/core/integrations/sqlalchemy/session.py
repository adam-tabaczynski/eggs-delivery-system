from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.settings import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionFactory = sessionmaker(engine, autoflush=False)
