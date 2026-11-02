# CLAUDE.md

AI Marketing Analytics Assistant: a Streamlit app (plus a terminal CLI) where users pick a marketing
campaign, generate an AI executive summary, and ask natural-language questions. Answers come
from OpenAI models grounded in pre-aggregated dbt mart data (loaded into pandas). Definition
questions go through RAG over markdown docs stored in Postgres/pgvector. **There is no text-to-SQL.**
See `ARCHITECTURE.md` for the full map, the request flow, and the known-issues list.

## Run

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py         # web app (hosted demo entry point)
python main.py                         # CLI version (README's `python -m app.main` is wrong)
python -m app.extracts.campaign_extract     # validate + re-export data/demo/*.csv from the marts (overwrites demo data)
python -m app.utils.knowledge_ingestion     # rebuild ai.knowledge_chunks embeddings (TRUNCATEs table)
cd marketing_analytics_dbt && dbt build --target neon   # see profiles.example.yml; NEON_DB_* env vars
pytest tests/                               # real test suite (conftest sets dummy OpenAI env + CSV mode)
                                            # tools/ holds older ad-hoc tests; some are broken
```

Env (`.env` at repo root): `OPENAI_API_KEY` and `OPENAI_MODEL` are required at import time.
`DATA_SOURCE` is `postgres` (target: dbt marts in Neon) or `csv` (offline fallback, reads `data/demo/`; the code default).
`ANALYTICS_SCHEMA` (default `dbt_dev_analytics`) fills `{{analytics_schema}}` in `app/sql/*.sql`. Set
`DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD` and `DB_SSLMODE=require` (Neon) for postgres mode, RAG, ingestion, and extracts.
See `.env.example`.

## Key files
- `streamlit_app.py`: UI and session state. `app/ui/cli.py` and `main.py` are the CLI.
- `app/services/analyst_service.py::process_analyst_question`: the UI-agnostic orchestrator.
- `app/config/router.py::route_question`: keyword router → `RouteResult(context_type, analysis_type, campaign_ids, visualization_request)`.
- `app/ai/analyst_chat.py::ask_analyst`: builds context, fills `prompts/analyst_guidelines.md`, calls the LLM.
- `app/ai/context_builder.py`: DataFrame rows → labelled text for the LLM. `app/ai/insight_signals.py` holds the pre-computed rankings.
- `app/ai/llm_client_api.py::generate_analysis`: the only text-generation call (Responses API, `OPENAI_MODEL`).
- `app/services/rag_service.py` + `app/utils/knowledge_search.py`: RAG (model hard-coded `gpt-5.5`).
- `app/utils/data_loader.py`: module-level globals `summary_df`, `segment_df`, `campaign_goals_df`, `customer_df`, `unique_campaigns_df`.
- `app/visualization/`: matplotlib PNG charts (`chart_dispatcher`) and their text equivalents (`chart_builder`).
- `prompts/*.md`: prompt templates using `{{placeholder}}` syntax (filled by `app/ai/prompt_builder.py`).
- `marketing_analytics_dbt/`: dbt project. `knowledge/*.md` holds the RAG source docs (split on `#`/`##` headings).

## Conventions noticed
- Python: absolute imports from `app.` and run from the repo root. Type hints with `X | None`. Dataclasses for
  results and state. Business/data errors are raised as `ValueError` (the UI catches only `ValueError`).
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
- Many modules do work at import time (settings validation, data loading), so tests rely on `tests/conftest.py`.
