# from app.utils.database import get_database_engine
from app.utils.file_utils import load_sql_extracts, file_export
import app.utils.data_validation as validation


def export_customer():
    # db_conn = get_database_engine()

    query = load_sql_extracts(["customer_segmentation"])

    df = query["customer_segmentation"]

    results = validation.validate_customer_segmentation_output(df)

    validation.print_validation_summary(results)

    file_export(df,"customer_segmentation.csv")


if __name__ == "__main__":
    export_customer()