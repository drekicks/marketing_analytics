import pandas as pd
import re
from datetime import datetime


def validate_customer_data(df: pd.DataFrame, valid_tiers: list = None) -> dict:
    results = {}
    today = pd.Timestamp(datetime.now().date())

    # --- Dataset shape (row/column count) ---
    results["_dataset_shape"] = {
        "row_count": df.shape[0],
        "column_count": df.shape[1],
        "columns": list(df.columns),
    }

    # --- Existing checks ---
    dup_mask = df.duplicated(subset="customer_id", keep=False)
    results["duplicate_customer_ids"] = {"count": dup_mask.sum(), "rows": df[dup_mask].sort_values("customer_id")}

    null_email_mask = df["email"].isna() | (df["email"].astype(str).str.strip() == "")
    results["null_emails"] = {"count": null_email_mask.sum(), "rows": df[null_email_mask]}

    negative_rev_mask = df["total_revenue"] < 0
    results["negative_revenue"] = {"count": negative_rev_mask.sum(), "rows": df[negative_rev_mask]}

    rental_dates = pd.to_datetime(df["most_recent_rental_date"], errors="coerce")
    future_date_mask = rental_dates > today
    results["future_rental_dates"] = {"count": future_date_mask.sum(), "rows": df[future_date_mask]}

    # unparseable_dates_mask = df["most_recent_rental_date"].notna() & rental_dates.isna()
    # results["unparseable_rental_dates"] = {"count": unparseable_dates_mask.sum(), "rows": df[unparseable_dates_mask]}

    missing_country_mask = df["country"].isna() | (df["country"].astype(str).str.strip() == "")
    results["missing_countries"] = {"count": missing_country_mask.sum(), "rows": df[missing_country_mask]}

    # --- New: duplicate emails ---
    dup_email_mask = df.duplicated(subset="email", keep=False) & df["email"].notna()
    results["duplicate_emails"] = {"count": dup_email_mask.sum(), "rows": df[dup_email_mask].sort_values("email")}

    # --- New: malformed email format ---
    email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    malformed_email_mask = df["email"].notna() & ~df["email"].astype(str).str.match(email_pattern)
    results["invalid_emails"] = {"count": malformed_email_mask.sum(), "rows": df[malformed_email_mask]}

    # --- New: negative or zero rentals ---
    bad_rentals_mask = df["total_rentals"] <= 0
    results["non_positive_rentals"] = {"count": bad_rentals_mask.sum(), "rows": df[bad_rentals_mask]}

    # --- New: rentals/revenue logical mismatch ---
    zero_rentals_with_revenue = (df["total_rentals"] == 0) & (df["total_revenue"] > 0)
    revenue_with_no_rentals = (df["total_revenue"] == 0) & (df["total_rentals"] > 0)
    mismatch_mask = zero_rentals_with_revenue | revenue_with_no_rentals
    results["rentals_revenue_mismatch"] = {"count": mismatch_mask.sum(), "rows": df[mismatch_mask]}

    # --- New: avg_payment_amount doesn't match total_revenue / total_rentals ---
    # calculated_avg = df["total_revenue"] / df["total_rentals"].replace(0, pd.NA)
    # avg_diff = (df["avg_payment_amount"] - calculated_avg).abs()
    # avg_mismatch_mask = avg_diff > 0.05  # tolerance for rounding
    # results["avg_payment_mismatch"] = {
    #     "count": avg_mismatch_mask.fillna(False).sum(),
    #     "rows": df[avg_mismatch_mask.fillna(False)],
    # }

    # --- New: unexpected customer_tier values ---
    # if valid_tiers is None:
    #     valid_tiers = ["High Value", "Medium Value", "Low Value"]
    # invalid_tier_mask = ~df["customer_tier"].isin(valid_tiers)
    # results["invalid_customer_tier"] = {"count": invalid_tier_mask.sum(), "rows": df[invalid_tier_mask]}

    # --- New: whitespace/case inconsistency in country ---
    trimmed_country = df["country"].astype(str).str.strip()
    has_whitespace_issue = df["country"].astype(str) != trimmed_country
    results["country_whitespace_issues"] = {"count": has_whitespace_issue.sum(), "rows": df[has_whitespace_issue]}

    return results


def print_validation_summary(results: dict):
    print("=" * 55)
    print("DATA VALIDATION SUMMARY")
    print("=" * 55)
    # --- Print dataset shape first, if present ---
    shape_info = results.get("_dataset_shape")
    if shape_info:
        print(f"{'Row Count':.<40}{shape_info['row_count']:>10}")
        print(f"{'Column Count':.<40}{shape_info['column_count']:>10}")
        print("-" * 55)

    # --- Print each validation check, skipping the shape entry ---
    for check_name, check_result in results.items():
        if check_name == "_dataset_shape":
            continue
        label = check_name.replace("_", " ").title()
        print(f"{label:.<40}{check_result['count']:>10} issue(s)")
    print("=" * 55)