"""NORMAL scenario: stable, ordinary synthetic enterprise communication."""

from __future__ import annotations

import numpy as np

from .common import (
    SERVICE_WEIGHTS,
    ephemeral_port,
    internal_subnet_ip,
    make_flow,
    service_port,
    split_rows,
)

# escalation anchor at e = 0 (pure NORMAL traffic); only the NORMAL tier is used here
NORMAL_BASE = {
    "packet_count": 48.0,
    "bytes_per_packet": 780.0,
    "inter_arrival_time": 0.45,
    "connection_frequency": 0.55,
}


def generate_normal(rng: np.random.Generator, total_rows: int, min_len: int = 10,
                    max_len: int = 30) -> list[list[dict]]:
    """Return a list of NORMAL sequences, each a list of ordered flow records."""
    sequences = []
    for length in split_rows(total_rows, min_len, max_len, rng):
        # one internal host talking to one internal server for the whole sequence
        subnet = int(rng.integers(1, 40))
        src_ip = internal_subnet_ip(rng, subnet)
        dst_ip = f"192.168.{subnet}.{int(rng.integers(240, 254))}"
        dst_port = service_port(rng, weights=SERVICE_WEIGHTS)
        protocol = "UDP" if dst_port == 53 else "TCP"
        # a small share of ordinary traffic is ICMP (path MTU / reachability checks)
        is_icmp = rng.random() < 0.06
        if is_icmp:
            protocol = "ICMP"

        rows = []
        for _ in range(length):
            duration = float(np.clip(rng.lognormal(np.log(6.0), 0.7), 0.35, 240.0))
            packets = int(np.clip(rng.lognormal(np.log(NORMAL_BASE["packet_count"]), 0.6), 4, 4000))
            bpp = float(np.clip(rng.lognormal(np.log(780.0), 0.35), 64.0, 9000.0))
            iat = float(np.clip(rng.lognormal(np.log(0.45), 0.55), 0.002, 8.0))
            conn_freq = float(np.clip(rng.lognormal(np.log(0.55), 0.5), 0.01, 12.0))
            rows.append(
                make_flow(
                    rng,
                    scenario="normal",
                    state="NORMAL",
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