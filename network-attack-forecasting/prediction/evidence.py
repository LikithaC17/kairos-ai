from typing import Dict, List


def extract_evidence(features: Dict[str, float]) -> List[str]:
    """
    Inspect behavioural features and produce human-readable evidence strings.
    Only emits evidence for features that are actually present in the input.
    Does NOT invent indicators that cannot be derived from the data.
    """
    evidence: List[str] = []

    # --- Volume / Rate indicators ---
    packet_rate = features.get("packet_rate", None)
    byte_rate   = features.get("byte_rate", None)
    conn_freq   = features.get("connection_frequency", None)
    iat         = features.get("inter_arrival_time", None)

    if packet_rate is not None:
        if packet_rate > 2000.0:
            evidence.append(
                f"Extreme packet rate ({packet_rate:.0f} pkts/s) — consistent with volumetric attack"
            )
        elif packet_rate > 500.0:
            evidence.append(
                f"High packet rate ({packet_rate:.0f} pkts/s) — potential DDoS or flood"
            )
        elif packet_rate > 100.0:
            evidence.append(f"Elevated packet rate ({packet_rate:.0f} pkts/s) detected")

    if byte_rate is not None:
        if byte_rate > 1_000_000.0:
            evidence.append(
                f"Very high byte throughput ({byte_rate/1e6:.1f} MB/s) — possible data exfiltration"
            )
        elif byte_rate > 500_000.0:
            evidence.append(f"Sudden traffic spike (byte volume: {byte_rate/1e3:.0f} KB/s)")

    if conn_freq is not None:
        if conn_freq > 100.0:
            evidence.append(
                f"Very high connection frequency ({conn_freq:.0f}/s) — scanning or brute-force likely"
            )
        elif conn_freq > 50.0:
            evidence.append(f"High connection frequency ({conn_freq:.0f}/s)")

    if iat is not None and iat < 0.01:
        evidence.append(
            f"Abnormally low inter-arrival time ({iat:.4f}s) — automated/scripted traffic"
        )

    # --- TCP / Protocol flag indicators ---
    syn_count = features.get("syn_count", None)
    if syn_count is not None and syn_count > 500:
        evidence.append(
            f"High SYN count ({syn_count:.0f}) — potential SYN flood or port scan"
        )

    failed_conn_ratio = features.get("failed_conn_ratio", None)
    if failed_conn_ratio is not None and failed_conn_ratio > 0.5:
        evidence.append(
            f"High failed connection ratio ({failed_conn_ratio:.0%}) — brute-force or credential stuffing"
        )

    # --- Traffic asymmetry indicators ---
    byte_asymmetry = features.get("byte_asymmetry", None)
    if byte_asymmetry is not None:
        if byte_asymmetry > 0.85:
            evidence.append(
                f"Strong outbound byte asymmetry ({byte_asymmetry:.0%}) — possible data exfiltration"
            )
        elif byte_asymmetry < 0.15:
            evidence.append(
                f"Strong inbound byte asymmetry ({byte_asymmetry:.0%}) — possible C2 command delivery"
            )

    # --- Entropy / diversity indicators ---
    port_entropy = features.get("port_entropy", None)
    if port_entropy is not None and port_entropy > 3.5:
        evidence.append(
            f"High destination port entropy ({port_entropy:.2f}) — horizontal port scan detected"
        )

    dst_ip_diversity = features.get("dst_ip_diversity", None)
    if dst_ip_diversity is not None and dst_ip_diversity > 50:
        evidence.append(
            f"High destination IP diversity ({dst_ip_diversity:.0f} unique IPs) — lateral movement or scanning"
        )

    return evidence
