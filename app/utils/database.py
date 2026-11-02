import os
import re
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, Engine

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Schema that holds the dbt marts and seeds the app reads
# (dbt target schema "dbt_dev" + the "analytics" custom schema).
DEFAULT_ANALYTICS_SCHEMA = "dbt_dev_analytics"

_SCHEMA_NAME_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*$")


def get_analytics_schema() -> str:
    """
    Return the schema containing the dbt marts, from ANALYTICS_SCHEMA.

    The value is inserted into SQL text, so it must be a plain lowercase
    identifier.
    """
    schema = os.getenv("ANALYTICS_SCHEMA", DEFAULT_ANALYTICS_SCHEMA).strip()

    if not _SCHEMA_NAME_PATTERN.match(schema):
        raise ValueError(
            f"Invalid ANALYTICS_SCHEMA {schema!r}. Use a lowercase schema "
            "name made of letters, digits and underscores."
        )

    return schema


@lru_cache(maxsize=1)
def get_database_engine() -> Engine:
    """
    Return the application's shared SQLAlchemy engine.

    One engine (and its connection pool) is reused for the life of the
    process instead of reconnecting on every query, which matters for a
    hosted database such as Neon. URL.create escapes special characters in
    the password.
    """
    port = os.getenv("DB_PORT")

    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(port) if port else None,
        database=os.getenv("DB_NAME"),
    )

    connect_args = {}

    if os.getenv("DB_SSLMODE"):
        connect_args["sslmode"] = os.getenv("DB_SSLMODE")

    return create_engine(
        database_url,
        connect_args=connect_args,
        # Serverless Postgres closes idle connections; check before reuse.
        pool_pre_ping=True,
    )
