import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path


env_path = Path(__file__).resolve().parent.parent.parent/ ".env"  # adjust based on where .env actually lives
load_dotenv(dotenv_path=env_path)

# Build the connection URL
DATABASE_URL = (
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:"
    f"{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:"
    f"{os.getenv('DB_PORT')}/"
    f"{os.getenv('DB_NAME')}"
)

# --- Create engine ---
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

# --- Session setup (for ORM usage) ---
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def get_session():
    """Provide a transactional scope for a series of operations."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

