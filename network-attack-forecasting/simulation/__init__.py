"""NetForecast AI Simulation Package

Synthetic multi-stage network attack traffic generation for training and
evaluating temporal forecasting models.
"""

from .common import (
    COLUMNS,
    LADDER_STATES,
    LADDER_INDEX,
    SERVICE_PORTS,
    PROTOCOLS,
    SERVICE_WEIGHTS,
    WEBSERVICE_PORTS,
    FEATURE_COLUMNS,
    private_ip,
    internal_subnet_ip,
    external_private_ip,
    ephemeral_port,
    service_port,
    protocol_for_port,
    e_to_state,
    label_and_severity,
    geometric_lerp,
    anchor_value,
    anchor_key,
    jitter,
    split_rows,
    make_flow,
)

from .normal import generate_normal
from .ddos import generate_ddos
from .beaconing import generate_beaconing
from .mixed_escalation import generate_mixed
from .scanning import generate_scanning
from .syn_flood import generate_syn_flood
from .udp_attack import generate_udp_attack
from .attack_simulator import main as run_attack_simulator

__all__ = [
    "COLUMNS",
    "LADDER_STATES",
    "LADDER_INDEX",
    "SERVICE_PORTS",
    "PROTOCOLS",
    "SERVICE_WEIGHTS",
    "WEBSERVICE_PORTS",
    "FEATURE_COLUMNS",
    "private_ip",
    "internal_subnet_ip",
    "external_private_ip",
    "ephemeral_port",
    "service_port",
    "protocol_for_port",
    "e_to_state",
    "label_and_severity",
    "geometric_lerp",
    "anchor_value",
    "anchor_key",
    "jitter",
    "split_rows",
    "make_flow",
    "generate_normal",
    "generate_ddos",
    "generate_beaconing",
    "generate_mixed",
    "generate_scanning",
    "generate_syn_flood",
    "generate_udp_attack",
    "run_attack_simulator",
]

__version__ = "0.1.0"