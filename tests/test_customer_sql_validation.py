"""The validator is the main guard on model-written SQL. No DB or LLM needed."""

import pytest

from app.services.customer_sql_service import validate_sql


@pytest.mark.parametrize(
    "sql",
    [
        "select customer_tier, count(*) as customers from cal group by 1 order by 2 desc",
        "with t as (select * from cal where treatment_group = 'TEST') "
        "select country, count(*) as n from t group by country order by n desc limit 10",
        "select customer_id, campaign_revenue, rank() over (order by campaign_revenue desc) as rnk "
        "from cal order by rnk limit 10",
        "select count(*) filter (where conversion_flag = 'Y') from cal where country ilike '%canada%'",
        "select treatment_group, avg(case when conversion_flag = 'Y' then 1.0 else 0 end) as rate "
        "from cal group by 1 order by 1",
        "select 'a' as x from cal union all select 'b' from cal",
        "select round(avg(campaign_revenue)::numeric, 2) as avg_revenue from cal",
    ],
)
def test_accepts_read_only_queries_on_cal(sql):
    assert validate_sql(sql)


@pytest.mark.parametrize(
    ("sql", "reason"),
    [
        ("", "empty"),
        ("   ", "empty"),
        ("drop table cal", "only SELECT"),
        ("delete from cal", "only SELECT"),
        ("update cal set campaign_revenue = 0", "only SELECT"),
        ("insert into cal (customer_id) values (1)", "only SELECT"),
        ("copy cal to '/tmp/out.csv'", "only SELECT"),
        ("set role postgres", "only SELECT"),
        ("select 1; drop table cal", "exactly one statement"),
        ("select 1 /* hi */; drop table cal", "exactly one statement"),
        ("select * from cal -- note\n; drop table cal", "exactly one statement"),
        ("select * into stolen from cal", "INTO"),
        ("select * from cal for update", "LOCK"),
        ("with x as (delete from cal returning *) select * from x", "DELETE"),
        ("select * from public.customer", "not allowed"),
        ("select * from dbt_dev_analytics.customer_analytic_layer", "not allowed"),
        ("select * from pg_catalog.pg_user", "not allowed"),
        ("select * from pg_user", "query only cal"),
        ("select (select usename from pg_user limit 1) from cal", "query only cal"),
        ("select pg_sleep(10)", "pg_sleep"),
        ("select pg_read_file('/etc/passwd')", "pg_read_file"),
        ("select current_setting('data_directory')", "current_setting"),
        ("select dblink('host=x', 'select 1')", "dblink"),
        ("select lo_import('/etc/passwd')", "lo_import"),
    ],
)
def test_rejects_unsafe_queries(sql, reason):
    with pytest.raises(ValueError, match=reason):
        validate_sql(sql)


def test_returns_sql_regenerated_without_comments():
    validated = validate_sql("select count(*) /* inline */ from cal -- trailing\n")

    assert validated == "SELECT COUNT(*) FROM cal"


def test_ctes_named_by_the_query_are_allowed():
    validated = validate_sql(
        "with converters as (select * from cal where conversion_flag = 'Y') "
        "select count(*) from converters"
    )

    assert "converters" in validated
