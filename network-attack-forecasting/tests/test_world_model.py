"""Unit and integration tests for the NetForecast AI temporal world model.

Run with:
    python -m pytest tests/test_world_model.py -v

Tests
-----
TestWorldModelArchitecture
    test_forward_output_shapes         — forward pass produces correct tensor shapes
    test_dual_head_independence        — current and next outputs differ (heads separate)
    test_log_softmax_output            — outputs are valid log-probabilities
    test_predict_dict_keys             — predict_dict() returns all required keys
    test_predict_dict_state_valid      — predicted states are from the valid label set
    test_predict_dict_probabilities_sum — current_probabilities sum to ~1.0

TestScaler
    test_fit_transform_shape           — scaler output shape matches input
    test_no_leakage_to_val             — scaler fit on train does not change on val
    test_transform_deterministic       — repeated transforms give identical results

TestInferenceInterface
    test_predict_output_schema         — predict() returns expected keys and types
    test_predict_confidence_range      — confidence is in [0, 1]
    test_predict_wrong_feature_count   — raises ValueError on bad input shape
    test_predict_1d_input_handled      — single feature vector is handled gracefully
    test_predict_batch_length          — predict_batch returns N dicts for N inputs

TestModelPersistence
    test_save_and_load_roundtrip       — saved and reloaded model produces identical output
    test_checkpoint_contains_config    — checkpoint dict has expected keys
"""

from __future__ import annotations

import pickle
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest
import torch

# ── ensure project root is importable ────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from models.temporal.lstm import (
    NetworkStateGRU,
    STATE_LABELS,
    NUM_FEATURES,
    NUM_STATES,
    FEATURE_COLUMNS,
    Log1pStandardScaler,
)
from models.temporal.inference import predict, predict_batch

# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

BATCH   = 8
SEQ_LEN = 20
F       = NUM_FEATURES   # 7


@pytest.fixture(scope="module")
def model() -> NetworkStateGRU:
    """Freshly initialised (untrained) model — sufficient for shape/schema tests."""
    m = NetworkStateGRU(
        input_size=F,
        hidden_size=64,
        num_layers=2,
        num_classes=NUM_STATES,
        dropout=0.0,      # disable dropout for deterministic tests
    )
    m.eval()
    return m


@pytest.fixture(scope="module")
def dummy_x() -> torch.Tensor:
    """Random input tensor of shape (BATCH, SEQ_LEN, F)."""
    torch.manual_seed(0)
    return torch.rand(BATCH, SEQ_LEN, F)


@pytest.fixture(scope="module")
def single_x() -> torch.Tensor:
    """Single-sequence tensor shape (1, SEQ_LEN, F)."""
    torch.manual_seed(1)
    return torch.rand(1, SEQ_LEN, F)


@pytest.fixture(scope="module")
def dummy_np_seq() -> np.ndarray:
    """Raw (unscaled) numpy sequence shape (SEQ_LEN, F)."""
    rng = np.random.default_rng(42)
    return rng.exponential(scale=50.0, size=(SEQ_LEN, F)).astype(np.float32)


@pytest.fixture(scope="module")
def fitted_scaler() -> Log1pStandardScaler:
    """Scaler fitted on synthetic training data."""
    rng = np.random.default_rng(0)
    X_train = rng.exponential(10.0, size=(200, SEQ_LEN, F)).astype(np.float32)
    scaler = Log1pStandardScaler()
    scaler.fit(X_train)
    return scaler


# ─────────────────────────────────────────────────────────────────────────────
# TestWorldModelArchitecture
# ─────────────────────────────────────────────────────────────────────────────

