"""
MITRE ATT&CK Enterprise Matrix Alignment for NetForecast AI.

Maps inferred attack stages and observable threat evidence strings to
verified MITRE ATT&CK Enterprise tactics and techniques:
- T1046: Network Service Discovery
- T1595: Active Scanning
- T1110: Brute Force
- T1021: Remote Services
- T1071: Application Layer Protocol (C2)
- T1048: Exfiltration Over Alternative Protocol
- T1498: Network Denial of Service
- T1486: Data Encrypted for Impact
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class MitreAttackMapping:
    tactic: str
    tactic_id: str
    technique: str
    technique_id: str
    confidence: float
    evidence: List[str]
    mitigations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tactic": self.tactic,
            "tactic_id": self.tactic_id,
            "technique": self.technique,
            "technique_id": self.technique_id,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "mitigations": self.mitigations,
        }


MITRE_TECHNIQUES: Dict[str, Dict[str, Any]] = {
    "T1046": {
        "technique_id": "T1046",
        "technique": "Network Service Discovery",
        "tactic": "Discovery",
        "tactic_id": "TA0007",
        "description": "Adversaries attempt to get a listing of services running on remote hosts.",
        "mitigations": [
            "Filter ingress traffic to sensitive ports.",
            "Use network intrusion detection rules to flag sequential port sweeps.",
        ],
    },
    "T1595": {
        "technique_id": "T1595",
        "technique": "Active Scanning",
        "tactic": "Reconnaissance",
        "tactic_id": "TA0043",
        "description": "Adversaries execute active reconnaissance scans to probe network defenses.",
        "mitigations": [
            "Deploy network edge rate-limiting for half-open connection attempts.",
            "Utilize blackhole routing or honeypots for scanning IPs.",
        ],
    },
    "T1110": {
        "technique_id": "T1110",
        "technique": "Brute Force",
        "tactic": "Credential Access",
        "tactic_id": "TA0006",
        "description": "Adversaries employ repeated authentication guessing against remote services.",
        "mitigations": [
            "Enforce account lockout policies after repeated failures.",
            "Mandate multi-factor authentication (MFA) across internet-facing portals.",
        ],
    },
    "T1021": {
        "technique_id": "T1021",
        "technique": "Remote Services",
        "tactic": "Lateral Movement",
        "tactic_id": "TA0008",
        "description": "Adversaries log into remote systems using services like SMB, SSH, or RDP.",
        "mitigations": [
            "Enforce network microsegmentation restricting internal east-west traffic.",
            "Disable legacy protocols like SMBv1 across internal subnets.",
        ],
    },
    "T1071": {
        "technique_id": "T1071",
        "technique": "Application Layer Protocol",
        "tactic": "Command and Control",
        "tactic_id": "TA0011",
        "description": "Adversaries communicate with external C2 servers using standard protocols.",
        "mitigations": [
            "Inspect egress web traffic with proxy TLS inspection.",
            "Flag periodic beaconing intervals in DNS/HTTP flow logs.",
        ],
    },
    "T1048": {
        "technique_id": "T1048",
        "technique": "Exfiltration Over Alternative Protocol",
        "tactic": "Exfiltration",
        "tactic_id": "TA0010",
        "description": "Adversaries exfiltrate data through unmonitored or alternative channels.",
        "mitigations": [
            "Enforce outbound data transfer limits and egress rate caps.",
            "Monitor asymmetric byte flows favoring outbound direction.",
        ],
    },
    "T1498": {
        "technique_id": "T1498",
        "technique": "Network Denial of Service",
        "tactic": "Impact",
        "tactic_id": "TA0040",
        "description": "Adversaries flood network interfaces to degrade or deny availability.",
        "mitigations": [
            "Activate BGP Anycast and upstream scrubbing centers.",
            "Enable SYN cookies on perimeter load balancers.",
        ],
    },
    "T1486": {
        "technique_id": "T1486",
        "technique": "Data Encrypted for Impact",
        "tactic": "Impact",
        "tactic_id": "TA0040",
        "description": "Adversaries encrypt data on target systems to interrupt operations.",
        "mitigations": [
            "Isolate compromised endpoints immediately from the network segment.",
            "Ensure immutable offline backup snapshots are maintained.",
        ],
    },
}


def map_to_mitre(
    attack_stage: str,
    evidence: Optional[List[str]] = None,
    threat_type: str = "",
    confidence: float = 0.85,
) -> MitreAttackMapping:
    """
    Correlates predicted stage and observable evidence with official MITRE ATT&CK techniques.
    """
    evidence = evidence or []
    stage_upper = attack_stage.strip().upper()
    threat_upper = threat_type.strip().upper()

    # Rule-based technique matching
    if "FLOOD" in threat_upper or "DDOS" in threat_upper or "VOLUMETRIC" in threat_upper:
        tech_id = "T1498"
    elif "SCAN" in stage_upper or "SCANNING" in threat_upper:
        tech_id = "T1046"
    elif "RECONNAISSANCE" in stage_upper:
        tech_id = "T1595"
    elif "INITIAL ACCESS" in stage_upper or "BRUTE" in threat_upper:
        tech_id = "T1110"
    elif "LATERAL MOVEMENT" in stage_upper:
        tech_id = "T1021"
    elif "COMMAND AND CONTROL" in stage_upper or "BEACON" in threat_upper or "C2" in threat_upper:
        tech_id = "T1071"
    elif "EXFILTRATION" in stage_upper:
        tech_id = "T1048"
    elif "IMPACT" in stage_upper:
        tech_id = "T1486"
    else:
        # Default / baseline fallback
        tech_id = "T1595"

    meta = MITRE_TECHNIQUES[tech_id]

    return MitreAttackMapping(
        tactic=meta["tactic"],
        tactic_id=meta["tactic_id"],
        technique=meta["technique"],
        technique_id=meta["technique_id"],
        confidence=round(confidence, 2),
        evidence=evidence,
        mitigations=meta["mitigations"],
    )
