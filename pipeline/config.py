"""Configuración central del pipeline: qué ligas, qué temporadas y dónde guardar."""
from pathlib import Path

BASE_URL = "https://raw.githubusercontent.com/openfootball/football.json/master"

# código de liga en openfootball -> nombre legible
LEAGUES = {
    "en.1": "Premier League",
    "es.1": "LaLiga",
    "de.1": "Bundesliga",
    "it.1": "Serie A",
    "fr.1": "Ligue 1",
}

SEASONS = ["2023-24", "2024-25", "2025-26", "2026-27"]

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "data" / "raw"
ETAGS_PATH = RAW_DIR / "_etags.json"
DB_PATH = ROOT_DIR / "data" / "futbol.duckdb"
DBT_DIR = ROOT_DIR / "futbol_dbt"
SITE_DIR = ROOT_DIR / "site"
