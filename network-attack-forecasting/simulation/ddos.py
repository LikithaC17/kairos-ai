"""DDoS-like scenario: synthetic high-volume statistical traffic.

No real traffic is generated or sent anywhere. These rows only *look like*
volumetric-flood statistics (high packet/byte rate, high connection frequency,
short inter-arrival times).
"""

from __future__ import annotations

import numpy as np

from .common import (
    anchor_key,
    e_to_state,
    external_private_ip,
    internal_subnet_ip,
    jitter,
    make_flow,
    split_rows,
)

DDOS_ANCHORS = {
    "NORMAL": {
        "flow_duration": 12.0,
        "packet_count": 60.0,
        "bytes_per_packet": 820.0,
        "inter_arrival_time": 0.50,
        "connection_frequency": 0.80,
    },
    "ELEVATED": {
        "flow_duration": 6.0,
        "packet_count": 1800.0,
        "bytes_per_packet": 1000.0,
        "inter_arrival_time": 0.06,
        "connection_frequency": 45.0,
    },
    "SUSPICIOUS": {
        "flow_duration": 2.0,
        "packet_count": 9000.0,
        "bytes_per_packet": 1150.0,
        "inter_arrival_time": 0.012,
        "connection_frequency": 260.0,
    },
    "ATTACK": {
        "flow_duration": 0.5,
        "packet_count": 26000.0,
        "bytes_per_packet": 1250.0,
        "inter_arrival_time": 0.0015,
        "connection_frequency": 1400.0,
    },
}


def generate_ddos(rng: np.random.Generator, total_rows: int, min_len: int = 10,
                  max_len: int = 30) -> list[list[dict]]:
    sequences = []
    for length in split_rows(total_rows, min_len, max_len, rng):
        victim_subnet = int(rng.integers(1, 40))
        dst_ip = f"192.168.{victim_subnet}.{int(rng.integers(1, 40))}"
        dst_port = int(rng.choice([80, 443, 8080]))
        sources = [internal_subnet_ip(rng, victim_subnet) for _ in range(int(rng.integers(2, 6)))]
        if int(rng.integers(0, 4)) == 0:
            sources.append(external_private_ip(rng))

        # ramp: head of the sequence still calm, tail fully saturated
        start_e = float(rng.choice([0.0, 0.35, 0.8]))
        end_e = 3.0 if rng.random() < 0.8 else 2.7
        ramp = np.linspace(start_e, end_e, length)

        rows = []
        for i in range(length):
            e = float(ramp[i])
            state = e_to_state(e)
            duration = float(np.clip(jitter(rng, anchor_key(DDOS_ANCHORS, e, "flow_duration"), 0.22), 0.05, 300.0))
            packets = int(np.clip(jitter(rng, anchor_key(DDOS_ANCHORS, e, "packet_count"), 0.30), 5, 400000))
            bpp = jitter(rng, anchor_key(DDOS_ANCHORS, e, "bytes_per_packet"), 0.12)
            iat = max(float(np.clip(jitter(rng, anchor_key(DDOS_ANCHORS, e, "inter_arrival_time"), 0.30), 0.0002, 5.0)), 1e-4)
            conn_freq = max(float(np.clip(jitter(rng, anchor_key(DDOS_ANCHORS, e, "connection_frequency"), 0.28), 0.01, 20000.0)), 1e-4)
            rows.append(
                make_flow(
                    rng,
                    scenario="ddos_like",
                    state=state,
                    src_ip=sources[i % len(sources)],
                    dst_ip=dst_ip,
                    src_port=int(rng.integers(1024, 65536)),
                    dst_port=dst_port,
                    protocol="TCP",
                    flow_duration=duration,
                    packet_count=packets,
                    byte_count=int(max(packets * bpp, packets * 64)),
                    inter_arrival_time=iat,
                    connection_frequency=conn_freq,
                )
            )
        sequences.append(rows)
    return sequences