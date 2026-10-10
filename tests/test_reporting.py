"""Unit tests for process mapping, security, roadmap, reporting, and CLI."""

import csv
import json
import os
from pathlib import Path

import pytest
from ai_audit.models import (
    AuditProject,
    BusinessContext,
    ChecklistStatus,
    ProcessStep,
    ProcessWorkflow,
    RiskLevel,
    RiskRegisterItem,
    SecurityChecklistItem,
)
from ai_audit.process_map import ProcessMapper
from ai_audit.project import ProjectManager
from ai_audit.reporting import ReportGenerator
from ai_audit.roadmap import RoadmapGenerator
from ai_audit.scoring import PrioritisationEngine
from ai_audit.security import SecurityAssessmentEngine


def test_mermaid_generation():
    wf = ProcessWorkflow(
        process_id="wf_onboarding",
        name="Client Onboarding",
        owner="Elena",
        department="Client Services",
        frequency="Per Client",
        annual_frequency_count=36.0,
        steps=[
            ProcessStep(
                step_id="step_1",
                order=1,
                title="Send Intake Form",
                actor="Ops",
                system="Gmail",
                description="Send form",
                handling_time_minutes=30.0,
            ),
            ProcessStep(
                step_id="step_2",
                order=2,
                title="Verify Access",
                actor="Director",
                system="HubSpot",
                description="Check permissions",
                is_decision=True,
                handling_time_minutes=15.0,
                bottleneck_identified=True,
                bottleneck_notes="Chasing logins",
            ),
        ],
    )

    mmd = ProcessMapper.generate_mermaid(wf)
    assert "flowchart TD" in mmd
    assert "wf_onboarding_start" in mmd
    assert "step_1" in mmd
    assert "step_2" in mmd
    assert 'step_2{"' in mmd  # Decision shape check
    assert "style step_2 fill:#fee2e2" in mmd  # Bottleneck style


def test_security_and_risk_engine():
    items = [
        SecurityChecklistItem(
            id="SEC-01",
            category="PII",
            title="Data Scrubbing",
            requirement="Scrub PII",
            status=ChecklistStatus.PASS.value,
        ),
        SecurityChecklistItem(
            id="SEC-02",
            category="Access",
            title="RBAC",
            requirement="Granular tokens",
            status=ChecklistStatus.NEEDS_ATTENTION.value,
        ),
    ]
    summary = SecurityAssessmentEngine.evaluate_checklist_summary(items)
    assert summary["pass_count"] == 1
    assert summary["needs_attention_count"] == 1
    assert summary["readiness_pct"] == 50.0

    risks = [
        RiskRegisterItem(
            risk_id="R-01",
            category="Model Error",
            description="Hallucination",
            likelihood=4,
            severity=4,
            mitigation_strategy="Human in the loop",
            residual_likelihood=1,
            residual_severity=2,
        )
    ]
    analysis = SecurityAssessmentEngine.analyze_risk_register(risks)
    assert analysis["total_risks"] == 1
    assert analysis["average_inherent_score"] == 16.0
    assert analysis["average_residual_score"] == 2.0
    assert analysis["risk_reduction_pct"] > 80.0


def test_roadmap_phase_organization_and_prototype_selection():
    sample = ProjectManager.create_sample_project()
    engine = PrioritisationEngine()
    ranked = engine.rank_opportunities(sample.opportunities)

    proto = RoadmapGenerator.select_first_prototype(ranked, sample.opportunities)
    assert proto is not None
    assert not proto.scoring_inputs.hard_stop_triggered

    phases = RoadmapGenerator.organize_phases(sample.roadmap)
    assert len(phases["Phase 1: Days 1–30 (Foundations, Security & First Prototype)"]) >= 2
    assert len(phases["Phase 2: Days 31–60 (Core Workflow Automation & System Integration)"]) >= 2
    assert len(phases["Phase 3: Days 61–90 (Scaling, Advanced AI Drafting & Continuous Optimization)"]) >= 2


def test_report_generation_and_deliverable_export(tmp_path: Path):
    sample = ProjectManager.create_sample_project()
    rg = ReportGenerator()

    # 1. Executive report
    exec_report = rg.generate_executive_report(sample)
    # Check all 12 key sections exist in output
    assert "1. Executive Summary" in exec_report
    assert "2. Business Context and Strategic Goals" in exec_report
    assert "3. Current-State Findings and Operational Workload Inventory" in exec_report
    assert "4. Key Process Bottlenecks and Friction Points" in exec_report
    assert "5. Prioritised Opportunity Register" in exec_report
    assert "6. Estimated Business Impact and Scenario Analysis" in exec_report
    assert "7. Recommended Architecture and Tool Choices" in exec_report
    assert "8. Security, Privacy, and Operational Risks" in exec_report
    assert "9. Ninety-Day Implementation Roadmap" in exec_report
    assert "10. Recommended First Prototype" in exec_report
    assert "11. Decisions Required from Leadership" in exec_report
    assert "12. Evidence Gaps and Immediate Next Steps" in exec_report

    # 2. Presentation Outline
    pres = rg.generate_presentation_outline(sample)
    assert "Executive Presentation" in pres
    assert "Slide 1:" in pres

    # 3. One-Page Summary
    one_page = rg.generate_one_page_summary(sample)
    assert "Executive Brief" in one_page

    # 4. Deliverables export
    out_dir = str(tmp_path / "test_outputs")
    files = rg.export_all_deliverables(sample, out_dir)

    assert Path(files["executive_report"]).exists()
    assert Path(files["presentation_outline"]).exists()
    assert Path(files["one_page_summary"]).exists()
    assert Path(files["opportunity_register_csv"]).exists()
    assert Path(files["opportunity_register_json"]).exists()
    assert Path(files["risk_register_csv"]).exists()
    assert Path(files["roadmap_90day_md"]).exists()
    assert Path(files["risk_register_md"]).exists()

    # Verify CSV contents valid
    with open(files["opportunity_register_csv"], "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert "Rank" in header
        assert "Prioritisation Score (0-100)" in header
        rows = list(reader)
        assert len(rows) == len(sample.opportunities)
