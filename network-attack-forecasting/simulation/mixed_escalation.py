"""Mixed temporal escalation: NORMAL -> ELEVATED -> SUSPICIOUS -> ATTACK.

Each sequence walks the state ladder gradually, so the numerical features evolve
smoothly instead of jumping between independent random rows.
"""

from __future__ import annotations

import numpy as np

from .common import (
    LADDER_STATES,
    anchor_key,
    ephemeral_port,
    external_private_ip,
    internal_subnet_ip,
    jitter,
    make_flow,
    protocol_for_port,
    service_port,
    split_rows,
)

MIXED_ANCHORS = {
    "NORMAL": {
        "flow_duration": 10.0,
        "packet_count": 55.0,
        "bytes_per_packet": 800.0,
        "inter_arrival_time": 0.50,
        "connection_frequency": 0.60,
    },
    "ELEVATED": {
        "flow_duration": 7.0,
        "packet_count": 420.0,
        "bytes_per_packet": 950.0,
        "inter_arrival_time": 0.18,
        "connection_frequency": 7.0,
    },
    "SUSPICIOUS": {
        "flow_duration": 3.0,
        "packet_count": 2600.0,
        "bytes_per_packet": 1050.0,
        "inter_arrival_time": 0.04,
        "connection_frequency": 60.0,
    },
    "ATTACK": {
        "flow_duration": 0.8,
        "packet_count": 14000.0,
        "bytes_per_packet": 1200.0,
        "inter_arrival_time": 0.003,
        "connection_frequency": 700.0,
    },
}


def _ladder_schedule(rng: np.random.Generator, length: int):
    """Build a gradual NORMAL..ATTACK schedule with fractional ramp steps."""
    # fraction of the sequence spent in each stage (escalation feels front-loaded)
    weights = np.array([rng.uniform(0.18, 0.30),
                        rng.uniform(0.15, 0.26),
                        rng.uniform(0.14, 0.26),
                        rng.uniform(0.20, 0.42)])
    weights = weights / weights.sum()
    counts = np.maximum((weights * length).round().astype(int), 1)
    while counts.sum() > length:
        counts[int(np.argmax(counts))] -= 1
    while counts.sum() < length:
        counts[int(rng.integers(0, 4))] += 1
    return [LADDER_STATES[i] for i in range(4) for _ in range(int(counts[i]))][:length]


def generate_mixed(rng: np.random.Generator, total_rows: int, min_len: int = 10,
                   max_len: int = 30) -> list[list[dict]]:
    sequences = []
    for length in split_rows(total_rows, min_len, max_len, rng):
        subnet = int(rng.integers(1, 40))
        src_ip = internal_subnet_ip(rng, subnet)
        # the host first talks internally, then reaches out to a remote endpoint
        internal_dst = f"192.168.{subnet}.{int(rng.integers(200, 254))}"
        external_dst = external_private_ip(rng)
        dst_ports = [service_port(rng), service_port(rng), int(rng.choice([443, 8080, 3306]))]

        stages = _ladder_schedule(rng, length)
        # fractional escalation coordinate so features ramp smoothly
        ramp = np.linspace(0.0, 3.0, length)
        ramp = ramp + rng.normal(0.0, 0.05, length)
        ramp = np.clip(ramp, 0.0, 3.0)

        rows = []
        for i in range(length):
            e = float(ramp[i])
            state = stages[i]
            going_external = e >= 1.5 or rng.random() < 0.3
            dst_ip = external_dst if going_external else internal_dst
            dst_port = dst_ports[2] if going_external else dst_ports[0]
            protocol = protocol_for_port(rng, dst_port)

            duration = float(np.clip(jitter(rng, anchor_key(MIXED_ANCHORS, e, "flow_duration"), 0.2), 0.05, 300.0))
            packets = int(np.clip(jitter(rng, anchor_key(MIXED_ANCHORS, e, "packet_count"), 0.28), 3, 400000))
            bpp = jitter(rng, anchor_key(MIXED_ANCHORS, e, "bytes_per_packet"), 0.1)
            iat = max(float(np.clip(jitter(rng, anchor_key(MIXED_ANCHORS, e, "inter_arrival_time"), 0.3), 0.0005, 8.0)), 1e-4)
            conn_freq = max(float(np.clip(jitter(rng, anchor_key(MIXED_ANCHORS, e, "connection_frequency"), 0.25), 0.01, 20000.0)), 1e-4)

            rows.append(
                make_flow(
                    rng,
                    scenario="mixed_escalation",
                    state=state,
                    src_ip=src_ip,
                    dst_ip=dst_ip,
                    src_port=ephemeral_port(rng),
                    dst_port=dst_port,
                    protocol=protocol,
                    flow_duration=duration,
                    packet_count=packets,
                    byte_count=int(max(packets * bpp, packets * 64)),
                    inter_arrival_time=iat,
                    connection_frequency=conn_freq,
                )
            )
        sequences.append(rows)
    return sequences