from app.utils import database
from app.utils.file_utils import load_sql_extracts, file_export
import app.utils.data_validation as validation


db_conn = database.engine

query = load_sql_extracts(["03_customer_extract"])

df = query["03_customer_extract"]
# print(df.head(5))

results = validation.validate_customer_data(df)

validation.print_validation_summary(results)

file_export(df,"customer_extract.csv")


