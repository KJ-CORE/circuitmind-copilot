from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

try:
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True
    )
    with engine.connect() as conn:
        pass
    print("[Database] Connected to PostgreSQL successfully.")
except Exception as e:
    print(f"[Database] PostgreSQL connection failed: {e}. Falling back to SQLite...")
    engine = create_engine(
        "sqlite:///./circuitmind.db",
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
