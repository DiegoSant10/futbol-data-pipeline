"""EXTRACT: descarga los JSON de openfootball y los guarda tal cual en data/raw.

Guardar el dato crudo sin modificar es una buena práctica: si mañana cambia la
lógica de transformación, se puede reprocesar sin volver a descargar.

Extracción incremental: por cada archivo se guarda su ETag (una huella que da el
servidor). En la siguiente ejecución se envía en la cabecera `If-None-Match`; si
el archivo no cambió, el servidor responde 304 y no se descarga nada.
"""
import json
import logging
from pathlib import Path

import requests

from pipeline.config import BASE_URL, ETAGS_PATH, LEAGUES, RAW_DIR, SEASONS

log = logging.getLogger(__name__)


def load_etags() -> dict:
    if ETAGS_PATH.exists():
        return json.loads(ETAGS_PATH.read_text(encoding="utf-8"))
    return {}


def download_file(season: str, league: str, etags: dict) -> Path | None:
    """Descarga un archivo si cambió. Devuelve su ruta, o None si no hubo cambios."""
    key = f"{season}/{league}"
    out_path = RAW_DIR / season / f"{league}.json"
    headers = {}
    if out_path.exists() and key in etags:
        headers["If-None-Match"] = etags[key]

    response = requests.get(f"{BASE_URL}/{key}.json", headers=headers, timeout=30)
    if response.status_code == 304:
        log.debug("Sin cambios: %s", key)
        return None
    response.raise_for_status()  # lanza excepción si la respuesta no es 200

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(response.content)
    if "ETag" in response.headers:
        etags[key] = response.headers["ETag"]
    log.info("Descargado %s", key)
    return out_path


def extract() -> list[Path]:
    """Devuelve la lista de archivos nuevos o modificados."""
    etags = load_etags()
    changed = []
    for season in SEASONS:
        for league in LEAGUES:
            try:
                path = download_file(season, league, etags)
            except requests.RequestException as exc:
                # un archivo que falla no debe tumbar todo el pipeline
                log.warning("No se pudo descargar %s/%s: %s", season, league, exc)
                continue
            if path:
                changed.append(path)

    ETAGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    ETAGS_PATH.write_text(json.dumps(etags, indent=2), encoding="utf-8")
    log.info("Extracción: %d archivos nuevos o modificados", len(changed))
    return changed
