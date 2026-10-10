import duckdb
import pandas as pd
import pytest

from pipeline import load as load_module
from pipeline.transform import COLUMNS, clean


def make_df(home_goals):
    row = {"league_code": "es.1", "league_name": "LaLiga", "season": "2026-27", "round": "1",
           "match_date": "2026-08-16", "home_team": "A", "away_team": "B",
           "home_goals": home_goals, "away_goals": 0 if home_goals is not None else None,
           "ht_home_goals": None, "ht_away_goals": None, "is_played": home_goals is not None}
    return clean(pd.DataFrame([row], columns=COLUMNS))


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    path = tmp_path / "test.duckdb"
    monkeypatch.setattr(load_module, "DB_PATH", path)
    return path


def read_matches(path):
    with duckdb.connect(str(path)) as con:
        return con.execute("SELECT home_goals, is_played FROM raw.matches").fetchall()


def test_upsert_updates_existing_match(db_path):
    load_module.load(make_df(None))  # partido programado, sin resultado
    load_module.load(make_df(2))     # se juega: misma clave, ahora con resultado
    assert read_matches(db_path) == [(2, True)]


def test_empty_load_keeps_existing_rows(db_path):
    load_module.load(make_df(1))
    load_module.load(clean(pd.DataFrame(columns=COLUMNS)))
    assert read_matches(db_path) == [(1, True)]


def test_full_refresh_replaces_table(db_path):
    load_module.load(make_df(1))
    load_module.load(clean(pd.DataFrame(columns=COLUMNS)), full_refresh=True)
    assert read_matches(db_path) == []
