import csv
import random
from pathlib import Path

RANDOM_SEED = 42


def main() -> None:
    rng = random.Random(RANDOM_SEED)

    # Build paths from THIS file location (works no matter where you run from)
    project_root = Path(__file__).resolve().parents[2]
    conversion_path = project_root / "app" / "generation" / "conversion_rates.csv"
    segmentation_path = project_root / "data" / "customer_segmentation.csv"
    output_path = project_root / "data" / "campaign_results.csv"

    conversion_lookup = {}
    with conversion_path.open(newline="", encoding="utf-8") as conversion_file:
        conversion_reader = csv.DictReader(conversion_file)
        for row in conversion_reader:
            conversion_lookup[row["market_segment"]] = {
                "test_conversion": float(row["test_conversion"]),
                "control_conversion": float(row["control_conversion"]),
            }

    campaign_id = "CMP-2026-001"
    campaign_name = "Summer Retention Offer"
    campaign_start_date = "2026-07-01"
    campaign_end_date = "2026-07-31"

    ordered_columns = [
        "customer_id",
        "customer_segment",
        "campaign_id",
        "campaign_name",
        "treatment_group",
        "contacted_flag",
        "response_flag",
        "conversion_flag",
        "campaign_revenue",
        "contact_cost",
        "offer_cost",
        "campaign_start_date",
        "campaign_end_date",
    ]

    segment_rows = {}
    with segmentation_path.open(newline="", encoding="utf-8-sig") as segmentation_file:
        segmentation_reader = csv.DictReader(segmentation_file)
        for row in segmentation_reader:
            customer_segment = row["market_segment"]
            if customer_segment not in segment_rows:
                segment_rows[customer_segment] = []
            segment_rows[customer_segment].append(row)

    records = []
    for customer_segment in sorted(segment_rows):
        rows_in_segment = segment_rows[customer_segment]
        rng.shuffle(rows_in_segment)

        segment_size = len(rows_in_segment)
        test_count = round(segment_size * 0.8)

        for index, row in enumerate(rows_in_segment):
            customer_id = int(row["customer_id"])
            rev_per_rentals = float(row["rev_per_rentals"])
            campaign_rentals = rng.choices([1, 2, 3], weights=[3, 2, 1], k=1)[0]

            treatment_group = "TEST" if index < test_count else "CONTROL"
            contacted_flag = "Y" if treatment_group == "TEST" else "N"

            segment_rates = conversion_lookup[customer_segment]
            if treatment_group == "TEST":
                response_probability = float(segment_rates["test_conversion"])
            else:
                response_probability = float(segment_rates["control_conversion"])

            response_flag = "Y" if rng.random() < response_probability else "N"
            conversion_flag = "Y" if response_flag == "Y" and rng.random() < 0.7 else "N"

            campaign_revenue = rev_per_rentals * campaign_rentals if conversion_flag == "Y" else 0.0
            offer_cost = 1.00 if conversion_flag == "Y" and treatment_group =="TEST" else 0.0
            contact_cost = .30 if contacted_flag == "Y" else 0.0

            records.append(
                {
                    "campaign_id": campaign_id,
                    "campaign_name": campaign_name,
                    "customer_id": customer_id,
                    "customer_segment": customer_segment,
                    "treatment_group": treatment_group,
                    "contacted_flag": contacted_flag,
                    "response_flag": response_flag,
                    "conversion_flag": conversion_flag,
                    "campaign_revenue": f"{campaign_revenue:.2f}",
                    "contact_cost": f"{contact_cost:.2f}",
                    "offer_cost": f"{offer_cost:.2f}",
                    "campaign_start_date": campaign_start_date,
                    "campaign_end_date": campaign_end_date,
                }
            )

    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=ordered_columns)
        writer.writeheader()
        writer.writerows(records)


if __name__ == "__main__":
    main()