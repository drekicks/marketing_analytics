"""
Customer-level questions answered with guarded, model-written SQL.

The model writes one SELECT against a virtual table named `cal`. Before it
runs, the query is:

1. Parsed and validated (validate_sql): exactly one read-only query that
   references only `cal` or its own CTEs, with no dangerous functions.
2. Re-generated from the parsed tree, so the text that runs is exactly the
   text that was validated.
3. Wrapped so `cal` is customer_analytic_layer pre-filtered to the campaigns
   in scope, with a row limit.
4. Executed as a restricted read-only database role inside a read-only
   transaction with a statement timeout.

Only the small result table is passed back to the model for interpretation.
"""

import logging
from dataclasses import dataclass

import pandas as pd
import sqlglot
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlglot import exp
from sqlglot.errors import ParseError

from app.ai.llm_client_api import generate_json
from app.ai.prompt_builder import build_prompt
from app.ai.prompt_loader import load_prompt
from app.utils.database import get_analytics_schema, get_readonly_engine

logger = logging.getLogger(__name__)

VIRTUAL_TABLE = "cal"
SOURCE_TABLE = "customer_analytic_layer"
MAX_RESULT_ROWS = 50
STATEMENT_TIMEOUT = "5s"
CONVERSATION_EXCHANGES = 3

# Functions that could read server state, files or other databases, or
# stall the connection. The read-only role is the main protection; this is
# defence in depth.
BLOCKED_FUNCTION_PREFIXES = ("pg_", "dblink", "lo_", "query_to_xml", "txid_")
BLOCKED_FUNCTIONS = {
    "current_setting",
    "set_config",
    "copy",
    "version",
    "inet_server_addr",
    "inet_client_addr",
}

# Node types that must never appear anywhere in the query.
BLOCKED_NODES = (exp.DDL, exp.DML, exp.Command, exp.Into, exp.Lock, exp.Copy)

SQL_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "sql": {"type": "string"},
        "explanation": {"type": "string"},
    },
    "required": ["sql", "explanation"],
    "additionalProperties": False,
}


class CustomerQueryError(Exception):
    """The model's query failed in the database (bad column, timeout, ...)."""


@dataclass
class CustomerQueryResult:
    sql: str
    explanation: str
    rows: pd.DataFrame
    truncated: bool
    campaign_ids: list[str]


def _reject(reason: str) -> None:
    raise ValueError(f"The generated query was rejected: {reason}")


def _function_name(node: exp.Func) -> str:
    if isinstance(node, exp.Anonymous):
        return str(node.name).lower()
    return node.sql_name().lower()


def validate_sql(sql: str) -> str:
    """
    Validate model-written SQL and return it re-generated from the parse tree.

    Raises:
        ValueError: If the SQL is not a single safe read-only query on `cal`.
    """
    if not sql or not sql.strip():
        _reject("it is empty.")

    try:
        # sqlglot logs a warning when it falls back to a raw Command node.
        sqlglot_logger = logging.getLogger("sqlglot")
        previous_level = sqlglot_logger.level
        sqlglot_logger.setLevel(logging.ERROR)
        try:
            statements = [
                statement
                for statement in sqlglot.parse(sql, read="postgres")
                if statement is not None
            ]
        finally:
            sqlglot_logger.setLevel(previous_level)
    except ParseError:
        _reject("it is not valid SQL.")

    if len(statements) != 1:
        _reject("it must be exactly one statement.")

    statement = statements[0]

    if not isinstance(statement, exp.Query):
        _reject("only SELECT queries are allowed.")

    for node in statement.walk():
        if isinstance(node, BLOCKED_NODES):
            _reject(f"{type(node).__name__.upper()} is not allowed.")

        if isinstance(node, exp.Func):
            name = _function_name(node)
            if name in BLOCKED_FUNCTIONS or name.startswith(BLOCKED_FUNCTION_PREFIXES):
                _reject(f"function {name}() is not allowed.")

    cte_names = {
        cte.alias_or_name.lower()
        for cte in statement.find_all(exp.CTE)
    }

    for table in statement.find_all(exp.Table):
        name = table.name.lower()

        if table.db or table.catalog:
            _reject(f"table {table.sql(dialect='postgres')} is not allowed.")

        if name != VIRTUAL_TABLE and name not in cte_names:
            _reject(f"table {name} is not allowed; query only {VIRTUAL_TABLE}.")

    # Re-generate without comments: what runs is exactly what was validated.
    return statement.sql(dialect="postgres", comments=False)


