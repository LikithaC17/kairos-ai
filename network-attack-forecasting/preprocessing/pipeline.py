"""End-to-end Traffic Preprocessing & Feature Pipeline for NetForecast AI.

Module: network-attack-forecasting.preprocessing.pipeline
Author: Vikas (Feature Engineering & Preprocessing)

Features:
- Fit-transform lifecycle strictly avoiding data leakage (scaler & encoder fit ONLY on train)
- Heavy-tail normalisation via Log1p + StandardScaler
- Produces model-ready temporal sequences consumed directly by Likitha's World Model (GRU / LSTM / Transformer)
- Supports both Core 7-feature set and Rich Cyber Feature set
- Full serialisation (save/load) for deployment & inference
- CLI interface for batch data processing
"""

from __future__ import annotations

import argparse
import json
import os
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from .clean import clean_traffic_data
from .feature_extraction import (
    CORE_WORLD_MODEL_FEATURES,
    extract_cyber_features,
    get_feature_column_names,
)
from .windowing import (
    create_sliding_windows,
    create_split_sequences,
    save_sequence_artifacts,
    split_temporal_dataset,
)


class TrafficPreprocessor:
    """End-to-end Preprocessor and Feature Pipeline for Network Traffic Data.

    Parameters
    ----------
    sequence_length : int
        Lookback history window length T (default 20).
    forecast_horizon : int
        Lookahead prediction step horizon K (default 1).
    use_core_features_only : bool
        If True, extracts only the 7 baseline features matching Likitha's GRU.
        If False, includes full rich cyber-domain features (entropy, flags, port distributions).
    apply_log1p : bool
        Whether to apply np.log1p before standard scaling to handle heavy-tailed network statistics.
    """

    def __init__(
        self,
        sequence_length: int = 20,
        forecast_horizon: int = 1,
        use_core_features_only: bool = False,
        apply_log1p: bool = True,
    ):
        self.sequence_length = sequence_length
        self.forecast_horizon = forecast_horizon
        self.use_core_features_only = use_core_features_only
        self.apply_log1p = apply_log1p

        self.scaler: Optional[StandardScaler] = None
        self.feature_columns: List[str] = []
        self.is_fitted: bool = False

    def _determine_feature_columns(self, df: pd.DataFrame) -> List[str]:
        """Determine valid numerical feature columns present in dataframe."""
        if self.use_core_features_only:
            cols = [c for c in CORE_WORLD_MODEL_FEATURES if c in df.columns]
        else:
            all_candidate = get_feature_column_names(include_extended=True)
            cols = [c for c in all_candidate if c in df.columns]
        return cols

    def fit(self, df_train: pd.DataFrame) -> "TrafficPreprocessor":
        """Fit preprocessor parameters strictly on training partition.

        Parameters
        ----------
        df_train : pd.DataFrame
            Raw or cleaned training traffic records.
        """
        # 1. Clean
        cleaned = clean_traffic_data(df_train, sort_chronological=True)

        # 2. Extract features
        featured = extract_cyber_features(cleaned, include_core_only=self.use_core_features_only)

        # 3. Determine feature columns
        self.feature_columns = self._determine_feature_columns(featured)

        # 4. Extract numerical matrix
        X_mat = featured[self.feature_columns].values.astype(np.float64)

        # 5. Apply Log1p if configured
        if self.apply_log1p:
            X_mat = np.log1p(np.maximum(X_mat, 0.0))

        # 6. Fit StandardScaler strictly on train
        self.scaler = StandardScaler()
        self.scaler.fit(X_mat)
        self.is_fitted = True

        return self

    def transform_df(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray]:
        """Transform raw or cleaned dataframe into scaled feature matrix using fitted parameters.

        Returns
        -------
        featured_df : pd.DataFrame
            DataFrame with all metadata, original columns, and engineered features.
        scaled_matrix : np.ndarray
            Scaled feature matrix of shape (N, F).
        """
        if not self.is_fitted or self.scaler is None:
            raise RuntimeError("TrafficPreprocessor must be fitted before calling transform_df()")

        # 1. Clean
        cleaned = clean_traffic_data(df, sort_chronological=True)

        # 2. Extract features
        featured = extract_cyber_features(cleaned, include_core_only=self.use_core_features_only)

        # Ensure all fitted feature columns exist
        for col in self.feature_columns:
            if col not in featured.columns:
                featured[col] = 0.0

        X_mat = featured[self.feature_columns].values.astype(np.float64)

        # 3. Apply Log1p if configured
        if self.apply_log1p:
            X_mat = np.log1p(np.maximum(X_mat, 0.0))

        # 4. Standard scale using training-fitted scaler
        scaled_matrix = self.scaler.transform(X_mat).astype(np.float32)

        return featured, scaled_matrix

    def transform_to_sequences(
        self,
        df: pd.DataFrame,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, pd.DataFrame]:
        """Transform dataframe directly into temporal sliding window sequences.

        Returns
        -------
        X : np.ndarray
            Shape (N, sequence_length, F).
        y_current : np.ndarray
            Shape (N,).
        y_next : np.ndarray
            Shape (N,).
        y_feat : np.ndarray
            Shape (N, F).
        meta_df : pd.DataFrame
            Target metadata and aligned attack stages.
        """
        featured_df, scaled_mat = self.transform_df(df)
        return create_sliding_windows(
            feature_matrix=scaled_mat,
            meta_df=featured_df,
            sequence_length=self.sequence_length,
            forecast_horizon=self.forecast_horizon,
        )

    def process_and_split(
        self,
        df: pd.DataFrame,
        train_frac: float = 0.70,
        val_frac: float = 0.15,
        test_frac: float = 0.15,
    ) -> Dict[str, Dict[str, Union[np.ndarray, pd.DataFrame]]]:
        """Complete leak-free pipeline:

        1. Clean and chronologically sort raw data
        2. Partition into train / val / test strictly by timestamp boundaries
        3. Fit scaler ONLY on train partition
        4. Transform each partition
        5. Generate sliding-window sequences strictly within each partition
        """
        # Step 1: Clean & sort
        cleaned = clean_traffic_data(df, sort_chronological=True)

        # Step 2: Split chronologically
        train_df, val_df, test_df = split_temporal_dataset(
            cleaned, train_frac=train_frac, val_frac=val_frac, test_frac=test_frac
        )

        # Step 3: Fit only on train
        self.fit(train_df)

        # Step 4: Transform each split
        train_feat, train_scaled = self.transform_df(train_df)
        val_feat, val_scaled = self.transform_df(val_df)
        test_feat, test_scaled = self.transform_df(test_df)

        # Step 5: Generate sequences strictly within split boundaries
        splits = {
            "train": (train_scaled, train_feat),
            "val": (val_scaled, val_feat),
            "test": (test_scaled, test_feat),
        }
        results = {}

        for name, (scaled_mat, feat_df) in splits.items():
            X, yc, yn, yf, meta = create_sliding_windows(
                feature_matrix=scaled_mat,
                meta_df=feat_df,
                sequence_length=self.sequence_length,
                forecast_horizon=self.forecast_horizon,
            )
            results[name] = {
                "X": X,
                "y_curr": yc,
                "y_next": yn,
                "y_feat": yf,
                "metadata": meta,
            }

        return results

    def save(self, filepath: Union[str, Path]) -> None:
        """Serialise fitted preprocessor to disk."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        artifact = {
            "sequence_length": self.sequence_length,
            "forecast_horizon": self.forecast_horizon,
            "use_core_features_only": self.use_core_features_only,
            "apply_log1p": self.apply_log1p,
            "feature_columns": self.feature_columns,
            "scaler": self.scaler,
            "is_fitted": self.is_fitted,
        }
        with open(filepath, "wb") as f:
            pickle.dump(artifact, f)

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "TrafficPreprocessor":
        """Load fitted preprocessor from disk."""
        with open(filepath, "rb") as f:
            artifact = pickle.load(f)

        preprocessor = cls(
            sequence_length=artifact["sequence_length"],
            forecast_horizon=artifact["forecast_horizon"],
            use_core_features_only=artifact["use_core_features_only"],
            apply_log1p=artifact["apply_log1p"],
        )
        preprocessor.feature_columns = artifact["feature_columns"]
        preprocessor.scaler = artifact["scaler"]
        preprocessor.is_fitted = artifact["is_fitted"]
        return preprocessor


def run_pipeline(
    input_path: Union[str, Path],
    output_dir: Union[str, Path],
    sequence_length: int = 20,
    forecast_horizon: int = 1,
    core_only: bool = False,
    train_frac: float = 0.70,
    val_frac: float = 0.15,
    test_frac: float = 0.15,
) -> Dict[str, Any]:
    """Execute end-to-end preprocessing, sequence generation, and artifact saving."""
    input_p = Path(input_path)
    output_d = Path(output_dir)
    output_d.mkdir(parents=True, exist_ok=True)

    print(f"[NetForecast Preprocessing] Loading {input_p}...")
    df = pd.read_csv(input_p)
    print(f"[NetForecast Preprocessing] Total records loaded: {len(df)}")

    preprocessor = TrafficPreprocessor(
        sequence_length=sequence_length,
        forecast_horizon=forecast_horizon,
        use_core_features_only=core_only,
    )

    split_results = preprocessor.process_and_split(
        df=df,
        train_frac=train_frac,
        val_frac=val_frac,
        test_frac=test_frac,
    )

    # Save sequence arrays and metadata
    saved_paths = save_sequence_artifacts(split_results, output_d)

    # Save fitted preprocessor
    preprocessor_path = output_d / "preprocessor.pkl"
    preprocessor.save(preprocessor_path)

    # Save feature metadata summary
    summary = {
        "input_file": str(input_p),
        "total_records": len(df),
        "sequence_length": sequence_length,
        "forecast_horizon": forecast_horizon,
        "feature_count": len(preprocessor.feature_columns),
        "feature_columns": preprocessor.feature_columns,
        "train_sequences": len(split_results["train"]["X"]),
        "val_sequences": len(split_results["val"]["X"]),
        "test_sequences": len(split_results["test"]["X"]),
        "X_shapes": {
            "train": list(split_results["train"]["X"].shape),
            "val": list(split_results["val"]["X"].shape),
            "test": list(split_results["test"]["X"].shape),
        },
        "preprocessor_path": str(preprocessor_path),
    }

    summary_path = output_d / "preprocessing_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"[NetForecast Preprocessing] Completed successfully!")
    print(f"  Train sequences (X): {split_results['train']['X'].shape}")
    print(f"  Val sequences   (X): {split_results['val']['X'].shape}")
    print(f"  Test sequences  (X): {split_results['test']['X'].shape}")
    print(f"  Saved artifacts to: {output_d}")

    return summary


def main():
    parser = argparse.ArgumentParser(description="Run complete NetForecast AI preprocessing pipeline")
    parser.add_argument("--input", type=Path, required=True, help="Input raw or simulated CSV")
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"), help="Output directory")
    parser.add_argument("--seq-len", type=int, default=20, help="Sequence history window length")
    parser.add_argument("--horizon", type=int, default=1, help="Forecasting step horizon")
    parser.add_argument("--core-only", action="store_true", help="Extract only core 7 baseline features")
    args = parser.parse_args()

    run_pipeline(
        input_path=args.input,
        output_dir=args.output_dir,
        sequence_length=args.seq_len,
        forecast_horizon=args.horizon,
        core_only=args.core_only,
    )


if __name__ == "__main__":
    main()
