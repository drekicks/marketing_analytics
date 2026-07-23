from app.utils import database
from app.utils.file_utils import load_sql_extracts, file_export
import app.utils.data_validation as validation


db_conn = database.engine

query = load_sql_extracts(["customer_segmentation"])

df = query["customer_segmentation"]
# print(df.head(5))

results = validation.validate_customer_segmentation_output(df)

validation.print_validation_summary(results)

file_export(df,"customer_segmentation.csv")