def build_wrapped_query(validated_sql: str) -> str:
    """Scope `cal` to the campaigns in scope and cap the number of rows."""
    schema = get_analytics_schema()

    return (
        f"WITH {VIRTUAL_TABLE} AS ("
        f"SELECT * FROM {schema}.{SOURCE_TABLE} "
        f"WHERE campaign_id = ANY(:campaign_ids)"
        f") "
        f"SELECT * FROM ({validated_sql}) AS q "
        f"LIMIT {MAX_RESULT_ROWS + 1}"
    )


def execute_customer_query(validated_sql: str, campaign_ids: list[str]) -> pd.DataFrame:
    """Run validated SQL as the read-only role, in a read-only transaction."""
    engine = get_readonly_engine()

    # Connection problems raised here (engine.begin, SET ...) propagate as
    # DBAPIError and are shown as "couldn't reach the database".
    with engine.begin() as conn:
        conn.exec_driver_sql("SET TRANSACTION READ ONLY")
        conn.exec_driver_sql(f"SET LOCAL statement_timeout = '{STATEMENT_TIMEOUT}'")

        # Errors from the model's query itself are worth one retry.
        try:
            result = conn.execute(
                text(build_wrapped_query(validated_sql)),
                {"campaign_ids": list(campaign_ids)},
            )
        except DBAPIError as error:
            message = str(getattr(error, "orig", error)).strip().splitlines()[0]
            raise CustomerQueryError(message) from error

        return pd.DataFrame(result.fetchall(), columns=list(result.keys()))


def _format_history(conversation_history: list[dict]) -> str:
    recent = (conversation_history or [])[-CONVERSATION_EXCHANGES:]
    if not recent:
        return "(none)"
    return "\n\n".join(
        f"User: {exchange['question']}\nAnalyst: {exchange['answer']}"
        for exchange in recent
    )


def _format_scope(campaign_ids: list[str], campaign_names: dict[str, str]) -> str:
    return "\n".join(
        f"- {campaign_id}: {campaign_names.get(campaign_id, 'unknown name')}"
        for campaign_id in campaign_ids
    )


def _request_sql(
    question: str,
    scope: str,
    history: str,
    previous_error: str,
) -> tuple[str, str]:
    prompt = build_prompt(
        template=load_prompt("customer_sql"),
        variables={
            "campaign_scope": scope,
            "conversation_history": history,
            "previous_error": previous_error or "(none)",
            "question": question,
        },
    )
    reply = generate_json(prompt, "customer_sql", SQL_RESPONSE_SCHEMA)
    return str(reply.get("sql", "")), str(reply.get("explanation", "")).strip()


def run_customer_query(
    question: str,
    campaign_ids: list[str],
    campaign_names: dict[str, str] | None = None,
    conversation_history: list[dict] | None = None,
) -> CustomerQueryResult:
    """
    Have the model write SQL for a customer-level question and run it safely.

    A query error (for example a misspelt column) gets one retry with the
    error fed back to the model. Validation failures and connection failures
    are not retried.
    """
    if not campaign_ids:
        raise ValueError("No campaign is selected for this customer question.")

    scope = _format_scope(campaign_ids, campaign_names or {})
    history = _format_history(conversation_history or [])
    previous_error = ""

    for attempt in (1, 2):
        raw_sql, explanation = _request_sql(question, scope, history, previous_error)
        validated_sql = validate_sql(raw_sql)

        try:
            rows = execute_customer_query(validated_sql, campaign_ids)
        except CustomerQueryError as error:
            message = str(error)
            logger.warning(
                "Customer query attempt %s failed: %s | SQL: %s",
                attempt, message, validated_sql,
            )
            previous_error = (
                "Your previous query failed. Fix it.\n"
                f"Query:\n{validated_sql}\n"
                f"Database error: {message}"
            )
            continue

        truncated = len(rows) > MAX_RESULT_ROWS

        return CustomerQueryResult(
            sql=validated_sql,
            explanation=explanation,
            rows=rows.head(MAX_RESULT_ROWS),
            truncated=truncated,
            campaign_ids=list(campaign_ids),
        )

    raise ValueError("I couldn't build a working query for that question.")


def build_customer_query_context(result: CustomerQueryResult) -> str:
    """Format the query result as the context for the interpretation prompt."""
    lines = [
        "CUSTOMER QUERY RESULT",
        "=====================",
        f"Campaigns in scope: {', '.join(result.campaign_ids)}",
        f"What the query measures: {result.explanation}",
        "",
        "The application ran this query against customer-level campaign data:",
        result.sql,
        "",
    ]

    if result.rows.empty:
        lines.append("The query returned no rows.")
    else:
        lines.append(result.rows.to_markdown(index=False))

        if result.truncated:
            lines.append(
                f"\nShowing the first {MAX_RESULT_ROWS} rows; the full result "
                "has more rows."
            )

    return "\n".join(lines)
