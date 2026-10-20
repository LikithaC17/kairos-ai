"""Cyber-domain feature engineering for network flow telemetry.

Module: network-attack-forecasting.preprocessing.feature_extraction
Author: Vikas (Feature Engineering & Preprocessing)

Features extracted:
1. packets/sec (packet_rate = packet_count / flow_duration)
2. bytes/sec (byte_rate = byte_count / flow_duration)
3. average packet size (bytes_per_packet = byte_count / packet_count)
4. flow duration (flow_duration)
5. connection frequency (connection_frequency)
6. SYN rate (syn_rate = syn_count / flow_duration)
7. ACK rate (ack_rate = ack_count / flow_duration) and syn_ack_ratio
8. Destination port distribution:
   - Well-known service port flags: 22 (SSH), 53 (DNS), 80 (HTTP), 443 (HTTPS), 3306 (MySQL), 8080 (Alt-HTTP)
   - Port class flags: system (<1024), registered (1024-49151), ephemeral (>=49152)
   - Normalized destination port
9. Destination-port entropy (dst_port_entropy via rolling Shannon entropy)
10. Source-IP entropy (src_ip_entropy via rolling Shannon entropy)
11. Inter-arrival time (inter_arrival_time)
12. Packet timing:
    - time_delta: elapsed seconds between consecutive flows
    - is_same_host_as_prev: host continuity indicator
13. Protocol statistics:
    - protocol one-hot encoding (TCP, UDP, ICMP)
"""

from __future__ import annotations

import argparse
import math
import sys
from collections import Counter
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd


# Known enterprise service ports
KNOWN_SERVICE_PORTS = [22, 53, 80, 443, 3306, 8080]
KNOWN_PROTOCOLS = ["TCP", "UDP", "ICMP"]

# Core features consumed by Likitha's baseline model
CORE_WORLD_MODEL_FEATURES = [
    "flow_duration",
    "packet_count",
    "byte_count",
    "packet_rate",
    "byte_rate",
    "inter_arrival_time",
    "connection_frequency",
]


def calculate_entropy(series: pd.Series) -> float:
    """Calculate Shannon entropy H(X) = -sum(p * log2(p)) for discrete values."""
    if len(series) == 0:
        return 0.0
    counts = Counter(series)
    total = len(series)
    entropy = 0.0
    for count in counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    return float(entropy)


def rolling_entropy(series: pd.Series, window_size: int = 15) -> np.ndarray:
    """Compute rolling Shannon entropy over a sliding temporal window of past records."""
    vals = series.values
    n = len(vals)
    result = np.zeros(n, dtype=np.float32)

    for i in range(n):
        start = max(0, i - window_size + 1)
        sub_window = vals[start : i + 1]
        result[i] = calculate_entropy(pd.Series(sub_window))

    return result


