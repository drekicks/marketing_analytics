import pandas as pd

from app.utils import database
from app.utils.file_utils import load_sql_extracts, file_export
import app.utils.data_validation as validation


def has_validation_errors(results: dict) -> bool:
    """Return True when any validation check reports errors."""
    return any(
        check_result["count"] > 0
        for check_name, check_result in results.items()
        if check_name != "_dataset_shape"
    )


def export_campaign_results() -> None:
    """Validate campaign data and export Tableau-ready datasets."""

    campaign_df = pd.read_sql(
        "SELECT * FROM public.campaign_results",
        database.engine,
    )

    customer_results = validation.customer_lvl_validation(campaign_df)

    validation.print_validation_summary(
        customer_results,
        title="CUSTOMER-LEVEL CAMPAIGN VALIDATION",
    )

    if has_validation_errors(customer_results):
        print("Exports stopped because customer-level validation failed.")
        return

    extracts = load_sql_extracts(
        [
            "campaign_summary",
            "campaign_segment_summary",
            "analytic_layer",
            "campaign_tableau_summary",
        ]
    )

    summary_df = extracts["campaign_summary"]
    segment_df = extracts["campaign_segment_summary"]
    analytic_df = extracts["analytic_layer"]
    tableau_df = extracts["campaign_tableau_summary"]

    performance_results = (
        validation.campaign_performance_validation(segment_df)
    )

    validation.print_validation_summary(
        performance_results,
        title="CAMPAIGN PERFORMANCE VALIDATION",
    )

    if has_validation_errors(performance_results):
        print("Exports stopped because performance validation failed.")
        return

    file_export(
        summary_df,
        "campaign_summary.csv",
    )
    file_export(
        segment_df,
        "campaign_segment_summary.csv",
    )
    file_export(
        analytic_df,
        "campaign_analytic_layer.csv",
    )
    file_export(
        tableau_df,
        "campaign_tableau_summary.csv",
    )

    print("Campaign Tableau extracts exported successfully.")


if __name__ == "__main__":
    export_campaign_results()