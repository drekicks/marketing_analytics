import pandas as pd
from datetime import datetime


# =============================================================================
# Validator 1: CRM-style customer extract
# (email, country, total_revenue, most_recent_rental_date, customer_tier, etc.)
# =============================================================================
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


# =============================================================================
# Validator 2: Customer segmentation dataset
# (customer_extract.csv + rental_count_per_category.csv + repeat_engagement_categories.csv)
# =============================================================================
def validate_segmentation_data(
    customer_df: pd.DataFrame,
    category_df: pd.DataFrame,
    category_engagement_df: pd.DataFrame,
    valid_tiers: list = None,
) -> dict:
    results = {}

    results["_dataset_shape"] = {
        "row_count": customer_df.shape[0],
        "column_count": customer_df.shape[1],
        "columns": list(customer_df.columns),
    }

    # --- Duplicate customer_id ---
    dup_mask = customer_df.duplicated(subset="customer_id", keep=False)
    results["duplicate_customer_ids"] = {
        "count": dup_mask.sum(), "rows": customer_df[dup_mask].sort_values("customer_id")
    }

    # --- Non-positive total_payments ---
    bad_payments_mask = customer_df["total_payments"] <= 0
    results["non_positive_payments"] = {
        "count": bad_payments_mask.sum(), "rows": customer_df[bad_payments_mask]
    }

    # --- Dates after the dataset's own snapshot date ---
    # NOTE: this data is historical (2005), so datetime.now() is meaningless here —
    # "today" for validation purposes is the latest rental date actually in the extract.
    last_rentals = pd.to_datetime(customer_df["last_rental"], errors="coerce")
    snapshot_date = last_rentals.max()
    future_mask = last_rentals > snapshot_date
    results["dates_after_snapshot"] = {
        "count": future_mask.sum(), "rows": customer_df[future_mask]
    }

    # --- first_rental after last_rental (impossible ordering) ---
    first_rentals = pd.to_datetime(customer_df["first_rental"], errors="coerce")
    bad_order_mask = first_rentals > last_rentals
    results["first_rental_after_last_rental"] = {
        "count": bad_order_mask.sum(), "rows": customer_df[bad_order_mask]
    }

    # --- days_since_last_rental can't exceed customer_tenure_days ---
    recency_gt_tenure_mask = customer_df["days_since_last_rental"] > customer_df["customer_tenure_days"]
    results["recency_exceeds_tenure"] = {
        "count": recency_gt_tenure_mask.sum(), "rows": customer_df[recency_gt_tenure_mask]
    }

    # --- unique_films can't exceed implied total rentals (total_payments / rev_per_rentals) ---
    # rev_per_rentals is rounded to 2 decimals in the extract, so allow 0.5 rental of
    # tolerance for rounding noise before flagging as a genuine issue.
    implied_total_rentals = customer_df["total_payments"] / customer_df["rev_per_rentals"].replace(0, pd.NA)
    unique_exceeds_mask = (customer_df["unique_films"] - implied_total_rentals) > 0.5
    results["unique_films_exceeds_rentals"] = {
        "count": unique_exceeds_mask.fillna(False).sum(),
        "rows": customer_df[unique_exceeds_mask.fillna(False)],
    }

    # --- customer_tier value check ---
    if valid_tiers is None:
        valid_tiers = ["High Value", "Medium Value", "Low Value"]
    invalid_tier_mask = ~customer_df["customer_tier"].isin(valid_tiers)
    results["invalid_customer_tier"] = {
        "count": invalid_tier_mask.sum(), "rows": customer_df[invalid_tier_mask]
    }

    # --- Tier proportion drift: NTILE(10) should yield ~10% High / 40% Medium / 50% Low ---
    tier_pct = customer_df["customer_tier"].value_counts(normalize=True)
    expected = {"High Value": 0.10, "Medium Value": 0.40, "Low Value": 0.50}
    drift = {tier: round(tier_pct.get(tier, 0) - expected[tier], 3) for tier in expected}
    drift_flagged = {t: d for t, d in drift.items() if abs(d) > 0.03}  # >3pt drift
    results["tier_proportion_drift"] = {"count": len(drift_flagged), "rows": drift_flagged}

    # --- Cross-file: customer coverage between extract and category rentals ---
    extract_ids = set(customer_df["customer_id"])
    category_ids = set(category_df["customer_id"])
    missing_from_category = extract_ids - category_ids
    missing_from_extract = category_ids - extract_ids
    results["customers_missing_category_rows"] = {
        "count": len(missing_from_category), "rows": sorted(missing_from_category)
    }
    results["category_customers_missing_from_extract"] = {
        "count": len(missing_from_extract), "rows": sorted(missing_from_extract)
    }

    # --- Cross-file: revenue reconciliation between customer_extract and category rentals ---
    cat_revenue = category_df.groupby("customer_id")["revenue_in_category"].sum()
    merged = customer_df.set_index("customer_id")["total_payments"].to_frame().join(cat_revenue)
    revenue_diff = (merged["total_payments"] - merged["revenue_in_category"]).abs()
    revenue_mismatch_mask = revenue_diff > 1.00  # $1 tolerance for rounding
    results["revenue_mismatch_across_files"] = {
        "count": revenue_mismatch_mask.fillna(False).sum(),
        "rows": merged[revenue_mismatch_mask.fillna(False)],
    }

    # --- Category rentals file: no duplicate customer x category rows ---
    dup_cat_mask = category_df.duplicated(subset=["customer_id", "category"], keep=False)
    results["duplicate_customer_category_rows"] = {
        "count": dup_cat_mask.sum(),
        "rows": category_df[dup_cat_mask].sort_values(["customer_id", "category"]),
    }

    # --- Category rentals file: rentals_in_category must be positive ---
    non_positive_cat_rentals_mask = category_df["rentals_in_category"] <= 0
    results["non_positive_category_rentals"] = {
        "count": non_positive_cat_rentals_mask.sum(), "rows": category_df[non_positive_cat_rentals_mask]
    }

    # --- Category breadth sanity: can't touch more categories than exist in the catalog ---
    breadth = category_df.groupby("customer_id")["category"].nunique()
    n_categories = category_df["category"].nunique()
    over_breadth = breadth[breadth > n_categories]
    results["category_breadth_exceeds_max"] = {"count": len(over_breadth), "rows": over_breadth}

    # --- Category engagement file: category set should match the rentals file, pct in [0,100] ---
    expected_cats = set(category_df["category"].unique())
    engagement_cats = set(category_engagement_df["category"].unique())
    mismatched_cats = expected_cats ^ engagement_cats  # symmetric difference
    results["category_engagement_category_mismatch"] = {
        "count": len(mismatched_cats), "rows": sorted(mismatched_cats)
    }
    pct_out_of_range_mask = (category_engagement_df["pct_repeat_engaged"] < 0) | (
        category_engagement_df["pct_repeat_engaged"] > 100
    )
    results["pct_repeat_engaged_out_of_range"] = {
        "count": pct_out_of_range_mask.sum(), "rows": category_engagement_df[pct_out_of_range_mask]
    }

    return results


