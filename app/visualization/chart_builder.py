import pandas as pd
# from app.config.paths import OUTPUT_DIR
from app.config.router import VisualizationRequest

# output = OUTPUT_DIR

def build_visualization_context(
        request: VisualizationRequest,
        campaign_id: str,
        segment_df: pd.DataFrame,
        summary_df: pd.DataFrame,
        campaign_ids: list[str] | None = None,
) -> str:
    if(
        request.subject == "segment"
        and request.metric=="conversion_rate"
    ):
        rows = segment_df.loc[segment_df["campaign_id"].astype(str) == campaign_id].copy()

        if rows.empty:
            raise ValueError(f"No data found for campaign ID {campaign_id}.")

        rows = rows.sort_values("segment_conversion_rate", ascending=False,)

        context_lines = [
            "VISUALIZATION DATA",
            f"Campaign ID: {campaign_id}",
            "Metric: Conversion Rate by Segment",
            "",
        ]

        for _, row in rows.iterrows():
            context_lines.append(
                f"{row['customer_segment']}: "
                f"{row['segment_conversion_rate']:.1%}"
            )

        return "\n".join(context_lines)

    if (
            request.subject == "segment"
            and request.metric == "revenue"
    ):
        rows = segment_df.loc[segment_df["campaign_id"].astype(str) == campaign_id].copy()

        if rows.empty:
            raise ValueError(f"No data found for campaign ID {campaign_id}.")

        rows = rows.sort_values("campaign_revenue", ascending=False,)

        context_lines = [
            "VISUALIZATION DATA",
            f"Campaign ID: {campaign_id}",
            "Metric: Revenue by Segment",
            "",
        ]

        for _, row in rows.iterrows():
            context_lines.append(
                f"{row['customer_segment']}: "
                f"${row['campaign_revenue']:.0f}"
            )

        return "\n".join(context_lines)

    if (
        request.subject == "campaign"
        and request.metric == "conversion_rate"
    ):
        rows = summary_df.copy()

        if campaign_ids:
            normalized_ids = {
                str(value).strip()
                for value in campaign_ids
            }

            rows = rows.loc[
                rows["campaign_id"]
                .astype(str)
                .str.strip()
                .isin(normalized_ids)
            ].copy()

        if rows.empty:
            raise ValueError("No data found for requested visualization.")

        rows = rows.sort_values("conversion_rate", ascending=False)

        context_lines = [
            "VISUALIZATION DATA",
            "Metric: Conversion Rate by Campaign",
            (
                f"Campaign Scope: {', '.join(campaign_ids)}"
                if campaign_ids
                else "Campaign Scope: All campaigns"
            ),
            "",
        ]

        for _, row in rows.iterrows():
            context_lines.append(
                f"Campaign ID: {row['campaign_id']}"
                f"Conversion Rate: {row['conversion_rate']:.2%}",
            )

        return "\n".join(context_lines)

    if (
        request.subject == "campaign"
        and request.metric == "revenue"
    ):
        rows = summary_df.copy()

        if campaign_ids:
            normalized_ids = {
                str(value).strip()
                for value in campaign_ids
            }

            rows = rows.loc[
                rows["campaign_id"]
                .astype(str)
                .str.strip()
                .isin(normalized_ids)
            ].copy()

        if rows.empty:
            raise ValueError("No data found for requested visualization.")

        rows = rows.sort_values("campaign_revenue", ascending=False)

        context_lines = [
            "VISUALIZATION DATA",
            "Metric: Revenue by Campaign",
            (
                f"Campaign Scope: {', '.join(campaign_ids)}"
                if campaign_ids
                else "Campaign Scope: All campaigns"
            ),
            "",
        ]

        for _, row in rows.iterrows():
            context_lines.append(
                f"Campaign ID: {row['campaign_id']}"
                f"Revenue: ${row['campaign_revenue']:.0f}",
            )

        return "\n".join(context_lines)

    raise ValueError(f"Invalid visualization request: {request}")
