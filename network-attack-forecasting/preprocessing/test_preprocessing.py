"""Unit and integration tests for NetForecast AI Preprocessing & Feature Engineering.

Module: network-attack-forecasting.preprocessing.test_preprocessing
Author: Vikas (Feature Engineering & Preprocessing)

Run with:
    python -m pytest preprocessing/test_preprocessing.py -v
or:
    python preprocessing/test_preprocessing.py
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from preprocessing.clean import (
    clean_missing_values,
    clean_traffic_data,
    enforce_chronological_ordering,
    handle_invalid_records,
)
from preprocessing.feature_extraction import (
    CORE_WORLD_MODEL_FEATURES,
    calculate_entropy,
    extract_cyber_features,
    get_feature_column_names,
    rolling_entropy,
)
from preprocessing.pipeline import TrafficPreprocessor
from preprocessing.windowing import (
    LADDER_STATES,
    STATE_TO_IDX,
    create_sliding_windows,
    create_split_sequences,
    map_state_to_stage,
    split_temporal_dataset,
)


@pytest.fixture
def sample_raw_df() -> pd.DataFrame:
    """Create a realistic sample network flow dataframe for testing."""
    rng = np.random.default_rng(42)
    n = 100

    timestamps = np.sort(rng.uniform(1700000000.0, 1700010000.0, size=n))
    protocols = rng.choice(["TCP", "UDP", "ICMP"], size=n, p=[0.7, 0.25, 0.05])
    states = rng.choice(["NORMAL", "ELEVATED", "SUSPICIOUS", "ATTACK"], size=n, p=[0.5, 0.2, 0.15, 0.15])
    labels = ["BENIGN" if s == "NORMAL" else "ATTACK" for s in states]
    severities = ["LOW" if s == "NORMAL" else "HIGH" for s in states]

    df = pd.DataFrame({
        "flow_id": range(n),
        "timestamp": timestamps,
        "src_ip": [f"192.168.1.{rng.integers(1, 10)}" for _ in range(n)],
        "dst_ip": [f"10.0.0.{rng.integers(1, 5)}" for _ in range(n)],
        "src_port": rng.integers(1024, 65535, size=n),
        "dst_port": rng.choice([22, 53, 80, 443, 3306, 8080, 9999], size=n),
        "protocol": protocols,
        "flow_duration": rng.uniform(0.01, 10.0, size=n),
        "packet_count": rng.integers(1, 500, size=n),
        "byte_count": rng.integers(64, 500000, size=n),
        "packet_rate": rng.uniform(1.0, 1000.0, size=n),
        "byte_rate": rng.uniform(100.0, 100000.0, size=n),
        "inter_arrival_time": rng.uniform(0.0001, 0.5, size=n),
        "connection_frequency": rng.uniform(0.1, 50.0, size=n),
        "scenario": ["normal" if s == "NORMAL" else "mixed" for s in states],
        "state": states,
        "label": labels,
        "severity": severities,
    })
    return df


class TestDataCleaning:
    def test_missing_values_imputed(self, sample_raw_df: pd.DataFrame):
        df = sample_raw_df.copy()
        # Introduce NaNs and Infs
        df.loc[0, "flow_duration"] = np.nan
        df.loc[1, "packet_count"] = np.nan
        df.loc[2, "packet_rate"] = np.inf
        df.loc[3, "protocol"] = np.nan
        df.loc[4, "state"] = np.nan

        cleaned = clean_missing_values(df)

        assert not cleaned.isnull().values.any()
        assert not np.isinf(cleaned["packet_rate"]).any()
        assert cleaned.loc[0, "flow_duration"] >= 1e-4
        assert cleaned.loc[1, "packet_count"] >= 1
        assert cleaned.loc[3, "protocol"] == "TCP"
        assert cleaned.loc[4, "state"] == "NORMAL"

    def test_invalid_records_repaired(self, sample_raw_df: pd.DataFrame):
        df = sample_raw_df.copy()
        # Introduce invalid values
        df.loc[0, "flow_duration"] = -5.0
        df.loc[1, "src_port"] = 99999
        df.loc[2, "packet_rate"] = -100.0
        df.loc[3, "protocol"] = "unknown_proto"

        repaired = handle_invalid_records(df, drop_invalid=False)

        assert repaired.loc[0, "flow_duration"] >= 1e-4
        assert repaired.loc[1, "src_port"] <= 65535
        assert repaired.loc[2, "packet_rate"] >= 0.0
        assert repaired.loc[3, "protocol"] in ["TCP", "UDP", "ICMP"]

    def test_chronological_ordering(self, sample_raw_df: pd.DataFrame):
        df = sample_raw_df.copy()
        # Scramble ordering
        scrambled = df.sample(frac=1.0, random_state=123)
        sorted_df = enforce_chronological_ordering(scrambled, timestamp_col="timestamp")

        assert sorted_df["timestamp"].is_monotonic_increasing
        assert (sorted_df.index == range(len(sorted_df))).all()


class TestFeatureExtraction:
    def test_entropy_calculation(self):
        # Uniform distribution has maximum entropy
        series_uniform = pd.Series([1, 2, 3, 4])
        ent_uniform = calculate_entropy(series_uniform)
        assert np.isclose(ent_uniform, 2.0)  # log2(4) = 2.0

        # Constant has zero entropy
        series_constant = pd.Series([1, 1, 1, 1])
        ent_constant = calculate_entropy(series_constant)
        assert np.isclose(ent_constant, 0.0)

    def test_feature_extraction_outputs(self, sample_raw_df: pd.DataFrame):
        feat_df = extract_cyber_features(sample_raw_df, entropy_window=10)

        # Check required cyber features exist
        expected_features = [
            "packet_rate",
            "byte_rate",
            "bytes_per_packet",
            "flow_duration",
            "connection_frequency",
            "syn_rate",
            "ack_rate",
            "syn_ack_ratio",
            "dst_port_normalized",
            "dst_port_entropy",
            "src_ip_entropy",
            "inter_arrival_time",
            "time_delta",
            "protocol_TCP",
            "protocol_UDP",
            "protocol_ICMP",
        ]
        for f in expected_features:
            assert f in feat_df.columns, f"Feature {f} missing in engineered features"

        # Check valid value ranges
        assert (feat_df["bytes_per_packet"] >= 0.0).all()
        assert (feat_df["dst_port_normalized"] >= 0.0).all()
        assert (feat_df["dst_port_normalized"] <= 1.0).all()
        assert (feat_df["dst_port_entropy"] >= 0.0).all()
        assert (feat_df["src_ip_entropy"] >= 0.0).all()
        assert (feat_df["time_delta"] >= 0.0).all()


class TestTemporalWindowing:
    def test_sliding_window_shapes_and_alignment(self, sample_raw_df: pd.DataFrame):
        seq_len = 15
        horizon = 1
        num_features = 7

        feat_mat = sample_raw_df[CORE_WORLD_MODEL_FEATURES].values.astype(np.float32)
        X, yc, yn, yf, meta_df = create_sliding_windows(
            feature_matrix=feat_mat,
            meta_df=sample_raw_df,
            sequence_length=seq_len,
            forecast_horizon=horizon,
        )

        expected_n = len(sample_raw_df) - seq_len - horizon + 1
        assert X.shape == (expected_n, seq_len, num_features)
        assert yc.shape == (expected_n,)
        assert yn.shape == (expected_n,)
        assert yf.shape == (expected_n, num_features)
        assert len(meta_df) == expected_n

        # Validate target alignment: next state matches meta_df
        for i in range(min(5, expected_n)):
            target_state_name = meta_df.loc[i, "target_state"]
            assert STATE_TO_IDX[target_state_name] == yn[i]

    def test_leak_free_split_sequences(self, sample_raw_df: pd.DataFrame):
        train_df, val_df, test_df = split_temporal_dataset(sample_raw_df, 0.70, 0.15, 0.15)

        assert len(train_df) == 70
        assert len(val_df) == 15
        assert len(test_df) == 15

        # Check timestamp isolation: train < val < test
        assert train_df["timestamp"].max() <= val_df["timestamp"].min()
        assert val_df["timestamp"].max() <= test_df["timestamp"].min()

        split_seqs = create_split_sequences(
            train_df, val_df, test_df,
            feature_columns=CORE_WORLD_MODEL_FEATURES,
            sequence_length=10,
        )

        assert "train" in split_seqs
        assert "val" in split_seqs
        assert "test" in split_seqs
        assert len(split_seqs["train"]["X"]) == 70 - 10
        assert len(split_seqs["val"]["X"]) == 15 - 10
        assert len(split_seqs["test"]["X"]) == 15 - 10


class TestPipelineIntegration:
    def test_traffic_preprocessor_end_to_end(self, sample_raw_df: pd.DataFrame):
        preprocessor = TrafficPreprocessor(sequence_length=10, use_core_features_only=False)

        results = preprocessor.process_and_split(sample_raw_df, 0.70, 0.15, 0.15)

        assert preprocessor.is_fitted
        assert len(preprocessor.feature_columns) > 10
        assert "train" in results
        assert "val" in results
        assert "test" in results

        X_train = results["train"]["X"]
        assert X_train.ndim == 3
        assert X_train.shape[1] == 10
        assert X_train.shape[2] == len(preprocessor.feature_columns)

        # Test persistence
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            preprocessor.save(tmp_path)
            loaded = TrafficPreprocessor.load(tmp_path)
            assert loaded.is_fitted
            assert loaded.feature_columns == preprocessor.feature_columns

            # Transform new df with loaded preprocessor
            _, scaled_mat = loaded.transform_df(sample_raw_df.head(20))
            assert scaled_mat.shape == (20, len(preprocessor.feature_columns))
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_core_features_mode(self, sample_raw_df: pd.DataFrame):
        preprocessor = TrafficPreprocessor(sequence_length=10, use_core_features_only=True)
        results = preprocessor.process_and_split(sample_raw_df, 0.70, 0.15, 0.15)

        assert preprocessor.feature_columns == CORE_WORLD_MODEL_FEATURES
        assert results["train"]["X"].shape[2] == 7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