class TestWorldModelArchitecture:

    def test_forward_output_shapes(self, model, dummy_x):
        """Forward pass must return two tensors of shape (batch, NUM_STATES)."""
        log_curr, log_next = model(dummy_x)
        assert log_curr.shape == (BATCH, NUM_STATES), (
            f"Expected current head shape ({BATCH}, {NUM_STATES}), got {log_curr.shape}"
        )
        assert log_next.shape == (BATCH, NUM_STATES), (
            f"Expected next head shape ({BATCH}, {NUM_STATES}), got {log_next.shape}"
        )

    def test_dual_head_independence(self, model, single_x):
        """The two heads must not produce identical outputs (they have separate weights)."""
        log_curr, log_next = model(single_x)
        # Allow for the tiny probability they are identical by chance — use allclose
        are_same = torch.allclose(log_curr, log_next, atol=1e-6)
        assert not are_same, (
            "current-state and next-state heads produced identical outputs — "
            "they should have independent parameters."
        )

    def test_log_softmax_output(self, model, dummy_x):
        """Outputs must be valid log-probabilities: exp sums to ~1.0 per sample."""
        log_curr, log_next = model(dummy_x)
        prob_curr = torch.exp(log_curr)
        prob_next = torch.exp(log_next)
        torch.testing.assert_close(
            prob_curr.sum(dim=1), torch.ones(BATCH), atol=1e-5, rtol=1e-5
        )
        torch.testing.assert_close(
            prob_next.sum(dim=1), torch.ones(BATCH), atol=1e-5, rtol=1e-5
        )

    def test_predict_dict_keys(self, model, single_x):
        """predict_dict must return all four required output keys."""
        result = model.predict_dict(single_x)
        required = {"current_state", "current_probabilities",
                    "predicted_next_state", "prediction_confidence"}
        assert required == set(result.keys()), (
            f"Missing keys: {required - set(result.keys())}"
        )

    def test_predict_dict_state_valid(self, model, single_x):
        """current_state and predicted_next_state must be valid state labels."""
        result = model.predict_dict(single_x)
        assert result["current_state"]        in STATE_LABELS
        assert result["predicted_next_state"] in STATE_LABELS

    def test_predict_dict_probabilities_sum(self, model, single_x):
        """current_probabilities values must sum to ~1.0."""
        result = model.predict_dict(single_x)
        total = sum(result["current_probabilities"].values())
        assert abs(total - 1.0) < 1e-3, (
            f"current_probabilities do not sum to 1.0 (got {total})"
        )

    def test_model_parameter_count(self, model):
        """Model should have a non-trivial number of parameters (sanity check)."""
        n_params = sum(p.numel() for p in model.parameters())
        assert n_params > 1000, f"Too few parameters: {n_params}"


# ─────────────────────────────────────────────────────────────────────────────
# TestScaler
# ─────────────────────────────────────────────────────────────────────────────

class TestScaler:

    def test_fit_transform_shape(self, fitted_scaler):
        """transform() must preserve the input shape."""
        rng = np.random.default_rng(5)
        X = rng.exponential(10.0, size=(50, SEQ_LEN, F)).astype(np.float32)
        X_s = fitted_scaler.transform(X)
        assert X_s.shape == X.shape, (
            f"Scaler changed shape from {X.shape} to {X_s.shape}"
        )

    def test_no_leakage_to_val(self):
        """mean_ and std_ must be set from training data only and stay unchanged."""
        rng = np.random.default_rng(7)
        X_train = rng.exponential(10.0, size=(100, SEQ_LEN, F)).astype(np.float32)
        X_val   = rng.exponential(50.0, size=(40,  SEQ_LEN, F)).astype(np.float32)

        scaler = Log1pStandardScaler()
        scaler.fit(X_train)

        mean_before = scaler.mean_.copy()
        std_before  = scaler.std_.copy()

        # Transforming validation data must NOT change the scaler statistics
        _ = scaler.transform(X_val)

        np.testing.assert_array_equal(scaler.mean_, mean_before)
        np.testing.assert_array_equal(scaler.std_,  std_before)

    def test_transform_deterministic(self, fitted_scaler):
        """Calling transform twice on the same array gives identical results."""
        rng = np.random.default_rng(9)
        X = rng.exponential(10.0, size=(30, SEQ_LEN, F)).astype(np.float32)
        X_s1 = fitted_scaler.transform(X)
        X_s2 = fitted_scaler.transform(X)
        np.testing.assert_array_equal(X_s1, X_s2)

    def test_scaler_picklable(self, fitted_scaler):
        """Scaler must survive a pickle/unpickle cycle (required for checkpoint)."""
        blob    = pickle.dumps(fitted_scaler)
        scaler2 = pickle.loads(blob)
        rng = np.random.default_rng(11)
        X = rng.exponential(10.0, size=(10, SEQ_LEN, F)).astype(np.float32)
        np.testing.assert_array_almost_equal(
            fitted_scaler.transform(X),
            scaler2.transform(X),
        )


# ─────────────────────────────────────────────────────────────────────────────
# TestInferenceInterface
# ─────────────────────────────────────────────────────────────────────────────

