import duckdb
import pandas as pd
import pytest

from pipeline import load as load_module
from pipeline.transform import COLUMNS, clean


def make_row(home_goals=1, home_team="A", league_code="es.1"):
    return {"league_code": league_code, "league_name": "LaLiga", "season": "2026-27", "round": "1",
            "match_date": "2026-08-16", "home_team": home_team, "away_team": "B",
            "home_goals": home_goals, "away_goals": 0 if home_goals is not None else None,
            "ht_home_goals": None, "ht_away_goals": None, "is_played": home_goals is not None}


def make_df(*rows):
    return clean(pd.DataFrame(list(rows), columns=COLUMNS))


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    path = tmp_path / "test.duckdb"
    monkeypatch.setattr(load_module, "DB_PATH", path)
    return path


def read_matches(path):
    with duckdb.connect(str(path)) as con:
        return con.execute(
            "SELECT league_code, home_team, home_goals FROM raw.matches ORDER BY ALL"
        ).fetchall()


def test_reload_updates_existing_match(db_path):
    load_module.load(make_df(make_row(home_goals=None)))  # partido programado, sin resultado
    load_module.load(make_df(make_row(home_goals=2)))     # se juega: ahora tiene resultado
    assert read_matches(db_path) == [("es.1", "A", 2)]


def test_reload_removes_stale_rows_in_same_partition(db_path):
    load_module.load(make_df(make_row(home_team="Old Name FC")))
    load_module.load(make_df(make_row(home_team="New Name FC")))  # equipo renombrado en la fuente
    assert read_matches(db_path) == [("es.1", "New Name FC", 1)]


def test_reload_keeps_other_partitions(db_path):
    load_module.load(make_df(make_row(league_code="es.1"), make_row(league_code="en.1")))
    load_module.load(make_df(make_row(home_goals=3, league_code="es.1")))
    assert read_matches(db_path) == [("en.1", "A", 1), ("es.1", "A", 3)]


def test_empty_load_keeps_existing_rows(db_path):
    load_module.load(make_df(make_row()))
    load_module.load(make_df())
    assert read_matches(db_path) == [("es.1", "A", 1)]


def test_full_refresh_replaces_table(db_path):
    load_module.load(make_df(make_row()))
    load_module.load(make_df(), full_refresh=True)
    assert read_matches(db_path) == []
