import pytest

from app.config.paths import SQL_DIR
from app.utils.database import DEFAULT_ANALYTICS_SCHEMA, get_analytics_schema
from app.utils.file_utils import load_sql, render_sql

APP_EXTRACTS = [
    "campaign_summary",
    "campaign_segment_summary",
    "analytic_layer",
    "unique_campaigns_list",
    "campaign_goals",
]


def test_default_schema_is_dbt_analytics_schema(monkeypatch):
    monkeypatch.delenv("ANALYTICS_SCHEMA", raising=False)

    assert get_analytics_schema() == DEFAULT_ANALYTICS_SCHEMA == "dbt_dev_analytics"


@pytest.mark.parametrize("name", APP_EXTRACTS)
def test_app_extracts_render_to_configured_schema(monkeypatch, name):
    monkeypatch.setenv("ANALYTICS_SCHEMA", "custom_analytics")

    sql = render_sql(load_sql(SQL_DIR / f"{name}.sql"))

    assert "{{" not in sql
    assert "custom_analytics." in sql
    assert "dbt_dev." not in sql


@pytest.mark.parametrize(
    "bad_schema",
    ["dbt_dev; drop table x", "Analytics", "public.x", "", "1schema"],
)
def test_invalid_schema_is_rejected(monkeypatch, bad_schema):
    monkeypatch.setenv("ANALYTICS_SCHEMA", bad_schema)

    with pytest.raises(ValueError, match="Invalid ANALYTICS_SCHEMA"):
        render_sql("select * from {{analytics_schema}}.campaign_goals")
