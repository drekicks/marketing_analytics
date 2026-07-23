"""
Run this FIRST, before generate_synthetic_data.py.

It checks a few things that can silently break a bulk insert into dvdrental:
- Whether `payment` (or any table) is range-partitioned, which restricts
  what dates you're allowed to insert
- Current row counts and PK ranges, so the generator knows where to start
- Existing date ranges, so you can decide whether to extend into new dates
  or stay within the historical window

Place this alongside your existing database.py / .env setup.
"""

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from app.utils import database
from sqlalchemy import create_engine, text

load_dotenv()

db_conn = database.engine

DATABASE_URL = (
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:"
    f"{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:"
    f"{os.getenv('DB_PORT')}/"
    f"{os.getenv('DB_NAME')}"
)
# engine = create_engine(DATABASE_URL)


def check_partitioning(conn):
    print("\n--- Partitioning check ---")
    query = text("""
        SELECT parent.relname AS parent_table, child.relname AS partition_name
        FROM pg_inherits
        JOIN pg_class parent ON pg_inherits.inhparent = parent.oid
        JOIN pg_class child ON pg_inherits.inhrelid = child.oid
        WHERE parent.relname IN ('payment', 'rental', 'customer')
        ORDER BY parent.relname, child.relname;
    """)
    df = pd.read_sql(query, conn)
    if df.empty:
        print("No partitioning detected on payment/rental/customer. Safe to insert any date.")
    else:
        print("PARTITIONING DETECTED — you'll need to stay within existing partition bounds")
        print("or create new partitions before inserting outside them:")
        print(df.to_string(index=False))
    return df


def check_row_counts_and_ids(conn):
    print("\n--- Row counts and current max IDs ---")
    tables = {
        "address": "address_id",
        "customer": "customer_id",
        "rental": "rental_id",
        "payment": "payment_id",
        "inventory": "inventory_id",
        "city": "city_id",
        "store": "store_id",
        "staff": "staff_id",
    }
    for table, pk in tables.items():
        try:
            result = pd.read_sql(
                text(f"SELECT COUNT(*) AS row_count, MAX({pk}) AS max_id FROM {table}"),
                conn,
            )
            print(f"{table:<12} rows={result['row_count'].iloc[0]:<8} max_{pk}={result['max_id'].iloc[0]}")
        except Exception as e:
            print(f"{table:<12} ERROR: {e}")


def check_date_ranges(conn):
    print("\n--- Existing date ranges ---")
    for table, col in [("rental", "rental_date"), ("payment", "payment_date"), ("customer", "create_date")]:
        try:
            result = pd.read_sql(
                text(f"SELECT MIN({col}) AS min_date, MAX({col}) AS max_date FROM {table}"),
                conn,
            )
            print(f"{table}.{col}: {result['min_date'].iloc[0]} to {result['max_date'].iloc[0]}")
        except Exception as e:
            print(f"{table}.{col} ERROR: {e}")


def check_store_inventory_split(conn):
    print("\n--- Inventory per store (for realistic rental assignment) ---")
    df = pd.read_sql(
        text("SELECT store_id, COUNT(*) AS inventory_count FROM inventory GROUP BY store_id ORDER BY store_id"),
        conn,
    )
    print(df.to_string(index=False))


if __name__ == "__main__":
    with db_conn.connect() as conn:
        check_partitioning(conn)
        check_row_counts_and_ids(conn)
        check_date_ranges(conn)
        check_store_inventory_split(conn)

    print("\nDone. If partitioning was detected on payment or rental, share the output")
    print("before running generate_synthetic_data.py — the date range in that script")
    print("will need to be adjusted to match.")
