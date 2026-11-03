# AI Marketing Analytics Application

🚀 Live Demo:

https://campaign-analytics-ai.streamlit.app

An AI-powered analytics application that enables business users to explore marketing campaign performance and governed business knowledge using natural language. Generate executive summaries, compare campaigns, visualize key metrics, ask analytical questions, and retrieve trusted business definitions and metric logic through an interactive Streamlit interface.

This portfolio project demonstrates an end-to-end Business-Ready Data and AI workflow, from data transformation, modeling, testing, and governance through analytics and AI-assisted analysis. It combines PostgreSQL, dbt, Python, SQL, pgvector, Tableau, Streamlit, and the OpenAI API to support both structured analytics and retrieval-augmented generation (RAG).

## Application Screenshots
<h6>Home Screen</h6>
<p align="center">
  <img src="assets/app_screenshot.png" width="900">
</p>

<h6>AI Analytics Example</h6>
<p align="center">
  <img src="assets/ai_example.png" width="900">
</p>

<h6>RAG Business Knowledge Example</h6>
<p align="center">
  <img src="assets/rag_example.png" width="900">
</p>

## Key Features

- AI-generated executive campaign summaries
- Natural language "Ask Analyst" experience
- Campaign comparison and performance insights
- Interactive visualizations
- Neon (serverless PostgreSQL) as the data source, with a CSV fallback for offline use
- Guarded text-to-SQL for customer-level questions
- Comparison answers laid out as tables
- Configurable OpenAI model (one setting for the whole app)

## Project Architecture

```mermaid
flowchart LR
    A[Data Sources]
    B[Business-Ready Data Layer]
    C[Knowledge / RAG Layer]
    D[Application / Orchestration Layer]
    E[AI Layer]
    F[Presentation Layer]
    A --> B
    B --> C
    B --> D
    C --> D
    D --> E
    E --> F
```

Data Layer
- PostgreSQL
- CSV Demo Data

Business-Ready Data Layer
- dbt Staging Models
- dbt Marts
- Data Quality Tests
- Business Rules
- SQL Extracts / Retrieval Queries

Knowledge / RAG Layer
- Markdown Business Knowledge
- Chunking
- Embedding
- pgvector
- Knowledge Retriebal

Application / Orchestration Layer
- Router
- Context Builder
- Session Manager
- Visualization Services
- RAG Service

AI Layer
- Prompt Templates
- OpenAI API

Presentation Layer
- CLI
- Streamlit
- Matplotlib

## Project Workflow

```mermaid
flowchart TD

    A[User Question]

    B[Router]
    C[Session Manager]
    D[Context Builder]

    E[Visualization Service]
    F[Analyst Service]

    G[Matplotlib]
    H[OpenAI API]

    I[Presentation Layer]
    J[RAG Service]

    A --> B
    B --> C
    C --> D
    B --> J

    D --> E
    D --> F

    E --> G
    F --> H

    G --> I
    H --> I
    J --> H
```

### SQL Analysis

Reusable SQL files are used to create campaign, customer, segment, and analytical summaries. SQL handles the primary filtering, aggregation, joins, and business logic before results are loaded into Python.

### Campaign Data

The project includes simulated campaign-result data loaded into PostgreSQL. These results support analysis such as:

- Campaign performance
- Customer response
- Segment performance
- Revenue and conversion metrics
- Engagement and recency patterns
- Campaign targeting opportunities

### Ask Analyst

Ask Analyst provides a conversational interface for exploring curated
campaign data.

Current capabilities include:

- Campaign performance summaries
- Segment-level performance analysis
- Campaign-to-campaign comparisons
- Customer-level campaign analysis (guarded text-to-SQL, see below)
- Portfolio-level insights and derived signals
- Session-aware follow-up questions
- Active-campaign switching
- Campaign and segment visualizations
- AI interpretation grounded in the same data used to create each chart

### Visual Analytics

Ask Analyst can generate and interpret bar charts for:

- Campaign revenue
- Campaign conversion rate
- Segment revenue
- Segment conversion rate

Example questions:

- `Chart conversion rate by segment`
- `Plot campaign revenue`

### Customer Questions (Guarded Text-to-SQL)

