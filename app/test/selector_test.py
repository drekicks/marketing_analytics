import pandas as pd

def select_campaign(
    campaign_df: pd.DataFrame
) -> tuple[str, str]:

    campaigns = _build_campaign_catalog(campaign_df)

    print("How would you like to find a campaign?")
    print("1. Enter Campaign ID")
    print("2. Guided Search")

    while True:
        choice = input("\nSelection: ").strip()

        if choice == "1":
            return _select_by_campaign_id(campaigns)

        if choice == "2":
            return _guided_campaign_search(campaigns)

        print("Please enter 1 or 2.")

def _build_campaign_catalog(
    campaign_df: pd.DataFrame
) -> pd.DataFrame:
    campaigns = (
        campaign_df[
            [
                "campaign_id",
                "campaign_name",
                "channel",
                "campaign_start_date",
            ]
        ]
        .drop_duplicates()
        .sort_values("campaign_name")
        .reset_index(drop=True)
    )

    campaigns["campaign_start_date"] = pd.to_datetime(
        campaigns["campaign_start_date"],
        errors="coerce",
    )
    campaigns = campaigns[
        campaigns["campaign_start_date"].notna()
    ].copy()

    campaigns["start_year"] = campaigns[
        "campaign_start_date"
    ].dt.year
    campaigns["start_month_num"] = campaigns[
        "campaign_start_date"
    ].dt.month
    campaigns["start_month"] = campaigns[
        "campaign_start_date"
    ].dt.month_name()

    return campaigns

def _select_by_campaign_id(
    campaigns: pd.DataFrame
) -> tuple[str, str]:

    while True:
        campaign_id = input(
            "\nEnter Campaign ID: "
        ).strip().upper()

        match = campaigns[
            campaigns["campaign_id"] == campaign_id
        ]

        if not match.empty:
            selected = match.iloc[0]

            return (
                selected["campaign_id"],
                selected["campaign_name"],
            )

        print("Campaign ID not found.")

def _guided_campaign_search(
    campaigns: pd.DataFrame
) -> tuple[str, str]:
    channel_options = sorted(
        [
            str(channel)
            for channel in campaigns["channel"]
            .dropna()
            .unique()
            .tolist()
        ]
    )
    selected_channel = _prompt_for_choice(
        "Select channel:",
        channel_options,
    )
    filtered_campaigns = campaigns[
        campaigns["channel"] == selected_channel
    ]

    year_options = sorted(
        filtered_campaigns["start_year"]
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )
    selected_year = _prompt_for_choice(
        "Select year:",
        [str(year) for year in year_options],
    )
    filtered_campaigns = filtered_campaigns[
        filtered_campaigns["start_year"]
        == int(selected_year)
    ]

    month_frame = (
        filtered_campaigns[
            ["start_month_num", "start_month"]
        ]
        .drop_duplicates()
        .sort_values("start_month_num")
    )
    month_options = month_frame["start_month"].tolist()
    selected_month = _prompt_for_choice(
        "Select month:",
        month_options,
    )
    filtered_campaigns = filtered_campaigns[
        filtered_campaigns["start_month"]
        == selected_month
    ]

    return _select_from_campaign_list(
        filtered_campaigns
    )


def _prompt_for_choice(
    prompt: str,
    options: list[str],
) -> str:
    while True:
        print(prompt)

        for index, option in enumerate(options, start=1):
            print(f"{index}. {option}")

        selection = input("\nSelection: ").strip()

        try:
            selected_index = int(selection) - 1

            if selected_index not in range(len(options)):
                raise ValueError

            return options[selected_index]
        except ValueError:
            print("Please enter a valid option number.")


def _select_from_campaign_list(
    campaigns: pd.DataFrame
) -> tuple[str, str]:
    campaigns_for_selection = campaigns.reset_index(
        drop=True
    )

    print("\nAvailable Campaigns")

    for index, row in enumerate(
        campaigns_for_selection.itertuples(index=False),
        start=1,
    ):
        print(
            f"{index}. "
            f"{row.campaign_name} "
            f"({row.campaign_id})"
        )

    while True:
        selection = input(
            "\nSelect a campaign number: "
        ).strip()

        try:
            selection_index = int(selection) - 1

            if selection_index not in campaigns_for_selection.index:
                raise ValueError

            selected_campaign = campaigns_for_selection.iloc[
                selection_index
            ]
            return (
                selected_campaign["campaign_id"],
                selected_campaign["campaign_name"],
            )
        except ValueError:
            print("Please enter a valid campaign number.")