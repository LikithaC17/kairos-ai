"""Data sanitization, missing-value imputation, and chronological ordering.

Module: network-attack-forecasting.preprocessing.clean
Author: Vikas (Feature Engineering & Preprocessing)

Features:
- Handles and imputes missing / NaN / infinite values
- Validates and filters or repairs invalid records (durations <= 0, invalid ports, negative rates)
- Strict chronological sorting by timestamp to eliminate lookahead bias
- IP and protocol validation and dtype coercion
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd


# Default canonical column lists
CANONICAL_COLUMNS = [
    "flow_id",
    "timestamp",
    "src_ip",
    "dst_ip",
    "src_port",
    "dst_port",
    "protocol",
    "flow_duration",
    "packet_count",
    "byte_count",
    "packet_rate",
    "byte_rate",
    "inter_arrival_time",
    "connection_frequency",
    "scenario",
    "state",
    "label",
    "severity",
]

NUMERICAL_FIELDS = [
    "flow_duration",
    "packet_count",
    "byte_count",
    "packet_rate",
    "byte_rate",
    "inter_arrival_time",
    "connection_frequency",
    "src_port",
    "dst_port",
]

CATEGORICAL_FIELDS = [
    "protocol",
    "scenario",
    "state",
    "label",
    "severity",
]


def clean_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Clean missing, NaN, and infinite values in network traffic dataframe.

    Numerical missing values are imputed with domain-safe defaults:
    - flow_duration: min safe duration 1e-4
    - packet_count / byte_count: min count 1
    - packet_rate / byte_rate: 0.0 or derived
    - inter_arrival_time / connection_frequency: 1e-6
    - ports: 0

    Categorical missing values are filled with standard defaults:
    - protocol: 'TCP'
    - state: 'NORMAL'
    - label: 'BENIGN'
    - severity: 'LOW'
    - scenario: 'normal'
    """
    df = df.copy()

    # Replace inf and -inf with NaN for uniform handling
    df.replace([np.inf, -np.inf], np.nan, inplace=True)

    # Impute numerical columns
    for col in NUMERICAL_FIELDS:
        if col in df.columns:
            if col in ["flow_duration"]:
                df[col] = df[col].fillna(1e-4)
            elif col in ["packet_count", "byte_count"]:
                df[col] = df[col].fillna(1)
            elif col in ["inter_arrival_time", "connection_frequency"]:
                df[col] = df[col].fillna(1e-6)
            elif col in ["src_port", "dst_port"]:
                df[col] = df[col].fillna(0)
            else:
                df[col] = df[col].fillna(0.0)

    # Impute categorical columns
    defaults = {
        "protocol": "TCP",
        "scenario": "normal",
        "state": "NORMAL",
        "label": "BENIGN",
        "severity": "LOW",
        "src_ip": "10.0.0.1",
        "dst_ip": "10.0.0.2",
    }
    for col, default_val in defaults.items():
        if col in df.columns:
            df[col] = df[col].fillna(default_val)

    # Ensure flow_id exists
    if "flow_id" in df.columns and df["flow_id"].isna().any():
        df["flow_id"] = range(len(df))

    return df


