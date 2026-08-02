# from app.utils.data_loader import summary_df
#
# import matplotlib.pyplot as plt
# from matplotlib.ticker import FuncFormatter
#
# # Sort for a cleaner chart (optional)
# plot_df = summary_df.sort_values("conversion_rate", ascending=False)
#
# fig, ax = plt.subplots(figsize=(8, 5))
# ax.bar(plot_df["campaign_id"].astype(str), plot_df["conversion_rate"])
#
# ax.set_title("Conversion Rate by Campaign")
# ax.set_xlabel("Campaign ID")
# ax.set_ylabel("Conversion Rate")
# ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.2%}"))
#
# plt.xticks(rotation=45, ha="right")
# plt.tight_layout()
# plt.savefig("conversion_rate_by_campaign.png", dpi=150)
# plt.show()

from app.config.router import extract_campaign_ids,route_question
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from app.utils.data_loader import summary_df


# def extract_campaign_ids(user_text: str, known_campaign_ids: list[str]) -> list[str]:
#     """Match known campaign IDs against free text, case-insensitive, word-boundary safe."""
#     text_lower = user_text.lower()
#     matched = [
#         cid for cid in known_campaign_ids
#         if re.search(rf"\b{re.escape(cid.lower())}\b", text_lower)
#     ]
#     return matched

route = route_question(question)
def plot_conversion_rate(summary_df, user_text: str = None):
    known_ids = route.campaign_ids

    selected_campaigns = extract_campaign_ids(user_text) if user_text else []

    if selected_campaigns:
        plot_df = summary_df[summary_df["campaign_id"].astype(str).isin(selected_campaigns)]
        title_suffix = f" — {', '.join(selected_campaigns)}"
    else:
        plot_df = summary_df  # no IDs found or no text provided — use all campaigns
        title_suffix = " — All Campaigns"

    plot_df = plot_df.sort_values("conversion_rate", ascending=False)

    if plot_df.empty:
        print("No campaign data available to plot.")
        return

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(plot_df["campaign_id"].astype(str), plot_df["conversion_rate"])

    ax.set_title(f"Conversion Rate by Campaign{title_suffix}")
    ax.set_xlabel("Campaign ID")
    ax.set_ylabel("Conversion Rate")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.2%}"))

    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig("conversion_rate_by_campaign_2.png", dpi=150)
    plt.show()


# Examples
plot_conversion_rate(summary_df, "Show conversion rate for CMP-2025-002 and CMP-2026-003")  # filtered
plot_conversion_rate(summary_df, "build a chart for conversion rate")     # no IDs found -> all campaigns
plot_conversion_rate(summary_df)                                          # no text at all -> all campaigns