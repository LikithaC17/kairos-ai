# 🛡️ NETSCOPE AI — Frontend Security Operations Center (SOC)

### AI-Based Network Attack Forecasting — Network Security World Model

Modern, production-ready Security Operations Center (SOC) dashboard built with **React**, **Vite**, **TypeScript**, **Tailwind CSS**, **Recharts**, and **Lucide Icons**.

Communicates the paradigm shift from traditional reactive intrusion detection (*"Is this traffic malicious right now?"*) to predictive temporal network security (*"What is happening now, what is likely to happen next, and how could the attack progress?"*).

---

## 🚀 Key Features

1. **Overview SOC Dashboard (`/dashboard`)**:
   - 10-second Judge Innovation summary: **"What Happens Next?"** banner connecting Current State → Latent Dynamic → Predicted State → MITRE ATT&CK Stage.
   - Comprehensive KPI telemetry cards: Packets/sec, Flows/sec, Current Threat Level, Active Threats, Forecast Risk, Attack Progression Probability, and ML Model Confidence.
   - Current Network State full profile: Source/Destination IP counts, TCP/UDP ratio, SYN/ACK ratio, MTU sizing, and connection duration.
   - Real-time Traffic Timeline chart with multi-metric toggles (Packets, Bytes, Flows, Packet Rate, Threat Activity) and time window filtering (1m, 5m, 15m, 1h, 24h).
   - Protocol breakdown donut chart (TCP, UDP, ICMP, DNS, HTTPS, HTTP).
   - Threat Taxonomy bar chart & interactive progression flow.

2. **Live Telemetry & Traffic Analysis (`/traffic`)**:
   - High-throughput flow monitoring with protocol filters and sliding observation windows.
   - Raw flow stream table displaying 7 continuous normalized temporal features.

3. **Intrusion Detection & Evidence (`/threats`)**:
   - Searchable, filterable, and sortable threat table with severity badges.
   - Slide-out **Threat Vector Investigation Panel** showing extracted packet evidence (packet rate, byte rate, IAT, burst frequency, entropy) and Explainable AI (XAI) rationale.

4. **Temporal World Model Attack Forecast (`/forecast`)**:
   - Multi-step forward horizon projection ($+1$ to $+10$ steps).
   - Attack Probability Trajectory line graph with 90% Bayesian Credible Interval confidence envelope.
   - Complete 6-stage Adversary Kill Chain progression flow with active status highlighting.
   - Network Security World Model latent space transition diagram ($S_t \rightarrow h_t \in \mathbb{R}^{128} \rightarrow P(S_{t+K} \mid S_t)$).

5. **Interactive Adversary Simulation (`/simulation`)**:
   - Dynamic demonstration rig supporting Multi-Stage Escalation, Botnet C2 Beaconing, Distributed Denial of Service (SYN Flood), and Benign Enterprise Traffic.
   - Play, pause, reset, step $+1$, speed control (0.5x, 1x, 2x, 4x), and look-ahead horizon adjustment.
   - Real-time step-by-step model probability distribution updates.

6. **MITRE ATT&CK Enterprise Matrix & Heatmap (`/mitre`)**:
   - Direct alignment with TTPs (T1046 Network Service Discovery, T1110 Brute Force, T1071 C2 Protocol, T1021 Remote Services, T1498 DoS, T1048 Exfiltration).
   - Interactive risk filters and live detection status.

7. **Security Alerts Feed (`/alerts`)**:
   - Triage queue of early warnings with review status toggle and one-click "Mark All As Reviewed".

8. **AI Model Insights & Explainability (`/model`)**:
   - Displays real PyTorch model parameters (168,712 weights, 2-layer GRU, 128 hidden dim).
   - Verifiable holdout metrics: 80.58% current state accuracy, 91.37% next state forecast accuracy, 2.1847 test loss.
   - SHAP (SHapley Additive exPlanations) global feature attribution chart.

9. **System Infrastructure Status (`/status`)**:
   - Real-time health monitoring of Frontend, REST API, ML World Model, Forecasting Engine, Simulation Engine, Feature Store, and MITRE Mapper.

10. **Platform Configuration (`/settings`)**:
    - Centralized API endpoint configuration (`VITE_API_URL`), custom backend overrides, and early warning probability thresholds.

---

## 🛠️ Tech Stack

- **Framework**: React 18, Vite 5, TypeScript 5
- **Styling**: Tailwind CSS (SOC Dark Theme), PostCSS, Autoprefixer
- **Charts & Visualizations**: Recharts
- **Icons**: Lucide React
- **Routing**: React Router v6
- **HTTP Client**: Centralized Axios with automatic offline demo fallback

---

## 💻 Quick Start

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure Environment
Create `.env` or use `.env.example`:
```env
VITE_API_URL=https://cyber-network-traffic.onrender.com
```

### 3. Start Development Server
```bash
npm run dev
```

### 4. Build for Production
```bash
npm run build
```

---

## 🔄 Backend Integration

To run the full end-to-end AI system with the live PyTorch GRU world model:
```bash
cd ../network-attack-forecasting
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000
```
If the backend is not running, the frontend gracefully activates **Offline Demo Mode** with high-fidelity synthetic telemetry, preventing blank screens or errors.
