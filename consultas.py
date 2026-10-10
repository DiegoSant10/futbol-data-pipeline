"""Consultas de ejemplo sobre la base generada por el pipeline.

Uso: python consultas.py "Premier League" 2024-25
"""
import sys

import duckdb

from pipeline.config import DB_PATH

league = sys.argv[1] if len(sys.argv) > 1 else "LaLiga"
season = sys.argv[2] if len(sys.argv) > 2 else "2024-25"

con = duckdb.connect(str(DB_PATH), read_only=True)

print(f"\nClasificación {league} {season}")
con.sql("""
    SELECT s.position AS pos, s.team AS equipo, s.played AS pj, s.won AS g, s.drawn AS e,
           s.lost AS p, s.goals_for AS gf, s.goals_against AS gc, s.goal_diff AS dg,
           s.points AS pts, f.last_5 AS ultimos_5
    FROM marts.standings s
    JOIN marts.team_form f USING (league_name, season, team)
    WHERE s.league_name = $league AND s.season = $season
    ORDER BY s.position
""", params={"league": league, "season": season}).show(max_rows=25)

print("\nPartidos sin resultado en la fuente")
con.sql("""
    SELECT league_name, season, COUNT(*) AS sin_resultado
    FROM raw.matches
    WHERE NOT is_played
    GROUP BY ALL
""").show()
