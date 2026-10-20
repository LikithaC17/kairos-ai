"""Dataset schema definition and validation for NetForecast AI.

Defines the canonical column schema, data types, and validation rules
for network flow records consumed by the preprocessing and modeling pipelines.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = [
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

OPTIONAL_COLUMNS = [
    "syn_count",
    "ack_count",
    "fin_count",
    "rst_count",
    "syn_ack_ratio",
    "unique_dst_ports",
    "unique_dst_ips",
    "port_entropy",
]

ALL_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS

COLUMN_DTYPES = {
    "flow_id": "int64",
    "timestamp": "float64",
    "src_ip": "object",
    "dst_ip": "object",
    "src_port": "int64",
    "dst_port": "int64",
    "protocol": "object",
    "flow_duration": "float64",
    "packet_count": "int64",
    "byte_count": "int64",
    "packet_rate": "float64",
    "byte_rate": "float64",
    "inter_arrival_time": "float64",
    "connection_frequency": "float64",
    "scenario": "object",
    "state": "object",
    "label": "object",
    "severity": "object",
    "syn_count": "int64",
    "ack_count": "int64",
    "fin_count": "int64",
    "rst_count": "int64",
    "syn_ack_ratio": "float64",
    "unique_dst_ports": "int64",
    "unique_dst_ips": "int64",
    "port_entropy": "float64",
}

VALID_STATES = ["NORMAL", "ELEVATED", "SUSPICIOUS", "ATTACK"]
VALID_LABELS = ["BENIGN", "SUSPICIOUS", "ATTACK"]
VALID_SEVERITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
VALID_PROTOCOLS = ["TCP", "UDP", "ICMP"]
VALID_SCENARIOS = ["normal", "ddos", "ddos_like", "beaconing", "c2_beaconing", "mixed", "mixed_escalation", "scanning", "syn_flood", "udp_attack"]

MIN_VALUES = {
    "flow_duration": 1e-4,
    "packet_count": 1,
    "byte_count": 1,
    "packet_rate": 0.0,
    "byte_rate": 0.0,
    "inter_arrival_time": 1e-6,
    "connection_frequency": 1e-6,
    "src_port": 0,
    "dst_port": 0,
    "syn_count": 0,
    "ack_count": 0,
    "fin_count": 0,
    "rst_count": 0,
    "syn_ack_ratio": 0.0,
    "unique_dst_ports": 1,
    "unique_dst_ips": 1,
    "port_entropy": 0.0,
}

MAX_VALUES = {
    "src_port": 65535,
    "dst_port": 65535,
    "syn_ack_ratio": 1e6,
}


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    stats: dict


def validate_schema(df: pd.DataFrame) -> ValidationResult:
    """Validate DataFrame against the canonical flow schema."""
    errors = []
    warnings = []

    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        errors.append(f"Missing required columns: {sorted(missing)}")

    extra = set(df.columns) - set(ALL_COLUMNS)
    if extra:
        warnings.append(f"Extra columns not in schema: {sorted(extra)}")

    if "state" in df.columns:
        invalid_states = set(df["state"].unique()) - set(VALID_STATES)
        if invalid_states:
            errors.append(f"Invalid state values: {sorted(invalid_states)}")

    if "label" in df.columns:
        invalid_labels = set(df["label"].unique()) - set(VALID_LABELS)
        if invalid_labels:
            errors.append(f"Invalid label values: {sorted(invalid_labels)}")

    if "severity" in df.columns:
        invalid_sev = set(df["severity"].unique()) - set(VALID_SEVERITIES)
        if invalid_sev:
            errors.append(f"Invalid severity values: {sorted(invalid_sev)}")

    if "protocol" in df.columns:
        invalid_proto = set(df["protocol"].unique()) - set(VALID_PROTOCOLS)
        if invalid_proto:
            errors.append(f"Invalid protocol values: {sorted(invalid_proto)}")

    if "scenario" in df.columns:
        invalid_scen = set(df["scenario"].unique()) - set(VALID_SCENARIOS)
        if invalid_scen:
            warnings.append(f"Unknown scenario values: {sorted(invalid_scen)}")

    for col, min_val in MIN_VALUES.items():
        if col in df.columns:
            if (df[col] < min_val).any():
                errors.append(f"Column '{col}' has values below minimum {min_val}")

    for col, max_val in MAX_VALUES.items():
        if col in df.columns:
            if (df[col] > max_val).any():
                errors.append(f"Column '{col}' has values above maximum {max_val}")

    if "timestamp" in df.columns:
        if not df["timestamp"].is_monotonic_increasing:
            warnings.append("Timestamps are not monotonically increasing")
        if df["timestamp"].isna().any():
            errors.append("Timestamp column contains NaN values")
        if (df["timestamp"] < 0).any():
            errors.append("Timestamp column contains negative values")

    null_counts = df[REQUIRED_COLUMNS].isnull().sum()
    null_cols = null_counts[null_counts > 0]
    if not null_cols.empty:
        errors.append(f"Required columns have null values: {null_cols.to_dict()}")

    stats = {
        "rows": len(df),
        "columns": len(df.columns),
        "states": df["state"].value_counts().to_dict() if "state" in df.columns else {},
        "scenarios": df["scenario"].value_counts().to_dict() if "scenario" in df.columns else {},
        "protocols": df["protocol"].value_counts().to_dict() if "protocol" in df.columns else {},
        "labels": df["label"].value_counts().to_dict() if "label" in df.columns else {},
        "time_span": float(df["timestamp"].max() - df["timestamp"].min()) if "timestamp" in df.columns else 0.0,
    }

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        stats=stats,
    )


def coerce_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce DataFrame columns to canonical dtypes."""
    df = df.copy()
    for col, dtype in COLUMN_DTYPES.items():
        if col in df.columns:
            try:
                if dtype == "object":
                    df[col] = df[col].astype(str)
                elif "int" in dtype:
                    df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
                elif "float" in dtype:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            except Exception:
                pass
    return df


def ensure_flow_id(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure flow_id column exists and is sequential."""
    df = df.copy()
    if "flow_id" not in df.columns:
        df.insert(0, "flow_id", range(len(df)))
    return df


def sort_by_timestamp(df: pd.DataFrame) -> pd.DataFrame:
    """Sort DataFrame by timestamp to ensure temporal ordering."""
    if "timestamp" in df.columns:
        return df.sort_values("timestamp").reset_index(drop=True)
    return df