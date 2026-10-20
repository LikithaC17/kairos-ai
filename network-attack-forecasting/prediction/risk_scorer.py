"""
Composite risk scoring for NetForecast AI.

Computes a calibrated 0-100 threat score and qualitative risk level
combining model probability distribution, feature anomaly severity,
and temporal persistence history.
"""

from typing import Dict, List, Tuple


def calculate_risk_score(
    current_state_prob: Dict[str, float],
    features: Dict[str, float],
    history: List[str],
) -> Tuple[int, str]:
    """
    Computes composite threat score (0-100) and risk level.

    Parameters
    ----------
    current_state_prob : Dict[str, float]
        Probabilities for NORMAL, ELEVATED, SUSPICIOUS, ATTACK.
    features : Dict[str, float]
        Current window behavioral features.
    history : List[str]
        Historical sequence of observed states.

    Returns
    -------
    Tuple[int, str] : (threat_score, risk_level)
    """
    # 1. State Severity Base (40% weight)
    p_norm = current_state_prob.get("NORMAL", 0.0)
    p_elev = current_state_prob.get("ELEVATED", 0.0)
    p_susp = current_state_prob.get("SUSPICIOUS", 0.0)
    p_attk = current_state_prob.get("ATTACK", 0.0)

    # Weighted severity expectation in [0, 100]
    state_severity = (p_norm * 5.0) + (p_elev * 35.0) + (p_susp * 65.0) + (p_attk * 95.0)

    # 2. Anomaly Indicators from Features (35% weight)
    anomaly_points = 0.0
    packet_rate = features.get("packet_rate", 0.0)
    byte_rate = features.get("byte_rate", 0.0)
    conn_freq = features.get("connection_frequency", 0.0)
    failed_conn_ratio = features.get("failed_conn_ratio", 0.0)
    syn_count = features.get("syn_count", 0.0)
    port_entropy = features.get("port_entropy", 0.0)

    if packet_rate > 2000.0:
        anomaly_points += 30.0
    elif packet_rate > 500.0:
        anomaly_points += 15.0

    if byte_rate > 1_000_000.0:
        anomaly_points += 20.0
    elif byte_rate > 300_000.0:
        anomaly_points += 10.0

    if conn_freq > 80.0 or port_entropy > 3.0:
        anomaly_points += 25.0

    if failed_conn_ratio > 0.5:
        anomaly_points += 25.0

    if syn_count > 400:
        anomaly_points += 25.0

    anomaly_score = min(100.0, anomaly_points)

    # 3. Persistence History (25% weight)
    # Count consecutive elevated/suspicious/attack states
    consecutive_elevated = 0
    for s in reversed(history):
        if s != "NORMAL":
            consecutive_elevated += 1
        else:
            break
    persistence_score = min(100.0, consecutive_elevated * 15.0)

    # Composite threat score calculation
    raw_score = (0.45 * state_severity) + (0.35 * anomaly_score) + (0.20 * persistence_score)

    # If state probability is overwhelmingly ATTACK, guarantee score >= 65
    if p_attk > 0.6:
        raw_score = max(raw_score, 65.0 + (p_attk * 30.0))

    score = int(max(0, min(100, round(raw_score))))

    # Qualitative risk classification
    if score <= 29:
        risk_level = "LOW"
    elif score <= 59:
        risk_level = "MEDIUM"
    elif score <= 79:
        risk_level = "HIGH"
    else:
        risk_level = "CRITICAL"

    return score, risk_level