def handle_invalid_records(df: pd.DataFrame, drop_invalid: bool = False) -> pd.DataFrame:
    """Filter or repair invalid network flow records.

    Rules enforced:
    - flow_duration > 0 (clipped to >= 1e-4)
    - packet_count >= 1 and byte_count >= 1
    - packet_rate >= 0 and byte_rate >= 0
    - port numbers in range [0, 65535]
    - valid protocols uppercase ('TCP', 'UDP', 'ICMP')
    - valid states ('NORMAL', 'ELEVATED', 'SUSPICIOUS', 'ATTACK')

    Parameters
    ----------
    df : pd.DataFrame
        Input traffic dataframe.
    drop_invalid : bool
        If True, drops unrepairable invalid rows; if False, clips/repairs them.
    """
    df = df.copy()

    if drop_invalid:
        valid_mask = pd.Series(True, index=df.index)
        if "flow_duration" in df.columns:
            valid_mask &= df["flow_duration"] > 0
        if "packet_count" in df.columns:
            valid_mask &= df["packet_count"] >= 1
        if "byte_count" in df.columns:
            valid_mask &= df["byte_count"] >= 1
        if "src_port" in df.columns:
            valid_mask &= (df["src_port"] >= 0) & (df["src_port"] <= 65535)
        if "dst_port" in df.columns:
            valid_mask &= (df["dst_port"] >= 0) & (df["dst_port"] <= 65535)
        df = df[valid_mask].copy()

    # Repair values
    if "flow_duration" in df.columns:
        df["flow_duration"] = np.clip(df["flow_duration"].astype(float), 1e-4, None)
    if "packet_count" in df.columns:
        df["packet_count"] = np.clip(df["packet_count"].astype(float), 1, None).astype(int)
    if "byte_count" in df.columns:
        df["byte_count"] = np.clip(df["byte_count"].astype(float), 1, None).astype(int)
    if "src_port" in df.columns:
        df["src_port"] = np.clip(df["src_port"].astype(float), 0, 65535).astype(int)
    if "dst_port" in df.columns:
        df["dst_port"] = np.clip(df["dst_port"].astype(float), 0, 65535).astype(int)
    if "packet_rate" in df.columns:
        df["packet_rate"] = np.clip(df["packet_rate"].astype(float), 0.0, None)
    if "byte_rate" in df.columns:
        df["byte_rate"] = np.clip(df["byte_rate"].astype(float), 0.0, None)
    if "inter_arrival_time" in df.columns:
        df["inter_arrival_time"] = np.clip(df["inter_arrival_time"].astype(float), 1e-6, None)
    if "connection_frequency" in df.columns:
        df["connection_frequency"] = np.clip(df["connection_frequency"].astype(float), 1e-6, None)

    # Standardize string fields
    if "protocol" in df.columns:
        df["protocol"] = df["protocol"].astype(str).str.upper()
        # map unknown protocols to TCP
        valid_protocols = {"TCP", "UDP", "ICMP"}
        df["protocol"] = df["protocol"].apply(lambda p: p if p in valid_protocols else "TCP")

    if "state" in df.columns:
        df["state"] = df["state"].astype(str).str.upper()
        valid_states = {"NORMAL", "ELEVATED", "SUSPICIOUS", "ATTACK"}
        df["state"] = df["state"].apply(lambda s: s if s in valid_states else "NORMAL")

    return df


def enforce_chronological_ordering(
    df: pd.DataFrame,
    timestamp_col: str = "timestamp",
) -> pd.DataFrame:
    """Sort dataframe strictly by timestamp to eliminate lookahead bias.

    If timestamp is datetime string or unix float, converts and orders.
    Resets index to ensure contiguous 0..N-1 ordering.
    """
    df = df.copy()
    if timestamp_col in df.columns:
        # Check if timestamp is datetime string or numeric
        if df[timestamp_col].dtype == object:
            parsed_ts = pd.to_datetime(df[timestamp_col], errors="coerce")
            if not parsed_ts.isna().all():
                df[timestamp_col] = parsed_ts
        df = df.sort_values(timestamp_col, ascending=True).reset_index(drop=True)
    return df


def clean_traffic_data(
    df: pd.DataFrame,
    drop_invalid: bool = False,
    sort_chronological: bool = True,
    timestamp_col: str = "timestamp",
) -> pd.DataFrame:
    """End-to-end cleaning pipeline for raw network flow data.

    1. Imputes missing/NaN/inf values
    2. Enforces non-negative valid ranges and valid category values
    3. Chronologically sorts records and resets index
    4. Ensures flow_id exists
    """
    cleaned = clean_missing_values(df)
    cleaned = handle_invalid_records(cleaned, drop_invalid=drop_invalid)

    if sort_chronological and timestamp_col in cleaned.columns:
        cleaned = enforce_chronological_ordering(cleaned, timestamp_col=timestamp_col)

    if "flow_id" not in cleaned.columns:
        cleaned.insert(0, "flow_id", range(len(cleaned)))
    else:
        # Re-number flow_id if sorted to preserve clean sequence tracking
        cleaned["flow_id"] = range(len(cleaned))

    return cleaned


def main():
    parser = argparse.ArgumentParser(description="Clean and sanitize network traffic CSV data")
    parser.add_argument("input_csv", type=Path, help="Path to input raw CSV")
    parser.add_argument("output_csv", type=Path, help="Path to output cleaned CSV")
    parser.add_argument("--drop-invalid", action="store_true", help="Drop unrepairable rows")
    args = parser.parse_args()

    if not args.input_csv.exists():
        print(f"Error: input file {args.input_csv} does not exist", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(args.input_csv)
    print(f"Loaded {len(df)} rows from {args.input_csv}")
    cleaned = clean_traffic_data(df, drop_invalid=args.drop_invalid)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(args.output_csv, index=False)
    print(f"Saved {len(cleaned)} cleaned rows to {args.output_csv}")


if __name__ == "__main__":
    main()
