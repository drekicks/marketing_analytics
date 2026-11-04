"""Report logic of scripts/compare_models.py (no API calls)."""

from scripts.compare_models import (
    DEFAULT_QUESTIONS,
    Combination,
    QuestionResult,
    load_questions,
    render_report,
    summarize,
)


def _combo(model, effort, timings, errors=()):
    combo = Combination(model=model, effort=effort, sql_model="strong-sql")
    for i, seconds in enumerate(timings):
        combo.results.append(
            QuestionResult(
                question=f"Q{i}",
                run=1,
                seconds=seconds,
                answer="" if i in errors else f"answer {i}",
                error="The AI service didn't respond." if i in errors else "",
                input_tokens=100,
                output_tokens=50,
                efforts_sent="" if i in errors else effort,
            )
        )
    return combo


def test_summary_uses_successful_answers_only():
    summary = summarize(_combo("mini", "low", [1.0, 3.0, 9.0, 2.0], errors={2}))

    assert summary["combination"] == "mini / low"
    assert summary["errors"] == 1
    assert summary["median_s"] == 2.0  # of 1.0, 3.0, 2.0
    assert summary["max_s"] == 3.0
    assert summary["input_tokens"] == 400


def test_summary_when_everything_failed():
    summary = summarize(_combo("mini", "low", [1.0], errors={0}))

    assert summary["median_s"] is None and summary["max_s"] is None


def test_report_has_table_and_answers_side_by_side():
    combos = [_combo("strong", "medium", [4.0, 5.0]), _combo("mini", "low", [1.0, 2.0])]

    report = render_report(
        combos,
        ["Q0", "Q1"],
        {"started": "2026-11-04 10:00", "campaign": "CMP-2026-004", "data_source": "csv", "runs": 1},
    )

    assert "| strong / medium | medium | strong-sql | 2 | 0 | 4.5 | 5.0 |" in report
    assert "| mini / low | low | strong-sql | 2 | 0 | 1.5 | 2.0 |" in report
    q0 = report.index("### Q0")
    assert report.index("**strong / medium**", q0) < report.index("**mini / low**", q0) < report.index("### Q1")


def test_load_questions_from_file_skips_blanks_and_comments(tmp_path):
    path = tmp_path / "questions.txt"
    path.write_text("# my questions\nWhich segment performed best?\n\n  Chart revenue by segment  \n")

    assert load_questions(str(path)) == ["Which segment performed best?", "Chart revenue by segment"]
    assert load_questions(None) == list(DEFAULT_QUESTIONS)


def test_summary_shows_effort_actually_sent():
    combo = _combo("legacy", "medium", [1.0, 2.0])
    for result in combo.results:
        result.efforts_sent = "default"

    assert summarize(combo)["effort_sent"] == "default"