Questions about individual customers or customer attributes, such as country, customer tier,
recency, favourite film category, or "how many / which / top 10 customers", are answered with
SQL that the model writes against the `customer_analytic_layer` dbt model in Neon. All other
questions use pre-aggregated data prepared by the application.

The generated SQL runs only after layered safety checks:

- **Validation (sqlglot):** exactly one read-only `SELECT`; no DDL, DML, `COPY`, `SET` or
  `SELECT ... INTO`; only the virtual table `cal`; no system functions. The query that runs is
  re-generated from the parsed query, so it is exactly what was validated.
- **Scoping:** `cal` is the customer table pre-filtered to the campaigns in the question (or the
  active campaign), with a row limit.
- **Read-only database role:** `app_readonly` can only `SELECT` from `customer_analytic_layer`,
  runs read-only transactions, and has a 5-second statement timeout.

The SQL used for each answer is shown in an expandable "SQL used" panel.

Example questions:

- `How many High Value customers converted in the test group?`
- `Which countries had the most converters?` and then `What about Canada?`

### Data Validation

Validation is performed before Tableau extracts are created.

Current validation includes:

- Customer-level campaign-result checks
- Campaign-performance checks
- Dataset shape summaries
- Prevention of exports when critical validation errors are found

### Tableau Extracts

The Tableau extracts are refreshed through a separate export script rather than automatically through `main.py`. 
This keeps the dashboard data stable and prevents the underlying CSV files from being overwritten whenever the Ask Analyst application is run.

The extract workflow creates curated CSV files such as:

```text
campaign_summary.csv
campaign_segment_summary.csv
campaign_analytic_layer.csv
campaign_tableau_summary.csv
campaign_goals.csv
unique_campaigns.csv
```

The same files in `data/demo/` are the app's offline fallback (`DATA_SOURCE=csv`), so they always
use the same column names as the dbt marts.

These files are intended to serve as controlled Tableau data sources.



## Technology Stack

- **Database:** PostgreSQL on Neon (serverless), pgvector
- **Transformation / Analytics Engineering:** dbt Core, SQL
- **SQL client:** DBeaver
- **Programming language:** Python
- **Data processing:** pandas
- **Database access:** SQLAlchemy, psycopg 3
- **SQL validation (text-to-SQL guardrails):** sqlglot
- **Dashboarding:** Tableau
- **Python visualization:** Matplotlib
- **AI integration:** OpenAI API
- **Application interface:** Streamlit web app; Python CLI
- **Development environment:** PyCharm
- **Testing:** pytest
- **Version control:** Git and GitHub

## Project Structure

```text
marketing_analytics/
├── streamlit_app.py          Streamlit web app
├── main.py                   CLI entry point
├── app/
│   ├── ai/                   prompts, context building, OpenAI calls, session state
│   ├── config/               settings, paths, question router
│   ├── services/             analyst orchestration, RAG, customer text-to-SQL
│   ├── sql/                  SQL extracts read from the dbt marts
│   ├── ui/                   CLI and shared user-facing error messages
│   ├── utils/                database, data loading, knowledge ingestion/search
│   ├── visualization/        matplotlib charts and their text equivalents
│   └── extracts/             validated CSV exports (Tableau + offline fallback)
├── prompts/                  prompt templates
├── marketing_analytics_dbt/  dbt project (staging, marts, seeds, tests, knowledge docs)
├── data/demo/                CSV snapshots of the marts
├── tests/                    pytest suite
├── requirements.txt          app dependencies
├── requirements-dev.txt      app dependencies + pytest
└── .env.example              environment variable template
```

See `ARCHITECTURE.md` for a detailed walkthrough of every module and the request flow.

## Retrieval-Augmented Generation (RAG)

The application supports business-knowledge questions using a Retrieval-Augmented Generation (RAG) workflow.

Structured analytics questions, such as campaign or segment performance, continue to use governed dbt marts and the existing context-building workflow.

Knowledge questions, such as:

- What does Churn Watchlist mean?
- How is Marketing ROI calculated?
- What quality checks apply to campaign performance?

are routed to the RAG service.

Business definitions, metric documentation, data-product descriptions, and data-quality rules are maintained as Markdown knowledge documents. These documents are chunked by business concept, converted to embeddings, and stored in PostgreSQL using pgvector.

