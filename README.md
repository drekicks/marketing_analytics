# DVD Rental Campaign Analytics

A portfolio analytics project built with PostgreSQL, SQL, Python, Tableau, and an AI-powered **Ask Analyst** workflow.

The project extends the PostgreSQL `dvdrental` sample database with simulated campaign data, customer segmentation, reusable SQL extracts, validation checks, Tableau-ready datasets, and a conversational analysis layer. It is designed to demonstrate an end-to-end analytics workflow: from source data and transformation through reporting, validation, and natural-language insight generation. 

The application supports configurable OpenAI models. During development, GPT-5.4 mini was used to minimize cost, while GPT-5.5 can be substituted for higher-quality analysis.

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

## Technology Stack

- **Database:** PostgreSQL
- **SQL client:** DBeaver
- **Programming language:** Python
- **Python libraries:** pandas, SQLAlchemy, psycopg2
- **Visualization:** Tableau
- **AI analysis:** Ask Analyst workflow
- **Development environment:** PyCharm
- **Version control:** Git and GitHub

## Project Workflow

```text
PostgreSQL dvdrental database
        |
        v
SQL transformations and analytical extracts
        |
        +------------------------------+
        |                              |
        v                              v
Validated Tableau CSV snapshots     Python DataFrames
        |                              |
        v                              v
Tableau dashboards                  Ask Analyst
```

The Tableau extracts are refreshed through a separate export script rather than automatically through `main.py`. This keeps the dashboard data stable and prevents the underlying CSV files from being overwritten whenever the Ask Analyst application is run.

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

The extract workflow creates curated CSV files such as:

```text
campaign_performance_summary.csv
campaign_segment_summary.csv
campaign_analytic_layer.csv
```

These files are intended to serve as controlled Tableau data sources.

### Ask Analyst

Ask Analyst provides a natural-language interface for exploring the curated analytical data. The application is intentionally separated from the Tableau export process so users can move between a stable dashboard and conversational analysis without triggering a data refresh. The application supports configurable OpenAI models. During development, GPT-5.4 mini was used to minimize cost, while GPT-5.5 can be substituted for higher-quality analysis.

## Visual Analytics

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
|-- app/
|   |-- main.py
|   |
|   |-- analysis/
|   |
|   |-- extracts/
|   |   `-- campaign_extract.py
|   |
|	|-- generation/
|   |   `-- campaign_generation.py
|   |
|   |-- prompts/
|   |
|   |-- sql/
|   |   |-- extracts/
|   |   `-- ...
|   |
|   `-- utils/
|       |-- database.py
|       |-- data_validation.py
|       |-- file_utils.py
|       `-- prompt_loader.py
|
|-- data/
|   |-- tableau/
|   `-- ...
|
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

Example version sequence:

```text
v0.1.0  Initial database and SQL setup
v0.2.0  Python extraction workflow
v0.3.0  Tableau analytical layer
v0.4.0  Campaign generation and validation
v0.5.0  Ask Analyst integration
v1.0.0  Portfolio-ready release
```

Normal development changes should use descriptive commit messages. Tags should be reserved for meaningful project versions.

## Roadmap

Planned or potential enhancements include:

- Expand the Ask Analyst prompt catalog
- Add more campaign and customer-level questions
- Improve response grounding and validation
- Add metadata describing each analytical dataset
- Add automated tests for utility functions
- Improve logging and exception handling
- Add configuration-driven extract definitions
- Document Tableau dashboards and business use cases
- Package a complete portfolio-ready release

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
