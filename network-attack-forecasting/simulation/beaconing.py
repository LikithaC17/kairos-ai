"""C2 / beaconing-like scenario: synthetic periodic callback behaviour.

The distinguishing signal is regularity, not volume: the same destination IP and
destination port are reused across a sequence and inter-arrival times stay near a
fixed period with very low jitter. Nothing is transmitted anywhere -- these are
synthetic records only.
"""

from __future__ import annotations

import numpy as np

from .common import (
    anchor_key,
    e_to_state,
    ephemeral_port,
    external_private_ip,
    internal_subnet_ip,
    jitter,
    make_flow,
    protocol_for_port,
    split_rows,
)

BEACON_ANCHORS = {
    "NORMAL": {
        "flow_duration": 12.0,
        "packet_count": 30.0,
        "bytes_per_packet": 620.0,
        "inter_arrival_time": 45.0,
        "connection_frequency": 0.30,
    },
    "ELEVATED": {
        "flow_duration": 10.0,
        "packet_count": 55.0,
        "bytes_per_packet": 700.0,
        "inter_arrival_time": 30.0,
        "connection_frequency": 0.60,
    },
    "SUSPICIOUS": {
        "flow_duration": 8.0,
        "packet_count": 90.0,
        "bytes_per_packet": 760.0,
        "inter_arrival_time": 15.0,
        "connection_frequency": 1.10,
    },
    "ATTACK": {
        "flow_duration": 6.0,
        "packet_count": 140.0,
        "bytes_per_packet": 820.0,
        "inter_arrival_time": 6.0,
        "connection_frequency": 2.00,
    },
}


def generate_beaconing(rng: np.random.Generator, total_rows: int, min_len: int = 10,
                       max_len: int = 30) -> list[list[dict]]:
    sequences = []
    for length in split_rows(total_rows, min_len, max_len, rng):
        subnet = int(rng.integers(1, 40))
        # one infected internal host beaconing out to one repeated C2 destination
        src_ip = internal_subnet_ip(rng, subnet)
        dst_ip = external_private_ip(rng)
        dst_port = int(rng.choice([443, 8080, 80, 53, 22, 3306]))
        protocol = protocol_for_port(rng, dst_port)

        # fixed callback period with small, bounded jitter -> regular periodicity
        base_period = float(np.exp(rng.uniform(np.log(4.0), np.log(180.0))))
        jitter_scale = float(rng.uniform(0.01, 0.06))
        phase = float(rng.uniform(0.0, base_period))

        # slow escalation over the sequence (low volume throughout)
        e0 = float(rng.uniform(0.6, 1.4))
        e1 = min(3.0, e0 + float(rng.uniform(0.2, 1.6)))
        ramp = np.linspace(e0, e1, length)

        rows = []
        for i in range(length):
            e = float(ramp[i])
            state = e_to_state(e)
            period = base_period * (1.0 - 0.25 * (e / 3.0))
            iat = max(period + rng.normal(0.0, jitter_scale * period) + phase * 0.02, 0.05)
            duration = float(np.clip(jitter(rng, anchor_key(BEACON_ANCHORS, e, "flow_duration"), 0.2), 0.2, 300.0))
            packets = int(np.clip(jitter(rng, anchor_key(BEACON_ANCHORS, e, "packet_count"), 0.25), 3, 3000))
            bpp = jitter(rng, anchor_key(BEACON_ANCHORS, e, "bytes_per_packet"), 0.1)
            conn_freq = max(jitter(rng, anchor_key(BEACON_ANCHORS, e, "connection_frequency"), 0.2), 1e-4)
            rows.append(
                make_flow(
                    rng,
                    scenario="c2_beaconing",
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