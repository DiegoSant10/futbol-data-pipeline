"""Chequeo rápido del resultado del pipeline: ¿están las tablas, tienen datos y son coherentes?

Uso: python verificar.py   (termina con código 1 si algún chequeo falla)
"""
import sys

import duckdb

from pipeline.config import DB_PATH, LEAGUES, SEASONS, SITE_DIR

results = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append(ok)
    print(f"  [{'OK' if ok else 'FALLO'}] {name}" + (f" -> {detail}" if detail else ""))


print("\nArchivos")
check("Base de datos existe", DB_PATH.exists(), str(DB_PATH))
check("Dashboard existe", (SITE_DIR / "index.html").exists(), str(SITE_DIR / "index.html"))
if not DB_PATH.exists():
    sys.exit(1)

con = duckdb.connect(str(DB_PATH), read_only=True)
one = lambda sql: con.execute(sql).fetchone()[0]

print("\nCapa raw")
total = one("SELECT COUNT(*) FROM raw.matches")
check("raw.matches tiene partidos", total > 0, f"{total} partidos")
partitions = one("SELECT COUNT(DISTINCT (league_code, season)) FROM raw.matches")
expected = len(LEAGUES) * len(SEASONS)
check("Todas las ligas-temporada cargadas", partitions == expected, f"{partitions} de {expected}")
# solo informativo: si la fuente no cambia (parón de selecciones), la carga incremental
# no toca ninguna fila y esta fecha no avanza, sin que eso sea un error
last_load = one("SELECT MAX(loaded_at) FROM raw.matches")
print(f"  [INFO] Último cambio cargado: {last_load}")

print("\nMarts (dbt)")
for table in ["standings", "team_form", "points_progression", "league_summary"]:
    n = one(f"SELECT COUNT(*) FROM marts.{table}")
    check(f"marts.{table} tiene filas", n > 0, f"{n} filas")
played = one("SELECT COUNT(*) FROM raw.matches WHERE is_played")
team_games = one("SELECT SUM(played) FROM marts.standings")
check("Cada partido jugado cuenta para 2 equipos", team_games == 2 * played,
      f"{team_games} = 2 x {played}")
leaders = one("SELECT COUNT(*) FROM marts.standings WHERE position = 1")
check("Hay un líder por liga-temporada", leaders >= partitions, f"{leaders} líderes")

ok = all(results)
print(f"\n{'Todo correcto' if ok else 'Hay chequeos fallidos'}: {sum(results)}/{len(results)}\n")
sys.exit(0 if ok else 1)