At query time, the user question is embedded and compared with the stored vectors. The most relevant knowledge chunks are retrieved and supplied to the LLM as grounded context.

This design separates structured analytical retrieval from business-knowledge retrieval while allowing both paths to support the same AI assistant.

### RAG Knowledge Store

The `ai.knowledge_chunks` table stores the business knowledge used by the RAG workflow.

| Column | Description |
|---|---|
| `id` | Unique identifier for the stored knowledge chunk |
| `source` | Markdown source file, such as `segments.md` or `metrics.md` |
| `title` | Business concept represented by the chunk |
| `category` | Top-level `#` heading the chunk belongs to (used for category lookups) |
| `content` | Full Markdown content for the business concept |
| `embedding` | 1536-dimensional vector representation generated by the embedding model |

The table is stored in the `ai` PostgreSQL schema rather than the dbt-managed `dbt_dev_analytics` schema because the table is populated by the AI knowledge-ingestion process rather than by dbt.

### Knowledge Ingestion Flow

Business knowledge is maintained in:

- `segments.md`
- `metrics.md`
- `data_products.md`
- `data_quality.md`

The ingestion workflow is:

Markdown documents  
→ load documents  
→ split into semantic chunks using Markdown `##` headings  
→ generate embeddings  
→ store chunk text, metadata, and vectors in `ai.knowledge_chunks`

The current implementation rebuilds the knowledge store when the documentation is refreshed rather than performing incremental updates.

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/drekicks/marketing_analytics.git
cd marketing_analytics
python -m venv .venv
```

### 2. Create and activate a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements-dev.txt
```

`requirements-dev.txt` installs the app dependencies plus pytest. Deployments use `requirements.txt`.

### 4. Configure environment variables

Copy `.env.example` to `.env` in the project root and fill in the values:

```env
OPENAI_API_KEY=...
OPENAI_MODEL=...                  # used for every AI answer

DATA_SOURCE=postgres              # postgres = Neon; csv = offline fallback in data/demo/
ANALYTICS_SCHEMA=dbt_dev_analytics

DB_HOST=your-endpoint.region.aws.neon.tech
DB_PORT=5432
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
DB_SSLMODE=require

DB_READONLY_USER=app_readonly     # customer text-to-SQL only (see below)
DB_READONLY_PASSWORD=...
```

The database settings are also needed in CSV mode for knowledge (RAG) questions.

Do not commit the `.env` file to GitHub.

### 5. Load the database

Restore the `dvdrental` sample database (plus the `campaign_results` and `customer_segment` tables) into the
`public` schema of your Neon (or local PostgreSQL) database, then build the dbt project (below).

Create the read-only role used for customer text-to-SQL (once, in the Neon SQL editor):

```sql
CREATE ROLE app_readonly LOGIN PASSWORD '<strong password>';
GRANT USAGE ON SCHEMA dbt_dev_analytics TO app_readonly;
GRANT SELECT ON dbt_dev_analytics.customer_analytic_layer TO app_readonly;
ALTER ROLE app_readonly SET default_transaction_read_only = on;
ALTER ROLE app_readonly SET statement_timeout = '5s';
```

## dbt Setup

The application uses dbt Core with the PostgreSQL adapter to build and validate the business-ready analytical layer.

Install:

```bash
pip install dbt-postgres
```

Copy the `neon` output from `marketing_analytics_dbt/profiles.example.yml` into `~/.dbt/profiles.yml`
and set `NEON_DB_HOST`, `NEON_DB_USER`, `NEON_DB_PASSWORD` and `NEON_DB_NAME`. Then:

```bash
cd marketing_analytics_dbt
dbt build --target neon
```

Models build into `dbt_dev_staging` and `dbt_dev_analytics`. On the `neon` target, dbt also re-grants
`SELECT` on `customer_analytic_layer` to `app_readonly` and sets its replica identity (required by the
logical-replication publication used by Fivetran).
## pgvector Setup

The RAG workflow uses the pgvector PostgreSQL extension to store and search embedding vectors.

After installing pgvector for the local PostgreSQL instance, enable the extension in the application database:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

