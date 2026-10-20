"""Shared helpers for the synthetic network-flow generator.

All data produced by this package is fully synthetic. No packet capture is
performed and no real system is contacted.
"""

from __future__ import annotations

import numpy as np

LADDER_STATES = ["NORMAL", "ELEVATED", "SUSPICIOUS", "ATTACK"]
LADDER_INDEX = {s: i for i, s in enumerate(LADDER_STATES)}

SERVICE_PORTS = [53, 80, 443, 22, 8080, 3306]
PROTOCOLS = ["TCP", "UDP", "ICMP"]

# Web / dns / ssh / db weighted like ordinary enterprise traffic
SERVICE_WEIGHTS = np.array([0.18, 0.34, 0.30, 0.06, 0.08, 0.04])

WEBSERVICE_PORTS = [80, 443, 8080]

COLUMNS = [
    "flow_id",
    "timestamp",
    "src_ip",
    "dst_ip",
    "src_port",
    "dst_port",
    "protocol",
    "flow_duration",
    "packet_count",
    "byte_count",
    "packet_rate",
    "byte_rate",
    "inter_arrival_time",
    "connection_frequency",
    "scenario",
    "state",
    "label",
    "severity",
]


def private_ip(rng: np.random.Generator) -> str:
    """Random RFC1918 address (10/8, 172.16/12, 192.168/16). Never public."""
    net = int(rng.integers(0, 3))
    if net == 0:
        parts = [10, int(rng.integers(0, 16)), int(rng.integers(0, 256)), int(rng.integers(1, 255))]
    elif net == 1:
        parts = [172, 16 + int(rng.integers(0, 16)), int(rng.integers(0, 256)), int(rng.integers(1, 255))]
    else:
        parts = [192, 168, int(rng.integers(0, 256)), int(rng.integers(1, 255))]
    return ".".join(str(p) for p in parts)


def internal_subnet_ip(rng: np.random.Generator, subnet: int) -> str:
    """Address inside 192.168.<subnet>.0/24 (host part never .0 or .255)."""
    return f"192.168.{subnet}.{int(rng.integers(1, 255))}"


def external_private_ip(rng: np.random.Generator) -> str:
    """Address inside 10.x.x.x / 172.16.x.x -- used as a synthetic 'remote' host."""
    if int(rng.integers(0, 2)) == 0:
        return f"10.{int(rng.integers(0, 32))}.{int(rng.integers(0, 256))}.{int(rng.integers(1, 255))}"
    return (
        f"172.16.{int(rng.integers(0, 16))}.{int(rng.integers(1, 255))}"
    )


def ephemeral_port(rng: np.random.Generator) -> int:
    return int(rng.integers(1024, 65536))


def service_port(rng: np.random.Generator, ports=None, weights=None) -> int:
    ports = SERVICE_PORTS if ports is None else ports
    if weights is None:
        return int(rng.choice(ports))
    return int(rng.choice(ports, p=weights))


def protocol_for_port(rng: np.random.Generator, port: int) -> str:
    if port == 53:
        return "UDP"
    if port == 22:
        return "TCP"
    return "TCP" if rng.random() < 0.92 else "UDP"


def e_to_state(e: float) -> str:
    """Map a continuous escalation coordinate onto a discrete state."""
    idx = int(np.clip(round(e), 0, 3))
    return LADDER_STATES[idx]


def label_and_severity(state: str, rng: np.random.Generator):
    if state == "NORMAL":
        return "BENIGN", "LOW"
    if state == "ELEVATED":
        label = "SUSPICIOUS" if rng.random() < 0.45 else "BENIGN"
        return label, "MEDIUM"
    if state == "SUSPICIOUS":
        return "SUSPICIOUS", "HIGH"
    return "ATTACK", "CRITICAL"


def geometric_lerp(lo: float, hi: float, t: float) -> float:
    """Geometric interpolation -- keeps rate-like quantities positive."""
    t = float(np.clip(t, 0.0, 1.0))
    return float(lo * (hi / lo) ** t)


def anchor_value(anchors: dict, e: float) -> float:
    """Interpolate an escalation anchor dict at continuous coordinate ``e``."""
    e = float(np.clip(e, 0.0, 3.0))
    i = int(np.floor(e))
    frac = e - i
    lo = anchors[LADDER_STATES[i]]
    if i >= 3:
        return lo
    hi = anchors[LADDER_STATES[i + 1]]
    return geometric_lerp(lo, hi, frac)


def anchor_key(anchors: dict, e: float, key: str) -> float:
    """Interpolate a single named anchor across the escalation ladder."""
    return anchor_value({s: v[key] for s, v in anchors.items()}, e)


def jitter(rng: np.random.Generator, value: float, sigma: float = 0.18) -> float:
    return float(value * float(np.exp(rng.normal(0.0, sigma))))


def split_rows(total: int, min_len: int, max_len: int, rng: np.random.Generator):
    """Split ``total`` rows into sequence lengths inside [min_len, max_len]."""
    lengths = []
    remaining = total
    while remaining > 0:
        if remaining <= max_len:
            lengths.append(remaining)
            break
        lo = min(min_len, remaining)
        span = max_len - lo + 1
        n = int(rng.integers(lo, lo + span))
        n = min(n, remaining)
        lengths.append(n)
        remaining -= n
    return lengths


def make_flow(
    rng: np.random.Generator,
    *,
    scenario: str,
    state: str,
    src_ip: str,
    dst_ip: str,
    src_port: int,
    dst_port: int,
    protocol: str,
    flow_duration: float,
    packet_count: int,
    byte_count: int,
    inter_arrival_time: float,
    connection_frequency: float,
) -> dict:
    """Assemble one flow record. Rates are derived exactly as required."""
    flow_duration = max(float(flow_duration), 1e-4)
    packet_count = int(max(packet_count, 1))
    byte_count = int(max(byte_count, 1))
    inter_arrival_time = max(float(inter_arrival_time), 1e-6)
    connection_frequency = max(float(connection_frequency), 1e-6)
    label, severity = label_and_severity(state, rng)
    return {
        "src_ip": src_ip,
        "dst_ip": dst_ip,
        "src_port": int(src_port),
        "dst_port": int(dst_port),
        "protocol": protocol,
        "flow_duration": round(flow_duration, 6),
        "packet_count": packet_count,
        "byte_count": byte_count,
        "packet_rate": round(packet_count / flow_duration, 6),
        "byte_rate": round(byte_count / flow_duration, 6),
        "inter_arrival_time": round(inter_arrival_time, 6),
        "connection_frequency": round(connection_frequency, 6),
        "scenario": scenario,
        "state": state,
        "label": label,
        "severity": severity,
    }


FEATURE_COLUMNS = [
    "flow_duration",
    "packet_count",
    "byte_count",
    "packet_rate",
    "byte_rate",
    "inter_arrival_time",
    "connection_frequency",
]