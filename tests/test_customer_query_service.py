"""Customer SQL flow with the LLM and database replaced by fakes."""

import pandas as pd
import pytest
from sqlalchemy.exc import OperationalError, ProgrammingError

import app.services.analyst_service as analyst_service
import app.services.customer_sql_service as customer_sql_service
from app.config.router import RouteResult
from app.config.settings import SessionState
from app.services.customer_sql_service import (
    CustomerQueryError,
    CustomerQueryResult,
    execute_customer_query,
    build_customer_query_context,
    build_wrapped_query,
    run_customer_query,
)

VALID_CAMPAIGN_IDS = {"CMP-2025-002", "CMP-2026-003", "CMP-2026-004"}
ACTIVE_CAMPAIGN_ID = "CMP-2026-004"


@pytest.fixture
def fake_llm(monkeypatch):
    """Queue of SQL replies the fake model returns, plus the prompts it saw."""
    replies: list[str] = []
    prompts: list[str] = []

    def fake_generate_json(prompt, schema_name, schema):
        prompts.append(prompt)
        return {"sql": replies.pop(0), "explanation": "Counts customers by tier."}

    monkeypatch.setattr(customer_sql_service, "generate_json", fake_generate_json)
    return replies, prompts


@pytest.fixture
def fake_db(monkeypatch):
    """Queue of results (DataFrames or exceptions) and the executed calls."""
    outcomes: list = []
    executed: list[tuple[str, list[str]]] = []

    def fake_execute(validated_sql, campaign_ids):
        executed.append((validated_sql, campaign_ids))
        outcome = outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(customer_sql_service, "execute_customer_query", fake_execute)
    return outcomes, executed


def _db_error(message: str) -> CustomerQueryError:
    """A failure of the model's query itself (what execute_customer_query raises)."""
    return CustomerQueryError(message)


def _connection_error() -> OperationalError:
    return OperationalError("connect", {}, Exception("could not connect to server"))


def test_wrapped_query_scopes_cal_and_limits_rows(monkeypatch):
    monkeypatch.setenv("ANALYTICS_SCHEMA", "dbt_dev_analytics")

    wrapped = build_wrapped_query("SELECT COUNT(*) FROM cal")

    assert wrapped.startswith(
        "WITH cal AS (SELECT * FROM dbt_dev_analytics.customer_analytic_layer "
        "WHERE campaign_id = ANY(:campaign_ids))"
    )
    assert wrapped.endswith("LIMIT 51")


def test_runs_validated_sql(fake_llm, fake_db):
    replies, prompts = fake_llm
    outcomes, executed = fake_db
    replies.append("select customer_tier, count(*) n from cal group by 1 order by 2 desc")
    outcomes.append(pd.DataFrame({"customer_tier": ["Low Value"], "n": [5]}))

    result = run_customer_query("How many customers per tier?", [ACTIVE_CAMPAIGN_ID])

    assert executed == [(result.sql, [ACTIVE_CAMPAIGN_ID])]
    assert result.sql.startswith("SELECT customer_tier, COUNT(*)")
    assert not result.truncated
    assert "How many customers per tier?" in prompts[0]
    assert ACTIVE_CAMPAIGN_ID in prompts[0]


def test_retries_once_with_database_error(fake_llm, fake_db):
    replies, prompts = fake_llm
    outcomes, executed = fake_db
    replies.extend(["select bad_column from cal", "select count(*) from cal"])
    outcomes.extend([_db_error('column "bad_column" does not exist'), pd.DataFrame({"count": [3]})])

    result = run_customer_query("How many customers?", [ACTIVE_CAMPAIGN_ID])

    assert len(executed) == 2
    assert result.sql == "SELECT COUNT(*) FROM cal"
    assert 'column "bad_column" does not exist' in prompts[1]
    assert "SELECT bad_column FROM cal" in prompts[1]


def test_gives_up_after_second_database_error(fake_llm, fake_db):
    replies, _ = fake_llm
    outcomes, _ = fake_db
    replies.extend(["select a from cal", "select b from cal"])
    outcomes.extend([_db_error("no a"), _db_error("no b")])

    with pytest.raises(ValueError, match="couldn't build a working query"):
        run_customer_query("How many customers?", [ACTIVE_CAMPAIGN_ID])


def test_connection_failure_is_not_retried(fake_llm, fake_db):
    replies, prompts = fake_llm
    outcomes, executed = fake_db
    replies.extend(["select count(*) from cal", "select count(*) from cal"])
    outcomes.append(_connection_error())

    with pytest.raises(OperationalError):
        run_customer_query("How many customers?", [ACTIVE_CAMPAIGN_ID])

    assert len(executed) == 1
    assert len(prompts) == 1


class _FakeConnection:
    def __init__(self, query_error=None):
        self.query_error = query_error

    def exec_driver_sql(self, sql):
        pass

    def execute(self, statement, params):
        raise self.query_error

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _FakeEngine:
    def __init__(self, connect_error=None, query_error=None):
        self.connect_error = connect_error
        self.query_error = query_error

    def begin(self):
        if self.connect_error:
            raise self.connect_error
        return _FakeConnection(self.query_error)


