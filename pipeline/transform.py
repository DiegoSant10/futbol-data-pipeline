"""TRANSFORM: convierte los JSON crudos en una tabla limpia de partidos (un partido por fila)."""
import json
import logging
from pathlib import Path

import pandas as pd

from pipeline.config import LEAGUES, RAW_DIR

log = logging.getLogger(__name__)

COLUMNS = [
    "league_code", "league_name", "season", "round", "match_date",
    "home_team", "away_team", "home_goals", "away_goals",
    "ht_home_goals", "ht_away_goals", "is_played",
]


def parse_score(score) -> tuple[list, list]:
    """Devuelve (final, descanso). La fuente usa varios formatos para `score`:
    {"ft": [..], "ht": [..]}, {"ft": [..]}, {} o ausente (no jugado/cancelado),
    y [0, 0] como forma abreviada de un 0-0 (temporada 2025-26).
    """
    empty = [None, None]
    if isinstance(score, list):
        return score, empty
    if isinstance(score, dict):
        return score.get("ft") or empty, score.get("ht") or empty
    return empty, empty


def parse_match(match: dict, league: str, season: str) -> dict:
    """Aplana un partido del JSON. Los partidos aún no jugados no traen marcador."""
    ft, ht = parse_score(match.get("score"))
    return {
        "league_code": league,
        "league_name": LEAGUES.get(league, league),
        "season": season,
        "round": match.get("round"),
        "match_date": match.get("date"),
        "home_team": match.get("team1"),
        "away_team": match.get("team2"),
        "home_goals": ft[0],
        "away_goals": ft[1],
        "ht_home_goals": ht[0],
        "ht_away_goals": ht[1],
        "is_played": ft[0] is not None,
    }


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Tipos correctos, sin duplicados, sin filas inválidas."""
    df = df.copy()
    df["match_date"] = pd.to_datetime(df["match_date"], errors="coerce").dt.date
    for col in ["home_goals", "away_goals", "ht_home_goals", "ht_away_goals"]:
        df[col] = df[col].astype("Int64")  # entero que admite nulos
    df["home_team"] = df["home_team"].str.strip()
    df["away_team"] = df["away_team"].str.strip()

    before = len(df)
    df = df.dropna(subset=["home_team", "away_team", "match_date"])
    df = df.drop_duplicates(subset=["league_code", "season", "home_team", "away_team"])
    if len(df) < before:
        log.info("Se descartaron %d filas inválidas o duplicadas", before - len(df))
    return df.reset_index(drop=True)


def transform(paths: list[Path] | None = None) -> pd.DataFrame:
    """Transforma los archivos indicados (por defecto, todos los de data/raw)."""
    if paths is None:
        paths = sorted(RAW_DIR.glob("*/*.json"))
    rows = []
    for path in paths:
        season, league = path.parent.name, path.stem
        data = json.loads(path.read_text(encoding="utf-8"))
        rows.extend(parse_match(m, league, season) for m in data.get("matches", []))

    df = clean(pd.DataFrame(rows, columns=COLUMNS))
    log.info("Transformados %d partidos (%d jugados)", len(df), df["is_played"].sum())
    return df
