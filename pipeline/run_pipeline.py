"""Punto de entrada: Extract -> Transform -> Load -> dbt build -> Dashboard.

Uso:
    python -m pipeline.run_pipeline                  # incremental (solo lo que cambió)
    python -m pipeline.run_pipeline --full-refresh   # reconstruye todo desde data/raw
    python -m pipeline.run_pipeline --skip-extract   # no descarga, usa los JSON locales
"""
import argparse
import logging
import os
import sys
import time

from dbt.cli.main import dbtRunner

from pipeline.config import DB_PATH, DBT_DIR
from pipeline.dashboard import build_dashboard
from pipeline.extract import extract
from pipeline.load import load
from pipeline.transform import transform

log = logging.getLogger("pipeline")


def run_dbt() -> None:
    """Ejecuta `dbt build`: construye los modelos y corre sus tests, en orden de dependencias."""
    os.environ["DBT_DUCKDB_PATH"] = str(DB_PATH)
    result = dbtRunner().invoke(
        ["build", "--project-dir", str(DBT_DIR), "--profiles-dir", str(DBT_DIR)]
    )
    if not result.success:
        # si un test de calidad falla, el dashboard NO se actualiza con datos malos
        log.error("dbt build falló: revisa los modelos y tests de futbol_dbt/")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline de datos de fútbol")
    parser.add_argument("--full-refresh", action="store_true", help="recargar todo desde cero")
    parser.add_argument("--skip-extract", action="store_true", help="usar los JSON ya descargados")
    args = parser.parse_args()

    # force=True: al importar dbt se configura el logger raíz y sin esto nuestros logs no saldrían
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                        force=True)

    start = time.perf_counter()
    changed = [] if args.skip_extract else extract()

    # en full refresh (o sin extracción) se procesan todos los archivos locales
    paths = None if args.full_refresh or args.skip_extract else changed
    df = transform(paths)
    load(df, full_refresh=args.full_refresh)

    run_dbt()
    build_dashboard()
    log.info("Pipeline completado en %.1f s", time.perf_counter() - start)


if __name__ == "__main__":
    main()
