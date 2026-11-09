"""Markdown fixes applied to model replies (no API calls)."""

import re
from types import SimpleNamespace

import pytest

import app.ai.llm_client_api as llm
from app.ai.markdown_cleanup import normalize_markdown
from app.ai.prompt_loader import load_prompt


def test_adds_space_after_heading_markers():
    text = "Overall the campaign met its goal.\n\n##Key Strengths\n- Lift\n\n###Detail\n#Title"

    assert normalize_markdown(text) == (
        "Overall the campaign met its goal.\n\n## Key Strengths\n- Lift\n\n### Detail\n# Title"
    )


@pytest.mark.parametrize(
    "text",
    [
        "## Key Strengths\n- Lift",
        "#1 priority is budget control",
        "Ranked #3 of 4 segments",
        "Plain text with no markdown.",
        "1. First\n2. Second",
    ],
)
def test_leaves_valid_or_non_heading_text_alone(text):
    assert normalize_markdown(text) == text


def test_does_not_touch_code_blocks():
    text = "Query:\n```sql\n#comment\nselect 1\n```\n##Next"

    assert normalize_markdown(text) == "Query:\n```sql\n#comment\nselect 1\n```\n## Next"


def test_unwraps_a_reply_fenced_as_markdown():
    text = "```markdown\nThe campaign met its goal.\n\n## Key Strengths\n- Lift\n```"

    assert normalize_markdown(text) == "The campaign met its goal.\n\n## Key Strengths\n- Lift"


def test_generate_analysis_returns_normalized_markdown(monkeypatch):
    reply = SimpleNamespace(
        output_text="Summary.\n\n##Key Strengths\n- Lift",
        usage=SimpleNamespace(input_tokens=1, output_tokens=1),
    )
    fake = SimpleNamespace(create=lambda **kwargs: reply)
    monkeypatch.setattr(llm, "client", SimpleNamespace(responses=fake))

    assert llm.generate_analysis("prompt", purpose="summary") == "Summary.\n\n## Key Strengths\n- Lift"


def test_executive_summary_prompt_uses_valid_headings():
    prompt = load_prompt("executive_summary")
    outside_code = re.sub(r"```.*?```", "", prompt, flags=re.DOTALL)

    assert not re.search(r"^#{1,6}[A-Za-z]", prompt, flags=re.MULTILINE)
    for heading in ("Key Strengths", "Key Weaknesses", "Business Risks", "Recommended Next Actions"):
        assert f"\n## {heading}\n" in prompt
    assert "## Executive Summary" not in prompt
    assert "Do not use bold or italic text." in outside_code
