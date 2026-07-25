import pandas as pd

from app.utils import database
import app.utils.data_validation as validation
from app.utils.file_utils import load_sql_extracts, file_export

db_conn = database.engine

df = pd.read_sql("select * from public.campaign_results", db_conn)

results = validation.customer_lvl_validation(df)

validation.print_validation_summary(results, title="CUSTOMER-LEVEL CAMPAIGN VALIDATION")

has_customer_level_errors = any(
    check_result["count"] > 0
    for check_name, check_result in results.items()
    if check_name != "_dataset_shape"
)

if not has_customer_level_errors:
    performance_query = load_sql_extracts(["campaign_performance_summary"])
    performance_df = performance_query["campaign_performance_summary"]
    performance_results = validation.campaign_performance_validation(performance_df)
    validation.print_validation_summary(performance_results, title="CAMPAIGN PERFORMANCE VALIDATION")
    segment_query = load_sql_extracts(["campaign_segment_summary"])
    segment_df = segment_query["campaign_segment_summary"]
    analytic_query = load_sql_extracts(["analytic_layer"])
    analytic_df = analytic_query["analytic_layer"]
    unique_campaigns_query = load_sql_extracts(["unique_campaigns_list"])
    unique_campaigns_df = unique_campaigns_query["unique_campaigns_list"]
    # Export summary file
    file_export(performance_df,"campaign_performance_summary.csv")
    file_export(segment_df,"campaign_segment_summary.csv")
    file_export(analytic_df,"campaign_analytic_layer.csv")
    file_export(unique_campaigns_df,"unique_campaigns.csv")