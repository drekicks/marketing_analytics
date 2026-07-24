from app.utils import database as db
from pathlib import Path
import pandas as pd
from sqlalchemy import text
from app.config.paths import DATA_DIR, SQL_DIR

db_conn = db.engine

# PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # adjust based on where utils.py actually lives
# # DATA_DIR = PROJECT_ROOT / "data"
# # DATA_DIR.mkdir(exist_ok=True)
#
# BASE_DIR = Path(__file__).resolve().parent.parent
# SQL_DIR = BASE_DIR / "sql"
#
# DATA_DIR = PROJECT_ROOT / "data"
# DATA_DIR.mkdir(parents=True, exist_ok=True)



def load_sql(file_path: Path) -> str:
    """Read a SQL file and return it as a string."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def load_sql_extracts(filenames: list[str], params: dict = None):
    """
        Execute specified SQL files and return results as DataFrames.

        Args:
            filenames: SQL filenames without the .sql extension.
            params: Optional SQL parameters.

        Returns:
            Dictionary of DataFrames keyed by filename.
        """
    results = {}
    with db_conn.connect() as conn:
        for name in filenames:
            sql_file = SQL_DIR / f"{name}.sql"
            if not sql_file.exists():
                raise FileNotFoundError(f"SQL file not found: {sql_file}")

            sql_query = load_sql(sql_file)
            df = pd.read_sql(text(sql_query), conn, params=params or {})
            results[name] = df

            # print(f"{name}: {len(df)} rows")
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
    output_path = DATA_DIR / filename
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"Saved {len(df)} rows to {output_path}")
    return output_path

