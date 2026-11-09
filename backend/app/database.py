from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import settings

class Base(DeclarativeBase):
    pass

url = settings().database_url
if url.startswith('sqlite:///') and ':memory:' not in url:
    from pathlib import Path
    Path(url.removeprefix('sqlite:///')).parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(url, connect_args={'check_same_thread': False} if url.startswith('sqlite') else {}, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

def get_db():
    with SessionLocal() as db:
        yield db
