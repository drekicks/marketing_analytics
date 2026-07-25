import pandas as pd
# from app.utils.file_utils import load_sql_extracts

def select_campaign(campaign_df: pd.DataFrame) -> tuple[str, str]:
    campaigns = (
        campaign_df[["campaign_id", "campaign_name"]]
        .drop_duplicates()
        .sort_values("campaign_name")
        .reset_index(drop=True)
    )
    print("Available campaigns:")

    for index, row in campaigns.iterrows():
        print(
            f"{index + 1}. "
            f"{row['campaign_name']} "
            f"({row['campaign_id']})"
        )

    while True:
        selection = input(
            "\nSelect a campaign number: "
        ).strip()

        try:
            selection_index = int(selection) - 1

            if selection_index not in campaigns.index:
                raise ValueError

            break
        except ValueError:
            print("Please enter a valid campaign number.")

    selected_campaign = campaigns.iloc[selection_index]

    campaign_id = selected_campaign["campaign_id"]
    campaign_name = selected_campaign["campaign_name"]

    # print(f'{campaign_id, campaign_name} selected')
    return campaign_id, campaign_name

# unique_campaigns_query = load_sql_extracts(["unique_campaigns_list"])
# unique_campaigns_df = unique_campaigns_query["unique_campaigns_list"]

# select_campaign(unique_campaigns_df)