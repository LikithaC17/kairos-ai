"""Dataset ingestion and preparation utilities for NetForecast AI.

Provides functions to load, validate, and prepare network flow datasets
from various sources (CSV, Parquet, synthetic generators) for downstream
preprocessing and modeling pipelines.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

from .schema import (
    ALL_COLUMNS,
    REQUIRED_COLUMNS,
    VALID_STATES,
    VALID_LABELS,
    VALID_SEVERITIES,
    VALID_PROTOCOLS,
    VALID_SCENARIOS,
    ValidationResult,
    coerce_dtypes,
    ensure_flow_id,
    sort_by_timestamp,
    validate_schema,
)


def load_csv(path: str | Path, **kwargs) -> pd.DataFrame:
    """Load flow records from CSV with default options."""
    df = pd.read_csv(path, **kwargs)
    return df


def load_parquet(path: str | Path, **kwargs) -> pd.DataFrame:
    """Load flow records from Parquet."""
    df = pd.read_parquet(path, **kwargs)
    return df


def load_dataset(path: str | Path, **kwargs) -> pd.DataFrame:
    """Load dataset from CSV or Parquet based on extension."""
    path = Path(path)
    if path.suffix.lower() in [".parquet", ".pq"]:
        return load_parquet(path, **kwargs)
    return load_csv(path, **kwargs)


def save_dataset(df: pd.DataFrame, path: str | Path, **kwargs) -> None:
    """Save dataset to CSV or Parquet based on extension."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() in [".parquet", ".pq"]:
        df.to_parquet(path, index=False, **kwargs)
    else:
        df.to_csv(path, index=False, **kwargs)


def prepare_dataset(
    df: pd.DataFrame,
    *,
    validate: bool = True,
    coerce: bool = True,
    sort: bool = True,
    add_flow_id: bool = True,
) -> tuple[pd.DataFrame, ValidationResult]:
    """Prepare a raw dataset for the preprocessing pipeline."""
    result_df = df.copy()

    if coerce:
        result_df = coerce_dtypes(result_df)

    if add_flow_id:
        result_df = ensure_flow_id(result_df)

    if sort:
        result_df = sort_by_timestamp(result_df)

    validation = ValidationResult(is_valid=True, errors=[], warnings=[], stats={})
    if validate:
        validation = validate_schema(result_df)
        if not validation.is_valid:
            raise ValueError(f"Dataset validation failed: {validation.errors}")

    return result_df, validation


def split_chronological(
    df: pd.DataFrame,
    train_frac: float = 0.7,
    val_frac: float = 0.15,
    test_frac: float = 0.15,
    timestamp_col: str = "timestamp",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split dataset chronologically to prevent temporal leakage."""
    if not np.isclose(train_frac + val_frac + test_frac, 1.0):
        raise ValueError("Fractions must sum to 1.0")

    df = sort_by_timestamp(df)
    n = len(df)
    train_end = int(n * train_frac)
    val_end = train_end + int(n * val_frac)

    train = df.iloc[:train_end].copy()
    val = df.iloc[train_end:val_end].copy()
    test = df.iloc[val_end:].copy()

    return train, val, test


def get_scenario_subset(df: pd.DataFrame, scenarios: list[str]) -> pd.DataFrame:
    """Filter dataset to include only specified scenarios."""
    if "scenario" not in df.columns:
        raise ValueError("Dataset has no 'scenario' column")
    return df[df["scenario"].isin(scenarios)].copy()


def get_state_subset(df: pd.DataFrame, states: list[str]) -> pd.DataFrame:
    """Filter dataset to include only specified states."""
    if "state" not in df.columns:
        raise ValueError("Dataset has no 'state' column")
    return df[df["state"].isin(states)].copy()


def balance_dataset(
    df: pd.DataFrame,
    target_col: str = "label",
    method: Literal["undersample", "oversample"] = "undersample",
    random_state: int = 42,
) -> pd.DataFrame:
    """Balance dataset by target label using undersampling or oversampling."""
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found")

    rng = np.random.default_rng(random_state)
    counts = df[target_col].value_counts()
    minority_class = counts.idxmin()
    majority_class = counts.idxmax()
    minority_count = counts.min()
    majority_count = counts.max()

    minority_df = df[df[target_col] == minority_class]
    majority_df = df[df[target_col] == majority_class]

    if method == "undersample":
        majority_sampled = majority_df.sample(n=minority_count, random_state=random_state)
        balanced = pd.concat([minority_df, majority_sampled], ignore_index=True)
    else:  # oversample
        minority_upsampled = minority_df.sample(n=majority_count, replace=True, random_state=random_state)
        balanced = pd.concat([majority_df, minority_upsampled], ignore_index=True)

    return balanced.sample(frac=1.0, random_state=random_state).reset_index(drop=True)


def summarize_dataset(df: pd.DataFrame) -> dict:
    """Generate a summary of the dataset for reporting."""
    summary = {
        "shape": df.shape,
        "memory_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
        "dtypes": df.dtypes.astype(str).to_dict(),
        "null_counts": df.isnull().sum().to_dict(),
    }

    for col in ["state", "scenario", "protocol", "label", "severity"]:
        if col in df.columns:
            summary[f"{col}_distribution"] = df[col].value_counts().to_dict()

    if "timestamp" in df.columns:
        summary["time_span_seconds"] = float(df["timestamp"].max() - df["timestamp"].min())
        summary["time_start"] = float(df["timestamp"].min())
        summary["time_end"] = float(df["timestamp"].max())

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        summary["numeric_stats"] = df[numeric_cols].describe().to_dict()

    return summary