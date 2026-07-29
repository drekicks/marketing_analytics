def validate_campaign_ids(
    summary_df,
    campaign_ids: list[str],
) -> None:
    requested_ids = {str(value) for value in campaign_ids}

    available_ids = set(
        summary_df["campaign_id"]
        .dropna()
        .astype(str)
        .unique()
    )

    missing_ids = requested_ids - available_ids

    if missing_ids:
        missing_list = ", ".join(sorted(missing_ids))

        raise ValueError(
            f"The following campaign IDs were not found: "
            f"{missing_list}"
        )