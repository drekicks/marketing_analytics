"""
Generate one random synthetic campaign and load it into Neon.

Run from the repo root (weekly via .github/workflows/weekly_campaign.yml):
    python -m tools.synthetic_data_creation.campaign_generation [--dry-run] [--seed N]

Each run:
1. Reads customers from public.customer_segment and per-segment conversion
   rates from conversion_rates.csv (next to this file).
2. Picks a random audience of at least MIN_AUDIENCE customers, sampled from
   each market segment in proportion to its share, split 80% TEST / 20% CONTROL.
3. Jitters each segment's baseline rate and lift so campaigns differ, then simulates
   response, conversion, revenue and costs per customer.
4. Builds exactly one goal row for the campaign.
5. Replaces any rows for that campaign_id in public.campaign_results and
   public.campaign_goals, in one transaction.

Afterwards run `dbt build --target neon` so the marts pick up the campaign.

The rates in conversion_rates.csv are FINAL conversion rates. Response is
drawn at rate / CONVERSION_GIVEN_RESPONSE, and that share of responders
converts, so the expected conversion rate equals the file's rate. (The old
script used the file's rate as the response rate, so realized conversion
came out at 0.7x the file.)

The script uses only app.utils.database, not app.config.settings, so it does
not need the OpenAI environment variables.
"""

from __future__ import annotations

import argparse
import csv
import os
import random
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

RATES_PATH = Path(__file__).resolve().parent / "conversion_rates.csv"

MARKET_SEGMENTS = ("Champion", "Churn Watchlist", "Growth", "Win-Back")
MIN_AUDIENCE = 5000
TEST_SHARE = 0.8
CONVERSION_GIVEN_RESPONSE = 0.7
JITTER_RANGE = (0.8, 1.2)       # scales the CONTROL (baseline) rate
LIFT_JITTER_RANGE = (0.5, 1.5)  # scales the TEST - CONTROL lift
MAX_RATE = 0.95
RENTAL_CHOICES = ([1, 2, 3], [3, 2, 1])  # values, weights
CONTACT_COST = 0.10
OFFER_COST = 0.50
BUDGET_FACTOR_RANGE = (1.1, 1.5)
DURATION_DAYS = (30, 45, 60)

CAMPAIGN_ID_PATTERN = re.compile(r"^CMP-(\d{4})-(\d{3})$")

# Raw column names, as read by marketing_analytics_dbt/models/staging/stg_campaign_results.sql.
RESULT_COLUMNS = [
    "customer_id",
    "customer_segment",
    "campaign_id",
    "campaign_name",
    "treatment_grp",
    "contacted_flg",
    "response_flg",
    "cnvrsn_flg",
    "cmpgn_rvn",
    "contact_cost",
    "offer_cost",
    "start_date",
    "end_date",
    "channel",
    "updated_at",
]

GOAL_COLUMNS = [
    "campaign_id",
    "campaign_name",
    "campaign_goal",
    "offer",
    "channel",
    "duration",
    "budget",
    "target_kpi",
    "secondary_kpi",
    "audience",
]

CHANNELS = {"Email": "EM", "Paid Media": "PM", "Outbound": "TM", "SMS": "SMS"}
OFFERS = ("5% off", "10% off", "15% off", "20% off", "Free rental")

# Goal, KPIs, audience description and name themes that fit together.
GOAL_TEMPLATES = (
    {
        "campaign_goal": "Acquire new customers",
        "target_kpi": "Incremental Conversions",
        "secondary_kpi": "Marketing ROI",
        "audience": "New",
        "themes": ("Welcome Offer", "Win Big Offer", "First Rental"),
    },
    {
        "campaign_goal": "Retain Customers",
        "target_kpi": "Absolute Lift",
        "secondary_kpi": "Test Conversion Rate",
        "audience": "Existing Customers",
        "themes": ("Retention Offer", "Loyalty Thank You", "Stay With Us"),
    },
    {
        "campaign_goal": "Increase Revenue",
        "target_kpi": "Campaign Revenue",
        "secondary_kpi": "Marketing ROI",
        "audience": "Existing Customers",
        "themes": ("Upsell Push", "Bundle Deal", "Premium Picks"),
    },
    {
        "campaign_goal": "Reactivate lapsed customers",
        "target_kpi": "Incremental Revenue",
        "secondary_kpi": "Absolute Lift",
        "audience": "Lapsed Customers",
        "themes": ("Reactivation", "We Miss You", "Come Back Offer"),
    },
)


@dataclass(frozen=True)
class SegmentRates:
    test: float
    control: float


