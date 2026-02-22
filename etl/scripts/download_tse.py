#!/usr/bin/env python3
"""Download TSE electoral data — candidates and campaign donations.

Usage:
    python etl/scripts/download_tse.py --years 2024
    python etl/scripts/download_tse.py --years 2018 2020 2022 2024
    python etl/scripts/download_tse.py --output-dir ./data/tse --years 2024
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import click
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from _download_utils import download_file, extract_zip

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

TSE_CDN = "https://cdn.tse.jus.br/estatistica/sead/odsele"

# Real TSE column names → pipeline expected names
CANDIDATO_COLS = {
    "SQ_CANDIDATO": "sq_candidato",
    "NR_CPF_CANDIDATO": "cpf",
    "NM_CANDIDATO": "nome",
    "DS_CARGO": "cargo",
    "SG_UF": "uf",
    "NM_UE": "municipio",
    "ANO_ELEICAO": "ano",
    "SG_PARTIDO": "partido",
    "NR_CANDIDATO": "nr_candidato",
}

DOACAO_COLS = {
    "SQ_CANDIDATO": "sq_candidato",
    "NR_CPF_CNPJ_DOADOR": "cpf_cnpj_doador",
    "NM_DOADOR": "nome_doador",
    "VR_RECEITA": "valor",
    "AA_ELEICAO": "ano",
    "NM_CANDIDATO": "nome_candidato",
    "SG_PARTIDO": "partido",
    "NR_CANDIDATO": "nr_candidato",
}


def _download_and_extract(
    url: str, name: str, raw_dir: Path, *, skip_existing: bool, timeout: int,
) -> list[Path]:
    """Download ZIP and extract, returning list of CSV paths."""
    zip_path = raw_dir / f"{name}.zip"
    if skip_existing and zip_path.exists():
        logger.info("Skipping (exists): %s", zip_path.name)
    else:
        if not download_file(url, zip_path, timeout=timeout):
            return []

    extract_dir = raw_dir / f"{name}_extracted"
    extract_dir.mkdir(parents=True, exist_ok=True)
    extracted = extract_zip(zip_path, extract_dir)
    return [f for f in extracted if f.suffix.lower() == ".csv"]


def _concat_state_csvs(csv_paths: list[Path], encoding: str = "latin-1") -> pd.DataFrame:
    """TSE distributes data as per-state CSVs inside the ZIP. Concatenate them."""
    frames = []
    for path in csv_paths:
        try:
            df = pd.read_csv(
                path, sep=";", encoding=encoding, dtype=str, keep_default_na=False,
            )
            frames.append(df)
        except Exception as e:
            logger.warning("Skipping %s: %s", path.name, e)
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True)
    logger.info("Concatenated %d files → %d rows", len(frames), len(combined))
    return combined


def _remap_and_write(
    df: pd.DataFrame, col_map: dict[str, str], output_path: Path, dataset: str,
) -> bool:
    """Remap columns and write pipeline-ready CSV."""
    available = {real: pipe for real, pipe in col_map.items() if real in df.columns}
    missing = set(col_map) - set(available)
    if missing:
        logger.warning("%s: missing source columns: %s", dataset, missing)

    mapped = df[list(available.keys())].rename(columns=available)
    mapped.to_csv(output_path, index=False, encoding="latin-1")
    logger.info("Wrote %d rows to %s", len(mapped), output_path)
    return True


def _download_candidates(
    years: list[int], raw_dir: Path, output_dir: Path, *, skip_existing: bool, timeout: int,
) -> bool:
    """Download and process candidate data for given election years."""
    all_csvs: list[Path] = []
    for year in years:
        url = f"{TSE_CDN}/consulta_cand/consulta_cand_{year}.zip"
        csvs = _download_and_extract(
            url, f"candidatos_{year}", raw_dir, skip_existing=skip_existing, timeout=timeout,
        )
        all_csvs.extend(csvs)

    if not all_csvs:
        logger.warning("No candidate CSVs downloaded")
        return False

    df = _concat_state_csvs(all_csvs)
    if df.empty:
        return False

    return _remap_and_write(df, CANDIDATO_COLS, output_dir / "candidatos.csv", "candidatos")


def _download_donations(
    years: list[int], raw_dir: Path, output_dir: Path, *, skip_existing: bool, timeout: int,
) -> bool:
    """Download and process campaign donation data for given election years."""
    all_csvs: list[Path] = []
    for year in years:
        url = (
            f"{TSE_CDN}/prestacao_contas/"
            f"prestacao_de_contas_eleitorais_candidatos_{year}.zip"
        )
        csvs = _download_and_extract(
            url, f"doacoes_{year}", raw_dir, skip_existing=skip_existing, timeout=timeout,
        )
        # Only use receitas_candidatos files (not despesas or doador_originario)
        csvs = [f for f in csvs if f.name.startswith("receitas_candidatos_")]
        all_csvs.extend(csvs)

    if not all_csvs:
        logger.warning("No donation CSVs downloaded")
        return False

    df = _concat_state_csvs(all_csvs)
    if df.empty:
        return False

    return _remap_and_write(df, DOACAO_COLS, output_dir / "doacoes.csv", "doacoes")


@click.command()
@click.option(
    "--years",
    multiple=True,
    type=int,
    default=[2024],
    help="Election years to download (e.g. --years 2018 --years 2022)",
)
@click.option("--output-dir", default="./data/tse", help="Output directory")
@click.option("--skip-existing/--no-skip-existing", default=True, help="Skip existing ZIPs")
@click.option("--timeout", type=int, default=600, help="Download timeout in seconds")
def main(years: tuple[int, ...], output_dir: str, skip_existing: bool, timeout: int) -> None:
    """Download TSE candidate and donation data."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    raw_dir = out / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    year_list = list(years)
    logger.info("=== TSE download: years %s ===", year_list)

    success_count = 0
    if _download_candidates(
        year_list, raw_dir, out, skip_existing=skip_existing, timeout=timeout,
    ):
        success_count += 1
    if _download_donations(
        year_list, raw_dir, out, skip_existing=skip_existing, timeout=timeout,
    ):
        success_count += 1

    logger.info("=== Done: %d/2 datasets downloaded ===", success_count)
    if success_count == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
