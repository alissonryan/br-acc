#!/usr/bin/env python3
"""Download CNPJ data from Receita Federal open data portal.

Usage:
    python etl/scripts/download_cnpj.py                    # download all (reference + main)
    python etl/scripts/download_cnpj.py --reference-only   # reference tables only (tiny)
    python etl/scripts/download_cnpj.py --files 1          # just first file of each type
    python etl/scripts/download_cnpj.py --types Empresas   # specific type only
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).parent))
from _download_utils import download_file, extract_zip, validate_csv

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://dadosabertos.rfb.gov.br/CNPJ/"

MAIN_TYPES = ["Empresas", "Socios", "Estabelecimentos"]
REFERENCE_FILES = [
    "Naturezas.zip",
    "Qualificacoes.zip",
    "Cnaes.zip",
    "Municipios.zip",
    "Paises.zip",
    "Motivos.zip",
]


EXPECTED_COLS = {
    "EMPRE": 7,
    "SOCIO": 11,
    "ESTABELE": 30,
    "Naturezas": 2,
    "Qualificacoes": 2,
    "Cnaes": 2,
    "Municipios": 2,
    "Paises": 2,
    "Motivos": 2,
}


@click.command()
@click.option("--output-dir", default="./data/cnpj", help="Base output directory")
@click.option("--files", type=int, default=10, help="Number of files per type (0-9)")
@click.option("--types", multiple=True, help="Specific types to download (Empresas, Socios, etc.)")
@click.option("--reference-only", is_flag=True, help="Download only reference tables")
@click.option("--skip-existing/--no-skip-existing", default=True, help="Skip already downloaded files")
@click.option("--skip-extract", is_flag=True, help="Skip extraction after download")
@click.option("--timeout", type=int, default=600, help="Download timeout in seconds")
def main(
    output_dir: str,
    files: int,
    types: tuple[str, ...],
    reference_only: bool,
    skip_existing: bool,
    skip_extract: bool,
    timeout: int,
) -> None:
    """Download and extract CNPJ data from Receita Federal."""
    base = Path(output_dir)
    raw_dir = base / "raw"
    extract_dir = base / "extracted"
    ref_dir = base / "reference"
    for d in [raw_dir, extract_dir, ref_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # --- Reference tables (always download, they're tiny) ---
    logger.info("=== Reference tables ===")
    for filename in REFERENCE_FILES:
        dest = raw_dir / filename
        if skip_existing and dest.exists():
            logger.info("Skipping (exists): %s", filename)
        else:
            download_file(f"{BASE_URL}{filename}", dest, timeout=timeout)

        if not skip_extract and dest.exists():
            extracted = extract_zip(dest, ref_dir)
            for f in extracted:
                table_name = f.stem.split(".")[0]
                expected = EXPECTED_COLS.get(table_name)
                validate_csv(f, expected_cols=expected)

    if reference_only:
        logger.info("Reference-only mode — done.")
        return

    # --- Main data files ---
    file_types = list(types) if types else MAIN_TYPES
    for file_type in file_types:
        logger.info("=== %s ===", file_type)
        for i in range(min(files, 10)):
            filename = f"{file_type}{i}.zip"
            dest = raw_dir / filename
            if skip_existing and dest.exists():
                logger.info("Skipping (exists): %s", filename)
            else:
                success = download_file(f"{BASE_URL}{filename}", dest, timeout=timeout)
                if not success:
                    continue

            if not skip_extract and dest.exists():
                extracted = extract_zip(dest, extract_dir)
                for f in extracted:
                    # Determine expected column count from filename
                    expected = None
                    for key, cols in EXPECTED_COLS.items():
                        if key in f.name:
                            expected = cols
                            break
                    validate_csv(f, expected_cols=expected)

    logger.info("=== Download complete ===")
    _print_summary(raw_dir, extract_dir, ref_dir)


def _print_summary(raw_dir: Path, extract_dir: Path, ref_dir: Path) -> None:
    """Print download summary with file counts and sizes."""
    for label, d in [("Raw ZIPs", raw_dir), ("Extracted", extract_dir), ("Reference", ref_dir)]:
        files = list(d.iterdir())
        total_size = sum(f.stat().st_size for f in files if f.is_file())
        logger.info(
            "%s: %d files, %.1f MB",
            label,
            len([f for f in files if f.is_file()]),
            total_size / 1e6,
        )


if __name__ == "__main__":
    main()
