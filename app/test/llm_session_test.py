from dataclasses import dataclass, field
from datetime import datetime
# import anthropic

from openai import BadRequestError, OpenAI, OpenAIError

from app.config.settings import MODEL_NAME, openai_api_key


if not openai_api_key:
    raise RuntimeError("OPENAI_API_KEY is not set. Check your .env loading.")

client = OpenAI(api_key=openai_api_key)

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

    def to_prompt_context(self) -> str:
        """Render only the fields relevant to steering the LLM's next response."""
        lines = []
        if self.active_campaign_id:
            lines.append(f"Active campaign: {self.active_campaign_id}")
        if self.active_segment:
            lines.append(f"Active segment: {self.active_segment}")
        if self.last_route:
            lines.append(
                f"Last route: {self.last_route.origin} -> "
                f"{self.last_route.destination} ({self.last_route.distance_km}km)"
            )
        return "\n".join(lines) if lines else "No active context."

    def recent_turns(self, n: int = 6) -> list[dict]:
        """Last n turns, formatted for the messages array."""
        return [
            {"role": t["role"], "content": t["content"]}
            for t in self.history[-n:]
        ]


# client = anthropic.Anthropic()

def call_llm(state: SessionState, user_input: str) -> str:
    state.log_turn("user", user_input)

    system_prompt = f"""You are a marketing analytics assistant.

Current session context:
{state.to_prompt_context()}

Use this context to inform your response. If active_campaign_id or 
active_segment is set, tailor suggestions to that campaign/segment."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=system_prompt,
        messages=state.recent_turns() + [{"role": "user", "content": user_input}],
    )

    reply = response.content[0].text
    state.log_turn("assistant", reply)
    return reply