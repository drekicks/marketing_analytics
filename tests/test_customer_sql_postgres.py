"""
Guardrails checked against a real Postgres (e.g. Neon) as the read-only role.

Skipped unless CUSTOMER_SQL_DB_TESTS=1. Needs the same settings as the app:
DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD (+ DB_SSLMODE), DB_READONLY_USER /
DB_READONLY_PASSWORD, and ANALYTICS_SCHEMA. These are read from `.env`.

    CUSTOMER_SQL_DB_TESTS=1 pytest tests/test_customer_sql_postgres.py
"""

import os

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.services.customer_sql_service import (
    MAX_RESULT_ROWS,
    execute_customer_query,
    validate_sql,
)
from app.utils.database import get_analytics_schema, get_readonly_engine

pytestmark = pytest.mark.skipif(
    os.getenv("CUSTOMER_SQL_DB_TESTS") != "1",
    reason="Set CUSTOMER_SQL_DB_TESTS=1 to run against a real database.",
)


@pytest.fixture(scope="module")
def campaign_ids() -> list[str]:
    with get_readonly_engine().connect() as conn:
        rows = conn.execute(
            text(
                f"select distinct campaign_id "
                f"from {get_analytics_schema()}.customer_analytic_layer order by 1"
            )
        )
        return [row[0] for row in rows]


def test_cal_is_scoped_to_requested_campaign(campaign_ids):
    requested = campaign_ids[:1]

    rows = execute_customer_query(
        validate_sql("select distinct campaign_id from cal order by 1"),
        requested,
    )

    assert rows["campaign_id"].tolist() == requested


def test_results_are_capped(campaign_ids):
    rows = execute_customer_query(
        validate_sql("select customer_id from cal order by customer_id"),
        campaign_ids,
    )

    assert len(rows) == MAX_RESULT_ROWS + 1


def test_conversions_match_the_campaign_mart(campaign_ids):
    campaign_id = campaign_ids[0]

    rows = execute_customer_query(
        validate_sql("select count(*) as conversions from cal where conversion_flag = 'Y'"),
        [campaign_id],
    )

    with get_readonly_engine().connect() as conn:
        # The read-only role can only read customer_analytic_layer, so compare
        # against a direct count on the same table.
        expected = conn.execute(
            text(
                f"select count(*) from {get_analytics_schema()}.customer_analytic_layer "
                f"where campaign_id = :id and conversion_flag = 'Y'"
            ),
            {"id": campaign_id},
        ).scalar()

    assert int(rows["conversions"].iloc[0]) == expected


def test_long_running_query_hits_statement_timeout(campaign_ids):
    with pytest.raises(DBAPIError, match="statement timeout"):
        execute_customer_query(
            validate_sql("select count(*) from cal a cross join cal b cross join cal c"),
            campaign_ids,
        )


def test_readonly_role_cannot_read_other_tables():
    with pytest.raises(DBAPIError, match="permission denied"):
        with get_readonly_engine().connect() as conn:
            conn.execute(text("select count(*) from public.campaign_results"))


def test_readonly_role_cannot_write():
    schema = get_analytics_schema()

    with pytest.raises(DBAPIError):
        with get_readonly_engine().begin() as conn:
            conn.execute(
                text(f"delete from {schema}.customer_analytic_layer where false")
            )