# =============================================================================
# Validator 3: Consolidated segmentation query output
# (04_customer_segmentation.sql -- one row per customer, all tiers/flags/
# primary_segment already computed by the query. No cross-file checks
# needed here since the joins already happened in SQL; instead this checks
# whether the SQL logic itself produced internally consistent output.)
# =============================================================================
def validate_customer_segmentation_output(df: pd.DataFrame) -> dict:
    results = {}

    results["_dataset_shape"] = {
        "row_count": df.shape[0],
        "column_count": df.shape[1],
        "columns": list(df.columns),
    }

    # --- Duplicate customer_id ---
    dup_mask = df.duplicated(subset="customer_id", keep=False)
    results["duplicate_customer_ids"] = {
        "count": dup_mask.sum(), "rows": df[dup_mask].sort_values("customer_id")
    }

    # --- Non-positive total_payments ---
    bad_payments_mask = df["total_payments"] <= 0
    results["non_positive_payments"] = {"count": bad_payments_mask.sum(), "rows": df[bad_payments_mask]}

    # --- days_since_last_rental can't exceed customer_tenure_days ---
    recency_gt_tenure_mask = df["days_since_last_rental"] > df["customer_tenure_days"]
    results["recency_exceeds_tenure"] = {
        "count": recency_gt_tenure_mask.sum(), "rows": df[recency_gt_tenure_mask]
    }

    # --- customer_tier must be one of the three expected values ---
    valid_tiers = ["High Value", "Medium Value", "Low Value"]
    invalid_tier_mask = ~df["customer_tier"].isin(valid_tiers)
    results["invalid_customer_tier"] = {"count": invalid_tier_mask.sum(), "rows": df[invalid_tier_mask]}

    # --- recency_segment must be one of the two expected values ---
    valid_recency = ["Active", "Lapsed", "Pre-Lapsed"]
    invalid_recency_mask = ~df["recency_segment"].isin(valid_recency)
    results["invalid_recency_segment"] = {"count": invalid_recency_mask.sum(), "rows": df[invalid_recency_mask]}

    # --- engagement_segment must be one of the three expected values ---
    valid_engagement = ["Very Low Engagement", "Low Engagement", "Moderate Engagement", "High Engagement", "Very High Engagement"]
    invalid_engagement_mask = ~df["engagement_segment"].isin(valid_engagement)
    results["invalid_engagement_segment"] = {
        "count": invalid_engagement_mask.sum(), "rows": df[invalid_engagement_mask]
    }

    # --- categories_touched must be between 1 and 16 (Sakila's category count) ---
    bad_breadth_mask = (df["categories_touched"] < 1) | (df["categories_touched"] > 16)
    results["category_breadth_out_of_range"] = {"count": bad_breadth_mask.sum(), "rows": df[bad_breadth_mask]}

    # --- category_engagement_tier should never be null ---
    # (a null here means the LEFT JOIN to category_engagement_final didn't find a
    # matching category name for that customer's top_rental_category -- usually a
    # spelling/casing mismatch between the category_rentals and category_engagement
    # CTEs, or a customer with zero category rental rows entirely)
    null_cat_tier_mask = df["category_engagement_tier"].isna()
    results["null_category_engagement_tier"] = {
        "count": null_cat_tier_mask.sum(), "rows": df[null_cat_tier_mask]
    }

    # --- top_rental_category should never be null if categories_touched > 0 ---
    null_top_cat_mask = df["top_rental_category"].isna() & (df["categories_touched"] > 0)
    results["null_top_category_with_rentals"] = {
        "count": null_top_cat_mask.sum(), "rows": df[null_top_cat_mask]
    }

    # --- Tier proportion drift: NTILE(10) should yield ~10% High / 40% Medium / 50% Low ---
    tier_pct = df["customer_tier"].value_counts(normalize=True)
    expected = {"High Value": 0.10, "Medium Value": 0.40, "Low Value": 0.50}
    drift = {tier: round(tier_pct.get(tier, 0) - expected[tier], 3) for tier in expected}
    drift_flagged = {t: d for t, d in drift.items() if abs(d) > 0.03}
    results["tier_proportion_drift"] = {"count": len(drift_flagged), "rows": drift_flagged}

    # --- primary_segment must be one of the known labels, never null ---
    valid_segments = [
        "Champion", "Win-Back VIP", "Win-Back Growth", "Win-Back Reactivation",
        "Upsell - Scale", "Upsell - Core","Engagement Growth",
        "Category Expansion", "Churn Watchlist", "Maintain"
    ]
    invalid_segment_mask = ~df["primary_segment"].isin(valid_segments)
    results["invalid_primary_segment"] = {"count": invalid_segment_mask.sum(), "rows": df[invalid_segment_mask]}

    # --- primary_segment must agree with the priority-ordered flags ---
    # Re-derives what primary_segment SHOULD be from the is_* flags using the same
    # priority order as the SQL CASE statement, and flags any row where the SQL
    # output disagrees with that logic (catches CASE-statement typos/reordering bugs).
    def expected_segment(row):
        if row["is_champion"]:
            return "Champion"
        if row["is_winback_vip"]:
            return "Win-Back VIP"
        if row["is_winback_growth"]:
            return "Win-Back Growth"
        if row["is_winback_reactivation"]:
            return "Win-Back Reactivation"
        if row["is_upsell_scale"]:
            return "Upsell - Scale"
        if row["is_upsell_core"]:
            return "Upsell - Core"
        if row["is_engagement_growth"]:
            return "Engagement Growth"
        # if row["is_narrow_explorer"]:
        #     return "Category Expansion"
        if row["is_churn_watchlist"]:
            return "Churn Watchlist"
        return "Maintain"

    recomputed = df.apply(expected_segment, axis=1)
    segment_mismatch_mask = recomputed != df["primary_segment"]
    results["primary_segment_flag_mismatch"] = {
        "count": segment_mismatch_mask.sum(),
        "rows": df[segment_mismatch_mask][["customer_id", "primary_segment"]].assign(
            expected=recomputed[segment_mismatch_mask]
        ),
    }

    return results


