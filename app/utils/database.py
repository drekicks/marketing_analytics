import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent.parent/ ".env"  # adjust based on where .env actually lives
load_dotenv(dotenv_path=env_path)

def get_database_engine():
    from sqlalchemy import create_engine

    # Build the connection URL
    DATABASE_URL = (
        f"postgresql+psycopg://{os.getenv('DB_USER')}:"
        f"{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}:"
        f"{os.getenv('DB_PORT')}/"
        f"{os.getenv('DB_NAME')}"
    )

    # --- Create engine ---
    return create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)


