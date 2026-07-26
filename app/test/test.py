from app.utils.file_utils import load_sql_extracts
from app.ui.campaign_selector import select_campaign

# from app.test.selector_test import select_campaign

# unique_campaigns_query = load_sql_extracts(["unique_campaigns_list"])
# unique_campaigns_df = unique_campaigns_query["unique_campaigns_list"]


# if __name__ == "__main__":
extracts = load_sql_extracts(["unique_campaigns_list"])
unique_campaigns_df = extracts["unique_campaigns_list"]

campaign_id, campaign_name = select_campaign(unique_campaigns_df)
print(f"\nSelected: {campaign_id} | {campaign_name}")