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


# --- framework-neutral cache ----------------------------------------------


def _frames(campaign_id):
    frame = pd.DataFrame({"campaign_id": [campaign_id]})
    return frame, frame, frame, frame


def test_postgres_data_is_cached_then_reloaded_after_ttl(monkeypatch):
    calls = []
    clock = [1000.0]

    def fake_load():
        calls.append(clock[0])
        return _frames(f"CMP-{len(calls)}")

    monkeypatch.setattr(data_loader, "DATA_SOURCE", "postgres")
    monkeypatch.setattr(data_loader, "load_postgres_data", fake_load)
    monkeypatch.setattr(data_loader.time, "monotonic", lambda: clock[0])
    data_loader.clear_campaign_data_cache()
    try:
        first = data_loader.get_campaign_data()
        clock[0] += data_loader.POSTGRES_CACHE_TTL_SECONDS - 1
        assert data_loader.get_campaign_data() is first
        assert len(calls) == 1

        clock[0] += 2
        reloaded = data_loader.get_campaign_data()
        assert len(calls) == 2
        assert reloaded.summary["campaign_id"].tolist() == ["CMP-2"]
    finally:
        monkeypatch.undo()
        data_loader.clear_campaign_data_cache()


def test_csv_data_is_loaded_once(monkeypatch):
    calls = []
    monkeypatch.setattr(data_loader, "DATA_SOURCE", "csv")
    monkeypatch.setattr(data_loader, "load_csv_data", lambda: calls.append(1) or _frames("CMP-1"))
    data_loader.clear_campaign_data_cache()
    try:
        data_loader.get_campaign_data()
        data_loader.get_campaign_data()
        assert len(calls) == 1
    finally:
        monkeypatch.undo()
        data_loader.clear_campaign_data_cache()


def test_failed_load_is_not_cached(monkeypatch):
    attempts = []

    def flaky_load():
        attempts.append(1)
        if len(attempts) == 1:
            raise RuntimeError("Neon is waking up")
        return _frames("CMP-1")

    monkeypatch.setattr(data_loader, "DATA_SOURCE", "postgres")
    monkeypatch.setattr(data_loader, "load_postgres_data", flaky_load)
    data_loader.clear_campaign_data_cache()
    try:
        try:
            data_loader.get_campaign_data()
        except RuntimeError:
            pass
        assert data_loader.get_campaign_data().summary["campaign_id"].tolist() == ["CMP-1"]
        assert len(attempts) == 2
    finally:
        monkeypatch.undo()
        data_loader.clear_campaign_data_cache()


def test_data_loader_does_not_import_streamlit():
    source = open(data_loader.__file__, encoding="utf-8").read()

    assert "import streamlit" not in source
