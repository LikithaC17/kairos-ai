"""Unit and integration tests for Multi-Model Architectures (GRU, LSTM, Transformer).

Verifies:
1. Architecture input/output tensor shapes and log_softmax validity.
2. Dual-head independence (Head A: Current State vs Head B: Next State).
3. Checkpoint persistence and loading for GRU, LSTM, and Transformer.
4. Inference interface compatibility across all 3 models.
5. EndToEndPipeline multi-model execution and switching.
6. API routes: /api/models/comparison, /api/models/active, and /api/model/info.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from models.temporal.gru import NetworkStateGRU, STATE_LABELS, NUM_FEATURES, NUM_STATES, Log1pStandardScaler
from models.temporal.lstm import NetworkStateLSTM
from models.temporal.transformer import NetworkStateTransformer
from models.temporal.inference import load_world_model, predict, predict_batch
from pipeline.orchestrator import EndToEndPipeline
from simulation.attack_simulator import SCENARIO_GENERATORS
import pandas as pd


@pytest.fixture(scope="module")
def sample_tensor():
    torch.manual_seed(42)
    return torch.rand(4, 20, NUM_FEATURES)


@pytest.fixture(scope="module")
def single_tensor():
    torch.manual_seed(42)
    return torch.rand(1, 20, NUM_FEATURES)


@pytest.fixture(scope="module")
def sample_numpy_sequence():
    rng = np.random.default_rng(42)
    return rng.uniform(1.0, 100.0, size=(20, NUM_FEATURES)).astype(np.float32)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Architecture Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestMultiModelArchitectures:
    def test_gru_shapes_and_log_softmax(self, sample_tensor):
        model = NetworkStateGRU(input_size=NUM_FEATURES, hidden_size=64, num_layers=2, num_classes=NUM_STATES, dropout=0.0)
        model.eval()
        with torch.no_grad():
            log_curr, log_next = model(sample_tensor)

        assert log_curr.shape == (4, NUM_STATES)
        assert log_next.shape == (4, NUM_STATES)
        # Log-softmax values must be <= 0, and exp must sum to ~1.0
        assert (log_curr <= 0.0).all()
        assert (log_next <= 0.0).all()
        probs_curr = torch.exp(log_curr).sum(dim=-1)
        probs_next = torch.exp(log_next).sum(dim=-1)
        assert torch.allclose(probs_curr, torch.ones(4), atol=1e-5)
        assert torch.allclose(probs_next, torch.ones(4), atol=1e-5)

    def test_lstm_shapes_and_dual_heads(self, sample_tensor):
        model = NetworkStateLSTM(input_size=NUM_FEATURES, hidden_size=64, num_layers=2, num_classes=NUM_STATES, dropout=0.0)
        model.eval()
        with torch.no_grad():
            log_curr, log_next = model(sample_tensor)

        assert log_curr.shape == (4, NUM_STATES)
        assert log_next.shape == (4, NUM_STATES)
        # Dual head independence: Head A and Head B outputs should differ
        assert not torch.allclose(log_curr, log_next)

    def test_transformer_shapes_and_dual_heads(self, sample_tensor):
        model = NetworkStateTransformer(input_size=NUM_FEATURES, d_model=32, nhead=2, num_layers=2, num_classes=NUM_STATES, dropout=0.0)
        model.eval()
        with torch.no_grad():
            log_curr, log_next = model(sample_tensor)

        assert log_curr.shape == (4, NUM_STATES)
        assert log_next.shape == (4, NUM_STATES)
        assert not torch.allclose(log_curr, log_next)
        probs_curr = torch.exp(log_curr).sum(dim=-1)
        assert torch.allclose(probs_curr, torch.ones(4), atol=1e-4)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Checkpoint Loading & Inference Interface
# ─────────────────────────────────────────────────────────────────────────────

class TestMultiModelInference:
    @pytest.mark.parametrize("m_type", ["gru", "lstm", "transformer"])
    def test_load_and_predict_each_model(self, m_type, sample_numpy_sequence):
        ckpt_dir = PROJECT_ROOT / "checkpoints"
        model, scaler = load_world_model(ckpt_dir, model_type=m_type)
        assert model is not None
        assert scaler is not None

        res = predict(model, scaler, sample_numpy_sequence)
        assert "current_state" in res
        assert "predicted_next_state" in res
        assert "current_probabilities" in res
        assert "prediction_confidence" in res
        assert res["current_state"] in STATE_LABELS
        assert res["predicted_next_state"] in STATE_LABELS
        assert 0.0 <= res["prediction_confidence"] <= 1.0

        # Probabilities sum to ~1.0
        prob_sum = sum(res["current_probabilities"].values())
        assert abs(prob_sum - 1.0) < 0.01

    @pytest.mark.parametrize("m_type", ["gru", "lstm", "transformer"])
    def test_predict_batch_each_model(self, m_type, sample_numpy_sequence):
        ckpt_dir = PROJECT_ROOT / "checkpoints"
        model, scaler = load_world_model(ckpt_dir, model_type=m_type)
        batch_input = np.repeat(sample_numpy_sequence[np.newaxis, :, :], 5, axis=0)

        results = predict_batch(model, scaler, batch_input)
        assert len(results) == 5
        for item in results:
            assert item["current_state"] in STATE_LABELS
            assert item["predicted_next_state"] in STATE_LABELS


# ─────────────────────────────────────────────────────────────────────────────
# 3. EndToEndPipeline Multi-Model Execution
# ─────────────────────────────────────────────────────────────────────────────

class TestEndToEndMultiModelPipeline:
    @pytest.fixture(scope="class")
    def sample_traffic_df(self):
        rng = np.random.default_rng(42)
        flows = SCENARIO_GENERATORS["mixed"](rng, 25)
        flat = [r for seq in flows for r in seq]
        return pd.DataFrame(flat)

    @pytest.mark.parametrize("m_type", ["gru", "lstm", "transformer"])
    def test_pipeline_execution_with_model(self, m_type, sample_traffic_df):
        pipe = EndToEndPipeline()
        result = pipe.run(sample_traffic_df, scenario_name="mixed", model_type=m_type)

        assert result.pipeline_status.get("AI World Model", "").startswith(f"PASS ({m_type.upper()})")
        assert result.decision["active_model"] == m_type.upper()
        assert result.decision["current_state"] in STATE_LABELS
        assert result.decision["predicted_next_state"] in STATE_LABELS
        assert len(result.forecast_steps) == pipe.forecast_horizon
        assert result.inference_latency_ms >= 0.0


# ─────────────────────────────────────────────────────────────────────────────
# 4. API Endpoints
# ─────────────────────────────────────────────────────────────────────────────

class TestApiMultiModelEndpoints:
    @pytest.fixture(scope="class")
    def client(self):
        from fastapi.testclient import TestClient
        from api.app import app
        return TestClient(app)

    def test_get_benchmark_comparison(self, client):
        resp = client.get("/api/models/comparison")
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data
        assert "gru" in data["models"]
        assert "lstm" in data["models"]
        assert "transformer" in data["models"]

        for m_key in ["gru", "lstm", "transformer"]:
            m_data = data["models"][m_key]
            assert "parameters" in m_data
            assert "next_state" in m_data
            assert "accuracy" in m_data["next_state"]
            assert "f1_macro" in m_data["next_state"]
            assert "auroc_macro" in m_data["next_state"]
            assert m_data["next_state"]["accuracy"] > 0.85

    def test_active_model_switch(self, client):
        # Switch to transformer
        post_resp = client.post("/api/models/active", json={"model": "transformer"})
        assert post_resp.status_code == 200
        assert post_resp.json()["active_model"] == "transformer"

        # Verify active model is transformer
        get_resp = client.get("/api/models/active")
        assert get_resp.status_code == 200
        assert get_resp.json()["active_model"] == "transformer"

        # Revert back to baseline GRU
        post_resp2 = client.post("/api/models/active", json={"model": "gru"})
        assert post_resp2.status_code == 200
        assert post_resp2.json()["active_model"] == "gru"

    def test_model_info_dynamic_metrics(self, client):
        for m in ["gru", "lstm", "transformer"]:
            resp = client.get(f"/api/model/info?model={m}")
            assert resp.status_code == 200
            data = resp.json()
            assert data["model_key"] == m
            assert "parameters" in data
            assert data["evaluation_metrics"]["next_state_accuracy"] > 0.85
            assert data["evaluation_metrics"]["f1_score"] > 0.80
            assert data["evaluation_metrics"]["auc_roc"] > 0.90
