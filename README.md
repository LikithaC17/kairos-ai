<div align="center">

# 🛡️ Threatora AI

### AI-Powered Network Attack Forecasting

**“Predict Tomorrow’s Threats, Today.”**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-GRU%20%7C%20LSTM%20%7C%20Transformer-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-REST%20Engine-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React%2018-SOC%20Dashboard-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-Bundler-646CFF?style=flat-square&logo=vite&logoColor=white)](https://vitejs.dev/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![Cross-Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-success?style=flat-square)](https://github.com/LikithaC17/Threatora-AI)
[![Tests](https://img.shields.io/badge/Tests-68%2F68%20Passing-brightgreen?style=flat-square&logo=pytest&logoColor=white)](https://pytest.org/)
[![MITRE ATT&CK](https://img.shields.io/badge/MITRE%20ATT%26CK-v14%20Aligned-informational?style=flat-square)](https://attack.mitre.org/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

<br/>

> **Threatora AI** is an end-to-end temporal security intelligence platform that models continuous network state dynamics, forecasts future attack states across multi-step horizons, predicts compound threat risk, maps precursors to MITRE ATT&CK techniques, and emits explainable early-warning alerts before an intrusion reaches critical impact. It features a multi-model comparative engine supporting **GRU** (baseline), **LSTM**, and **Transformer** architectures with live dynamic switching.

</div>

---

## 📌 Project Status

All core modules have been fully implemented, integrated, validated, and tested end-to-end:

| Component | Status | Notes |
| :--- | :---: | :--- |
| **System Architecture** | 🟢 Complete | Unified 11-stage pipeline orchestrator connecting all subsystems |
| **Dataset & Simulation** | 🟢 Complete | 8 synthetic scenario generators (`normal`, `scanning`, `syn_flood`, `ddos`, `beaconing`, `udp_attack`, `mixed`, `recovery`) |
| **Preprocessing & Cleaning** | 🟢 Complete | Zero-leakage imputation, chronological sorting, and protocol validation |
| **Cyber Feature Extraction** | 🟢 Complete | Core 7 time-series features + Shannon port/IP entropy, TCP flag ratios |
| **Topological Graph State** | 🟢 Complete | NetworkX graph builder computing degree, density, star score, and clustering |
| **Temporal Windowing** | 🟢 Complete | Strict sliding window sequence generation ($W=20$, $F=7$) |
| **AI Forecasting Models** | 🟢 Complete | Three distinct PyTorch sequence models: **GRU** (Baseline), **LSTM** (Recurrent), and **Transformer** (Attention) |
| **Fair Empirical Evaluation** | 🟢 Complete | Evaluated on identical held-out test split ($N=450$) reporting accuracy, Macro-F1, AUROC, latency, and parameter size |
| **Controlled Horizon Forecast**| 🟢 Complete | $K$-step lookahead state trajectory and decaying confidence projections |
| **Risk & Threat Scoring** | 🟢 Complete | Compound $0-100$ threat score combining model probabilities and anomalies |
| **MITRE ATT&CK Mapping** | 🟢 Complete | Direct heuristic alignment with 8 enterprise ATT&CK techniques |
| **Explainable AI (XAI)** | 🟢 Complete | Feature attribution vectors and natural-language SOC explanation narratives |
| **Alert Engine** | 🟢 Complete | Real-time threshold evaluation with recommended SOC containment playbooks |
| **FastAPI REST API** | 🟢 Complete | High-performance endpoints with dynamic model switching and real measured latency telemetry |
| **React SOC Dashboard** | 🟢 Complete | Vite + React 18 + Tailwind CSS interface with Live Model switching, architecture tabs, and comparative benchmark matrix |
| **Cross-Platform Support** | 🟢 Complete | Native scripts for Windows (`run.bat`), Linux/macOS (`run.sh`), and Docker |
| **Test Verification** | 🟢 Complete | **68/68 tests passing** (Pipeline: 11, Multi-Models: 15, Engine: 17, World Model: 16, Preprocessing: 9) |

---

## 📑 Table of Contents

1. [Work Process & Pipeline Workflow](#1-work-process--pipeline-workflow)
2. [Problem Statement & Motivation](#2-problem-statement--motivation)
3. [System Architecture](#3-system-architecture)
4. [The 11-Stage End-to-End Pipeline](#4-the-11-stage-end-to-end-pipeline)
5. [AI World Models & Forecasting Engine](#5-ai-world-models--forecasting-engine)
   - [Empirical Multi-Model Benchmark Comparison](#empirical-multi-model-benchmark-comparison)
   - [Architectural Deep Dive: GRU, LSTM, and Transformer](#architectural-deep-dive-gru-lstm-and-transformer)
   - [Dynamic Runtime Model Switching](#dynamic-runtime-model-switching)
6. [Threat Scoring & State Transition Ladder](#6-threat-scoring--state-transition-ladder)
7. [MITRE ATT&CK & Explainable AI](#7-mitre-attck--explainable-ai)
8. [Cross-Platform Execution Guide](#8-cross-platform-execution-guide)
9. [Model Training & Evaluation Protocol](#9-model-training--evaluation-protocol)
10. [REST API Documentation](#10-rest-api-documentation)
11. [SOC Dashboard Guide](#11-soc-dashboard-guide)
12. [Repository Structure](#12-repository-structure)
13. [Author & Single Contributor](#13-author--single-contributor)
14. [Test Suite & Verification Results](#14-test-suite--verification-results)
15. [License](#15-license)

---

## 1. Work Process & Pipeline Workflow

The operational work process of Threatora AI converts raw network flows into proactive early-warning intelligence through an unbroken 11-stage flow:

```text
       1. TRAFFIC INGESTION / ATTACK SIMULATION
                          ↓
       2. DATA CLEANING & REPAIR (Preprocessing & Feature Engine)
                          ↓
       3. CYBER FEATURE ENGINEERING (Preprocessing & Feature Engine)
                          ↓
       4. TOPOLOGICAL NETWORK GRAPH CONSTRUCTION (Security Intelligence Engine)
                          ↓
       5. TEMPORAL SLIDING WINDOWING (Preprocessing & Feature Engine)
                          ↓
       6. DUAL-HEAD WORLD MODEL INFERENCE (GRU / LSTM / Transformer)
             ┐œ── Head A: Current Security State Classification
             ┐”── Head B: Next Security State Prediction
                          ↓
       7. K-STEP LOOKAHEAD HORIZON FORECASTING (Prediction Engine)
                          ↓
       8. COMPOUND THREAT & RISK SCORING (Prediction Engine)
                          ↓
       9. MITRE ATT&CK TACTIC & TECHNIQUE MAPPING (Security Intelligence Engine)
                          ↓
      10. EXPLAINABLE AI (XAI) ATTRIBUTION (Security Intelligence Engine)
                          ↓
      11. SOC EARLY WARNING ALERT & MITIGATION PLAYBOOK (Security Intelligence Engine)
                          ↓
      12. REACT SOC DASHBOARD VISUALIZATION & DYNAMIC MODEL SWITCHER
```

---

## 2. Problem Statement & Motivation

Traditional Network Intrusion Detection Systems (NIDS) are inherently **reactive**:
1. **Lagging Detection:** An alert fires only after high-volume malicious traffic has already overwhelmed network boundaries.
2. **Alert Fatigue:** SOC analysts are inundated with thousands of isolated alerts without temporal context or attack trajectory insight.
3. **Black-Box Confusion:** Alerts rarely provide actionable intelligence connecting observed precursors to forward-looking MITRE ATT&CK techniques.

**Threatora AI transforms network defense from reactive detection to predictive forecasting:**
- Instead of detecting attacks after the fact, Threatora AI continuously projects the network's state trajectory forward in time ($t+1, t+2, \dots, t+K$).
- It correlates subtle reconnaissance and staging precursors (port scans, SYN asymmetry, C2 beacons) to predict transitions into full-blown DDoS or exfiltration before disruption occurs.

---

## 3. System Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                            THREATORA AI PLATFORM                               │
┐”─────────────────────────────────────────────────────────────────────────────┐˜
                                      │
       ┌──────────────────────────────┐´──────────────────────────────┐
       ▼                                                             ▼
┌──────────────────────────────┐              ┌──────────────────────────────┐
│     FASTAPI REST ENGINE      │              │     REACT SOC DASHBOARD      │
│  (Port 8000 / Async Telemetry)│              │    (Port 5173 / Vite + TS)   │
┐”──────────────────────────────┐˜              ┐”──────────────────────────────┐˜
       │                                                             │
       ▼                                                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         11-STAGE PIPELINE ENGINE                            │
┐œ─────────────────────────────────────────────────────────────────────────────┐¤
│ 1. Ingestion    2. Cleaning    3. Features   4. Graph State  5. Windowing   │
│                                                                             │
│ 6. World Models (Dual-Head PyTorch Sequence Architectures)                 │
│    ┐œ── GRU (Baseline): 2-Layer Recurrent Gated Unit (168k params)          │
│    ┐œ── LSTM: 2-Layer Long Short-Term Memory with Cell State (219k params)   │
│    ┐”── Transformer: Sinusoidal Positional Encoding + Attention (76k params) │
│                                                                             │
│ 7. Forecasting  8. Risk Engine 9. MITRE Map  10. XAI Vectors 11. Alerts     │
┐”─────────────────────────────────────────────────────────────────────────────┐˜
```

---

## 4. The 11-Stage End-to-End Pipeline

### Stage 1: Traffic Ingestion & Attack Simulation
Ingests raw NetFlow/IPFIX records, PCAP exports, or on-demand synthetic multi-stage scenarios:
* `normal`: Legitimate enterprise communications (HTTP, HTTPS, DNS, SSH).
* `scanning`: Vertical and horizontal port enumeration sweeps.
* `syn_flood`: High-frequency TCP SYN packet flood with asymmetric completion.
* `ddos`: High-throughput distributed volumetric traffic saturation.
* `beaconing`: Periodic C2 heartbeats with consistent inter-arrival times.
* `udp_attack`: High-rate UDP datagram flood.
* `mixed_escalation`: Progressive ramp from normal baseline to full attack.
* `recovery`: Stepwise cool-down from active attack back to normal operations.

### Stage 2: Data Cleaning & Preprocessing ([`clean.py`](network-attack-forecasting/preprocessing/clean.py))
* Chronological timestamp sorting to guarantee causal sequence alignment.
* Outlier clipping and zero-leakage missing-value imputation (forward fill and median baseline).
* Protocol standardization and port range categorization.

### Stage 3: Cyber Feature Engineering ([`feature_extraction.py`](network-attack-forecasting/preprocessing/feature_extraction.py))
Extracts the **Core 7 Time-Series Features** consumed by all sequence models:
1. `flow_duration`: Duration of network connection in seconds.
2. `packet_count`: Total packets transmitted in the window.
3. `byte_count`: Total volume transferred in bytes.
4. `packet_rate`: Packet velocity ($\text{packets} / \text{sec}$).
5. `byte_rate`: Bandwidth throughput ($\text{bytes} / \text{sec}$).
6. `inter_arrival_time`: Delta between consecutive packets.
7. `connection_frequency`: Active connection initiation frequency.

Additional domain features extracted include Shannon entropy for destination ports and source IPs, SYN/ACK ratios, and host continuity flags.

### Stage 4: Topological Network Graph ([`network_graph.py`](network-attack-forecasting/graph/network_graph.py))
Builds directed graph $G_t = (V, E)$ for each window:
* **Nodes ($V$):** Internal and external IP endpoints.
* **Edges ($E$):** Active network flows weighted by byte count and protocol.
* **Metrics:** Degree centrality, density, clustering coefficients, and star score (detecting centralized scanning hubs and C2 controllers).

### Stage 5: Temporal Windowing ([`windowing.py`](network-attack-forecasting/preprocessing/windowing.py))
Constructs temporal sequence matrices with sliding window length $T=20$ and feature dimension $F=7$. Temporal boundaries are strictly enforced to prevent future-data leakage across splits.

### Stage 6: AI World Model Inference ([`inference.py`](network-attack-forecasting/models/temporal/inference.py))
Executes the dynamically active sequence model (**GRU**, **LSTM**, or **Transformer**):
* Preprocessed via `Log1pStandardScaler` fitted strictly on training data.
* **Head A (Current State):** Classifies the observed window into 4 security states.
* **Head B (Next State):** Forecasts the security state for step $t+1$.

### Stage 7: K-Step Lookahead Forecasting ([`prediction_engine.py`](network-attack-forecasting/prediction/prediction_engine.py))
Projects future trajectories over $K=3$ future horizons ($+5\text{s}, +10\text{s}, +15\text{s}$) combining model probability outputs with state transition dynamics, calculating decaying confidence margins:

$$\text{Confidence}_{t+k} = \max\left(0.10, \;\text{Confidence}_t - k \times 0.08\right)$$

### Stage 8: Threat & Risk Scoring ([`risk_scorer.py`](network-attack-forecasting/prediction/risk_scorer.py))
Computes a compound $0-100$ threat score:

$$\text{Score} = 0.45 \times \text{StateSeverity} + 0.35 \times \text{AnomalyPoints} + 0.20 \times \text{PersistenceScore}$$

* **$0 - 29$:** LOW Risk (Normal baseline activity)
* **$30 - 59$:** MEDIUM Risk (Elevated reconnaissance)
* **$60 - 79$:** HIGH Risk (Suspicious staging / C2 activity)
* **$80 - 100$:** CRITICAL Risk (Active attack / Volumetric impact)

### Stage 9: MITRE ATT&CK Mapping ([`attack_mapping.py`](network-attack-forecasting/mitre/attack_mapping.py))
Automatically correlates detected and forecasted stages to official MITRE Enterprise ATT&CK techniques:
* `T1046`: Network Service Discovery (Port Scanning)
* `T1595`: Active Scanning (IP sweeps)
* `T1110`: Brute Force Authentication
* `T1021`: Remote Services (Lateral Movement)
* `T1071`: Application Layer Protocol (C2 Beaconing)
* `T1048`: Exfiltration Over Alternative Protocol
* `T1498`: Network Denial of Service (SYN / UDP Flooding)
* `T1486`: Data Encrypted for Impact

### Stage 10: Explainable AI ([`shap_analysis.py`](network-attack-forecasting/explainability/shap_analysis.py))
Calculates feature attribution weights to identify the exact telemetry indicators driving the forecast and generates natural-language explanations for SOC analysts.

### Stage 11: Alert & SOC Playbook Generation ([`alert_engine.py`](network-attack-forecasting/prediction/alert_engine.py))
Generates structured early-warning alerts whenever the threat score exceeds the threshold ($35$), packaging the alert with MITRE IDs, observed evidence, and actionable containment playbooks.

---

## 5. AI World Models & Forecasting Engine

Threatora AI implements **three distinct temporal sequence forecasting architectures**, each maintaining a **dual-head structure** where Head A classifies the observed current network state and Head B forecasts the next state $t+1$:

```text
Input Tensor: (Batch, T=20, F=7)
       │
       ▼
Log1p Normalisation  ──▶  Temporal Backbone (GRU / LSTM / Transformer)
                                   │
                                   ▼
                         Final Latent Representation (dim: 128 / 64)
                                   │
                  ┌────────────────┐´────────────────┐
                  ▼                                 ▼
          [ HEAD A: Current ]              [ HEAD B: Next State ]
         Linear(H → 64) + ReLU            Linear(H → 64) + ReLU
         Linear(64 → 4) + LogSoftmax      Linear(64 → 4) + LogSoftmax
                  │                                 │
                  ▼                                 ▼
        P(State_t | X_<=t)                P(State_t+1 | X_<=t)
```

### Empirical Multi-Model Benchmark Comparison

All three architectures were trained and evaluated on an **identical held-out test split ($N=450$)** with zero temporal data leakage across sessions. Below are the measured empirical results:

| Metric / Attribute | GRU (Baseline) | LSTM (Recurrent) | Transformer (Self-Attention) |
| :--- | :---: | :---: | :---: |
| **Model Type** | 2-Layer Recurrent Gated Unit | 2-Layer LSTM with Cell State | 2-Layer Multi-Head Self-Attention |
| **Trainable Parameters** | 168,712 | 219,272 | **76,424 (Lightest)** |
| **Checkpoint Size** | 665.6 KB | 863.2 KB | **438.6 KB (Smallest)** |
| **Inference Latency (1 sample)** | 2.30 ms | 1.92 ms | **1.01 ms (Fastest)** |
| **Batch-32 Latency** | 5.98 ms | 6.84 ms | **3.89 ms** |
| **Next State Accuracy** | **94.44%** | 92.00% | 93.78% |
| **Current State Accuracy** | **93.11%** | 90.67% | 91.56% |
| **Next State Macro-F1** | **0.9238** | 0.8631 | 0.9127 |
| **Next State Macro-AUROC**| **0.9933** | 0.9927 | 0.9925 |
| **Primary Strength** | **Highest overall accuracy & F1 score** | Explicit cell memory & sequence capacity | **54.7% fewer parameters & $2.3\times$ faster inference** |

#### Class-Wise Performance Breakdown (Next State Task, Held-Out Test Set)

| Security State | Support | GRU Precision / Recall / F1 | LSTM Precision / Recall / F1 | Transformer Precision / Recall / F1 |
| :--- | :---: | :---: | :---: | :---: |
| **NORMAL** | 95 | **1.000 / 1.000 / 1.000** | 1.000 / 1.000 / 1.000 | 1.000 / 1.000 / 1.000 |
| **ELEVATED** | 40 | **0.805 / 0.825 / 0.815** | 0.857 / 0.600 / 0.706 | 0.773 / 0.850 / 0.810 |
| **SUSPICIOUS**| 114 | **0.927 / 0.886 / 0.906** | 0.849 / 0.789 / 0.818 | 0.922 / 0.825 / 0.870 |
| **ATTACK** | 201 | 0.960 / 0.985 / 0.972 | 0.965 / 0.980 / 0.972 | **0.952 / 0.990 / 0.971** |

> **Key Empirical Insight:** In accordance with rigorous scientific evaluation, we avoid claiming Transformer is universally best. On this structured tabular network telemetry dataset, the **GRU baseline achieves the best classification accuracy (94.44%) and Macro-F1 (0.9238)**, while the **Transformer delivers the lowest computational footprint (76k parameters) and fastest execution latency (1.01 ms)**.

### Architectural Deep Dive: GRU, LSTM, and Transformer

1. **GRU (Baseline) — [`models/temporal/gru.py`](network-attack-forecasting/models/temporal/gru.py):**
   - 2-layer Gated Recurrent Unit, hidden dimension 128, dropout 0.3.
   - Combines reset and update gates to track short-to-medium dependencies without excessive parameter bloat.
   - Dual linear projection heads ($128 \to 64 \to 4$).

2. **LSTM (Recurrent) — [`models/temporal/lstm.py`](network-attack-forecasting/models/temporal/lstm.py):**
   - 2-layer Long Short-Term Memory network, hidden dimension 128, dropout 0.3.
   - Explicit memory cell ($C_t$) and hidden state ($h_t$) to mitigate vanishing gradients across longer flow histories.
   - Dual linear projection heads ($128 \to 64 \to 4$).

3. **Transformer (Self-Attention) — [`models/temporal/transformer.py`](network-attack-forecasting/models/temporal/transformer.py):**
   - Linear feature projection to $d_{\text{model}}=64$.
   - Sinusoidal temporal positional encoding capturing flow ordering without recurrence.
   - 2 Transformer Encoder layers with 4 attention heads each, feed-forward dimension $d_{\text{ff}}=128$, and layer normalization.
   - Sequence pooling with dual linear projection heads ($64 \to 64 \to 4$).

### Dynamic Runtime Model Switching

The system provides live model switching without restarting the backend:
- Query active model: `GET /api/models/active`
- Switch active model: `POST /api/models/active` with `{"model": "transformer"}`
- Retrieve full comparison matrix: `GET /api/models/comparison`
- Dashboard UI allows SOC operators to select any model tab on **Model Insights** and activate it with 1 click.

---

## 6. Threat Scoring & State Transition Ladder

The internal security state machine enforces an escalating and recovering transition ladder:

$$\textbf{NORMAL} \;\rightleftharpoons\; \textbf{ELEVATED} \;\rightleftharpoons\; \textbf{SUSPICIOUS} \;\rightleftharpoons\; \textbf{ATTACK}$$

### State Ladder Characteristics

| State | Typical Traffic Signal | Attack Stage Mapping | Baseline Threat Score |
| :--- | :--- | :--- | :--- |
| **NORMAL** | Standard web, DNS, API traffic | Baseline Operations | $0 - 20$ |
| **ELEVATED** | Port sweeps, high destination port entropy | Reconnaissance, Scanning | $21 - 45$ |
| **SUSPICIOUS** | Low-frequency periodic beacons, bursty connections | Initial Access, C2 Channel | $46 - 70$ |
| **ATTACK** | Packet floods, extreme throughput, SYN asymmetry | Lateral Movement, Impact | $71 - 100$ |

### Recovery Transition Mechanics
When attack traffic ceases and normal baseline traffic returns, the system transitions downward through history, acknowledging recovery explicitly:

$$\text{ATTACK } (t=1, \text{Score } 95) \;\longrightarrow\; \text{NORMAL } (t=2, \text{Stage: Recovery}, \text{Score } 8) \;\longrightarrow\; \text{NORMAL } (t=3, \text{Stage: Baseline}, \text{Score } 2)$$

---

## 7. MITRE ATT&CK & Explainable AI

For every observation window, Threatora AI produces an integrated Threat Intelligence and Explainability payload:

```json
{
  "current_state": "ATTACK",
  "threat_type": "Volumetric DDoS Attack",
  "threat_score": 95,
  "risk_level": "CRITICAL",
  "confidence": 1.0,
  "predicted_next_state": "NORMAL",
  "predicted_stage": "Recovery",
  "prediction_confidence": 0.92,
  "mitre_mapping": {
    "tactic": "Impact",
    "tactic_id": "TA0040",
    "technique": "Network Denial of Service",
    "technique_id": "T1498",
    "confidence": 0.95,
    "mitigations": [
      "Activate BGP Anycast and upstream scrubbing centers.",
      "Enable SYN cookies on perimeter load balancers."
    ]
  },
  "explainability": {
    "important_features": ["packet_rate", "byte_rate", "connection_frequency"],
    "explanation": "Prediction of ATTACK (Threat Score: 95) is primarily driven by abnormal elevation in: packet_rate (+1.00), byte_rate (+1.00)."
  }
}
```

---

## 8. Cross-Platform Execution Guide

Threatora AI is tested and operational across **Windows**, **Linux**, **macOS**, and **Docker**.

### Method 1: Linux & macOS (1-Command Script)

```bash
# Clone the repository
git clone https://github.com/LikithaC17/Threatora-AI.git
cd Threatora-AI

# Run startup script
chmod +x run.sh
./run.sh
```

### Method 2: Windows (1-Click Batch File)

Double-click **`run.bat`** or run in PowerShell / CMD:

```powershell
.\run.bat
```

### Method 3: Universal Docker Containerization (Any OS)

Run the multi-container production system (FastAPI backend + Nginx frontend):

```bash
# 1. Build backend and frontend images
docker compose build

# 2. Launch all services
docker compose up
```

Services will be accessible at:
- **Threatora AI Dashboard**: [http://localhost:5173](http://localhost:5173)
- **FastAPI Backend & Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Verification**: [http://localhost:8000/health](http://localhost:8000/health)

### Method 4: Manual Step-by-Step Execution

#### Step 1: Install Python Dependencies
```bash
cd network-attack-forecasting
python -m venv .venv

# Activate venv
# Linux/macOS: source .venv/bin/activate
# Windows:     .venv\Scripts\activate

pip install -r requirements.txt
```

#### Step 2: Start FastAPI Backend
```bash
python -m uvicorn api.app:app --host 127.0.0.1 --port 8000
```

#### Step 3: Start React Dashboard
```bash
cd dashboard
npm install
npm run dev
```

---

## 9. Model Training & Evaluation Protocol

Threatora AI provides reproducible scripts for training and evaluating all three models under identical temporal splits:

### 1. Train Sequence Models
```bash
cd network-attack-forecasting

# Train baseline GRU
python models/temporal/train.py --model gru --epochs 30 --batch_size 32

# Train recurrent LSTM
python models/temporal/train.py --model lstm --epochs 30 --batch_size 32

# Train multi-head Transformer
python models/temporal/train.py --model transformer --epochs 30 --batch_size 32

# Train all three models in sequence
python models/temporal/train.py --model all
```

### 2. Fair Model Evaluation & Benchmark Generation
```bash
# Evaluate all models on held-out test data and generate benchmark_comparison.json
python models/temporal/evaluate.py --model all
```

This generates:
- `checkpoints/benchmark_comparison.json`: Complete empirical comparison metrics.
- `checkpoints/confusion_matrix_{gru,lstm,transformer}_{current,next}.png`: Confusion matrix plots.
- `checkpoints/eval_report.json`: Summary evaluation report.

---

## 10. REST API Documentation

When the backend runs, interactive Swagger documentation is available at **`http://127.0.0.1:8000/docs`**.

| Endpoint | Method | Purpose |
| :--- | :---: | :--- |
| `/health` or `/api/health` | `GET` | Health check reporting backend status, model readiness, active model, and real latency. |
| `/api/predict/current` | `GET` | Returns current security decision, alerts, graph snapshot, and timeline. |
| `/api/models/comparison` | `GET` | Returns side-by-side empirical benchmark metrics for GRU, LSTM, and Transformer. |
| `/api/models/active` | `GET` | Returns the currently active world model identifier. |
| `/api/models/active` | `POST` | Dynamically switches active model (`{"model": "gru" \| "lstm" \| "transformer"}`). |
| `/api/model/info` | `GET` | Returns architectural specifications and empirical metrics (`?model=transformer`). |
| `/api/simulate` | `POST` | Simulates an attack scenario (`scanning`, `ddos`, etc.) through the full pipeline. |
| `/api/traffic/analyze` | `POST` | Ingests raw traffic flow records and executes the 11-stage pipeline. |
| `/api/mitre/techniques` | `GET` | Returns the official enterprise MITRE ATT&CK technique catalog. |
| `/api/pipeline/status` | `GET` | Operational status check across all 11 individual pipeline stages. |

---

## 11. SOC Dashboard Guide

Open [**`http://localhost:5173`**](http://localhost:5173) in your web browser:

1. **Header Bar:** Displays live backend connection status, active model badge (GRU / LSTM / Transformer), and measured inference latency (`~2-6 ms`).
2. **Model Insights Page:**
   - **Architecture Inspection Tabs:** Deep-dive into GRU, LSTM, and Transformer specifications, hidden dimensions, heads, and parameters.
   - **Active Model Switcher:** Switch the operational live model in real time.
   - **Side-by-Side Comparison Matrix:** Complete empirical table comparing parameter count, checkpoint size, latency, Next-State accuracy, Macro-F1, and AUROC.
3. **Scenario Test Suite:** Trigger on-demand simulation runs (`Normal`, `Elevated`, `Suspicious`, `Attack`, `Recovery`).
4. **World Model Transition Diagram:** Visualizes current state vs. forecasted next state with confidence bars.
5. **Security State Cards:** Displays compound Threat Score, Risk Level, Attack Stage, and Model Confidence.
6. **Evidence & Feature Panel:** Identifies driving anomalies and traffic distributions.
7. **Predictive Timeline:** Forward lookahead projections ($+5\text{s}, +10\text{s}, +15\text{s}$) with packet rates.
8. **Alerts Feed:** Actionable early warnings with MITRE mitigation playbooks.

---

## 12. Repository Structure

```text
Threatora-AI/
┐œ── run.sh                          # One-command startup script for Linux/macOS
┐œ── run.bat                         # One-command startup script for Windows
┐œ── Dockerfile                      # Production Docker container image
┐œ── docker-compose.yml              # Multi-container orchestration (Backend + Dashboard)
┐œ── README.md                       # Master research and integration documentation
┐œ── .gitignore                      # Git ignore rules
│
┐”── network-attack-forecasting/
    ┐œ── requirements.txt            # Python dependencies
    ┐œ── .gitignore                  # Subdirectory cache exclusions
    │
    ┐œ── checkpoints/
    │   ┐œ── world_model_gru.pt      # Trained Dual-Head GRU baseline PyTorch model
    │   ┐œ── world_model_lstm.pt     # Trained Dual-Head LSTM PyTorch model
    │   ┐œ── world_model_transformer.pt # Trained Dual-Head Transformer PyTorch model
    │   ┐œ── world_model_scaler.pkl  # Fitted Log1p Standard Scaler
    │   ┐”── benchmark_comparison.json # Empirical multi-model benchmark evaluation
    │
    ┐œ── configs/
    │   ┐”── config.yaml             # System hyperparameters and configuration
    │
    ┐œ── dataset/
    │   ┐œ── ingestion.py            # Flow & packet ingestion logic
    │   ┐”── schema.py               # Dataset validation schemas
    │
    ┐œ── preprocessing/
    │   ┐œ── clean.py                # Data sanitization and chronological sorting
    │   ┐œ── feature_extraction.py   # Core 7 features + cyber domain metrics
    │   ┐œ── pipeline.py             # Preprocessing orchestration pipeline
    │   ┐”── windowing.py            # Sliding temporal window generator (T=20, F=7)
    │
    ┐œ── graph/
    │   ┐”── network_graph.py        # NetworkX topological graph builder (G_t)
    │
    ┐œ── models/
    │   ┐œ── baseline/
    │   │   ┐œ── logistic_regression.py # L2-regularized baseline forecaster
    │   │   ┐”── xgboost_forecaster.py  # Gradient-boosted sequence forecaster
    │   ┐”── temporal/
    │       ┐œ── gru.py              # Dual-Head NetworkStateGRU architecture
    │       ┐œ── lstm.py             # Dual-Head NetworkStateLSTM architecture
    │       ┐œ── transformer.py      # Dual-Head NetworkStateTransformer architecture
    │       ┐œ── inference.py        # Multi-model inference loader and execution engine
    │       ┐œ── train.py            # Multi-model training pipeline (--model all)
    │       ┐”── evaluate.py         # Multi-model evaluation and benchmark reporter
    │
    ┐œ── prediction/
    │   ┐œ── schemas.py              # SecurityDecision and WorldModelOutput contracts
    │   ┐œ── state_machine.py        # Temporal state ladder and recovery mapping
    │   ┐œ── threat_classifier.py    # Threat category heuristics
    │   ┐œ── risk_scorer.py          # Compound 0-100 risk scoring formula
    │   ┐œ── evidence.py             # Behavioral indicator extraction
    │   ┐œ── alert_engine.py         # Structured SOC alerting engine
    │   ┐”── prediction_engine.py    # Master engine orchestrating prediction & K-step forecast
    │
    ┐œ── simulation/
    │   ┐œ── attack_simulator.py     # Master attack simulation CLI and scenario registry
    │   ┐œ── normal.py               # Normal baseline flow generator
    │   ┐œ── scanning.py             # Reconnaissance port scan generator
    │   ┐œ── syn_flood.py            # TCP SYN flood generator
    │   ┐œ── ddos.py                 # Volumetric DDoS attack generator
    │   ┐œ── beaconing.py            # C2 beaconing generator
    │   ┐œ── udp_attack.py           # High-rate UDP flood generator
    │   ┐œ── mixed_escalation.py     # Multi-stage escalation ramp generator
    │   ┐”── common.py               # Shared IP/port synthesis utilities
    │
    ┐œ── mitre/
    │   ┐”── attack_mapping.py       # Enterprise MITRE ATT&CK technique mapping
    │
    ┐œ── explainability/
    │   ┐”── shap_analysis.py        # Feature contribution attribution & explanation
    │
    ┐œ── pipeline/
    │   ┐”── orchestrator.py         # EndToEndPipeline master orchestrator (11 stages)
    │
    ┐œ── api/
    │   ┐”── app.py                  # FastAPI REST serving service
    │
    ┐œ── dashboard/                  # React 18 + Vite SOC Dashboard
    │   ┐œ── src/
    │   │   ┐œ── components/         # UI Components (Header, Cards, Timeline, Alerts, etc.)
    │   │   ┐œ── pages/              # ModelInsights, Dashboard, Alerts, MITRE, Simulation
    │   │   ┐œ── services/           # Typed API clients (modelApi, forecastApi, simulationApi)
    │   │   ┐œ── types/              # TypeScript interfaces mirroring Python schemas
    │   │   ┐”── App.tsx             # Root dashboard component
    │   ┐œ── package.json
    │   ┐”── vite.config.ts
    │
    ┐”── tests/                      # Automated Test Suite (68/68 Passing)
        ┐œ── test_end_to_end_pipeline.py # Full pipeline, states 1-5, and API tests
        ┐œ── test_multi_models.py        # GRU, LSTM, Transformer architecture & API tests
        ┐œ── test_prediction_engine.py   # Schemas, forecasting, and risk scoring tests
        ┐œ── test_world_model.py         # Architecture, dual-head, and scaler tests
        ┐”── test_preprocessing.py       # Cleaning, feature extraction, and windowing tests
```

---

## 13. Author & Single Contributor

**Threatora AI** was designed, architected, and developed end-to-end by **Likitha C** ([@LikithaC17](https://github.com/LikithaC17)) as a unified predictive network security and temporal attack forecasting platform.

| Subsystem | Engineering Deliverables & Implementation |
| :--- | :--- |
| **Forecasting Sequence Models** | Implemented three dual-head architectures: baseline `NetworkStateGRU`, recurrent `NetworkStateLSTM`, and multi-head attention `NetworkStateTransformer` with zero-leakage training in `models/temporal/`. |
| **Comparative Benchmark Engine** | Built fair empirical evaluation pipeline reporting accuracy, macro-F1, AUROC, latency, and parameter footprint side-by-side on held-out test data in `models/temporal/evaluate.py`. |
| **Dynamic Model Orchestration** | Implemented multi-model caching and runtime model switching in `pipeline/orchestrator.py` and `api/app.py`. |
| **Dataset & Attack Simulation** | Multi-protocol synthetic flow schemas and 8 discrete scenario generators (`normal`, `scanning`, `syn_flood`, `ddos`, `beaconing`, `udp_attack`, `mixed_escalation`, `recovery`) in `simulation/`. |
| **Preprocessing & Feature Engineering** | Zero-leakage chronological sorting, missing-value imputation, protocol validation, 7 continuous temporal cyber features, Shannon port/IP entropy, and sliding temporal windowing ($W=20, F=7$) in `preprocessing/`. |
| **Topological Network Graph** | Dynamic directed NetworkX graph engine constructing $G_t = (V, E)$ to calculate degree centrality, density, clustering coefficients, and star topology scanning hub detection in `graph/`. |
| **Compound Threat & Risk Scoring** | Quantitative $0-100$ compound threat scoring algorithm, state transition ladder, and automated SOC containment playbooks in `prediction/`. |
| **MITRE ATT&CK & Explainable AI** | Enterprise ATT&CK v14 heuristic technique alignment (`T1046`, `T1595`, `T1110`, `T1021`, `T1071`, `T1048`, `T1498`, `T1486`) and SHAP feature attribution vectors in `mitre/` and `explainability/`. |
| **FastAPI REST Serving Backend** | High-throughput asynchronous REST serving pipeline, dynamic scenario runner, live model telemetry, and health monitoring in `api/`. |
| **Interactive SOC Operations Dashboard** | Vite + React 18 + TypeScript + Tailwind CSS dashboard with interactive timelines, live progression flows, radar graphs, architecture inspector, and comparative benchmark matrix in `dashboard/`. |

---

## 14. Test Suite & Verification Results

All 68 automated unit and integration tests execute successfully without errors:

```text
============================= test session starts =============================
platform win32 -- Python 3.14.0, pytest-9.1.1, pluggy-1.6.0
collected 68 items

network-attack-forecasting/tests/test_end_to_end_pipeline.py ........... [ 16%]
network-attack-forecasting/tests/test_multi_models.py .................. [ 38%]
network-attack-forecasting/tests/test_prediction_engine.py ............. [ 63%]
network-attack-forecasting/tests/test_world_model.py .................... [ 86%]
network-attack-forecasting/preprocessing/test_preprocessing.py ......... [100%]

======================= 68 passed, 3 warnings in 14.45s =======================
```

### Verified State Progression Outputs

* **NORMAL Traffic:** $\to$ `State=NORMAL`, `Threat Score=7`, `Risk=LOW`, `Inference Latency=2.30 ms`
* **Port Scanning:** $\to$ `State=ELEVATED`, `Stage=Reconnaissance`, `Technique=T1595 Active Scanning`
* **C2 Beaconing:** $\to$ `State=SUSPICIOUS`, `Stage=Initial Access`, `Threat Score=44`
* **DDoS Attack:** $\to$ `State=ATTACK`, `Stage=Lateral Movement`, `Threat Score=95`, `Risk=CRITICAL`
* **Recovery Phase:** $\to$ `T1: ATTACK (95)` $\to$ `T2: NORMAL (Stage: Recovery, Score: 8)` $\to$ `T3: NORMAL (Score: 2)`
* **Honest Model Error:** When checkpoint is intentionally disconnected, returns `MODEL_UNAVAILABLE` with `confidence=0.0` (zero fake fallbacks).

---

## 15. License

Distributed under the **MIT License**. See `LICENSE` for details.

---

<div align="center">

**Threatora AI &bull; Autonomous Network Attack Forecasting & Threat Defense**

*“Predict Tomorrow’s Threats, Today.”*

Authored & Maintained by **Likitha C** ([@LikithaC17](https://github.com/LikithaC17))
</div>
