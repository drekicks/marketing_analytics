from pathlib import Path


APP_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = APP_DIR.parent

SQL_DIR = APP_DIR / "sql"
PROMPT_DIR = PROJECT_ROOT / "prompts"
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"
OUTPUT_DIR = PROJECT_ROOT / "output"
DEMO_DATA_DIR = PROJECT_ROOT / "data"/"demo"
DBT_PROJECT_DIR = PROJECT_ROOT / "marketing_analytics_dbt"
KNOWLEDGE_DIR = PROJECT_ROOT / "marketing_analytics_dbt" / "knowledge"

DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)