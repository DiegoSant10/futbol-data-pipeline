"""Genera site/index.html: un dashboard estático con los datos de los marts incrustados.

Al ser un único HTML sin servidor, se puede abrir con doble clic o publicar en GitHub Pages.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import duckdb

from pipeline.config import DB_PATH, SITE_DIR

log = logging.getLogger(__name__)

TEMPLATE_PATH = Path(__file__).with_name("dashboard_template.html")


def query_records(con: duckdb.DuckDBPyConnection, sql: str) -> list[dict]:
    cursor = con.execute(sql)
    columns = [c[0] for c in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def collect_data() -> dict:
    # sin read_only: dbt-duckdb deja su conexión abierta en este mismo proceso y
    # DuckDB no permite abrir el mismo archivo con una configuración distinta
    with duckdb.connect(str(DB_PATH)) as con:
        standings = query_records(con, """
            select s.league_name, s.season, s.position, s.team, s.played, s.won, s.drawn,
                   s.lost, s.goals_for, s.goals_against, s.goal_diff, s.points, f.last_5
            from marts.standings s
            left join marts.team_form f using (league_name, season, team)
            order by s.league_name, s.season, s.position
        """)
        summary = query_records(con, "select * from marts.league_summary")
        # puntos acumulados como lista por equipo: {"LaLiga|2024-25": {"Equipo": [3, 4, 7, ...]}}
        progression: dict = {}
        for row in query_records(con, """
            select league_name, season, team, list(cumulative_points order by games_played) as pts
            from marts.points_progression
            group by all
        """):
            key = f"{row['league_name']}|{row['season']}"
            progression.setdefault(key, {})[row["team"]] = [int(p) for p in row["pts"]]

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "standings": standings,
        "summary": summary,
        "progression": progression,
    }


def build_dashboard() -> Path:
    data = collect_data()
    payload = json.dumps(data, ensure_ascii=False, default=str).replace("</", "<\\/")
    html = TEMPLATE_PATH.read_text(encoding="utf-8").replace("/*__DATA__*/null", payload)

    SITE_DIR.mkdir(parents=True, exist_ok=True)
    out_path = SITE_DIR / "index.html"
    out_path.write_text(html, encoding="utf-8")
    log.info("Dashboard generado: %s (%.0f KB)", out_path, out_path.stat().st_size / 1024)
    return out_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    build_dashboard()