def extract_cyber_features(
    df: pd.DataFrame,
    entropy_window: int = 15,
    include_core_only: bool = False,
) -> pd.DataFrame:
    """Engineer cyber-domain features from raw/cleaned flow records.

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned flow records sorted chronologically.
    entropy_window : int
        Window size for rolling entropy calculation (default 15).
    include_core_only : bool
        If True, outputs only the 7 baseline features for compatibility.

    Returns
    -------
    pd.DataFrame
        DataFrame with enriched domain features.
    """
    df = df.copy()

    # 1. Flow Duration (safe positive)
    if "flow_duration" in df.columns:
        dur = np.maximum(df["flow_duration"].astype(float).values, 1e-4)
    else:
        dur = np.ones(len(df), dtype=float)
        df["flow_duration"] = dur

    # 2. Packet Count & Byte Count (safe positive)
    pkt_cnt = np.maximum(df["packet_count"].astype(float).values if "packet_count" in df.columns else np.ones(len(df)), 1.0)
    byte_cnt = np.maximum(df["byte_count"].astype(float).values if "byte_count" in df.columns else np.ones(len(df)), 1.0)

    # 3. Packets/sec (packet_rate) & Bytes/sec (byte_rate)
    df["packet_rate"] = np.round(pkt_cnt / dur, 6)
    df["byte_rate"] = np.round(byte_cnt / dur, 6)

    # 4. Average Packet Size (bytes_per_packet)
    df["bytes_per_packet"] = np.round(byte_cnt / pkt_cnt, 4)

    # 5. Connection Frequency & Inter-arrival time
    if "connection_frequency" not in df.columns:
        df["connection_frequency"] = 1.0
    if "inter_arrival_time" not in df.columns:
        df["inter_arrival_time"] = 0.01

    if include_core_only:
        return df

    # 6. SYN rate & ACK rate & syn_ack_ratio
    if "syn_count" in df.columns:
        syn = df["syn_count"].astype(float).values
    else:
        # If syn_count not directly captured, infer from TCP SYN flood / scanning indicators
        syn = np.where(df.get("protocol", "TCP") == "TCP", np.maximum(1.0, pkt_cnt * 0.1), 0.0)

    if "ack_count" in df.columns:
        ack = df["ack_count"].astype(float).values
    else:
        ack = np.where(df.get("protocol", "TCP") == "TCP", np.maximum(1.0, pkt_cnt * 0.8), 0.0)

    df["syn_rate"] = np.round(syn / dur, 6)
    df["ack_rate"] = np.round(ack / dur, 6)
    df["syn_ack_ratio"] = np.round(syn / np.maximum(ack, 1.0), 4)

    # 7. Destination Port Distribution & Service flags
    if "dst_port" in df.columns:
        dst_p = df["dst_port"].astype(float).values
        df["dst_port_normalized"] = np.round(dst_p / 65535.0, 6)
        df["dst_port_is_system"] = (dst_p < 1024).astype(int)
        df["dst_port_is_registered"] = ((dst_p >= 1024) & (dst_p <= 49151)).astype(int)
        df["dst_port_is_ephemeral"] = (dst_p >= 49152).astype(int)

        # Discrete indicators for known server services
        for port in KNOWN_SERVICE_PORTS:
            df[f"dst_port_{port}"] = (dst_p == port).astype(int)

        # 8. Destination-Port Entropy (rolling over recent traffic)
        df["dst_port_entropy"] = rolling_entropy(df["dst_port"], window_size=entropy_window)
    else:
        df["dst_port_entropy"] = 0.0

    # 9. Source-IP Entropy (rolling)
    if "src_ip" in df.columns:
        df["src_ip_entropy"] = rolling_entropy(df["src_ip"], window_size=entropy_window)
        # Host continuity: 1 if same source IP as previous flow
        df["is_same_host_as_prev"] = (df["src_ip"] == df["src_ip"].shift(1)).fillna(False).astype(int)
    else:
        df["src_ip_entropy"] = 0.0
        df["is_same_host_as_prev"] = 0

    # 10. Packet Timing & Time Delta
    if "timestamp" in df.columns:
        ts = df["timestamp"]
        if pd.api.types.is_datetime64_any_dtype(ts):
            time_delta = ts.diff().dt.total_seconds().fillna(0.0)
        else:
            time_delta = ts.diff().fillna(0.0)
        df["time_delta"] = np.maximum(time_delta.values, 0.0)
    else:
        df["time_delta"] = 0.0

    # 11. Protocol Statistics (One-Hot Indicators)
    proto_series = df["protocol"].astype(str).str.upper() if "protocol" in df.columns else pd.Series(["TCP"] * len(df))
    for proto in KNOWN_PROTOCOLS:
        df[f"protocol_{proto}"] = (proto_series == proto).astype(int)

    return df


def get_feature_column_names(
    include_extended: bool = True,
) -> List[str]:
    """Return ordered list of numerical feature columns used for modeling."""
    if not include_extended:
        return CORE_WORLD_MODEL_FEATURES

    extended_features = CORE_WORLD_MODEL_FEATURES + [
        "bytes_per_packet",
        "syn_rate",
        "ack_rate",
        "syn_ack_ratio",
        "dst_port_normalized",
        "dst_port_is_system",
        "dst_port_is_registered",
        "dst_port_is_ephemeral",
        "dst_port_entropy",
        "src_ip_entropy",
        "is_same_host_as_prev",
        "time_delta",
    ]
    for port in KNOWN_SERVICE_PORTS:
        extended_features.append(f"dst_port_{port}")
    for proto in KNOWN_PROTOCOLS:
        extended_features.append(f"protocol_{proto}")

    return extended_features


def main():
    parser = argparse.ArgumentParser(description="Extract domain cyber features from cleaned network traffic")
    parser.add_argument("input_csv", type=Path, help="Path to input cleaned CSV")
    parser.add_argument("output_csv", type=Path, help="Path to output feature CSV")
    parser.add_argument("--entropy-window", type=int, default=15, help="Rolling entropy window size")
    parser.add_argument("--core-only", action="store_true", help="Output only core 7 features")
    args = parser.parse_args()

    if not args.input_csv.exists():
        print(f"Error: input file {args.input_csv} does not exist", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(args.input_csv)
    print(f"Loaded {len(df)} rows from {args.input_csv}")
    feat_df = extract_cyber_features(df, entropy_window=args.entropy_window, include_core_only=args.core_only)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    feat_df.to_csv(args.output_csv, index=False)
    print(f"Saved {len(feat_df)} rows with {len(feat_df.columns)} columns to {args.output_csv}")


if __name__ == "__main__":
    main()
