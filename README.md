# DVD Rental Campaign Analytics

A portfolio analytics project built with PostgreSQL, SQL, Python, Tableau, and an AI-powered **Ask Analyst** workflow.

The project extends the PostgreSQL `dvdrental` sample database with simulated campaign data, customer segmentation, reusable SQL extracts, validation checks, Tableau-ready datasets, and a conversational analysis layer. It is designed to demonstrate an end-to-end analytics workflow: from source data and transformation through reporting, validation, and natural-language insight generation. 

The application supports configurable OpenAI models, allowing development to balance response quality, latency, and API cost.

## Project Goals

This project demonstrates how an analyst can:

- Explore transactional customer and rental data with SQL
- Build reusable analytical datasets
- Generate and validate simulated campaign results
- Create curated CSV extracts for Tableau
- Separate controlled reporting snapshots from application execution
- Use Python to coordinate data access and analysis
- Add an AI-assisted experience for answering business questions
- Apply production-minded practices such as modular code, validation, environment configuration, and version control

## Demo Mode

The portfolio release will include a Streamlit web interface hosted on
Streamlit Community Cloud.

The hosted version will use synthetic demonstration data and allow users to:

- Select a campaign
- Generate an executive summary
- Ask natural-language business questions
- Compare campaigns
- Explore segment performance
- Generate and interpret charts

No local installation will be required for the hosted demo.

## Technology Stack

- **Database:** PostgreSQL
- **SQL client:** DBeaver
- **Programming language:** Python
- **Data processing:** pandas
- **Database access:** SQLAlchemy, psycopg2
- **Dashboarding:** Tableau
- **Python visualization:** Matplotlib
- **AI integration:** OpenAI API
- **Application interface:** Python CLI; Streamlit planned for Demo Mode
- **Development environment:** PyCharm
- **Testing:** pytest
- **Version control:** Git and GitHub

## Project Workflow

flowchart TD

    A[User Question]

    B[Router]
    C[Session Manager]
    D[Context Builder]

    E[Visualization]
    F[Ask Analyst]

    G[Matplotlib]
    H[OpenAI API]

    I[CLI / Streamlit UI]

    A --> B
    B --> C
    C --> D

    D --> E
    D --> F

    E --> G
    F --> H

    G --> I
    H --> I


## Key Features

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
campaign_performance_summary.csv
campaign_segment_summary.csv
campaign_analytic_layer.csv
```

These files are intended to serve as controlled Tableau data sources.

### Ask Analyst

Ask Analyst provides a conversational interface for exploring curated
campaign data.

Current capabilities include:

- Campaign performance summaries
- Segment-level performance analysis
- Campaign-to-campaign comparisons
- Customer-level campaign analysis
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

## Example Project Structure

```text
project-root/
|
app/
├── ai/
│   ├── analyst_chat.py
│   ├── context_builder.py
│   ├── prompt_builder.py
│   ├── prompt_loader.py
│   ├── session_state_manager.py
│   └── llm_client_api.py
├── analysis/
├── config/
│   ├── paths.py
│   ├── router.py
│   └── settings.py
├── extracts/
├── generation/
├── prompts/
├── sql/
├── ui/
├── utils/
└── visualization/
    ├── chart_builder.py
    ├── chart_dispatcher.py
    ├── campaign_charts.py
    └── segment_charts.py
|-- main.py
|-- .env
|-- .gitignore
|-- requirements.txt
`-- README.md
```

The exact structure may evolve as the Ask Analyst functionality is expanded.

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/drekicks/marketing_analytics.git
cd <repository-folder>
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
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root.

Example:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=dvdrental
DB_USER=your_username
DB_PASSWORD=your_password
```

Additional variables may be required for the AI integration.

Do not commit the `.env` file to GitHub.

### 5. Load the database

Install PostgreSQL and restore the `dvdrental` sample database. Then run any project-specific SQL needed to create the campaign tables, views, or analytical layers.

## Running the Project

### Run Ask Analyst

From the project root:

```bash
python -m app.main
```

This runs the application without refreshing the Tableau CSV extracts.

### Refresh Tableau Extracts

Run the campaign extract workflow separately:

```bash
python -m app.extracts.campaign_extract
```

This workflow:

1. Reads campaign results from PostgreSQL
2. Runs customer-level validation
3. Stops if customer-level errors are found
4. Loads the analytical SQL extracts
5. Runs campaign-performance validation
6. Exports the approved Tableau-ready CSV files

## Example Extract Logic

```python
extracts = load_sql_extracts(
    [
        "campaign_performance_summary",
        "campaign_segment_summary",
        "analytic_layer",
    ]
)

performance_df = extracts["campaign_performance_summary"]
segment_df = extracts["campaign_segment_summary"]
analytic_df = extracts["analytic_layer"]
```

The DataFrames are loaded directly from SQL. CSV is used as a downstream reporting format rather than as the primary source for the Python analysis.

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

v0.5.0  Initial Ask Analyst integration
v0.6.0  Campaign and segment analysis
v0.7.0  Insight Explorer and derived signals
v0.8.0  Session management and conversational context
v0.9.0  Visual analytics
v1.0.0  Hosted Streamlit portfolio demo

Normal development changes should use descriptive commit messages. Tags should be reserved for meaningful project versions.

## Roadmap

### Before v1.0

- Complete visual-analytics regression testing
- Harden error handling and supported-request validation
- Refresh project documentation and architecture diagrams
- Add synthetic, demo-safe datasets
- Build the Streamlit presentation layer
- Deploy to Streamlit Community Cloud
- Add API usage safeguards
- Validate the hosted application with external users

### Post-v1 Backlog

- Scenario-planning workflows
- Cross-object analytical datasets
- Data-quality assistant
- Forecasting and planning modules
- Additional chart types
- Agent-based multi-step analysis

## Business Value

This project reflects a practical analytics workflow rather than a single dashboard or isolated script. It demonstrates the ability to:

- Translate business questions into analytical logic
- Build reusable SQL and Python components
- Validate data before publishing results
- Support both dashboard and conversational analysis
- Separate operational workflows to protect reporting consistency
- Communicate technical outputs in a business-friendly format

## Data Source

The project uses the PostgreSQL `dvdrental` sample database as its foundational dataset. Campaign data and related analytical layers are created for demonstration and portfolio purposes. The project contains 10,000 simulated customers with rental and payment details. Keys are created to ensure records can be joined to other tables. The original database only had 599 records. 

- Original 599 customers' dates (payment, return, rental) were updated to bring the current (update rental dates to current.sql)

## License

This project is intended for educational and portfolio use. Add an open-source license before distributing or accepting external contributions.
