import os
import re
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, Engine

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Schema that holds the dbt marts the app reads
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


def _connection_settings() -> tuple[str | None, int | None, str | None, dict]:
    """Host, port, database name and connect_args shared by both engines."""
    port = os.getenv("DB_PORT")

    connect_args = {}

    if os.getenv("DB_SSLMODE"):
        connect_args["sslmode"] = os.getenv("DB_SSLMODE")

    return (
        os.getenv("DB_HOST"),
        int(port) if port else None,
        os.getenv("DB_NAME"),
        connect_args,
    )


@lru_cache(maxsize=1)
def get_readonly_engine() -> Engine:
    """
    Return the engine for model-generated SQL (customer questions).

    It connects as the restricted Neon role in DB_READONLY_USER, which can
    only SELECT from customer_analytic_layer and defaults to read-only
    transactions with a statement timeout. There is deliberately no
    fallback to the main application user.
    """
    username = os.getenv("DB_READONLY_USER")
    password = os.getenv("DB_READONLY_PASSWORD")

    if not username or not password:
        raise ValueError(
            "Customer-level questions need the read-only database user. "
            "Set DB_READONLY_USER and DB_READONLY_PASSWORD."
        )

    host, port, database, connect_args = _connection_settings()

    return create_engine(
        URL.create(
            drivername="postgresql+psycopg",
            username=username,
            password=password,
            host=host,
            port=port,
            database=database,
        ),
        connect_args=connect_args,
        pool_pre_ping=True,
    )


@lru_cache(maxsize=1)
def get_database_engine() -> Engine:
    """
    Return the application's shared SQLAlchemy engine.

    One engine (and its connection pool) is reused for the life of the
    process instead of reconnecting on every query, which matters for a
    hosted database such as Neon. URL.create escapes special characters in
    the password.
    """
    host, port, database, connect_args = _connection_settings()

    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=host,
        port=port,
        database=database,
    )

    return create_engine(
        database_url,
        connect_args=connect_args,
        # Serverless Postgres closes idle connections; check before reuse.
        pool_pre_ping=True,
    )
