from dataclasses import dataclass
from pathlib import Path

@dataclass
class AnalystResult:
    answer: str
    campaign_id: str | None = None
    chart_path: Path | None = None
    chart_title: str | None = None