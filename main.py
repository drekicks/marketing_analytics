from app.ui.campaign_selector import select_campaign
from app.utils.data_loader import unique_campaigns_df
from app.config.settings import SessionState
from app.ui.cli import run_cli_chat,show_executive_summary

def main() -> None:
    # Load initial application data and establish the default campaign.
    valid_campaign_ids = {
        str(value).strip()
        for value in unique_campaigns_df["campaign_id"].dropna()
    }

    default_campaign_id, campaign_name = select_campaign(unique_campaigns_df)
    session_state = SessionState(
        active_campaign_id=default_campaign_id
    )

    conversation_history: list[dict] = []

    show_executive_summary(default_campaign_id,campaign_name)

    run_cli_chat(
        session_state=session_state,
        default_campaign_id=default_campaign_id,
        valid_campaign_ids=valid_campaign_ids,
        conversation_history=conversation_history,
    )


if __name__ == "__main__":
    main()