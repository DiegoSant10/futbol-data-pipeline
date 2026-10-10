"""LOAD: guarda los partidos limpios en DuckDB (tabla raw.matches).

Carga incremental por partición: cada archivo de origen es una liga-temporada. Cuando
un archivo cambia, se borran TODOS los partidos de esa liga-temporada y se insertan
los nuevos, dentro de una transacción. Así un partido que desaparece o cambia de clave
en la fuente (p. ej. un equipo renombrado) no deja filas obsoletas, y las demás
ligas-temporadas no se tocan. Con full_refresh=True se borra la tabla entera.
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

        partitions = df[["league_code", "season"]].drop_duplicates()
        con.execute("BEGIN TRANSACTION")
        try:
            # DuckDB puede leer los DataFrames `partitions` y `df` directamente por su nombre
            con.execute("""
                DELETE FROM raw.matches m
                USING partitions p
                WHERE m.league_code = p.league_code AND m.season = p.season
            """)
            con.execute("INSERT INTO raw.matches SELECT *, now() FROM df")
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")  # si algo falla, la tabla queda como estaba
            raise
        total = con.execute("SELECT COUNT(*) FROM raw.matches").fetchone()[0]
        log.info("raw.matches: %d ligas-temporada reemplazadas (%d filas), %d filas en total",
                 len(partitions), len(df), total)
