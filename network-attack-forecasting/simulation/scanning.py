"""Port/Network scanning scenario: synthetic reconnaissance traffic.

The distinguishing signal is high destination port diversity and/or high unique
destination IP count from a single source, with low volume per connection.
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

SCAN_ANCHORS = {
    "NORMAL": {
        "flow_duration": 8.0,
        "packet_count": 12.0,
        "bytes_per_packet": 520.0,
        "inter_arrival_time": 0.30,
        "connection_frequency": 2.0,
    },
    "ELEVATED": {
        "flow_duration": 3.0,
        "packet_count": 24.0,
        "bytes_per_packet": 480.0,
        "inter_arrival_time": 0.08,
        "connection_frequency": 15.0,
    },
    "SUSPICIOUS": {
        "flow_duration": 1.0,
        "packet_count": 48.0,
        "bytes_per_packet": 440.0,
        "inter_arrival_time": 0.02,
        "connection_frequency": 80.0,
    },
    "ATTACK": {
        "flow_duration": 0.3,
        "packet_count": 90.0,
        "bytes_per_packet": 400.0,
        "inter_arrival_time": 0.005,
        "connection_frequency": 300.0,
    },
}

SCAN_TYPES = ["vertical", "horizontal", "block", "stealth"]


def generate_scanning(rng: np.random.Generator, total_rows: int, min_len: int = 10,
                      max_len: int = 30) -> list[list[dict]]:
    sequences = []
    for length in split_rows(total_rows, min_len, max_len, rng):
        subnet = int(rng.integers(1, 40))
        scanner_ip = internal_subnet_ip(rng, subnet)
        scan_type = rng.choice(SCAN_TYPES)

        if scan_type == "vertical":
            dst_ips = [f"192.168.{subnet}.{int(rng.integers(1, 255))}"]
            dst_ports = rng.integers(1, 65536, size=int(rng.integers(20, 200)))
        elif scan_type == "horizontal":
            dst_ips = [f"192.168.{int(rng.integers(1, 40))}.{int(rng.integers(1, 40))}" for _ in range(int(rng.integers(10, 80)))]
            dst_ports = [int(rng.choice([22, 80, 443, 445, 3389, 3306, 5432]))]
        elif scan_type == "block":
            dst_ips = [f"192.168.{subnet}.{int(rng.integers(1, 255))}" for _ in range(int(rng.integers(30, 150)))]
            dst_ports = rng.integers(1, 10000, size=int(rng.integers(10, 50)))
        else:  # stealth
            dst_ips = [f"192.168.{subnet}.{int(rng.integers(1, 255))}"]
            dst_ports = rng.integers(1, 65536, size=int(rng.integers(50, 300)))

        start_e = float(rng.uniform(0.2, 1.0))
        end_e = min(3.0, start_e + float(rng.uniform(1.0, 2.5)))
        ramp = np.linspace(start_e, end_e, length)

        rows = []
        for i in range(length):
            e = float(ramp[i])
            state = e_to_state(e)
            dst_ip = rng.choice(dst_ips)
            dst_port = int(rng.choice(dst_ports))
            protocol = protocol_for_port(rng, dst_port)

            duration = float(np.clip(jitter(rng, anchor_key(SCAN_ANCHORS, e, "flow_duration"), 0.25), 0.01, 60.0))
            packets = int(np.clip(jitter(rng, anchor_key(SCAN_ANCHORS, e, "packet_count"), 0.35), 1, 2000))
            bpp = jitter(rng, anchor_key(SCAN_ANCHORS, e, "bytes_per_packet"), 0.15)
            iat = max(float(np.clip(jitter(rng, anchor_key(SCAN_ANCHORS, e, "inter_arrival_time"), 0.4), 0.0002, 2.0)), 1e-4)
            conn_freq = max(float(np.clip(jitter(rng, anchor_key(SCAN_ANCHORS, e, "connection_frequency"), 0.3), 0.01, 5000.0)), 1e-4)

            rows.append(
                make_flow(
                    rng,
                    scenario="scanning",
                    state=state,
                    src_ip=scanner_ip,
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