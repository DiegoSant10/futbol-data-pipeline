import pandas as pd

from pipeline.transform import COLUMNS, clean, parse_match


def test_parse_played_match():
    match = {"round": "Matchday 1", "date": "2024-08-16", "team1": "A", "team2": "B",
             "score": {"ht": [0, 0], "ft": [2, 1]}}
    row = parse_match(match, "es.1", "2024-25")
    assert row["home_goals"] == 2 and row["away_goals"] == 1
    assert row["league_name"] == "LaLiga"
    assert row["is_played"] is True


def test_parse_unplayed_match_has_no_score():
    match = {"round": "Matchday 38", "date": "2026-05-20", "team1": "A", "team2": "B"}
    row = parse_match(match, "es.1", "2025-26")
    assert row["home_goals"] is None
    assert row["is_played"] is False


def test_parse_list_score_is_full_time():
    match = {"date": "2025-08-16", "team1": "A", "team2": "B", "score": [0, 0]}
    row = parse_match(match, "en.1", "2025-26")
    assert (row["home_goals"], row["away_goals"]) == (0, 0)
    assert row["ht_home_goals"] is None
    assert row["is_played"] is True


def test_parse_canceled_match():
    match = {"date": "2026-05-17", "team1": "A", "team2": "B", "status": "canceled"}
    assert parse_match(match, "fr.1", "2025-26")["is_played"] is False


def test_clean_removes_duplicates_and_invalid_rows():
    base = {"league_code": "es.1", "league_name": "LaLiga", "season": "2024-25", "round": "1",
            "match_date": "2024-08-16", "home_team": " A ", "away_team": "B",
            "home_goals": 1, "away_goals": 0, "ht_home_goals": 0, "ht_away_goals": 0,
            "is_played": True}
    no_team = {**base, "home_team": None}
    df = clean(pd.DataFrame([base, base, no_team], columns=COLUMNS))
    assert len(df) == 1
    assert df.loc[0, "home_team"] == "A"  # se eliminan espacios
