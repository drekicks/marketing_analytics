"""
Generates synthetic customers + full transaction history (rentals, payments)
and inserts them into your existing dvdrental Postgres database.

RUN check_schema.py FIRST. If it detects partitioning on payment/rental,
adjust NEW_DATA_START / NEW_DATA_END below to fall within existing partition
bounds, or create new partitions before running this.

Install dependency once:
    pip install faker --break-system-packages   (or without the flag, outside a managed env)

What this does:
1. Pulls existing reference data (cities, stores, staff, inventory) so every
   new row respects real foreign keys.
2. Generates NUM_NEW_CUSTOMERS new customers, each with their own address.
3. Generates a random number of rentals per customer (Poisson-distributed,
   so most customers rent a modest amount and a few rent a lot — mirrors
   real-world skew).
4. Generates one payment per rental, using the film's actual rental_rate,
   with a ~10% chance of an added late fee for realism.
5. Bulk-inserts everything in chunks, then resets each table's sequence so
   future inserts (e.g., from your app) don't collide with these new IDs.
"""

import os
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from faker import Faker
from sqlalchemy import text
from app.utils import database

# ============================================================
# CONFIG — adjust these
# ============================================================
NUM_NEW_CUSTOMERS = 9_000
AVG_RENTALS_PER_CUSTOMER = 15  # Poisson lambda; actual avg will be ~lambda+1
NEW_DATA_START = datetime(2023, 1, 1)
NEW_DATA_END = datetime(2026, 7, 1)   # adjust to "today" if you want ongoing recency
LATE_FEE_PROBABILITY = 0.10
OUTSTANDING_RENTAL_PROBABILITY = 0.02  # % of rentals with no return_date yet
INSERT_CHUNK_SIZE = 5_000
RANDOM_SEED = 42

# ============================================================
load_dotenv()

# DATABASE_URL = (
#     f"postgresql+psycopg2://{os.getenv('DB_USER')}:"
#     f"{os.getenv('DB_PASSWORD')}@"
#     f"{os.getenv('DB_HOST')}:"
#     f"{os.getenv('DB_PORT')}/"
#     f"{os.getenv('DB_NAME')}"
# )
engine = database.engine

fake = Faker()
Faker.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


def random_date(start: datetime, end: datetime) -> datetime:
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))


def load_reference_data(conn):
    print("Loading reference data from existing tables...")
    city_ids = pd.read_sql(text("SELECT city_id FROM city"), conn)["city_id"].tolist()
    store_ids = pd.read_sql(text("SELECT store_id FROM store"), conn)["store_id"].tolist()
    staff_by_store = pd.read_sql(text("SELECT staff_id, store_id FROM staff"), conn)
    inventory_df = pd.read_sql(text("""
        SELECT i.inventory_id, i.store_id, f.rental_rate, f.rental_duration
        FROM inventory i
        JOIN film f ON f.film_id = i.film_id
    """), conn)

    max_ids = {}
    for table, pk in [("address", "address_id"), ("customer", "customer_id"),
                       ("rental", "rental_id"), ("payment", "payment_id")]:
        result = pd.read_sql(text(f"SELECT MAX({pk}) AS m FROM {table}"), conn)
        max_ids[table] = int(result["m"].iloc[0] or 0)

    print(f"  {len(city_ids)} cities, {len(store_ids)} stores, {len(inventory_df)} inventory items")
    print(f"  Current max IDs: {max_ids}")
    return city_ids, store_ids, staff_by_store, inventory_df, max_ids


def generate_addresses_and_customers(city_ids, store_ids, max_ids):
    print(f"\nGenerating {NUM_NEW_CUSTOMERS:,} customers + addresses...")
    address_rows = []
    customer_rows = []
    used_emails = set()

    for i in range(NUM_NEW_CUSTOMERS):
        address_id = max_ids["address"] + i + 1
        customer_id = max_ids["customer"] + i + 1
        city_id = random.choice(city_ids)
        store_id = random.choice(store_ids)

        address_rows.append({
            "address_id": address_id,
            "address": fake.street_address(),
            "address2": None,
            "district": fake.state(),
            "city_id": city_id,
            "postal_code": fake.postcode(),
            "phone": fake.phone_number()[:20],
            "last_update": datetime.now(),
        })

        first = fake.first_name()
        last = fake.last_name()
        email = f"{first.lower()}.{last.lower()}@sakilacustomer.org"
        # guard against duplicate emails (same name generated twice)
        suffix = 1
        base_email = email
        while email in used_emails:
            email = base_email.replace("@", f"{suffix}@")
            suffix += 1
        used_emails.add(email)

        active = 1 if random.random() < 0.85 else 0

        customer_rows.append({
            "customer_id": customer_id,
            "store_id": store_id,
            "first_name": first,
            "last_name": last,
            "email": email,
            "address_id": address_id,
            "activebool": bool(active),
            "create_date": random_date(NEW_DATA_START, NEW_DATA_END).date(),
            "last_update": datetime.now(),
            "active": active,
        })

    return pd.DataFrame(address_rows), pd.DataFrame(customer_rows)


