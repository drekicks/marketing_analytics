"""Tests for the weekly synthetic campaign generator (no database)."""

import random
from collections import Counter
from datetime import date

import pytest

from tools.synthetic_data_creation import campaign_generation as cg

SEGMENT_SIZES = {"Champion": 2867, "Growth": 4348, "Churn Watchlist": 2124, "Win-Back": 1260}
RUN_DATE = date(2026, 11, 2)


@pytest.fixture(scope="module")
def customers():
    rng = random.Random(0)
    rows, next_id = [], 1
    for segment, size in SEGMENT_SIZES.items():
        for _ in range(size):
            rows.append({"customer_id": next_id, "market_segment": segment,
                         "rev_per_rentals": round(rng.uniform(1, 5), 2)})
            next_id += 1
    return rows


@pytest.fixture(scope="module")
def rates():
    return cg.load_rates()


@pytest.fixture(scope="module")
def campaign(customers, rates):
    return cg.generate_campaign(customers, rates, ["CMP-2026-004"], RUN_DATE, seed=123)


def test_rates_file_has_all_segments(rates):
    assert set(rates) == set(cg.MARKET_SEGMENTS)
    assert rates["Champion"] == cg.SegmentRates(test=0.4, control=0.33)


def test_load_rates_rejects_control_above_test(tmp_path):
    path = tmp_path / "rates.csv"
    path.write_text("market_segment,test_conversion,control_conversion\n"
                    "Champion,0.2,0.3\nChurn Watchlist,0.2,0.1\nGrowth,0.2,0.1\nWin-Back,0.2,0.1\n")
    with pytest.raises(ValueError, match="Champion"):
        cg.load_rates(path)


def test_audience_meets_minimum_and_covers_every_segment(campaign):
    results = campaign.results
    assert len(results) >= cg.MIN_AUDIENCE
    assert set(r["customer_segment"] for r in results) == set(SEGMENT_SIZES)
    assert len({r["customer_id"] for r in results}) == len(results)


def test_audience_is_proportional(campaign):
    counts = Counter(r["customer_segment"] for r in campaign.results)
    total, base = len(campaign.results), sum(SEGMENT_SIZES.values())
    for segment, size in SEGMENT_SIZES.items():
        assert abs(counts[segment] - total * size / base) <= 2


def test_allocate_audience_sums_exactly():
    for size in (5000, 7777, sum(SEGMENT_SIZES.values())):
        allocation = cg.allocate_audience(SEGMENT_SIZES, size)
        assert sum(allocation.values()) == size
        assert all(1 <= allocation[s] <= SEGMENT_SIZES[s] for s in SEGMENT_SIZES)


def test_too_few_customers_raises(rates):
    few = [{"customer_id": i, "market_segment": "Champion", "rev_per_rentals": 2} for i in range(100)]
    with pytest.raises(ValueError, match="minimum audience"):
        cg.generate_campaign(few, rates, [], RUN_DATE, seed=1)


def test_test_control_split_is_80_20(campaign):
    by_segment = Counter((r["customer_segment"], r["treatment_grp"]) for r in campaign.results)
    for segment in SEGMENT_SIZES:
        n = by_segment[(segment, "TEST")] + by_segment[(segment, "CONTROL")]
        assert by_segment[(segment, "TEST")] == round(n * cg.TEST_SHARE)


def test_exactly_one_goal_matching_results(campaign):
    goal = campaign.goal
    assert set(goal) == set(cg.GOAL_COLUMNS)
    assert all(goal[c] not in (None, "") for c in ("campaign_goal", "target_kpi", "offer", "audience"))
    assert {r["campaign_id"] for r in campaign.results} == {goal["campaign_id"]}
    assert {r["campaign_name"] for r in campaign.results} == {goal["campaign_name"]}
    assert {r["channel"] for r in campaign.results} == {goal["channel"]}
    assert goal["duration"] == f"{campaign.spec.duration_days} days"
    assert goal["budget"] >= 100


def test_result_rows_use_raw_column_names(campaign):
    for row in campaign.results[:50]:
        assert list(row) == cg.RESULT_COLUMNS
        assert row["updated_at"] is not None


def test_cost_rules_match_dbt_tests(campaign):
    for r in campaign.results:
        if r["treatment_grp"] == "CONTROL":
            assert r["contact_cost"] == 0 and r["offer_cost"] == 0 and r["contacted_flg"] == "N"
        else:
            assert r["contact_cost"] > 0 and r["contacted_flg"] == "Y"
            assert (r["offer_cost"] > 0) == (r["cnvrsn_flg"] == "Y")
        if r["cnvrsn_flg"] == "Y":
            assert r["response_flg"] == "Y" and r["cmpgn_rvn"] > 0
        else:
            assert r["cmpgn_rvn"] == 0


def test_dates_end_before_run_date(campaign):
    spec = campaign.spec
    assert spec.end_date == date(2026, 11, 1)
    assert (spec.end_date - spec.start_date).days + 1 == spec.duration_days


def test_jittered_rates_stay_valid(rates):
    rng = random.Random(7)
    for _ in range(200):
        for segment, r in cg.jitter_rates(rates, rng).items():
            assert 0 <= r.control < r.test <= cg.MAX_RATE
            lift = rates[segment].test - rates[segment].control
            assert 0.5 * lift - 1e-3 <= r.test - r.control <= 1.5 * lift + 1e-3


def test_conversion_rate_matches_file_rate(rates):
    """Regression: the old script converted at 0.7x the file's rate."""
    rng = random.Random(42)
    n = 20000
    many = [{"customer_id": i, "market_segment": "Champion", "rev_per_rentals": 3} for i in range(n)]
    spec = cg.build_spec([], RUN_DATE, rng)
    results = cg.simulate_customers(many, spec, {"Champion": rates["Champion"]}, rng,
                                    updated_at=None, min_audience=n)
    for group, expected in (("TEST", 0.40), ("CONTROL", 0.33)):
        rows = [r for r in results if r["treatment_grp"] == group]
        actual = sum(r["cnvrsn_flg"] == "Y" for r in rows) / len(rows)
        assert actual == pytest.approx(expected, abs=0.02)


def test_next_campaign_id():
    existing = ["CMP-2026-003", "CMP-2026-004", "CMP-2025-002", "junk", None]
    assert cg.next_campaign_id(existing, 2026) == "CMP-2026-005"
    assert cg.next_campaign_id(existing, 2027) == "CMP-2027-001"


def test_new_id_does_not_collide(campaign):
    assert campaign.spec.campaign_id == "CMP-2026-005"


def test_runs_are_random_unless_seeded(customers, rates):
    a = cg.generate_campaign(customers, rates, [], RUN_DATE)
    b = cg.generate_campaign(customers, rates, [], RUN_DATE)
    assert a.seed != b.seed
    assert [r["customer_id"] for r in a.results] != [r["customer_id"] for r in b.results]

    c = cg.generate_campaign(customers, rates, [], RUN_DATE, seed=99)
    d = cg.generate_campaign(customers, rates, [], RUN_DATE, seed=99)
    strip = lambda rows: [{k: v for k, v in r.items() if k != "updated_at"} for r in rows]
    assert strip(c.results) == strip(d.results) and c.goal == d.goal
