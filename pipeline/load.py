"""LOAD: guarda los partidos limpios en DuckDB (tabla raw.matches).

Carga incremental (upsert): la tabla tiene clave primaria por partido. Si el partido
ya existe se actualiza (p. ej. se jugó y ahora tiene resultado); si no, se inserta.
Con full_refresh=True se borra la tabla y se carga desde cero.
"""
import logging

import duckdb
import pandas as pd

from pipeline.config import DB_PATH

log = logging.getLogger(__name__)

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS raw.matches (
    league_code   VARCHAR NOT NULL,
    league_name   VARCHAR NOT NULL,
    season        VARCHAR NOT NULL,
    round         VARCHAR,
    match_date    DATE    NOT NULL,
    home_team     VARCHAR NOT NULL,
    away_team     VARCHAR NOT NULL,
    home_goals    INTEGER,
    away_goals    INTEGER,
    ht_home_goals INTEGER,
    ht_away_goals INTEGER,
    is_played     BOOLEAN NOT NULL,
    loaded_at     TIMESTAMP NOT NULL,
    PRIMARY KEY (league_code, season, home_team, away_team)
)
"""


def load(df: pd.DataFrame, full_refresh: bool = False) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(DB_PATH)) as con:
        con.execute("CREATE SCHEMA IF NOT EXISTS raw")
        if full_refresh:
            con.execute("DROP TABLE IF EXISTS raw.matches")
        con.execute(CREATE_TABLE)

        if df.empty:
            log.info("No hay partidos nuevos que cargar")
            return

        # DuckDB puede leer el DataFrame `df` directamente por su nombre
        con.execute("INSERT OR REPLACE INTO raw.matches SELECT *, now() FROM df")
        total = con.execute("SELECT COUNT(*) FROM raw.matches").fetchone()[0]
        log.info("raw.matches: %d filas cargadas/actualizadas, %d en total", len(df), total)