def customer_lvl_validation(df: pd.DataFrame) -> dict:
    results = {}

    results["_dataset_shape"] = {
        "row_count": df.shape[0],
        "column_count": df.shape[1],
        "columns": list(df.columns),
    }

    valid_groups = ["TEST", "CONTROL"]
    invalid_treatment_mask = ~df["treatment_grp"].isin(valid_groups)
    results["invalid_treatment_group"] = {
        "count": invalid_treatment_mask.sum(),
        "rows": df[invalid_treatment_mask],
    }

    control_contacted_mask = (df["treatment_grp"] == "CONTROL") & (df["contacted_flg"] == "Y")
    results["control_contacted"] = {
        "count": control_contacted_mask.sum(),
        "rows": df[control_contacted_mask],
    }

    negative_campaign_revenue_mask = df["cmpgn_rvn"] < 0
    results["negative_campaign_revenue"] = {
        "count": negative_campaign_revenue_mask.sum(),
        "rows": df[negative_campaign_revenue_mask],
    }

    negative_campaign_cost_mask = df["offer_cost"] < 0
    results["negative_campaign_cost"] = {
        "count": negative_campaign_cost_mask.sum(),
        "rows": df[negative_campaign_cost_mask],
    }

    duplicate_customer_mask = df.duplicated(subset="customer_id", keep=False)
    results["duplicate_customer_ids"] = {
        "count": duplicate_customer_mask.sum(),
        "rows": df[duplicate_customer_mask].sort_values("customer_id"),
    }

    conversion_revenue_mismatch_mask = (df["cnvrsn_flg"] == "Y") & (df["cmpgn_rvn"] <= 0)
    results["conversion_with_non_positive_revenue"] = {
        "count": conversion_revenue_mismatch_mask.sum(),
        "rows": df[conversion_revenue_mismatch_mask],
    }

    converted_offer_with_no_cost = (df["cnvrsn_flg"] == "Y") & (df["offer_cost"] <= 0) & (df["treatment_grp"]=="TEST")
    results["converted_offer_with_no_cost"] = {
        "count": converted_offer_with_no_cost.sum(),
        "rows": df[converted_offer_with_no_cost],
    }

    return results