def test_query_errors_become_customer_query_errors(monkeypatch):
    engine = _FakeEngine(
        query_error=ProgrammingError("SELECT", {}, Exception('column "x" does not exist'))
    )
    monkeypatch.setattr(customer_sql_service, "get_readonly_engine", lambda: engine)

    with pytest.raises(CustomerQueryError, match='column "x" does not exist'):
        execute_customer_query("SELECT x FROM cal", [ACTIVE_CAMPAIGN_ID])


def test_connection_errors_are_not_wrapped(monkeypatch):
    engine = _FakeEngine(connect_error=_connection_error())
    monkeypatch.setattr(customer_sql_service, "get_readonly_engine", lambda: engine)

    with pytest.raises(OperationalError):
        execute_customer_query("SELECT 1 FROM cal", [ACTIVE_CAMPAIGN_ID])


def test_unsafe_sql_is_rejected_without_running(fake_llm, fake_db):
    replies, _ = fake_llm
    _, executed = fake_db
    replies.append("delete from cal")

    with pytest.raises(ValueError, match="rejected"):
        run_customer_query("Delete all customers", [ACTIVE_CAMPAIGN_ID])

    assert executed == []


def test_truncates_to_fifty_rows(fake_llm, fake_db):
    replies, _ = fake_llm
    outcomes, _ = fake_db
    replies.append("select customer_id from cal order by 1")
    outcomes.append(pd.DataFrame({"customer_id": range(51)}))

    result = run_customer_query("List customers", [ACTIVE_CAMPAIGN_ID])

    assert result.truncated
    assert len(result.rows) == 50
    assert "Showing the first 50 rows" in build_customer_query_context(result)


def test_context_reports_empty_result():
    context = build_customer_query_context(
        CustomerQueryResult(
            sql="SELECT 1",
            explanation="Nothing.",
            rows=pd.DataFrame(),
            truncated=False,
            campaign_ids=[ACTIVE_CAMPAIGN_ID],
        )
    )

    assert context.startswith("CUSTOMER QUERY RESULT")
    assert "The query returned no rows." in context


# --- process_analyst_question wiring -------------------------------------


@pytest.fixture
def service_fakes(monkeypatch):
    """Postgres mode with fake SQL runner and fake interpretation call."""
    query_calls: list[dict] = []
    ask_calls: list[dict] = []

    def fake_run_customer_query(**kwargs):
        query_calls.append(kwargs)
        return CustomerQueryResult(
            sql="SELECT COUNT(*) FROM cal",
            explanation="Counts customers.",
            rows=pd.DataFrame({"count": [42]}),
            truncated=False,
            campaign_ids=kwargs["campaign_ids"],
        )

    def fake_ask_analyst(**kwargs):
        ask_calls.append(kwargs)
        return "42 customers."

    monkeypatch.setattr(analyst_service, "DATA_SOURCE", "postgres")
    monkeypatch.setattr(analyst_service, "run_customer_query", fake_run_customer_query)
    monkeypatch.setattr(analyst_service, "ask_analyst", fake_ask_analyst)
    return query_calls, ask_calls


def _ask(question, session=None, history=None):
    return analyst_service.process_analyst_question(
        question=question,
        session_state=session or SessionState(active_campaign_id=ACTIVE_CAMPAIGN_ID),
        default_campaign_id=ACTIVE_CAMPAIGN_ID,
        valid_campaign_ids=VALID_CAMPAIGN_IDS,
        conversation_history=history or [],
    )


def test_customer_question_returns_sql_and_interprets_result(service_fakes):
    query_calls, ask_calls = service_fakes

    result = _ask("How many customers in Canada converted?")

    assert result.answer == "42 customers."
    assert result.sql == "SELECT COUNT(*) FROM cal"
    assert query_calls[0]["campaign_ids"] == [ACTIVE_CAMPAIGN_ID]
    assert len(ask_calls) == 1
    assert ask_calls[0]["context"].startswith("CUSTOMER QUERY RESULT")


def test_customer_question_uses_campaigns_named_in_question(service_fakes):
    query_calls, _ = service_fakes

    _ask("How many customers converted in CMP-2025-002?")

    assert query_calls[0]["campaign_ids"] == ["CMP-2025-002"]


def test_customer_question_rejects_unknown_campaign(service_fakes):
    with pytest.raises(ValueError, match="does not exist"):
        _ask("How many customers converted in CMP-2026-999?")


def test_follow_up_stays_on_customer_route(service_fakes):
    query_calls, _ = service_fakes
    session = SessionState(active_campaign_id=ACTIVE_CAMPAIGN_ID)

    _ask("How many customers in Canada converted?", session=session)
    result = _ask("What about Mexico?", session=session)

    assert result.sql == "SELECT COUNT(*) FROM cal"
    assert len(query_calls) == 2


def test_follow_up_without_customer_context_is_unchanged(service_fakes):
    query_calls, ask_calls = service_fakes
    session = SessionState(
        active_campaign_id=ACTIVE_CAMPAIGN_ID,
        last_route=RouteResult(context_type="segment", analysis_type="summary", campaign_ids=[]),
    )

    result = _ask("What about Mexico?", session=session)

    assert result.sql is None
    assert query_calls == []
    assert ask_calls[0]["context"] is None


def test_customer_question_needs_postgres(monkeypatch, service_fakes):
    monkeypatch.setattr(analyst_service, "DATA_SOURCE", "csv")

    with pytest.raises(ValueError, match="DATA_SOURCE=postgres"):
        _ask("How many customers in Canada converted?")
