# CLAUDE.md

AI Marketing Analytics Assistant: a Streamlit app (plus a terminal CLI) where users pick a marketing
campaign, generate an AI executive summary, and ask natural-language questions. Answers come
from OpenAI models grounded in pre-aggregated dbt mart data (loaded into pandas). Definition
questions go through RAG over markdown docs stored in Postgres/pgvector. **Customer-level questions only** use
guarded text-to-SQL (`app/services/customer_sql_service.py`); everything else uses prepared context.
See `ARCHITECTURE.md` for the full map, the request flow, and the known-issues list.

## Run

```bash
pip install -r requirements-dev.txt   # app deps + pytest (deploys use requirements.txt)
streamlit run streamlit_app.py         # web app (hosted demo entry point)
chainlit run chainlit_app.py           # chat app (pip install -r requirements-chainlit.txt; Python ≤ 3.13, nest_asyncio breaks on 3.14; Render via render.yaml)
python main.py                         # CLI version (README's `python -m app.main` is wrong)
python -m app.extracts.campaign_extract     # validate + re-export data/demo/*.csv from the marts (overwrites demo data)
python -m app.utils.knowledge_ingestion     # rebuild ai.knowledge_chunks embeddings (TRUNCATEs table)
python -m tools.synthetic_data_creation.campaign_generation --dry-run   # weekly random campaign → Neon raw tables (drop --dry-run to load)
cd marketing_analytics_dbt && dbt build --target neon   # see profiles.example.yml; NEON_DB_* env vars
pytest                                      # from the repo root; pytest.ini adds the root to sys.path
                                            # (conftest sets dummy OpenAI env + CSV mode; no network)
                                            # tools/ holds older ad-hoc tests; some are broken
```

Env (`.env` at repo root): `OPENAI_API_KEY` and `OPENAI_MODEL` are required at import time.
`DATA_SOURCE` is `postgres` (target: dbt marts in Neon) or `csv` (offline fallback, reads `data/demo/`; the code default).
`ANALYTICS_SCHEMA` (default `dbt_dev_analytics`) fills `{{analytics_schema}}` in `app/sql/*.sql`. Set
`DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD` and `DB_SSLMODE=require` (Neon) for postgres mode, RAG, ingestion, and extracts.
`DB_READONLY_USER/DB_READONLY_PASSWORD` (role `app_readonly`, SQL in ARCHITECTURE.md §6) are required for customer questions.
See `.env.example`.

## Key files
- `streamlit_app.py`: Streamlit UI and session state. `chainlit_app.py` (+ testable helpers in `app/ui/chainlit_support.py`):
  Chainlit chat UI on the same back end. `app/ui/cli.py` and `main.py` are the CLI. UIs stay thin: logic belongs in `app/services/`.
