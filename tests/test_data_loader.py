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
    monkeypatch.setattr(data_loader, "load_campaign_list_version", lambda: ("3", "CMP-2026-004"))
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


# --- "anything new?" check -------------------------------------------------


class _FakeNeon:
    """Counts full loads and version checks; the version can be changed or made to fail."""

    def __init__(self, monkeypatch):
        self.loads = 0
        self.checks = 0
        self.version = ("3", "CMP-2026-004")
        self.fail_check = False
        self.clock = 1000.0
        monkeypatch.setattr(data_loader, "DATA_SOURCE", "postgres")
        monkeypatch.setattr(data_loader, "load_postgres_data", self._load)
        monkeypatch.setattr(data_loader, "load_campaign_list_version", self._version)
        monkeypatch.setattr(data_loader.time, "monotonic", lambda: self.clock)
        monkeypatch.setattr(data_loader, "CAMPAIGN_CHECK_SECONDS", 60)
        data_loader.clear_campaign_data_cache()

    def _load(self):
        self.loads += 1
        return _frames(f"load-{self.loads}")

    def _version(self):
        self.checks += 1
        if self.fail_check:
            raise ConnectionError("Neon is waking up")
        return self.version


def test_no_check_within_the_check_interval(monkeypatch):
    neon = _FakeNeon(monkeypatch)
    try:
        first = data_loader.get_campaign_data()
        checks_after_load = neon.checks
        neon.clock += 59
        assert data_loader.get_campaign_data() is first
        assert neon.checks == checks_after_load and neon.loads == 1
    finally:
        data_loader.clear_campaign_data_cache()


def test_unchanged_campaign_list_keeps_the_cache(monkeypatch):
    neon = _FakeNeon(monkeypatch)
    try:
        first = data_loader.get_campaign_data()
        neon.clock += 61
        assert data_loader.get_campaign_data() is first
        assert neon.loads == 1 and neon.checks == 2
    finally:
        data_loader.clear_campaign_data_cache()


def test_new_campaign_triggers_a_reload_at_the_next_check(monkeypatch):
    neon = _FakeNeon(monkeypatch)
    try:
        data_loader.get_campaign_data()
        neon.version = ("4", "CMP-2026-006")
        neon.clock += 61
        reloaded = data_loader.get_campaign_data()
        assert neon.loads == 2
        assert reloaded.summary["campaign_id"].tolist() == ["load-2"]

        neon.clock += 61  # same new version: no further reload
        assert data_loader.get_campaign_data() is reloaded
        assert neon.loads == 2
    finally:
        data_loader.clear_campaign_data_cache()


def test_failed_check_keeps_serving_cached_data(monkeypatch):
    neon = _FakeNeon(monkeypatch)
    try:
        first = data_loader.get_campaign_data()
        neon.fail_check = True
        neon.clock += 61
        assert data_loader.get_campaign_data() is first
        assert neon.loads == 1
    finally:
        data_loader.clear_campaign_data_cache()


def test_csv_mode_never_checks(monkeypatch):
    calls = []
    monkeypatch.setattr(data_loader, "load_campaign_list_version", lambda: calls.append(1))
    monkeypatch.setattr(data_loader, "DATA_SOURCE", "csv")
    data_loader.clear_campaign_data_cache()
    try:
        data_loader.get_campaign_data()
        data_loader.get_campaign_data()
        assert calls == []
    finally:
        data_loader.clear_campaign_data_cache()