@dataclass(frozen=True)
class CampaignSpec:
    campaign_id: str
    campaign_name: str
    channel: str
    offer: str
    duration_days: int
    start_date: date
    end_date: date
    goal_template: dict


@dataclass
class GeneratedCampaign:
    spec: CampaignSpec
    seed: int
    rates: dict[str, SegmentRates]
    results: list[dict]
    goal: dict


# ----------------------------------------------------------------------------
# Pure logic (no database); covered by tests/test_campaign_generation.py
# ----------------------------------------------------------------------------

def load_rates(path: Path = RATES_PATH) -> dict[str, SegmentRates]:
    """Read and validate the per-segment conversion rates."""
    rates: dict[str, SegmentRates] = {}

    with path.open(newline="", encoding="utf-8-sig") as rates_file:
        for row in csv.DictReader(rates_file):
            segment = row["market_segment"].strip()
            test = float(row["test_conversion"])
            control = float(row["control_conversion"])

            if not (0 <= control <= test <= 1):
                raise ValueError(
                    f"Rates for {segment} must satisfy 0 <= control <= test <= 1 "
                    f"(got test={test}, control={control})."
                )
            rates[segment] = SegmentRates(test=test, control=control)

    missing = set(MARKET_SEGMENTS) - set(rates)
    if missing:
        raise ValueError(f"{path.name} is missing segments: {', '.join(sorted(missing))}")

    return rates


def jitter_rates(
    rates: dict[str, SegmentRates],
    rng: random.Random,
    jitter_range: tuple[float, float] = JITTER_RANGE,
    lift_range: tuple[float, float] = LIFT_JITTER_RANGE,
) -> dict[str, SegmentRates]:
    """
    Vary each segment's rates per campaign.

    The CONTROL baseline and the TEST lift are scaled separately, so a
    segment with positive lift in the file keeps positive lift (jittering
    TEST and CONTROL independently could erase it).
    """
    jittered = {}
    for segment, segment_rates in rates.items():
        control = segment_rates.control * rng.uniform(*jitter_range)
        lift = (segment_rates.test - segment_rates.control) * rng.uniform(*lift_range)
        test = min(MAX_RATE, control + lift)
        control = min(control, test)
        jittered[segment] = SegmentRates(test=round(test, 4), control=round(control, 4))
    return jittered


def allocate_audience(
    segment_sizes: dict[str, int],
    audience_size: int,
) -> dict[str, int]:
    """
    Split audience_size across segments in proportion to their sizes.

    Every segment gets at least one customer and never more than it has; the
    rounding remainder goes to the largest segment.
    """
    total = sum(segment_sizes.values())
    if audience_size > total:
        raise ValueError(f"Audience {audience_size} is larger than the customer base ({total}).")

    allocation = {
        segment: min(size, max(1, round(audience_size * size / total)))
        for segment, size in segment_sizes.items()
    }

    largest = max(segment_sizes, key=segment_sizes.get)
    allocation[largest] += audience_size - sum(allocation.values())

    if not 1 <= allocation[largest] <= segment_sizes[largest]:
        raise ValueError("Could not allocate the audience across segments.")

    return allocation


def next_campaign_id(existing_ids: list[str], year: int) -> str:
    """Next CMP-<year>-NNN after the highest existing number for that year."""
    numbers = [
        int(match.group(2))
        for campaign_id in existing_ids
        if (match := CAMPAIGN_ID_PATTERN.match(campaign_id or "")) and int(match.group(1)) == year
    ]
    next_number = max(numbers, default=0) + 1
    if next_number > 999:
        raise ValueError(f"No campaign IDs left for {year}.")
    return f"CMP-{year}-{next_number:03d}"


