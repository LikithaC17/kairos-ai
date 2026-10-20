"""
Threat classification heuristics based on network feature indicators and state.
"""

from typing import Dict


def classify_threat(features: Dict[str, float], current_state: str) -> str:
    """
    Classifies the specific threat type based on observed network telemetry features.
    
    Parameters
    ----------
    features : Dict[str, float]
        Current window behavioral feature dictionary.
    current_state : str
        State label: NORMAL, ELEVATED, SUSPICIOUS, or ATTACK.

    Returns
    -------
    str : Descriptive threat category.
    """
    if current_state == "NORMAL":
        return "Normal Operations"

    packet_rate = features.get("packet_rate", 0.0)
    byte_rate = features.get("byte_rate", 0.0)
    conn_freq = features.get("connection_frequency", 0.0)
    syn_count = features.get("syn_count", 0.0)
    failed_conn_ratio = features.get("failed_conn_ratio", 0.0)
    byte_asymmetry = features.get("byte_asymmetry", 0.0)
    port_entropy = features.get("port_entropy", 0.0)
    dst_ip_diversity = features.get("dst_ip_diversity", 0.0)

    # Heuristic signature matches
    if syn_count > 500 or (packet_rate > 1000.0 and failed_conn_ratio > 0.6):
        return "SYN Flood Attack"

    if packet_rate > 2000.0 or byte_rate > 2_000_000.0:
        return "Volumetric DDoS Attack"

    if conn_freq > 80.0 or port_entropy > 3.5 or dst_ip_diversity > 40:
        return "Port & Network Scanning"

    if failed_conn_ratio > 0.5:
        return "Brute Force Authentication"

    if byte_asymmetry > 0.85 and byte_rate > 500_000.0:
        return "Data Exfiltration"

    if current_state == "SUSPICIOUS":
        return "C2 Beaconing / Probing"

    if current_state == "ATTACK":
        return "Multi-Stage Attack in Progress"

    return "Anomalous Traffic Escalation"
