"""NetForecast AI Dataset Package

Dataset acquisition, schema verification, and preparation utilities for
the AI-based Network Attack Forecasting project.
"""

from .schema import (
    ALL_COLUMNS,
    REQUIRED_COLUMNS,
    OPTIONAL_COLUMNS,
    VALID_STATES,
    VALID_LABELS,
    VALID_SEVERITIES,
    VALID_PROTOCOLS,
    VALID_SCENARIOS,
    COLUMN_DTYPES,
    MIN_VALUES,
    MAX_VALUES,
    ValidationResult,
    validate_schema,
    coerce_dtypes,
    ensure_flow_id,
    sort_by_timestamp,
)

from .ingestion import (
    load_csv,
    load_parquet,
    load_dataset,
    save_dataset,
    prepare_dataset,
    split_chronological,
    get_scenario_subset,
    get_state_subset,
    balance_dataset,
    summarize_dataset,
)

__all__ = [
    "ALL_COLUMNS",
    "REQUIRED_COLUMNS",
    "OPTIONAL_COLUMNS",
    "VALID_STATES",
    "VALID_LABELS",
    "VALID_SEVERITIES",
    "VALID_PROTOCOLS",
    "VALID_SCENARIOS",
    "COLUMN_DTYPES",
    "MIN_VALUES",
    "MAX_VALUES",
    "ValidationResult",
    "validate_schema",
    "coerce_dtypes",
    "ensure_flow_id",
    "sort_by_timestamp",
    "load_csv",
    "load_parquet",
    "load_dataset",
    "save_dataset",
    "prepare_dataset",
    "split_chronological",
    "get_scenario_subset",
    "get_state_subset",
    "balance_dataset",
    "summarize_dataset",
]

__version__ = "0.1.0"