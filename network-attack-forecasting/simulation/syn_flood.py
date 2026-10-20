"""SYN flood scenario: synthetic TCP handshake exhaustion traffic.

The distinguishing signal is extremely high SYN-to-ACK ratio, very short flow
durations, and massive connection attempt rates with minimal data transfer.
Nothing is transmitted anywhere -- these are synthetic records only.
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
    service_port,
    split_rows,
)

SYNFLOOD_ANCHORS = {
    "NORMAL": {
        "flow_duration": 10.0,
        "packet_count": 15.0,
        "bytes_per_packet": 600.0,
        "inter_arrival_time": 0.40,
        "connection_frequency": 1.0,
    },
    "ELEVATED": {
        "flow_duration": 2.0,
        "packet_count": 60.0,
        "bytes_per_packet": 480.0,
        "inter_arrival_time": 0.05,
        "connection_frequency": 50.0,
    },
    "SUSPICIOUS": {
        "flow_duration": 0.5,
        "packet_count": 200.0,
        "bytes_per_packet": 440.0,
        "inter_arrival_time": 0.008,
        "connection_frequency": 400.0,
    },
    "ATTACK": {
        "flow_duration": 0.05,
        "packet_count": 3.0,
        "bytes_per_packet": 48.0,
        "inter_arrival_time": 0.0003,
        "connection_frequency": 5000.0,
    },
}


def generate_syn_flood(rng: np.random.Generator, total_rows: int, min_len: int = 10,
                       max_len: int = 30) -> list[list[dict]]:
    sequences = []
    for length in split_rows(total_rows, min_len, max_len, rng):
        victim_subnet = int(rng.integers(1, 40))
        dst_ip = f"192.168.{victim_subnet}.{int(rng.integers(1, 40))}"
        dst_port = int(rng.choice([80, 443, 8080, 22, 21, 25]))
        protocol = "TCP"

        attacker_ips = [internal_subnet_ip(rng, victim_subnet) for _ in range(int(rng.integers(3, 12)))]
        if rng.random() < 0.3:
            attacker_ips.extend([external_private_ip(rng) for _ in range(int(rng.integers(2, 8)))])

        start_e = float(rng.choice([0.5, 1.0, 1.5]))
        end_e = 3.0
        ramp = np.linspace(start_e, end_e, length)

        rows = []
        for i in range(length):
            e = float(ramp[i])
            state = e_to_state(e)
            src_ip = attacker_ips[i % len(attacker_ips)]

            duration = float(np.clip(jitter(rng, anchor_key(SYNFLOOD_ANCHORS, e, "flow_duration"), 0.4), 0.005, 30.0))
            packets = int(np.clip(jitter(rng, anchor_key(SYNFLOOD_ANCHORS, e, "packet_count"), 0.5), 1, 10))
            bpp = jitter(rng, anchor_key(SYNFLOOD_ANCHORS, e, "bytes_per_packet"), 0.2)
            iat = max(float(np.clip(jitter(rng, anchor_key(SYNFLOOD_ANCHORS, e, "inter_arrival_time"), 0.5), 0.00005, 0.1)), 1e-6)
            conn_freq = max(float(np.clip(jitter(rng, anchor_key(SYNFLOOD_ANCHORS, e, "connection_frequency"), 0.35), 1.0, 100000.0)), 1e-4)

            rows.append(
                make_flow(
                    rng,
                    scenario="syn_flood",
                    state=state,
                    src_ip=src_ip,
                    dst_ip=dst_ip,
                    src_port=ephemeral_port(rng),
                    dst_port=dst_port,
                    protocol=protocol,
                    flow_duration=duration,
                    packet_count=packets,
                    byte_count=int(max(packets * bpp, packets * 48)),
                    inter_arrival_time=iat,
                    connection_frequency=conn_freq,
                )
            )
        sequences.append(rows)
    return sequences