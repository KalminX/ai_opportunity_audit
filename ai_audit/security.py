"""Security and Data-Readiness Assessment Engine.

Evaluates data governance, privacy guardrails, API security, and produces
a formal Risk Register with inherent vs residual risk scoring.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from ai_audit.models import (
    ChecklistStatus,
    EvidenceLevel,
    RiskLevel,
    RiskRegisterItem,
    SecurityChecklistItem,
)


class SecurityAssessmentEngine:
    """Manages security checklists, data-readiness gates, and risk registers."""

    DISCLAIMER = (
        "DISCLAIMER: This assessment is an operational and technical evaluation of AI data readiness "
        "and security practices. It does NOT constitute legal advice or formal regulatory compliance certification. "
        "Engage qualified legal counsel for binding GDPR, CCPA, or industry-specific compliance determinations."
    )

    @staticmethod
    def get_standard_checklist_definitions() -> List[Dict[str, str]]:
        """Returns the 8 core security and data-readiness checklist dimensions."""
        return [
            {
                "id": "SEC-01",
                "category": "Personal & Confidential Data",
                "title": "PII and Sensitive Data Identification & Redaction",
                "requirement": "Identify all client PII, confidential financials, and sensitive credentials across workflows; enforce automated tokenization or redaction before model processing.",
            },
            {
                "id": "SEC-02",
                "category": "Access Controls & Least Privilege",
                "title": "Role-Based Access Control (RBAC) & API Token Scopes",
                "requirement": "Automation tools and AI integrations must use granular, least-privilege API keys and scoped service accounts; enforce MFA for administrative consoles.",
            },
            {
                "id": "SEC-03",
                "category": "Data Retention & Deletion",
                "title": "Retention Schedules and Right-to-be-Forgotten Compliance",
                "requirement": "Establish clear data retention windows for intermediate logs, generated drafts, and vector embeddings; provide documented mechanisms to purge client data upon offboarding.",
            },
            {
                "id": "SEC-04",
                "category": "Vendor Terms & Model Training",
                "title": "Zero-Data-Retention (ZDR) and No-Training Verification",
                "requirement": "Contractually ensure that LLM vendors and cloud platforms do not use client data or prompt history to train foundation models.",
            },
            {
                "id": "SEC-05",
                "category": "Data Residency & Jurisdiction",
                "title": "Geographic Storage and Cross-Border Transfer Compliance",
                "requirement": "Verify regional data residency (e.g. EU/UK/US data center storage) for all third-party services holding customer or business records.",
            },
            {
                "id": "SEC-06",
                "category": "Human Review & Escalation Guardrails",
                "title": "Human-in-the-Loop Approval & Fallback Pathways",
                "requirement": "Mandate explicit human approval for all external client communications, financial transactions, and high-impact contractual changes; provide deterministic manual fallbacks when systems fail.",
            },
            {
                "id": "SEC-07",
                "category": "Auditability, Reliability & Telemetry",
                "title": "Immutable Audit Logging and Execution Monitoring",
                "requirement": "Log all prompt invocations, automation execution payloads, user approvals, and error states to centralized tamper-resistant log stores.",
            },
            {
                "id": "SEC-08",
                "category": "Integration Security & Secrets Management",
                "title": "Centralized Secrets Vault and Key Rotation",
                "requirement": "Store all API tokens and OAuth secrets in a dedicated vault (e.g., AWS Secrets Manager, 1Password Secrets); prohibit plaintext secrets in code or workflow visual builders.",
            },
        ]

    @classmethod
    def evaluate_checklist_summary(cls, items: List[SecurityChecklistItem]) -> Dict[str, Any]:
        """Summarizes security checklist readiness."""
        total = len(items)
        passed = sum(1 for i in items if i.status == ChecklistStatus.PASS.value)
        attention = sum(1 for i in items if i.status == ChecklistStatus.NEEDS_ATTENTION.value)
        failed = sum(1 for i in items if i.status == ChecklistStatus.FAIL.value)
        na = sum(1 for i in items if i.status == ChecklistStatus.NOT_APPLICABLE.value)

        readiness_pct = (passed / (total - na) * 100.0) if (total - na) > 0 else 0.0

        return {
            "total_items": total,
            "pass_count": passed,
            "needs_attention_count": attention,
            "fail_count": failed,
            "na_count": na,
            "readiness_pct": round(readiness_pct, 1),
            "is_ready_for_deployment": failed == 0 and attention <= 2,
        }

    @classmethod
    def analyze_risk_register(cls, risks: List[RiskRegisterItem]) -> Dict[str, Any]:
        """Evaluates aggregate risk posture before and after mitigation."""
        critical_inherent = sum(1 for r in risks if r.inherent_risk_level == RiskLevel.CRITICAL.value)
        high_inherent = sum(1 for r in risks if r.inherent_risk_level == RiskLevel.HIGH.value)
        critical_residual = sum(1 for r in risks if r.residual_risk_level == RiskLevel.CRITICAL.value)
        high_residual = sum(1 for r in risks if r.residual_risk_level == RiskLevel.HIGH.value)

        avg_inherent = (sum(r.inherent_risk_score for r in risks) / len(risks)) if risks else 0.0
        avg_residual = (sum(r.residual_risk_score for r in risks) / len(risks)) if risks else 0.0

        risk_reduction_pct = (
            ((avg_inherent - avg_residual) / avg_inherent * 100.0) if avg_inherent > 0 else 0.0
        )

        return {
            "total_risks": len(risks),
            "critical_inherent_count": critical_inherent,
            "high_inherent_count": high_inherent,
            "critical_residual_count": critical_residual,
            "high_residual_count": high_residual,
            "average_inherent_score": round(avg_inherent, 1),
            "average_residual_score": round(avg_residual, 1),
            "risk_reduction_pct": round(risk_reduction_pct, 1),
        }
