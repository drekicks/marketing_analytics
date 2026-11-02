from app.ai.session_state_manager import (
    resolve_campaign_id,
    resolve_comparison_campaign_ids,
)
from app.config.router import RouteResult
from app.config.settings import SessionState


def test_resolve_campaign_id_updates_active_campaign_from_latest_question() -> None:
    session = SessionState(active_campaign_id="CMP-2026-001")

    route = RouteResult(
        context_type="campaign",
        analysis_type="comparison",
        campaign_ids=["CMP-2026-002"],
    )

    resolved_campaign_id = resolve_campaign_id(
        session_state=session,
        route=route,
        default_campaign_id="CMP-2026-001",
    )

    assert resolved_campaign_id == "CMP-2026-002"
    assert session.active_campaign_id == "CMP-2026-002"
    assert session.last_route == route


def test_resolve_campaign_id_uses_session_campaign_for_follow_up_questions() -> None:
    session = SessionState(active_campaign_id="CMP-2026-002")

    follow_up_route = RouteResult(
        context_type="campaign",
        analysis_type="summary",
        campaign_ids=[],
    )

    resolved_campaign_id = resolve_campaign_id(
        session_state=session,
        route=follow_up_route,
        default_campaign_id="CMP-2026-001",
    )

    assert resolved_campaign_id == "CMP-2026-002"
    assert session.active_campaign_id == "CMP-2026-002"
    assert session.last_route == follow_up_route


def test_resolve_campaign_id_switches_to_latest_explicit_campaign() -> None:
    session = SessionState(active_campaign_id="CMP-2026-003")

    switch_route = RouteResult(
        context_type="campaign",
        analysis_type="campaign",
        campaign_ids=["CMP-2026-004"],
    )

    resolved_campaign_id = resolve_campaign_id(
        session_state=session,
        route=switch_route,
        default_campaign_id="CMP-2026-003",
    )

    assert resolved_campaign_id == "CMP-2026-004"
    assert session.active_campaign_id == "CMP-2026-004"

    follow_up_route = RouteResult(
        context_type="campaign",
        analysis_type="summary",
        campaign_ids=[],
    )

    follow_up_campaign_id = resolve_campaign_id(
        session_state=session,
        route=follow_up_route,
        default_campaign_id="CMP-2026-003",
    )

    assert follow_up_campaign_id == "CMP-2026-004"


def test_resolve_campaign_id_prefers_latest_when_multiple_campaigns_mentioned() -> None:
    session = SessionState(active_campaign_id="CMP-2026-003")

    route = RouteResult(
        context_type="campaign",
        analysis_type="comparison",
        campaign_ids=["CMP-2026-003", "CMP-2026-004"],
    )

    resolved_campaign_id = resolve_campaign_id(
        session_state=session,
        route=route,
        default_campaign_id="CMP-2026-003",
    )

    assert resolved_campaign_id == "CMP-2026-004"
    assert session.active_campaign_id == "CMP-2026-004"


def test_resolve_campaign_id_does_not_update_active_campaign_for_invalid_explicit_campaign() -> None:
    session = SessionState(active_campaign_id="CMP-2026-003")

    route = RouteResult(
        context_type="campaign",
        analysis_type="campaign",
        campaign_ids=["CMP-2026-999"],
    )

    resolved_campaign_id = resolve_campaign_id(
        session_state=session,
        route=route,
        default_campaign_id="CMP-2026-001",
        valid_campaign_ids={"CMP-2026-001", "CMP-2026-003", "CMP-2026-004"},
    )

    assert resolved_campaign_id == "CMP-2026-999"
    assert session.active_campaign_id == "CMP-2026-003"

    follow_up_route = RouteResult(
        context_type="campaign",
        analysis_type="summary",
        campaign_ids=[],
    )

    follow_up_campaign_id = resolve_campaign_id(
        session_state=session,
        route=follow_up_route,
        default_campaign_id="CMP-2026-001",
    )

    assert follow_up_campaign_id == "CMP-2026-003"


def test_resolve_comparison_campaign_ids_includes_previous_active_campaign() -> None:
    comparison_ids = resolve_comparison_campaign_ids(
        explicit_campaign_ids=["CMP-2026-004"],
        previous_active_campaign_id="CMP-2026-003",
        fallback_campaign_id="CMP-2026-001",
    )

    assert comparison_ids == ["CMP-2026-003", "CMP-2026-004"]


def test_resolve_comparison_campaign_ids_does_not_duplicate_campaign() -> None:
    comparison_ids = resolve_comparison_campaign_ids(
        explicit_campaign_ids=["CMP-2026-004"],
        previous_active_campaign_id="CMP-2026-004",
        fallback_campaign_id="CMP-2026-001",
    )

    assert comparison_ids == ["CMP-2026-004"]
