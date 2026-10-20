"""UDP-based attack scenario: synthetic volumetric/reflection UDP traffic.

The distinguishing signal is UDP protocol dominance, high packet/byte rates,
amplification-friendly destination ports (DNS, NTP, SNMP, etc.), and
asymmetric packet sizes (small requests, large responses simulated).
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
    split_rows,
)

# Amplification-prone UDP services
AMPLIFICATION_PORTS = {
    53: 50.0,     # DNS
    123: 30.0,    # NTP
    161: 8.0,     # SNMP
    1900: 5.0,    # SSDP
    11211: 4.0,   # Memcached
    19: 3.0,      # Chargen
}

UDP_ANCHORS = {
    "NORMAL": {
        "flow_duration": 12.0,
        "packet_count": 35.0,
        "bytes_per_packet": 540.0,
        "inter_arrival_time": 0.35,
        "connection_frequency": 1.5,
    },
    "ELEVATED": {
        "flow_duration": 4.0,
        "packet_count": 500.0,
        "bytes_per_packet": 1200.0,
        "inter_arrival_time": 0.04,
        "connection_frequency": 30.0,
    },
    "SUSPICIOUS": {
        "flow_duration": 1.5,
        "packet_count": 3000.0,
        "bytes_per_packet": 1400.0,
        "inter_arrival_time": 0.006,
        "connection_frequency": 200.0,
    },
    "ATTACK": {
        "flow_duration": 0.2,
        "packet_count": 25000.0,
        "bytes_per_packet": 1500.0,
        "inter_arrival_time": 0.0004,
        "connection_frequency": 2000.0,
    },
}


def generate_udp_attack(rng: np.random.Generator, total_rows: int, min_len: int = 10,
                        max_len: int = 30) -> list[list[dict]]:
    sequences = []
    ports_list = list(AMPLIFICATION_PORTS.keys())
    ports_weights = np.array(list(AMPLIFICATION_PORTS.values()))
    ports_weights = ports_weights / ports_weights.sum()

    for length in split_rows(total_rows, min_len, max_len, rng):
        victim_subnet = int(rng.integers(1, 40))
        dst_ip = f"192.168.{victim_subnet}.{int(rng.integers(1, 40))}"
        dst_port = int(rng.choice(ports_list, p=ports_weights))
        protocol = "UDP"

        reflector_ips = [external_private_ip(rng) for _ in range(int(rng.integers(5, 25)))]

        start_e = float(rng.choice([0.3, 0.8, 1.2]))
        end_e = 3.0 if rng.random() < 0.85 else 2.8
        ramp = np.linspace(start_e, end_e, length)

        rows = []
        for i in range(length):
            e = float(ramp[i])
            state = e_to_state(e)
            src_ip = reflector_ips[i % len(reflector_ips)]

            duration = float(np.clip(jitter(rng, anchor_key(UDP_ANCHORS, e, "flow_duration"), 0.25), 0.01, 120.0))
            packets = int(np.clip(jitter(rng, anchor_key(UDP_ANCHORS, e, "packet_count"), 0.35), 5, 100000))
            bpp = jitter(rng, anchor_key(UDP_ANCHORS, e, "bytes_per_packet"), 0.15)
            iat = max(float(np.clip(jitter(rng, anchor_key(UDP_ANCHORS, e, "inter_arrival_time"), 0.4), 0.0001, 1.0)), 1e-4)
            conn_freq = max(float(np.clip(jitter(rng, anchor_key(UDP_ANCHORS, e, "connection_frequency"), 0.3), 0.01, 50000.0)), 1e-4)

            rows.append(
                make_flow(
                    rng,
                    scenario="udp_attack",
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