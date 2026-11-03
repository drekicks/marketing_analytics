"""get_campaign_data() must reload after the cache is cleared, so a running
app picks up campaigns added to the database (e.g. by the weekly job)."""

import pandas as pd

from app.utils import data_loader


def _write_demo(directory, campaign_ids):
    pd.DataFrame({"campaign_id": campaign_ids}).to_csv(directory / "campaign_summary.csv", index=False)
    pd.DataFrame({"campaign_id": campaign_ids}).to_csv(directory / "campaign_segment_summary.csv", index=False)
    pd.DataFrame({"campaign_id": campaign_ids}).to_csv(directory / "campaign_goals.csv", index=False)
    pd.DataFrame({"campaign_id": campaign_ids, "campaign_name": campaign_ids}).to_csv(
        directory / "unique_campaigns.csv", index=False
    )


def test_get_campaign_data_returns_all_datasets():
    data = data_loader.get_campaign_data()
    for frame in (data.summary, data.segment, data.goals, data.unique_campaigns):
        assert isinstance(frame, pd.DataFrame) and not frame.empty


def test_new_campaign_appears_after_cache_clear(tmp_path, monkeypatch):
    monkeypatch.setattr(data_loader, "DEMO_DATA_DIR", tmp_path)
    data_loader.clear_campaign_data_cache()
    try:
        _write_demo(tmp_path, ["CMP-2026-004"])
        assert data_loader.get_campaign_data().unique_campaigns["campaign_id"].tolist() == ["CMP-2026-004"]

        _write_demo(tmp_path, ["CMP-2026-004", "CMP-2026-005"])
        data_loader.clear_campaign_data_cache()
        assert "CMP-2026-005" in data_loader.get_campaign_data().unique_campaigns["campaign_id"].tolist()
    finally:
        monkeypatch.undo()
        data_loader.clear_campaign_data_cache()


def test_unsupported_data_source(monkeypatch):
    monkeypatch.setattr(data_loader, "DATA_SOURCE", "excel")
    try:
        data_loader.get_campaign_data()
    except ValueError as error:
        assert "Unsupported DATA_SOURCE" in str(error)
    else:
        raise AssertionError("expected ValueError")
