"""Answer layout rules in the analyst prompt (deterministic, no LLM)."""

import pytest

from app.ai.analyst_chat import (
    DERIVED_SIGNAL_RESPONSE_FORMAT,
    EVIDENCE_LAYOUT_RULES,
    INSIGHT_RESPONSE_FORMAT,
    STANDARD_RESPONSE_FORMAT,
    _get_response_format_instructions,
)
from app.ai.prompt_builder import build_prompt
from app.ai.prompt_loader import load_prompt

ALL_FORMATS = [
    STANDARD_RESPONSE_FORMAT,
    INSIGHT_RESPONSE_FORMAT,
    DERIVED_SIGNAL_RESPONSE_FORMAT,
]


@pytest.mark.parametrize("response_format", ALL_FORMATS)
def test_every_format_includes_the_table_layout_rules(response_format):
    assert EVIDENCE_LAYOUT_RULES in response_format


def test_layout_rules_require_a_table_for_multi_item_comparisons():
    assert "Use a Markdown table when the evidence compares 2 or more items" in EVIDENCE_LAYOUT_RULES
    assert "Never list the same metric once per item as separate bullets." in EVIDENCE_LAYOUT_RULES
    assert "| Segment | Absolute lift (pp) | Marketing ROI |" in EVIDENCE_LAYOUT_RULES


def test_standard_format_no_longer_mandates_bullets():
    assert "short-bulleted list" not in STANDARD_RESPONSE_FORMAT
    assert "Markdown tables are allowed" in STANDARD_RESPONSE_FORMAT


def test_standard_format_puts_the_conclusion_first():
    conclusion = STANDARD_RESPONSE_FORMAT.index("Begin with one direct conclusion")
    evidence = STANDARD_RESPONSE_FORMAT.index("The data shows:")

    assert conclusion < evidence


def test_insight_formats_keep_their_sections():
    for heading in (
        "## Campaign Assessment",
        "## Key Insights",
        "## What This Means",
        "## Recommended Actions",
        "## Limitations",
    ):
        assert heading in INSIGHT_RESPONSE_FORMAT

    for heading in ("## Key Insights", "## What This Means", "## Limitations"):
        assert heading in DERIVED_SIGNAL_RESPONSE_FORMAT


@pytest.mark.parametrize(
    ("context_type", "question", "expected"),
    [
        ("insight", "Overall, which segment had the highest revenue?", DERIVED_SIGNAL_RESPONSE_FORMAT),
        ("insight", "What are the key takeaways?", INSIGHT_RESPONSE_FORMAT),
        ("segment", "Which segment performed best?", STANDARD_RESPONSE_FORMAT),
        ("campaign", "Compare to CMP-2026-003", STANDARD_RESPONSE_FORMAT),
        ("customer_campaign", "Which countries had the most converters?", STANDARD_RESPONSE_FORMAT),
    ],
)
def test_format_is_chosen_by_context_type(context_type, question, expected):
    assert _get_response_format_instructions(context_type, question) == expected


@pytest.mark.parametrize("response_format", ALL_FORMATS)
def test_full_prompt_has_no_unresolved_placeholders(response_format):
    prompt = build_prompt(
        template=load_prompt("analyst_guidelines"),
        variables={
            "response_format_instructions": response_format,
            "campaign_context": "context",
            "conversation_history": "",
            "question": "Which segment performed best?",
        },
    )

    assert "EVIDENCE LAYOUT" in prompt
