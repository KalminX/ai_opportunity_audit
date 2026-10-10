"""Unit tests for domain models."""

import pytest
from ai_audit.models import (
    AuditProject,
    AutomationType,
    BusinessContext,
    ChecklistStatus,
    EvidenceLevel,
    FinancialAssumptions,
    HumanInTheLoop,
    Opportunity,
    ProcessStep,
    ProcessWorkflow,
    RiskLevel,
    RiskRegisterItem,
    ScoringInputs,
    ScoringWeights,
    SecurityChecklistItem,
)
from ai_audit.project import ProjectManager


def test_process_step_and_workflow_calculations():
    steps = [
        ProcessStep(
            step_id="s1",
            order=1,
            title="Manual Task 1",
            actor="Analyst",
            system="Sheets",
            description="Do task",
            is_manual=True,
            handling_time_minutes=30.0,
        ),
        ProcessStep(
            step_id="s2",
            order=2,
            title="Automated Step",
            actor="System",
            system="API",
            description="Sync",
            is_manual=False,
            handling_time_minutes=0.0,
        ),
        ProcessStep(
            step_id="s3",
            order=3,
            title="Manual Review",
            actor="Director",
            system="Docs",
            description="Review",
            is_manual=True,
            is_approval=True,
            handling_time_minutes=15.0,
            bottleneck_identified=True,
        ),
    ]

    wf = ProcessWorkflow(
        process_id="wf_test",
        name="Test Workflow",
        owner="Lead",
        department="Ops",
        frequency="Weekly",
        annual_frequency_count=52.0,
        steps=steps,
    )

    assert wf.total_manual_handling_time_minutes() == 45.0
    # 45 mins * 52 runs = 2340 mins = 39.0 hours
    assert wf.total_annual_manual_hours() == 39.0
    assert len(wf.bottleneck_steps()) == 1
    assert wf.bottleneck_steps()[0].step_id == "s3"


def test_scoring_weights_validation():
    valid = ScoringWeights(
        business_value=0.30,
        data_readiness=0.20,
        delivery_confidence=0.20,
        implementation_effort=0.15,
        operational_risk=0.15,
    )
    assert valid.validate() is True

    invalid = ScoringWeights(
        business_value=0.50,
        data_readiness=0.20,
        delivery_confidence=0.20,
        implementation_effort=0.15,
        operational_risk=0.15,
    )
    assert invalid.validate() is False


def test_risk_register_item_scoring():
    risk = RiskRegisterItem(
        risk_id="R-1",
        category="Privacy",
        description="Data leak",
        likelihood=4,
        severity=5,
        mitigation_strategy="Encryption & ZDR",
        residual_likelihood=1,
        residual_severity=2,
        owner="Security Officer",
    )

    assert risk.inherent_risk_score == 20
    assert risk.inherent_risk_level == RiskLevel.CRITICAL.value
    assert risk.residual_risk_score == 2
    assert risk.residual_risk_level == RiskLevel.LOW.value

    d = risk.to_dict()
    assert d["inherent_risk_score"] == 20
    assert d["residual_risk_score"] == 2


def test_project_serialization_roundtrip():
    sample = ProjectManager.create_sample_project()
    json_str = sample.to_json()
    loaded = AuditProject.from_json(json_str)

    assert loaded.project_id == sample.project_id
    assert loaded.business_context.company_name == sample.business_context.company_name
    assert len(loaded.workflows) == len(sample.workflows)
    assert len(loaded.opportunities) == len(sample.opportunities)
    assert len(loaded.security_checklist) == len(sample.security_checklist)
    assert len(loaded.risk_register) == len(sample.risk_register)
    assert len(loaded.roadmap) == len(sample.roadmap)
