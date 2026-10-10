"""Reporting Engine and Deliverable Exporter.

Generates complete Markdown executive reports, presentation slide decks,
one-page summaries, and CSV/JSON registers from structured project data.
"""

from __future__ import annotations

import csv
import io
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ai_audit.financials import FinancialCalculator, FinancialScenario
from ai_audit.models import AuditProject, Opportunity, RiskRegisterItem
from ai_audit.process_map import ProcessMapper
from ai_audit.roadmap import RoadmapGenerator
from ai_audit.scoring import PrioritisationEngine
from ai_audit.security import SecurityAssessmentEngine


class ReportGenerator:
    """Renders formatted reports and exports structured data files."""

    def __init__(self, template_dir: Optional[str] = None):
        if template_dir is None:
            template_dir = str(Path(__file__).parent / "templates")
        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def prepare_context(self, project: AuditProject) -> Dict[str, Any]:
        """Calculates all scores, financial projections, process maps, and roadmap data."""
        engine = PrioritisationEngine(project.scoring_weights)
        ranked_scores = engine.rank_opportunities(project.opportunities)
        opp_map = {o.id: o for o in project.opportunities}

        # Financial results across scenarios
        fin_expected = [
            FinancialCalculator.calculate_opportunity(o, FinancialScenario.EXPECTED)
            for o in project.opportunities
        ]
        fin_conservative = [
            FinancialCalculator.calculate_opportunity(o, FinancialScenario.CONSERVATIVE)
            for o in project.opportunities
        ]
        fin_optimistic = [
            FinancialCalculator.calculate_opportunity(o, FinancialScenario.OPTIMISTIC)
            for o in project.opportunities
        ]

        portfolio_expected = FinancialCalculator.calculate_portfolio_totals(fin_expected)
        portfolio_conservative = FinancialCalculator.calculate_portfolio_totals(fin_conservative)
        portfolio_optimistic = FinancialCalculator.calculate_portfolio_totals(fin_optimistic)

        fin_map = {r.opportunity_id: r for r in fin_expected}

        # Mermaid process diagrams
        mermaid_maps = {
            wf.process_id: ProcessMapper.generate_mermaid(wf, direction="TD")
            for wf in project.workflows
        }

        # Security evaluation
        security_summary = SecurityAssessmentEngine.evaluate_checklist_summary(project.security_checklist)
        risk_analysis = SecurityAssessmentEngine.analyze_risk_register(project.risk_register)

        # Roadmap phases & prototype
        roadmap_phases = RoadmapGenerator.organize_phases(project.roadmap)
        first_prototype = RoadmapGenerator.select_first_prototype(ranked_scores, project.opportunities)
        first_prototype_title = first_prototype.title if first_prototype else "Automated Reporting Assistant"
        first_prototype_rationale = (
            first_prototype.why_ai_or_why_not
            if first_prototype
            else "High value, high data readiness, internal-only human verification loop."
        )

        phase1_cost = sum(
            init.estimated_cost_usd
            for init in roadmap_phases.get("Phase 1: Days 1–30 (Foundations, Security & First Prototype)", [])
        )

        return {
            "project": project,
            "ranked_scores": ranked_scores,
            "opp_map": opp_map,
            "financial_results": fin_expected,
            "fin_map": fin_map,
            "portfolio": portfolio_expected,
            "portfolio_conservative": portfolio_conservative,
            "portfolio_optimistic": portfolio_optimistic,
            "mermaid_maps": mermaid_maps,
            "security_summary": security_summary,
            "risk_analysis": risk_analysis,
            "roadmap_phases": roadmap_phases,
            "first_prototype_title": first_prototype_title,
            "first_prototype_rationale": first_prototype_rationale,
            "phase1_cost": phase1_cost,
            "security_disclaimer": SecurityAssessmentEngine.DISCLAIMER,
        }

    def generate_executive_report(self, project: AuditProject) -> str:
        """Renders the comprehensive 12-section Markdown executive report."""
        template = self.env.get_template("executive_report.md.j2")
        context = self.prepare_context(project)
        return template.render(context)

    def generate_roadmap_markdown(self, project: AuditProject) -> str:
        """Renders the standalone 90-day implementation roadmap."""
        template = self.env.get_template("roadmap_90day.md.j2")
        context = self.prepare_context(project)
        return template.render(context)

    def generate_risk_register_markdown(self, project: AuditProject) -> str:
        """Renders the standalone security and risk register report."""
        template = self.env.get_template("risk_register.md.j2")
        context = self.prepare_context(project)
        return template.render(context)

    def generate_presentation_outline(self, project: AuditProject) -> str:
        """Renders the executive presentation slide deck."""
        template = self.env.get_template("presentation_outline.md.j2")
        context = self.prepare_context(project)
        return template.render(context)

    def generate_one_page_summary(self, project: AuditProject) -> str:
        """Renders the one-page executive brief."""
        template = self.env.get_template("one_page_summary.md.j2")
        context = self.prepare_context(project)
        return template.render(context)

    @classmethod
    def export_opportunities_csv(cls, project: AuditProject) -> str:
        """Exports the opportunity register to CSV format."""
        engine = PrioritisationEngine(project.scoring_weights)
        ranked = engine.rank_opportunities(project.opportunities)
        score_by_id = {s.opportunity_id: s for s in ranked}

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "Rank",
                "ID",
                "Title",
                "Workflow",
                "Automation Type",
                "Human In The Loop",
                "Business Value (1-5)",
                "Data Readiness (1-5)",
                "Delivery Confidence (1-5)",
                "Implementation Effort (1-5)",
                "Operational Risk (1-5)",
                "Prioritisation Score (0-100)",
                "Tier",
                "Hard Stop Status",
                "Responsible Owner",
                "Annual Hours Baseline",
                "Net Hours Saved/Yr",
                "Capacity Released ($/Yr)",
                "Direct Cash Savings ($/Yr)",
                "Implementation Cost ($)",
                "Payback (Months)",
            ]
        )

        for opp in project.opportunities:
            score = score_by_id.get(opp.id)
            fin = FinancialCalculator.calculate_opportunity(opp, FinancialScenario.EXPECTED)
            rank = score.rank if score else 0
            final_score = score.final_score if score else 0.0
            tier = score.tier if score else "Unscored"
            hard_stop = "BLOCKED" if (score and score.is_hard_stop_blocked) else "CLEAR"

            writer.writerow(
                [
                    rank,
                    opp.id,
                    opp.title,
                    opp.workflow_id,
                    opp.automation_type,
                    opp.human_in_the_loop,
                    opp.scoring_inputs.business_value,
                    opp.scoring_inputs.data_readiness,
                    opp.scoring_inputs.delivery_confidence,
                    opp.scoring_inputs.implementation_effort,
                    opp.scoring_inputs.operational_risk,
                    final_score,
                    tier,
                    hard_stop,
                    opp.responsible_owner,
                    fin.baseline_annual_hours,
                    fin.net_hours_saved_annual,
                    fin.capacity_released_value_usd,
                    fin.direct_cash_savings_usd,
                    fin.implementation_cost_usd,
                    fin.payback_period_months or "N/A",
                ]
            )

        return output.getvalue()

    @classmethod
    def export_opportunities_json(cls, project: AuditProject) -> str:
        """Exports the opportunity register and scores to structured JSON."""
        engine = PrioritisationEngine(project.scoring_weights)
        ranked = engine.rank_opportunities(project.opportunities)
        score_by_id = {s.opportunity_id: s for s in ranked}

        records = []
        for opp in project.opportunities:
            score = score_by_id.get(opp.id)
            fin = FinancialCalculator.calculate_opportunity(opp, FinancialScenario.EXPECTED)
            d = opp.to_dict()
            d["scoring_breakdown"] = (
                {
                    "rank": score.rank,
                    "final_score": score.final_score,
                    "tier": score.tier,
                    "is_hard_stop_blocked": score.is_hard_stop_blocked,
                    "hard_stop_reason": score.hard_stop_reason,
                    "explanation": score.explanation,
                }
                if score
                else {}
            )
            d["financial_projection_expected"] = {
                "baseline_annual_hours": fin.baseline_annual_hours,
                "net_hours_saved_annual": fin.net_hours_saved_annual,
                "capacity_released_value_usd": fin.capacity_released_value_usd,
                "direct_cash_savings_usd": fin.direct_cash_savings_usd,
                "total_gross_annual_value_usd": fin.total_gross_annual_value_usd,
                "net_first_year_benefit_usd": fin.net_first_year_benefit_usd,
                "payback_period_months": fin.payback_period_months,
            }
            records.append(d)

        return json.dumps(records, indent=2)

    @classmethod
    def export_risks_csv(cls, project: AuditProject) -> str:
        """Exports the risk register to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "Risk ID",
                "Category",
                "Description",
                "Likelihood (1-5)",
                "Severity (1-5)",
                "Inherent Risk Score",
                "Inherent Risk Level",
                "Mitigation Strategy",
                "Residual Likelihood (1-5)",
                "Residual Severity (1-5)",
                "Residual Risk Score",
                "Residual Risk Level",
                "Owner",
            ]
        )

        for r in project.risk_register:
            writer.writerow(
                [
                    r.risk_id,
                    r.category,
                    r.description,
                    r.likelihood,
                    r.severity,
                    r.inherent_risk_score,
                    r.inherent_risk_level,
                    r.mitigation_strategy,
                    r.residual_likelihood,
                    r.residual_severity,
                    r.residual_risk_score,
                    r.residual_risk_level,
                    r.owner,
                ]
            )

        return output.getvalue()

    def export_all_deliverables(self, project: AuditProject, output_dir: str) -> Dict[str, str]:
        """Generates and writes all report deliverables to disk."""
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        maps_dir = out_path / "process_maps"
        maps_dir.mkdir(parents=True, exist_ok=True)

        created_files = {}

        # 1. Executive Report
        exec_report = self.generate_executive_report(project)
        exec_file = out_path / "executive_report.md"
        exec_file.write_text(exec_report, encoding="utf-8")
        created_files["executive_report"] = str(exec_file)

        # 2. Presentation Outline
        pres_outline = self.generate_presentation_outline(project)
        pres_file = out_path / "presentation_outline.md"
        pres_file.write_text(pres_outline, encoding="utf-8")
        created_files["presentation_outline"] = str(pres_file)

        # 3. One-Page Summary
        one_page = self.generate_one_page_summary(project)
        one_page_file = out_path / "one_page_summary.md"
        one_page_file.write_text(one_page, encoding="utf-8")
        created_files["one_page_summary"] = str(one_page_file)

        # 4. Opportunity Register CSV & JSON
        opp_csv = self.export_opportunities_csv(project)
        opp_csv_file = out_path / "opportunity_register.csv"
        opp_csv_file.write_text(opp_csv, encoding="utf-8")
        created_files["opportunity_register_csv"] = str(opp_csv_file)

        opp_json = self.export_opportunities_json(project)
        opp_json_file = out_path / "opportunity_register.json"
        opp_json_file.write_text(opp_json, encoding="utf-8")
        created_files["opportunity_register_json"] = str(opp_json_file)

        # 5. Risk Register CSV & Markdown
        risk_csv = self.export_risks_csv(project)
        risk_csv_file = out_path / "risk_register.csv"
        risk_csv_file.write_text(risk_csv, encoding="utf-8")
        created_files["risk_register_csv"] = str(risk_csv_file)

        risk_md = self.generate_risk_register_markdown(project)
        risk_md_file = out_path / "risk_register.md"
        risk_md_file.write_text(risk_md, encoding="utf-8")
        created_files["risk_register_md"] = str(risk_md_file)

        # 6. Roadmap 90-Day Markdown
        roadmap_md = self.generate_roadmap_markdown(project)
        roadmap_md_file = out_path / "roadmap_90day.md"
        roadmap_md_file.write_text(roadmap_md, encoding="utf-8")
        created_files["roadmap_90day_md"] = str(roadmap_md_file)

        # 7. Process Maps (Mermaid files)
        for wf in project.workflows:
            mmd = ProcessMapper.generate_mermaid(wf)
            mmd_file = maps_dir / f"{wf.process_id}.mmd"
            mmd_file.write_text(mmd, encoding="utf-8")
            created_files[f"process_map_{wf.process_id}"] = str(mmd_file)

        return created_files
