"""Shared download utilities for ETL data acquisition scripts."""

from __future__ import annotations

import logging
import zipfile
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)


def download_file(url: str, dest: Path, *, timeout: int = 600) -> bool:
    """Download a file with streaming and resume support.

    Returns True on success, False on failure.
    """
    partial = dest.with_suffix(dest.suffix + ".partial")
    start_byte = partial.stat().st_size if partial.exists() else 0

    headers = {}
    if start_byte > 0:
        headers["Range"] = f"bytes={start_byte}-"
        logger.info("Resuming %s from %.1f MB", dest.name, start_byte / 1e6)

    try:
        with httpx.stream(
            "GET", url, follow_redirects=True, timeout=timeout, headers=headers,
        ) as response:
            if response.status_code == 416:
                logger.info("Already complete: %s", dest.name)
                if partial.exists():
                    partial.rename(dest)
                return True

            response.raise_for_status()

            total = response.headers.get("content-length")
            total_mb = f"{int(total) / 1e6:.1f} MB" if total else "unknown size"
            logger.info("Downloading %s (%s)...", dest.name, total_mb)

            mode = "ab" if start_byte > 0 else "wb"
            downloaded = start_byte
            with open(partial, mode) as f:
                for chunk in response.iter_bytes(chunk_size=65_536):
                    f.write(chunk)
                    downloaded += len(chunk)

            partial.rename(dest)
            logger.info("Downloaded: %s (%.1f MB)", dest.name, downloaded / 1e6)
            return True

    except httpx.HTTPError as e:
        logger.warning("Failed to download %s: %s", dest.name, e)
        return False


def extract_zip(zip_path: Path, output_dir: Path) -> list[Path]:
    """Extract ZIP and return list of extracted files.

    Deletes corrupted ZIPs for re-download.
    """
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            zf.extractall(output_dir)
        logger.info("Extracted %d files from %s", len(names), zip_path.name)
        return [output_dir / n for n in names]
    except zipfile.BadZipFile:
        logger.warning("Bad ZIP file: %s — deleting for re-download", zip_path.name)
        zip_path.unlink()
        return []


def validate_csv(
    path: Path,
    *,
    expected_cols: int | None = None,
    encoding: str = "latin-1",
    sep: str = ";",
) -> bool:
    """Quick validation: read first 10 rows, check encoding and column count."""
    try:
        import pandas as pd

        df = pd.read_csv(
            path,
            sep=sep,
            encoding=encoding,
            header=None,
            dtype=str,
            nrows=10,
            keep_default_na=False,
        )
        if df.empty:
            logger.warning("Empty file: %s", path.name)
            return False
        if expected_cols and len(df.columns) != expected_cols:
            logger.warning(
                "%s: expected %d cols, got %d", path.name, expected_cols, len(df.columns),
            )
            return False
        logger.info("Validated %s: %d cols, first row OK", path.name, len(df.columns))
        return True
    except Exception as e:
        logger.warning("Validation failed for %s: %s", path.name, e)
        return False
