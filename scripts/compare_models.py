"""
Compare OpenAI models and reasoning effort on the app's own questions.

Runs each question through the real back end (process_analyst_question) for
every model x effort combination, timing each answer, and writes a report
with a summary table and the answers side by side.

Makes real OpenAI calls with the key in .env (a small cost), and uses the data
source configured there (DATA_SOURCE=postgres to include customer SQL questions).

Example:
    python -m scripts.compare_models --models gpt-5.4,gpt-5.4-mini --efforts low,medium
"""

import argparse
import csv
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

DEFAULT_QUESTIONS = (
    "How did the campaign perform?",
    "Which segment performed best?",
    "Compare to CMP-2026-003",
    "What are the key takeaways?",
    "Chart revenue by segment",
    "Which countries had the most converters?",
    "How many High Value customers converted in the test group?",
    "Define customer segments",
    "Explain lapsed customers",
)


@dataclass
class QuestionResult:
    question: str
    run: int
    seconds: float
    answer: str = ""
    error: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    efforts_sent: str = ""


@dataclass
class Combination:
    model: str
    effort: str
    sql_model: str
    results: list[QuestionResult] = field(default_factory=list)

    @property
    def label(self) -> str:
        return f"{self.model} / {self.effort}"


def load_questions(path: str | None) -> list[str]:
    """Questions from a file (one per line, # for comments), else the defaults."""
    if not path:
        return list(DEFAULT_QUESTIONS)
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]


def summarize(combo: Combination) -> dict:
    """Median/max seconds, errors and token totals for one combination."""
    ok = [r.seconds for r in combo.results if not r.error]
    return {
        "combination": combo.label,
        "sql_model": combo.sql_model,
        "answers": len(combo.results),
        "errors": sum(1 for r in combo.results if r.error),
        "median_s": round(statistics.median(ok), 2) if ok else None,
        "max_s": round(max(ok), 2) if ok else None,
        "input_tokens": sum(r.input_tokens for r in combo.results),
        "output_tokens": sum(r.output_tokens for r in combo.results),
        # What was actually sent: a model that rejects reasoning gets "default".
        "effort_sent": ", ".join(sorted({e for r in combo.results for e in r.efforts_sent.split(",") if e})) or "-",
    }