```sql
CREATE TABLE ai.knowledge_chunks (
    id bigserial primary key,
    source text not null,
    category text,
    title text not null,
    content text not null,
    embedding vector(1536) not null
);
```

Load or refresh the knowledge store (rebuilds the table):

```bash
python -m app.utils.knowledge_ingestion
```

## Running the Project

### Run the Streamlit app

From the project root:

```bash
streamlit run streamlit_app.py
```

### Run the CLI

```bash
python main.py
```

Neither command refreshes the Tableau CSV extracts.

### Run the tests

```bash
pytest
```

Tests use the demo CSVs and dummy OpenAI settings, so they need no network. To also check the
text-to-SQL guardrails against your database:

```bash
CUSTOMER_SQL_DB_TESTS=1 pytest tests/test_customer_sql_postgres.py
```

### Refresh Tableau Extracts

Run the campaign extract workflow separately:

```bash
python -m app.extracts.campaign_extract
```

## Example Extract Logic

```python
extracts = load_sql_extracts(
    [
        "campaign_summary",
        "campaign_segment_summary",
        "analytic_layer",
    ]
)

performance_df = extracts["campaign_summary"]
segment_df = extracts["campaign_segment_summary"]
analytic_df = extracts["analytic_layer"]
```

The DataFrames are loaded directly from SQL (the dbt marts, schema set by `ANALYTICS_SCHEMA`). CSV is used as a downstream reporting format rather than as the primary source for the Python analysis.

## Design Decisions

### SQL as the primary analytical source

SQL is used to create the analytical datasets because it keeps business logic centralized, reusable, and close to the database.

### CSV as a controlled reporting artifact

CSV files are used for Tableau compatibility, portability, and point-in-time snapshots. They are not automatically regenerated each time the main application runs.

### Separate Tableau and Ask Analyst execution

The Tableau export script is intentionally separate from `main.py`. This allows a user to begin with a stable Tableau dashboard and then continue the analysis in Ask Analyst using the same approved data context.

### Validation before export

Tableau outputs are only created after the underlying campaign data passes validation. This reduces the risk of publishing incomplete or inconsistent reporting datasets.

## Versioning

The project uses Git tags and GitHub Releases for meaningful milestones.

Version sequence:

- v0.5.0  Initial Ask Analyst integration
- v0.6.0  Campaign and segment analysis
- v0.7.0  Insight Explorer and derived signals
- v0.8.0  Session management and conversational context
- v0.9.0  Visual analytics
- v1.0.0  Hosted Streamlit portfolio demo
- v1.1.0  Business-Ready Data + RAG

Normal development changes should use descriptive commit messages. Tags should be reserved for meaningful project versions.

## Business Value

This project reflects a practical analytics workflow rather than a single dashboard or isolated script. It demonstrates the ability to:

- Translate business questions into analytical logic
- Build reusable SQL and Python components
- Validate data before publishing results
- Support both dashboard and conversational analysis
- Separate operational workflows to protect reporting consistency
- Communicate technical outputs in a business-friendly format

## Data Source
The project extends the PostgreSQL dvdrental sample database with simulated marketing campaign data, customer segmentation, reusable SQL extracts, validation checks, Tableau-ready datasets, and an AI-powered conversational analysis layer. It was designed to demonstrate an end-to-end analytics solution, from source data and transformation through reporting, validation, visualization, and natural-language insight generation.
The dbt project supports both PostgreSQL and Snowflake targets. Source configuration and transformation SQL were standardized for cross-platform compatibility. Snowflake implementation includes raw-data ingestion, staging and mart models, automated data-quality tests, lineage, and warehouse query inspection.

## Future Vision

- [ ] Cross-object analytical datasets
- [ ] Data-quality assistant
- [ ] AI-generated explanations aligned with visualization datasets
- [ ] Tableau dashboard integration with AI drill-through
- [ ] Additional visualization types (trend, distribution, composition)
- [ ] Retrieval-Augmented Generation (RAG) for customer-level analysis
- [ ] Multi-agent architecture for specialized analytics workflows
- [ ] Scenario planning and forecasting capabilities

## License

Copyright © 2026 Andre Ferree. All rights reserved. This repository is provided for portfolio and demonstration purposes only. No permission is granted to copy, modify, distribute, or use the source code for commercial purposes without prior written permission.
