# Pipeline de datos de fútbol ⚽

Pipeline de datos de punta a punta sobre las 5 grandes ligas europeas (2023-24 a 2026-27):
extracción incremental, carga en DuckDB, modelado y tests con dbt, dashboard web y
orquestación diaria con GitHub Actions.

## Arquitectura

```
openfootball (JSON)
      │  EXTRACT  (Python + requests, incremental con ETag: solo baja lo que cambió)
      ▼
data/raw/*.json                       capa raw: datos tal cual
      │  TRANSFORM (pandas: aplanar, tipar, deduplicar, normalizar formatos)
      │  LOAD      (upsert en DuckDB por clave primaria de partido)
      ▼
raw.matches
      │  dbt build (modelos + 13 tests de calidad de datos)
      ▼
staging.stg_matches  →  intermediate.int_team_matches  →  marts.standings
                                                          marts.team_form
                                                          marts.points_progression
                                                          marts.league_summary
      │  DASHBOARD (HTML estático con los datos incrustados)
      ▼
site/index.html  →  GitHub Pages
```

Todo lo orquesta `.github/workflows/pipeline.yml`: se ejecuta cada día a las 06:00 UTC,
corre los tests, restaura el estado anterior (`data/`) para que la carga sea incremental
y, solo si todos los tests de dbt pasan, publica el dashboard.

## Uso local

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt

.\.venv\Scripts\python -m pipeline.run_pipeline                 # incremental
.\.venv\Scripts\python -m pipeline.run_pipeline --full-refresh  # reconstruir todo
.\.venv\Scripts\python -m pipeline.run_pipeline --skip-extract  # sin descargar
start site\index.html                                            # abrir el dashboard

.\.venv\Scripts\python consultas.py "LaLiga" 2026-27             # clasificación en consola
.\.venv\Scripts\python -m pytest                                 # tests de Python
```

dbt también puede usarse directamente:

```powershell
cd futbol_dbt
$env:DBT_DUCKDB_PATH = "..\data\futbol.duckdb"
..\.venv\Scripts\dbt build --profiles-dir .
..\.venv\Scripts\dbt docs generate --profiles-dir .; ..\.venv\Scripts\dbt docs serve --profiles-dir .
```

## Estructura

| Ruta | Qué hace |
|---|---|
| `pipeline/extract.py` | Descarga incremental con cabecera `If-None-Match` (ETag) |
| `pipeline/transform.py` | Normaliza los 4 formatos del marcador y limpia los datos |
| `pipeline/load.py` | `INSERT OR REPLACE` en `raw.matches` (upsert) o full refresh |
| `pipeline/dashboard.py` | Consulta los marts y genera `site/index.html` |
| `futbol_dbt/` | Modelos SQL por capas y tests de calidad de datos |
| `tests/` | Tests unitarios (pytest) de la transformación y la carga |

## Calidad de datos: hallazgos

- El campo `score` llega en 4 formatos distintos (dict con `ft`/`ht`, dict solo con `ft`,
  vacío, y la lista `[0, 0]` como abreviatura de 0-0 en 2025-26). `parse_score` los normaliza.
- La fuente no tiene el resultado de la jornada 38 de LaLiga y la Serie A 2024-25 (10 partidos
  cada una), así que esas clasificaciones quedan incompletas. Hay 1 partido cancelado en la Ligue 1 2025-26.
- Tests de dbt: unicidad del partido, valores aceptados, y reglas de negocio
  (puntos = 3·G + E; goles a favor = goles en contra en cada liga).

## Fuente

[openfootball/football.json](https://github.com/openfootball/football.json) — dominio público.