- Chainlit branding (ClariMotive): `public/theme.json` (colors/fonts), `public/logo_*.svg` + `public/favicon.svg`
  (placeholder wordmark; sources in `assets/brand/` with the site's `styles.css`), `public/custom.css`, and `[UI]` in `.chainlit/config.toml`.
- `app/services/analyst_service.py::process_analyst_question`: the UI-agnostic orchestrator.
- `app/config/router.py::route_question`: keyword router → `RouteResult(context_type, analysis_type, campaign_ids, visualization_request)`.
- `app/ai/analyst_chat.py::ask_analyst`: builds context, fills `prompts/analyst_guidelines.md`, calls the LLM.
- `app/ai/context_builder.py`: DataFrame rows → labelled text for the LLM. `app/ai/insight_signals.py` holds the pre-computed rankings.
- `app/ai/llm_client_api.py`: all OpenAI calls. `generate_analysis(prompt, purpose="answer"|"summary")` and `generate_json`
  (SQL) pick `OPENAI_MODEL` / `OPENAI_SUMMARY_MODEL` / `OPENAI_SQL_MODEL` and send `OPENAI_REASONING_EFFORT` (default `low`;
  retried once without it if a model rejects it). `configure_models()` overrides at runtime. Compare models with
  `python -m scripts.compare_models` (real API calls).
- `app/services/rag_service.py` + `app/utils/knowledge_search.py`: RAG (answers via `generate_analysis`, so `OPENAI_MODEL`).
- `app/ui/errors.py::user_message` + `app/errors.py` (`ConfigurationError`, `LLMServiceError`): user-facing error text for both UIs.
- `app/services/customer_sql_service.py` + `prompts/customer_sql.md`: customer-level text-to-SQL (`validate_sql`,
  `run_customer_query`, `build_customer_query_context`). `llm_client_api.generate_json` returns structured `{sql, explanation}`.
  Users see `build_display_sql` output (scoped `cal` CTE over the real table, runnable as-is); it is never executed.
- `app/utils/data_loader.py`: `get_campaign_data()` → `CampaignData(summary, segment, goals, unique_campaigns)`, cached
  (framework-neutral in-process cache, no Streamlit import; Postgres TTL 10 min; `clear_campaign_data_cache()` backs the Refresh Data buttons). Call it inside functions,
  never import DataFrames at module level, or new campaigns won't appear until a restart. Customer-level data is queried from Neon, not loaded.
- `app/visualization/`: matplotlib PNG charts (`chart_dispatcher`) and their text equivalents (`chart_builder`).
- `prompts/*.md`: prompt templates using `{{placeholder}}` syntax (filled by `app/ai/prompt_builder.py`).
- `tools/synthetic_data_creation/campaign_generation.py`: weekly synthetic campaign generator (results + exactly one goal per campaign
  into `public.campaign_results` / `public.campaign_goals`); scheduled by `.github/workflows/weekly_campaign.yml`
  (Monday primary + 2 backup slots; `--skip-if-recent` makes the backups no-ops once a campaign is loaded).
- `marketing_analytics_dbt/`: dbt project. `knowledge/*.md` holds the RAG source docs (split on `#`/`##` headings).

## Conventions noticed
- Python: absolute imports from `app.` and run from the repo root. Type hints with `X | None`. Dataclasses for
  results and state. Errors: raise `ValueError` with a user-ready message for business/data problems,
  `LLMServiceError` for AI-service failures, `ConfigurationError` for missing settings; let DB errors propagate.
  UIs catch `Exception` and show `user_message(error)`, never raw tracebacks. One OpenAI client (`llm_client_api.client`).
- Routing: `route_question` runs once per question in `process_analyst_question`; pass `route=` to `ask_analyst`.
  Scope words live only in `router.SCOPE_TERMS` / `is_scope_request`. Customer-grain questions (a specific customer ID, or a
  scope word plus a customer attribute) route to customer SQL before broad insight; with a scope word they cover all campaigns. Add new routes with a case in `tests/test_router.py`.
- Module layout: `config/` (settings, paths, routing), `ai/` (prompting and context), `services/` (orchestration),
  `utils/` (I/O and DB), `visualization/`, `extracts/` (offline export scripts), `sql/` (one static query per file,
  loaded by name via `file_utils.load_sql_extracts([...])`).
- Prompts live in `prompts/<name>.md` and load with `load_prompt("<name>")`. Unresolved `{{vars}}` raise.
- Campaign IDs look like `CMP-YYYY-NNN`. The "segment" in app code means the 4-value market segment
  (Champion / Growth / Win-Back / Churn Watchlist).
- dbt: `models/staging/stg_<table>.sql` (views, rename raw abbreviations such as `cnvrsn_flg` → `conversion_flag`) and
  `models/marts/<entity>_summary.sql` / `customer_analytic_layer.sql` (tables). YAML lives in `staging.yml`/`marts.yml`,
  singular tests in `tests/assert_<model>_<check>.sql`. SQL is lowercase with CTE chains and Jinja comments `{# #}`
  for disabled code. Avoid Postgres-only syntax (e.g. `FILTER`) so it stays Snowflake-compatible.
- Column names: the dbt marts are the source of truth. Demo CSVs must keep identical columns
  (`tests/test_context_builders.py::test_demo_csv_columns_match_dbt_marts`). Rename in dbt first, then code, then re-export CSVs.
- SQL extracts reference `{{analytics_schema}}.<model>`, never a hard-coded schema.
- Customer text-to-SQL is security-sensitive. Model SQL must go through `validate_sql` (sqlglot: one SELECT, only `cal`,
  no DDL/DML/system functions; re-generated from the AST) and run via `execute_customer_query` (read-only role,
  read-only transaction, 5s timeout, campaign-scoped `cal` wrapper, row limit). Never execute model SQL any other way,
  and never grant `app_readonly` more than SELECT on `customer_analytic_layer`. Add a rejection test for every new
  threat in `tests/test_customer_sql_validation.py`. DB guardrail tests: `CUSTOMER_SQL_DB_TESTS=1 pytest tests/test_customer_sql_postgres.py`.
- Many modules do work at import time (settings validation), so tests rely on `tests/conftest.py`.