def season_for(day: date) -> str:
    return ("Winter", "Spring", "Summer", "Fall")[(day.month % 12) // 3]


def build_spec(existing_ids: list[str], run_date: date, rng: random.Random) -> CampaignSpec:
    """Choose campaign ID, name, channel, offer and dates."""
    template = rng.choice(GOAL_TEMPLATES)
    channel = rng.choice(list(CHANNELS))
    duration_days = rng.choice(DURATION_DAYS)
    end_date = run_date - timedelta(days=1)
    start_date = end_date - timedelta(days=duration_days - 1)

    return CampaignSpec(
        campaign_id=next_campaign_id(existing_ids, start_date.year),
        campaign_name=f"{season_for(start_date)} {rng.choice(template['themes'])} {CHANNELS[channel]}",
        channel=channel,
        offer=rng.choice(OFFERS),
        duration_days=duration_days,
        start_date=start_date,
        end_date=end_date,
        goal_template=template,
    )


def simulate_customers(
    customers: list[dict],
    spec: CampaignSpec,
    rates: dict[str, SegmentRates],
    rng: random.Random,
    updated_at: datetime,
    min_audience: int = MIN_AUDIENCE,
) -> list[dict]:
    """
    Sample the audience and simulate one result row per customer.

    customers: dicts with customer_id, market_segment, rev_per_rentals.
    """
    by_segment: dict[str, list[dict]] = {}
    for customer in customers:
        by_segment.setdefault(customer["market_segment"], []).append(customer)

    unknown = set(by_segment) - set(rates)
    if unknown:
        raise ValueError(f"No conversion rates for segments: {', '.join(sorted(unknown))}")

    total = sum(len(rows) for rows in by_segment.values())
    if total < min_audience:
        raise ValueError(f"Only {total} customers available; the minimum audience is {min_audience}.")

    audience_size = rng.randint(min_audience, total)
    allocation = allocate_audience({s: len(r) for s, r in by_segment.items()}, audience_size)

    results = []
    for segment in sorted(by_segment):
        sampled = rng.sample(by_segment[segment], allocation[segment])
        test_count = round(len(sampled) * TEST_SHARE)

        for index, customer in enumerate(sampled):
            is_test = index < test_count
            conversion_rate = rates[segment].test if is_test else rates[segment].control
            response_probability = min(1.0, conversion_rate / CONVERSION_GIVEN_RESPONSE)

            responded = rng.random() < response_probability
            converted = responded and rng.random() < CONVERSION_GIVEN_RESPONSE
            rentals = rng.choices(*RENTAL_CHOICES, k=1)[0]

            revenue = float(customer["rev_per_rentals"] or 0) * rentals if converted else 0.0

            results.append({
                "customer_id": int(customer["customer_id"]),
                "customer_segment": segment,
                "campaign_id": spec.campaign_id,
                "campaign_name": spec.campaign_name,
                "treatment_grp": "TEST" if is_test else "CONTROL",
                "contacted_flg": "Y" if is_test else "N",
                "response_flg": "Y" if responded else "N",
                "cnvrsn_flg": "Y" if converted else "N",
                "cmpgn_rvn": round(revenue, 2),
                "contact_cost": CONTACT_COST if is_test else 0.0,
                "offer_cost": OFFER_COST if is_test and converted else 0.0,
                "start_date": spec.start_date,
                "end_date": spec.end_date,
                "channel": spec.channel,
                "updated_at": updated_at,
            })

    return results


def build_goal(spec: CampaignSpec, results: list[dict], rng: random.Random) -> dict:
    """One goal row for the campaign; budget is the actual cost plus headroom."""
    total_cost = sum(row["contact_cost"] + row["offer_cost"] for row in results)
    budget = max(100.0, round(total_cost * rng.uniform(*BUDGET_FACTOR_RANGE), -2))
    template = spec.goal_template

    return {
        "campaign_id": spec.campaign_id,
        "campaign_name": spec.campaign_name,
        "campaign_goal": template["campaign_goal"],
        "offer": spec.offer,
        "channel": spec.channel,
        "duration": f"{spec.duration_days} days",
        "budget": budget,
        "target_kpi": template["target_kpi"],
        "secondary_kpi": template["secondary_kpi"],
        "audience": template["audience"],
    }


def generate_campaign(
    customers: list[dict],
    base_rates: dict[str, SegmentRates],
    existing_ids: list[str],
    run_date: date,
    seed: int | None = None,
    jitter: bool = True,
) -> GeneratedCampaign:
    """Build a full campaign (results + goal). Random unless a seed is given."""
    if seed is None:
        seed = random.SystemRandom().randrange(2**32)
    rng = random.Random(seed)

    spec = build_spec(existing_ids, run_date, rng)
    rates = jitter_rates(base_rates, rng) if jitter else dict(base_rates)
    updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    results = simulate_customers(customers, spec, rates, rng, updated_at)
    goal = build_goal(spec, results, rng)

    return GeneratedCampaign(spec=spec, seed=seed, rates=rates, results=results, goal=goal)


def summarize(campaign: GeneratedCampaign) -> str:
    """Readable per-segment summary for logs."""
    spec = campaign.spec
    lines = [
        f"{spec.campaign_id} | {spec.campaign_name} | {spec.channel} | "
        f"{spec.start_date} to {spec.end_date} | seed={campaign.seed}",
        f"Goal: {campaign.goal['campaign_goal']} | offer {campaign.goal['offer']} | "
        f"budget ${campaign.goal['budget']:,.0f}",
        f"Audience: {len(campaign.results)}",
    ]
    for segment in sorted(campaign.rates):
        for group in ("TEST", "CONTROL"):
            rows = [r for r in campaign.results
                    if r["customer_segment"] == segment and r["treatment_grp"] == group]
            if not rows:
                continue
            target = campaign.rates[segment].test if group == "TEST" else campaign.rates[segment].control
            actual = sum(r["cnvrsn_flg"] == "Y" for r in rows) / len(rows)
            lines.append(f"  {segment:<16} {group:<7} n={len(rows):>5}  "
                         f"target={target:.3f}  actual={actual:.3f}")
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# Database I/O
# ----------------------------------------------------------------------------

def _table_columns(connection, table: str) -> set[str]:
    from sqlalchemy import text

    rows = connection.execute(
        text("select column_name from information_schema.columns "
             "where table_schema = 'public' and table_name = :table"),
        {"table": table},
    )
    return {row[0] for row in rows}


def _require_columns(connection, table: str, required: list[str]) -> None:
    columns = _table_columns(connection, table)
    if not columns:
        raise ValueError(
            f"public.{table} does not exist. For campaign_goals, run "
            "tools/synthetic_data_creation/create_campaign_goals_table.sql once."
        )
    missing = [column for column in required if column not in columns]
    if missing:
        raise ValueError(f"public.{table} is missing columns: {', '.join(missing)}")


def fetch_inputs(engine) -> tuple[list[dict], list[str]]:
    """Customers from public.customer_segment and every existing campaign ID."""
    from sqlalchemy import text

    with engine.connect() as connection:
        _require_columns(connection, "customer_segment",
                         ["customer_id", "market_segment", "rev_per_rentals"])
        _require_columns(connection, "campaign_results", RESULT_COLUMNS)
        _require_columns(connection, "campaign_goals", GOAL_COLUMNS)

        customers = [
            dict(row._mapping)
            for row in connection.execute(text(
                "select customer_id, market_segment, rev_per_rentals "
                "from public.customer_segment where market_segment is not null"
            ))
        ]
        existing_ids = [
            row[0]
            for row in connection.execute(text(
                "select campaign_id from public.campaign_results "
                "union select campaign_id from public.campaign_goals"
            ))
        ]
    return customers, existing_ids


def load_campaign(engine, campaign: GeneratedCampaign) -> None:
    """Replace this campaign's rows in both raw tables, in one transaction."""
    from sqlalchemy import text

    def insert_sql(table: str, columns: list[str]):
        return text(
            f"insert into public.{table} ({', '.join(columns)}) "
            f"values ({', '.join(':' + c for c in columns)})"
        )

    params = {"campaign_id": campaign.spec.campaign_id}
    with engine.begin() as connection:
        connection.execute(text("delete from public.campaign_results where campaign_id = :campaign_id"), params)
        connection.execute(text("delete from public.campaign_goals where campaign_id = :campaign_id"), params)
        connection.execute(insert_sql("campaign_results", RESULT_COLUMNS), campaign.results)
        connection.execute(insert_sql("campaign_goals", GOAL_COLUMNS), campaign.goal)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--seed", type=int, help="Reproduce a previous run (default: random).")
    parser.add_argument("--dry-run", action="store_true", help="Generate and print, but do not write to Neon.")
    parser.add_argument("--run-date", type=date.fromisoformat, default=date.today(),
                        help="Pretend today is this date (YYYY-MM-DD).")
    args = parser.parse_args(argv)

    missing = [name for name in ("DB_HOST", "DB_NAME", "DB_USER") if not os.getenv(name)]
    if missing:
        raise ValueError(
            f"Missing database settings: {', '.join(missing)}. Set them in .env locally, "
            "or as repository secrets for the GitHub workflow."
        )

    from app.utils.database import get_database_engine

    engine = get_database_engine()
    customers, existing_ids = fetch_inputs(engine)
    campaign = generate_campaign(customers, load_rates(), existing_ids, args.run_date, seed=args.seed)

    print(summarize(campaign))

    if args.dry_run:
        print("Dry run: nothing written.")
        return

    load_campaign(engine, campaign)
    print(f"Loaded {len(campaign.results)} result rows and 1 goal row for {campaign.spec.campaign_id}. "
          "Next: dbt build --target neon")


if __name__ == "__main__":
    main()
