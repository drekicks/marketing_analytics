# from dataclasses import dataclass, field
# from datetime import datetime
#
# @dataclass
# class RouteResult:
#     origin: str
#     destination: str
#     distance_km: float
#
# @dataclass
# class SessionState:
#     active_campaign_id: str | None = None
#     active_segment: str | None = None
#     last_route: RouteResult | None = None
#     history: list[str] = field(default_factory=list)
#     created_at: datetime = field(default_factory=datetime.now)
#
#     def set_campaign(self, campaign_id: str) -> None:
#         self.active_campaign_id = campaign_id
#         self.history.append(f"switched to campaign {campaign_id}")
#
#     def set_segment(self, segment: str) -> None:
#         self.active_segment = segment
#         self.history.append(f"switched to segment {segment}")
#
#     def reset(self) -> None:
#         self.active_campaign_id = None
#         self.active_segment = None
#         self.last_route = None
#         self.history.clear()
#
#
# # --- usage ---
# session = SessionState()
#
# session.set_campaign("Q3_retention")
# session.set_segment("high_value_churn_risk")
# session.last_route = RouteResult("email", "sms_fallback", distance_km=0)
#
# print(session.active_campaign_id)   # Q3_retention
# print(session.history)              # ['switched to campaign Q3_retention', 'switched to segment high_value_churn_risk']
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class RouteResult:
    origin: str
    destination: str
    distance_km: float

@dataclass
class SessionState:
    session_id: str
    active_campaign_id: str | None = None
    active_segment: str | None = None
    last_route: RouteResult | None = None
    turn_count: int = 0
    history: list[dict] = field(default_factory=list)
    last_active: datetime = field(default_factory=datetime.now)

    def log_turn(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})
        self.turn_count += 1
        self.last_active = datetime.now()


class SessionManager:
    """Keeps track of active sessions, in-memory."""
    def __init__(self):
        self._sessions: dict[str, SessionState] = {}

    def get_or_create(self, session_id: str) -> SessionState:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionState(session_id=session_id)
        return self._sessions[session_id]

    def reset(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


# --- agent loop usage ---
manager = SessionManager()

def handle_message(session_id: str, user_input: str) -> str:
    state = manager.get_or_create(session_id)
    state.log_turn("user", user_input)

    # Example: intent detection updates session state
    if "campaign" in user_input.lower():
        state.active_campaign_id = "Q3_retention"

    # Route decision might depend on session state
    if state.active_campaign_id and not state.active_segment:
        response = "Which segment do you want to target for this campaign?"
    else:
        response = f"Got it. Working with campaign {state.active_campaign_id}."

    state.log_turn("assistant", response)
    return response


# simulate a conversation
print(handle_message("sess_001", "Let's set up a campaign"))
print(handle_message("sess_001", "Target high value churn risk"))