def campaign_performance_validation(df: pd.DataFrame) -> dict:
    results = {}

    results["_dataset_shape"] = {
        "row_count": df.shape[0],
        "column_count": df.shape[1],
        "columns": list(df.columns),
    }

    test_respn_rt_out_of_range = (df["test_respn_rt"] < 0) | (df["test_respn_rt"] > 1)
    results["test_response_rate_out_of_range"] = {
        "count": test_respn_rt_out_of_range.sum(),
        "rows": df[test_respn_rt_out_of_range],
    }

    test_cnvrsn_rt_out_of_range = (df["test_cnvrsn_rt"] < 0) | (df["test_cnvrsn_rt"] > 1)
    results["test_conversion_rate_out_of_range"] = {
        "count": test_cnvrsn_rt_out_of_range.sum(),
        "rows": df[test_cnvrsn_rt_out_of_range],
    }

    cntrl_respn_rt_out_of_range = (df["cntrl_respn_rt"] < 0) | (df["cntrl_respn_rt"] > 1)
    results["control_response_rate_out_of_range"] = {
        "count": cntrl_respn_rt_out_of_range.sum(),
        "rows": df[cntrl_respn_rt_out_of_range],
    }

    cntrl_cnvrsn_rt_out_of_range = (df["cntrl_cnvrsn_rt"] < 0) | (df["cntrl_cnvrsn_rt"] > 1)
    results["control_conversion_rate_out_of_range"] = {
        "count": cntrl_cnvrsn_rt_out_of_range.sum(),
        "rows": df[cntrl_cnvrsn_rt_out_of_range],
    }

    return results


# =============================================================================
# Shared printer — used by all three validators
# =============================================================================
def print_validation_summary(results: dict, title: str = "DATA VALIDATION SUMMARY"):
    print("=" * 59)
    print(title)
    print("=" * 59)
    shape_info = results.get("_dataset_shape")
    if shape_info:
        print(f"{'Row Count':.<40}{shape_info['row_count']:>10}")
        print(f"{'Column Count':.<40}{shape_info['column_count']:>10}")
        print("-" * 59)

    for check_name, check_result in results.items():
        if check_name == "_dataset_shape":
            continue
        label = check_name.replace("_", " ").title()
        print(f"{label:.<40}{check_result['count']:>10} issue(s)")
    print("=" * 59)


if __name__ == "__main__":
    # validate_customer_data(crm_df) -- CRM-style extract (email, country, total_revenue, etc.)

    # validate_segmentation_data(customer_df, category_df, category_engagement_df) --
    # only relevant if you're still pulling the three separate queries (03_customer_extract,
    # rental_count_per_category, repeat_engagement_categories) as three separate files.

    # validate_customer_segmentation_output(df) -- the one to use for 04_customer_segmentation.sql,
    # since that query already consolidates everything into a single output.
    df = pd.read_csv("/home/claude/work/consolidated_segmentation_output.csv")
    seg_output_results = validate_customer_segmentation_output(df)
    print_validation_summary(seg_output_results, title="CUSTOMER SEGMENTATION OUTPUT VALIDATION")