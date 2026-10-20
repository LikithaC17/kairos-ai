"""
Security Alert Generation Engine for NetForecast AI.

Translates high-risk forecasting decisions into structured, actionable
Security Operations Center (SOC) early-warning alerts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import time
from typing import Any, Dict, List, Optional
import uuid

from mitre.attack_mapping import MitreAttackMapping


@dataclass
class SecurityAlert:
    id: str
    alert_id: str
    timestamp: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    title: str
    description: str
    stage: str
    attack_stage: str
    risk_score: int
    confidence: float
    evidence: List[str]
    recommended_action: str
    recommended_context: str
    mitre_technique_id: str
    mitre_tactic: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AlertEngine:
    """
    Evaluates SecurityDecisions and generates alerts when threat thresholds are crossed.
    """

    def __init__(self, alert_threshold: int = 35):
        self.alert_threshold = alert_threshold

    def evaluate_decision(
        self,
        timestamp: str,
        risk_score: int,
        confidence: float,
        attack_stage: str,
        predicted_stage: str,
        threat_type: str,
        evidence: List[str],
        mitre_mapping: MitreAttackMapping,
    ) -> Optional[SecurityAlert]:
        """
        Emits a structured SecurityAlert if threat score exceeds the activation threshold.
        """
        if risk_score < self.alert_threshold:
            return None

        # Determine severity
        if risk_score >= 80:
            severity = "CRITICAL"
        elif risk_score >= 60:
            severity = "HIGH"
        elif risk_score >= 40:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        uid = f"ALT-{str(uuid.uuid4())[:8].upper()}"

        title = f"{severity} Threat Alert: {threat_type} Projected ({predicted_stage})"
        description = (
            f"Forecast engine detected elevated risk score of {risk_score}/100. "
            f"Predicted transition toward '{predicted_stage}' with {confidence*100:.1f}% confidence."
        )

        rec_actions = mitre_mapping.mitigations if mitre_mapping else []
        action_str = "; ".join(rec_actions[:2]) if rec_actions else "Monitor network traffic telemetry."

        rec_context = (
            f"Adversary activity matches MITRE ATT&CK {mitre_mapping.technique_id} "
            f"({mitre_mapping.technique}) in tactic {mitre_mapping.tactic}."
        )

        return SecurityAlert(
            id=uid,
            alert_id=uid,
            timestamp=timestamp,
            severity=severity,
            title=title,
            description=description,
            stage=attack_stage,
            attack_stage=attack_stage,
            risk_score=risk_score,
            confidence=round(confidence, 2),
            evidence=evidence,
            recommended_action=action_str,
            recommended_context=rec_context,
            mitre_technique_id=mitre_mapping.technique_id if mitre_mapping else "T1595",
            mitre_tactic=mitre_mapping.tactic if mitre_mapping else "Reconnaissance",
        )
