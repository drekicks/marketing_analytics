from app.config.settings import SessionState
from app.config.router import RouteResult


def resolve_campaign_id(
    session_state: SessionState,
    route: RouteResult,
    default_campaign_id: str,
    valid_campaign_ids: set[str] | None = None,
) -> str:
    session_state.last_route = route

    if route.campaign_ids:
        latest_campaign_id = route.campaign_ids[-1]

        if valid_campaign_ids is None or latest_campaign_id in valid_campaign_ids:
            session_state.active_campaign_id = latest_campaign_id

        return latest_campaign_id
    elif session_state.active_campaign_id is None:
        session_state.active_campaign_id = default_campaign_id

    return session_state.active_campaign_id or default_campaign_id


def resolve_comparison_campaign_ids(
    explicit_campaign_ids: list[str],
    previous_active_campaign_id: str | None,
    fallback_campaign_id: str,
) -> list[str]:
    normalized_ids: list[str] = []

    for campaign_id in explicit_campaign_ids:
        normalized_campaign_id = str(campaign_id).strip()
        if normalized_campaign_id and normalized_campaign_id not in normalized_ids:
            normalized_ids.append(normalized_campaign_id)

    if len(normalized_ids) >= 2:
        return normalized_ids

    if len(normalized_ids) == 1:
        baseline_campaign_id = (
            str(previous_active_campaign_id).strip()
            if previous_active_campaign_id is not None
            else str(fallback_campaign_id).strip()
        )

        if baseline_campaign_id and baseline_campaign_id != normalized_ids[0]:
            return [baseline_campaign_id, normalized_ids[0]]

    return normalized_ids