def render_report(combos: list[Combination], questions: list[str], meta: dict) -> str:
    """Markdown report: settings, summary table, then each question's answers side by side."""
    lines = [
        "# Model comparison",
        "",
        f"Run {meta['started']} · campaign {meta['campaign']} · data source {meta['data_source']} · "
        f"{meta['runs']} run(s) per question.",
        "",
        "## Summary",
        "",
        "| Model / effort | Effort sent | SQL model | Answers | Errors | Median s | Max s | Input tokens | Output tokens |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for combo in combos:
        s = summarize(combo)
        lines.append(
            f"| {s['combination']} | {s['effort_sent']} | {s['sql_model']} | {s['answers']} | {s['errors']} | "
            f"{s['median_s'] if s['median_s'] is not None else '-'} | "
            f"{s['max_s'] if s['max_s'] is not None else '-'} | "
            f"{s['input_tokens']:,} | {s['output_tokens']:,} |"
        )

    lines += ["", "## Answers", ""]
    for question in questions:
        lines += [f"### {question}", ""]
        for combo in combos:
            for r in (r for r in combo.results if r.question == question):
                status = f"error: {r.error}" if r.error else f"{r.seconds:.2f} s"
                lines += [f"**{combo.label}** (run {r.run}, {status})", ""]
                if r.answer:
                    lines += [r.answer, ""]
        lines += ["---", ""]
    return "\n".join(lines)


def write_csv(path: Path, combos: list[Combination]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["model", "effort", "sql_model", "question", "run", "seconds",
                         "error", "input_tokens", "output_tokens"])
        for combo in combos:
            for r in combo.results:
                writer.writerow([combo.model, combo.effort, combo.sql_model, r.question, r.run,
                                 r.seconds, r.error, r.input_tokens, r.output_tokens])


def run_combination(combo: Combination, questions: list[str], campaign_id: str,
                    valid_ids: set[str], runs: int, summary_model: str | None) -> None:
    import app.ai.llm_client_api as llm
    from app.config.settings import SessionState
    from app.services.analyst_service import process_analyst_question
    from app.ui.errors import user_message

    llm.configure_models()
    llm.configure_models(answer=combo.model, sql=combo.sql_model,
                         summary=summary_model or combo.model, effort=combo.effort)

    for run in range(1, runs + 1):
        for question in questions:
            llm.usage_log = []
            started = time.perf_counter()
            result = QuestionResult(question=question, run=run, seconds=0.0)
            try:
                answer = process_analyst_question(
                    question=question,
                    session_state=SessionState(active_campaign_id=campaign_id),
                    default_campaign_id=campaign_id,
                    valid_campaign_ids=valid_ids,
                    conversation_history=[],
                )
                result.answer = answer.answer
            except Exception as error:  # noqa: BLE001 - recorded in the report
                result.error = user_message(error)
            result.seconds = round(time.perf_counter() - started, 2)
            result.input_tokens = sum(c["input_tokens"] or 0 for c in llm.usage_log)
            result.output_tokens = sum(c["output_tokens"] or 0 for c in llm.usage_log)
            result.efforts_sent = ",".join(sorted({c["effort"] for c in llm.usage_log}))
            combo.results.append(result)
            print(f"  {combo.label:<32} {result.seconds:>6.2f} s  {'ERROR ' if result.error else ''}{question}")

    llm.usage_log = None
    llm.configure_models()


def main(argv: list[str] | None = None) -> Path:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--models", required=True, help="Comma-separated model names for answers")
    parser.add_argument("--efforts", default="low", help="Comma-separated reasoning efforts (default: low)")
    parser.add_argument("--sql-model", help="Model for customer SQL in every combination (default: the answer model)")
    parser.add_argument("--summary-model", help="Model for executive summaries (not exercised by questions)")
    parser.add_argument("--campaign", help="Campaign ID (default: the first campaign)")
    parser.add_argument("--questions", help="Text file with one question per line")
    parser.add_argument("--runs", type=int, default=1, help="Runs per question (default: 1)")
    parser.add_argument("--out", default=None, help="Output folder (default: output/model_comparison)")
    args = parser.parse_args(argv)

    from app.config.paths import OUTPUT_DIR
    from app.utils.data_loader import DATA_SOURCE, get_campaign_data

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    efforts = [e.strip() for e in args.efforts.split(",") if e.strip()]
    questions = load_questions(args.questions)

    data = get_campaign_data()
    valid_ids = {str(c).strip() for c in data.unique_campaigns["campaign_id"].dropna()}
    campaign_id = args.campaign or str(data.unique_campaigns["campaign_id"].iloc[0]).strip()

    combos = [Combination(model=m, effort=e, sql_model=args.sql_model or m) for m in models for e in efforts]
    calls = len(combos) * len(questions) * args.runs
    print(f"Comparing {len(combos)} combination(s) x {len(questions)} questions x {args.runs} run(s) "
          f"= {calls} answers (real OpenAI calls). Campaign {campaign_id}, data source {DATA_SOURCE}.")

    started = datetime.now()
    for combo in combos:
        run_combination(combo, questions, campaign_id, valid_ids, args.runs, args.summary_model)

    out_dir = Path(args.out) if args.out else OUTPUT_DIR / "model_comparison"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = started.strftime("%Y%m%d-%H%M%S")
    report = out_dir / f"{stamp}.md"
    report.write_text(
        render_report(combos, questions, {"started": started.strftime("%Y-%m-%d %H:%M"),
                                          "campaign": campaign_id, "data_source": DATA_SOURCE,
                                          "runs": args.runs}),
        encoding="utf-8",
    )
    write_csv(out_dir / f"{stamp}.csv", combos)

    print("\nSummary (median/max seconds per answer):")
    for combo in combos:
        s = summarize(combo)
        print(f"  {s['combination']:<32} median {s['median_s']} s, max {s['max_s']} s, "
              f"errors {s['errors']}, effort sent: {s['effort_sent']}")
    print(f"\nReport: {report}")
    return report


if __name__ == "__main__":
    main()
