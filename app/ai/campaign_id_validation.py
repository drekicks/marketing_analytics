def validate_campaign_ids(
    summary_df,
    campaign_ids: list[str],
) -> None:
    """
    Confirm that every requested campaign ID exists in the summary data.

    Raises:
        ValueError: If one or more requested campaign IDs are missing.
    """

    requested_ids = {
        str(value).strip()
        for value in campaign_ids
    }

    available_ids = {
        str(value).strip()
        for value in summary_df["campaign_id"]
        .dropna()
        .tolist()
    }

    missing_ids = requested_ids - available_ids

    if not missing_ids:
        return

    if len(missing_ids) == 1:
        missing_id = next(iter(missing_ids))

        raise ValueError(
            f"Campaign ID {missing_id} does not exist."
        )

    raise ValueError(
        "The following campaign IDs do not exist: "
        + ", ".join(sorted(missing_ids))
        + "."
    )