def generate_rentals_and_payments(customer_df, staff_by_store, inventory_df, max_ids):
    print(f"\nGenerating rentals and payments (avg ~{AVG_RENTALS_PER_CUSTOMER + 1}/customer)...")
    rental_rows = []
    payment_rows = []
    rental_id_counter = max_ids["rental"]
    payment_id_counter = max_ids["payment"]

    for _, cust in customer_df.iterrows():
        n_rentals = int(np.random.poisson(lam=AVG_RENTALS_PER_CUSTOMER)) + 1
        store_inventory = inventory_df[inventory_df["store_id"] == cust["store_id"]]
        store_staff = staff_by_store[staff_by_store["store_id"] == cust["store_id"]]

        if store_inventory.empty or store_staff.empty:
            continue  # skip if a store has no inventory/staff (shouldn't happen in dvdrental)

        for _ in range(n_rentals):
            rental_id_counter += 1
            inv_row = store_inventory.sample(1).iloc[0]
            staff_id = int(store_staff.sample(1).iloc[0]["staff_id"])
            rental_date = random_date(NEW_DATA_START, NEW_DATA_END)
            is_returned = random.random() > OUTSTANDING_RENTAL_PROBABILITY
            duration = int(inv_row["rental_duration"])
            return_date = (
                rental_date + timedelta(days=random.randint(1, duration + 5))
                if is_returned else None
            )

            rental_rows.append({
                "rental_id": rental_id_counter,
                "rental_date": rental_date,
                "inventory_id": int(inv_row["inventory_id"]),
                "customer_id": cust["customer_id"],
                "return_date": return_date,
                "staff_id": staff_id,
                "last_update": datetime.now(),
            })

            payment_id_counter += 1
            amount = float(inv_row["rental_rate"])
            if random.random() < LATE_FEE_PROBABILITY:
                amount += round(random.uniform(1.0, 3.0), 2)
            payment_date = rental_date + timedelta(days=random.randint(0, 3))

            payment_rows.append({
                "payment_id": payment_id_counter,
                "customer_id": cust["customer_id"],
                "staff_id": staff_id,
                "rental_id": rental_id_counter,
                "amount": round(amount, 2),
                "payment_date": payment_date,
            })

    rental_df = pd.DataFrame(rental_rows)
    payment_df = pd.DataFrame(payment_rows)
    print(f"  Generated {len(rental_df):,} rentals, {len(payment_df):,} payments")
    print(f"  Total synthetic revenue: ${payment_df['amount'].sum():,.2f}")
    return rental_df, payment_df


def bulk_insert(df: pd.DataFrame, table: str, conn):
    print(f"  Inserting {len(df):,} rows into {table}...")
    df.to_sql(table, conn, if_exists="append", index=False,
              method="multi", chunksize=INSERT_CHUNK_SIZE)


def reset_sequence(table: str, pk: str, conn):
    conn.execute(text(f"""
        SELECT setval(
            pg_get_serial_sequence('{table}', '{pk}'),
            (SELECT MAX({pk}) FROM {table})
        )
    """))


def main():
    with engine.begin() as conn:  # single transaction — all-or-nothing
        city_ids, store_ids, staff_by_store, inventory_df, max_ids = load_reference_data(conn)

        address_df, customer_df = generate_addresses_and_customers(city_ids, store_ids, max_ids)
        rental_df, payment_df = generate_rentals_and_payments(
            customer_df, staff_by_store, inventory_df, max_ids
        )

        print("\nInserting into database...")
        bulk_insert(address_df, "address", conn)
        bulk_insert(customer_df, "customer", conn)
        bulk_insert(rental_df, "rental", conn)
        bulk_insert(payment_df, "payment", conn)

        print("\nResetting sequences...")
        for table, pk in [("address", "address_id"), ("customer", "customer_id"),
                           ("rental", "rental_id"), ("payment", "payment_id")]:
            reset_sequence(table, pk, conn)

        print("\nDone. Transaction committed.")
        print(f"Added {len(customer_df):,} customers, {len(rental_df):,} rentals, "
              f"{len(payment_df):,} payments.")


if __name__ == "__main__":
    main()
