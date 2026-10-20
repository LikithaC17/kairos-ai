"""NetForecast AI Preprocessing & Feature Engineering Package.

Module: network-attack-forecasting.preprocessing
Author: Vikas (Feature Engineering & Preprocessing)

Public API:
- clean_traffic_data: Data cleaning, missing-value imputation, chronological sorting
- extract_cyber_features: Domain cyber signals (packets/sec, bytes/sec, SYN/ACK rates, port & IP entropy)
- create_sliding_windows: Generates ML-ready temporal sequences (N, T, F) for World Model
- split_temporal_dataset: Zero-leakage chronological train/val/test splitting
- create_split_sequences: Leak-free sequence creation within split boundaries
- save_sequence_artifacts: Saves numpy arrays and aligned metadata CSVs
- TrafficPreprocessor: Complete Scikit-Learn style pipeline transformer
- CORE_WORLD_MODEL_FEATURES: 7 baseline features consumed by Likitha's GRU
- get_feature_column_names: Full ordered list of engineered cyber features
"""

from __future__ import annotations

from .clean import (
    clean_missing_values,
    clean_traffic_data,
    enforce_chronological_ordering,
    handle_invalid_records,
)
from .feature_extraction import (
    CORE_WORLD_MODEL_FEATURES,
    calculate_entropy,
    extract_cyber_features,
    get_feature_column_names,
    rolling_entropy,
)
from .pipeline import TrafficPreprocessor, run_pipeline
from .windowing import (
    LADDER_STATES,
    STATE_TO_IDX,
    STATE_TO_STAGES,
    create_sliding_windows,
    create_split_sequences,
    map_state_to_stage,
    save_sequence_artifacts,
    split_temporal_dataset,
)

__all__ = [
    # Cleaning
    "clean_traffic_data",
    "clean_missing_values",
    "handle_invalid_records",
    "enforce_chronological_ordering",
    # Features
    "extract_cyber_features",
    "calculate_entropy",
    "rolling_entropy",
    "get_feature_column_names",
    "CORE_WORLD_MODEL_FEATURES",
    # Windowing
    "create_sliding_windows",
    "split_temporal_dataset",
    "create_split_sequences",
    "save_sequence_artifacts",
    "map_state_to_stage",
    "LADDER_STATES",
    "STATE_TO_IDX",
    "STATE_TO_STAGES",
    # Pipeline
    "TrafficPreprocessor",
    "run_pipeline",
]
