from pathlib import Path

import pandas as pd
from sqlalchemy import text

from app.config.paths import DATA_DIR, SQL_DIR
from app.utils.database import get_analytics_schema, get_database_engine

ANALYTICS_SCHEMA_PLACEHOLDER = "{{analytics_schema}}"


def load_sql(file_path: Path) -> str:
    """Read a SQL file and return it as a string."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def render_sql(sql_query: str) -> str:
    """Replace the {{analytics_schema}} placeholder with the configured schema."""
    return sql_query.replace(
        ANALYTICS_SCHEMA_PLACEHOLDER,
        get_analytics_schema(),
    )


def load_sql_extracts(filenames: list[str], params: dict = None):
    """
        Execute specified SQL files and return results as DataFrames.

        Args:
            filenames: SQL filenames without the .sql extension.
            params: Optional SQL parameters.

        Returns:
            Dictionary of DataFrames keyed by filename.
        """
    engine = get_database_engine()
    results = {}

    with engine.connect() as conn:
        for name in filenames:
            sql_file = SQL_DIR / f"{name}.sql"
            if not sql_file.exists():
                raise FileNotFoundError(f"SQL file not found: {sql_file}")

            sql_query = render_sql(load_sql(sql_file))
            df = pd.read_sql(text(sql_query), conn, params=params or {})
            results[name] = df

    return results


def file_export(df: pd.DataFrame, filename: str):
    """
        Export a DataFrame to the project's data directory.

        Args:
            df: DataFrame to export.
            filename: Output filename. '.csv' will be appended if omitted.

        Returns:
            Path to the exported CSV file.
        """
    if not filename.lower().endswith(".csv"):
        filename += ".csv"
    output_path = DATA_DIR / "demo"/filename
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"Saved {len(df)} rows to {output_path}")
    return output_path
