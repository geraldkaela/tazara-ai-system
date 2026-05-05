"""Historical data collection and cleaning pipeline for Phase 2.

This module discovers CSV files under `data/raw/`, applies basic cleaning
and feature extraction, aggregates to daily cargo demand, and writes the
processed output to `data/simulated/cargo_demand.csv` which the forecasting
models expect.

Usage:
    python forecasting/data_pipeline.py --raw-dir data/raw --out data/simulated/cargo_demand.csv
"""
from __future__ import annotations

import argparse
import glob
import logging
from pathlib import Path
from typing import List

import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def discover_csv_files(raw_dir: str = "data/raw") -> List[Path]:
    p = Path(raw_dir)
    files = sorted(p.glob("**/*.csv"))
    logger.info(f"Found {len(files)} raw CSV files under {raw_dir}")
    return files


def load_csv(path: Path) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, parse_dates=["date"] if "date" in pd.read_csv(path, nrows=0).columns else None)
    except Exception:
        # fallback without parse_dates
        df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from {path}")
    return df


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    # Standard cleaning steps useful for time series demand data
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    # Drop rows without date or cargo value
    if "cargo_tons" in df.columns:
        df = df.dropna(subset=["cargo_tons"])
    # Fill missing numeric columns with 0
    num_cols = df.select_dtypes(include="number").columns.tolist()
    df[num_cols] = df[num_cols].fillna(0)

    return df


def aggregate_daily(df: pd.DataFrame, date_col: str = "date", value_col: str = "cargo_tons") -> pd.DataFrame:
    if date_col not in df.columns:
        raise ValueError("DataFrame must contain a 'date' column for aggregation")

    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.set_index(date_col)
    # Aggregate by day summing cargo
    daily = df[value_col].resample("D").sum().rename("cargo_tons").to_frame()
    daily = daily.reset_index()
    return daily


def run_pipeline(raw_dir: str = "data/raw", out_path: str = "data/simulated/cargo_demand.csv") -> Path:
    files = discover_csv_files(raw_dir)
    if not files:
        logger.warning("No raw files found — creating empty processed file with headers")
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=["date", "cargo_tons"]).to_csv(out_path, index=False)
        return Path(out_path)

    frames = []
    for f in files:
        df = load_csv(f)
        df = clean_dataframe(df)
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)

    # Try to detect cargo column name variants
    if "cargo_tons" not in combined.columns:
        # common alternatives
        for alt in ["cargo", "tons", "volume", "cargo_volume"]:
            if alt in combined.columns:
                combined = combined.rename(columns={alt: "cargo_tons"})
                break

    daily = aggregate_daily(combined)

    out_p = Path(out_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    daily.to_csv(out_p, index=False)
    logger.info(f"Wrote processed daily demand to {out_p} ({len(daily)} rows)")
    return out_p


def _cli():
    parser = argparse.ArgumentParser(description="Run historical data collection and cleaning pipeline")
    parser.add_argument("--raw-dir", default="data/raw", help="Directory with raw CSV files")
    parser.add_argument("--out", default="data/simulated/cargo_demand.csv", help="Output processed CSV path")
    args = parser.parse_args()
    run_pipeline(args.raw_dir, args.out)


if __name__ == "__main__":
    _cli()