class TestInferenceInterface:

    def test_predict_output_schema(self, model, fitted_scaler, dummy_np_seq):
        """predict() must return the full required output schema."""
        result = predict(model, fitted_scaler, dummy_np_seq, device="cpu")
        assert isinstance(result, dict)
        assert "current_state"         in result
        assert "current_probabilities" in result
        assert "predicted_next_state"  in result
        assert "prediction_confidence" in result
        assert isinstance(result["current_state"],         str)
        assert isinstance(result["current_probabilities"], dict)
        assert isinstance(result["predicted_next_state"],  str)
        assert isinstance(result["prediction_confidence"], float)

    def test_predict_confidence_range(self, model, fitted_scaler, dummy_np_seq):
        """prediction_confidence must be in [0.0, 1.0]."""
        result = predict(model, fitted_scaler, dummy_np_seq, device="cpu")
        conf = result["prediction_confidence"]
        assert 0.0 <= conf <= 1.0, f"Confidence out of range: {conf}"

    def test_predict_probabilities_sum(self, model, fitted_scaler, dummy_np_seq):
        """current_probabilities values must sum to ≈1.0."""
        result = predict(model, fitted_scaler, dummy_np_seq, device="cpu")
        total = sum(result["current_probabilities"].values())
        assert abs(total - 1.0) < 1e-3, f"Probs sum to {total}, expected ~1.0"

    def test_predict_wrong_feature_count(self, model, fitted_scaler):
        """predict() must raise ValueError if feature count is wrong."""
        bad_seq = np.random.rand(SEQ_LEN, F + 3).astype(np.float32)
        with pytest.raises(ValueError, match="Expected"):
            predict(model, fitted_scaler, bad_seq, device="cpu")

    def test_predict_1d_input_handled(self, model, fitted_scaler):
        """A 1-D input of length F should be accepted as a single time step."""
        single_step = np.random.rand(F).astype(np.float32)
        # Should not raise; shape (1, F) → broadcast to (1, 1, F)
        result = predict(model, fitted_scaler, single_step, device="cpu")
        assert "current_state" in result

    def test_predict_batch_length(self, model, fitted_scaler):
        """predict_batch(N sequences) must return exactly N dicts."""
        N = 12
        rng = np.random.default_rng(55)
        seqs = rng.exponential(10.0, size=(N, SEQ_LEN, F)).astype(np.float32)
        results = predict_batch(model, fitted_scaler, seqs, device="cpu")
        assert len(results) == N, f"Expected {N} results, got {len(results)}"
        for r in results:
            assert "current_state" in r

    def test_predict_state_labels_valid(self, model, fitted_scaler, dummy_np_seq):
        """Both state labels in output must belong to STATE_LABELS."""
        result = predict(model, fitted_scaler, dummy_np_seq, device="cpu")
        assert result["current_state"]        in STATE_LABELS
        assert result["predicted_next_state"] in STATE_LABELS


# ─────────────────────────────────────────────────────────────────────────────
# TestModelPersistence
# ─────────────────────────────────────────────────────────────────────────────

class TestModelPersistence:

    def test_save_and_load_roundtrip(self, model, single_x):
        """Model saved to disk and reloaded must produce identical output."""
        model.eval()
        with torch.no_grad():
            log_c_orig, log_n_orig = model(single_x)

        with tempfile.TemporaryDirectory() as tmpdir:
            ckpt_path = Path(tmpdir) / "test_model.pt"
            checkpoint = {
                "model_state_dict": model.state_dict(),
                "config": {
                    "input_size":  F,
                    "hidden_size": 64,
                    "num_layers":  2,
                    "num_classes": NUM_STATES,
                    "dropout":     0.0,
                },
                "state_labels":    STATE_LABELS,
                "feature_columns": FEATURE_COLUMNS,
            }
            torch.save(checkpoint, ckpt_path)

            # Reload
            ckpt  = torch.load(ckpt_path, map_location="cpu")
            cfg   = ckpt["config"]
            model2 = NetworkStateGRU(
                input_size=cfg["input_size"],
                hidden_size=cfg["hidden_size"],
                num_layers=cfg["num_layers"],
                num_classes=cfg["num_classes"],
                dropout=cfg["dropout"],
            )
            model2.load_state_dict(ckpt["model_state_dict"])
            model2.eval()

            with torch.no_grad():
                log_c_loaded, log_n_loaded = model2(single_x)

        torch.testing.assert_close(log_c_orig, log_c_loaded, atol=1e-6, rtol=1e-6)
        torch.testing.assert_close(log_n_orig, log_n_loaded, atol=1e-6, rtol=1e-6)

    def test_checkpoint_contains_config(self, model):
        """Saved checkpoint must contain model_state_dict and config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ckpt_path = Path(tmpdir) / "check.pt"
            checkpoint = {
                "model_state_dict": model.state_dict(),
                "config": {
                    "input_size":  F,
                    "hidden_size": 64,
                    "num_layers":  2,
                    "num_classes": NUM_STATES,
                    "dropout":     0.0,
                },
                "state_labels":    STATE_LABELS,
                "feature_columns": FEATURE_COLUMNS,
                "metrics": {"test_acc_current": 0.0, "test_acc_next": 0.0},
            }
            torch.save(checkpoint, ckpt_path)
            loaded = torch.load(ckpt_path, map_location="cpu")

        required_keys = {"model_state_dict", "config", "state_labels", "feature_columns"}
        assert required_keys.issubset(set(loaded.keys())), (
            f"Missing checkpoint keys: {required_keys - set(loaded.keys())}"
        )
        assert loaded["state_labels"] == STATE_LABELS
        assert loaded["feature_columns"] == FEATURE_COLUMNS
