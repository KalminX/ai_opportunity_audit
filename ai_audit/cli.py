"""Command-Line Interface for AI Opportunity Audit & Automation Roadmap Toolkit.

Provides commands to initialize audits, map workflows, evaluate opportunities,
calculate financial scenarios, review security checklists, generate roadmaps,
and export executive reports.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from ai_audit.financials import FinancialCalculator, FinancialScenario
from ai_audit.models import AuditProject
from ai_audit.process_map import ProcessMapper
from ai_audit.project import ProjectManager
from ai_audit.reporting import ReportGenerator
from ai_audit.roadmap import RoadmapGenerator
from ai_audit.scoring import PrioritisationEngine
from ai_audit.security import SecurityAssessmentEngine
from ai_audit.web.server import start_server


def load_project_or_exit(file_path: Optional[str]) -> AuditProject:
    """Helper to load project or default to data/sample_project.json."""
    path = file_path or "data/sample_project.json"
    p = Path(path)
    if not p.exists():
        # Fallback to creating sample in memory if default not found
        if path == "data/sample_project.json":
            sample = ProjectManager.create_sample_project()
            ProjectManager.save_project(sample, "data/sample_project.json")
            return sample
        print(f"Error: Project file '{path}' not found.", file=sys.stderr)
        sys.exit(1)
    return ProjectManager.load_project(str(p))


def cmd_init(args: argparse.Namespace) -> None:
    """Initializes a new audit project."""
    target = Path(args.file or "data/new_audit.json")
    if target.exists() and not args.force:
        print(f"File '{target}' already exists. Use --force to overwrite.", file=sys.stderr)
        sys.exit(1)

    if args.sample:
        project = ProjectManager.create_sample_project()
        print(f"✨ Initialized sample case study for 'Apex Growth Partners' at: {target}")
    else:
        # Load blank template
        blank_path = Path("data/blank_template.json")
        if blank_path.exists():
            project = ProjectManager.load_project(str(blank_path))
        else:
            project = ProjectManager.create_sample_project()
        project.project_name = args.name or "New AI Opportunity Audit"
        print(f"✨ Initialized new audit project '{project.project_name}' at: {target}")

    ProjectManager.save_project(project, str(target))
    print("Use 'ai-audit info --file " + str(target) + "' to inspect.")


def cmd_info(args: argparse.Namespace) -> None:
    """Displays business context, tech stack, and scope summary."""
    project = load_project_or_exit(args.file)
    bc = project.business_context

    print(f"\n========================================================")
    print(f"  {project.project_name.upper()}")
    print(f"========================================================")
    print(f"Client Organization : {bc.company_name} ({bc.industry})")
    print(f"Headcount / Revenue : {bc.size_employees} FTEs | ${bc.annual_revenue_usd:,.0f} USD")
    print(f"Audit Date / Lead   : {project.audit_date} | {project.consultant_name}")
    print(f"\n--- Strategic Objectives ---")
    for i, obj in enumerate(bc.strategic_objectives, 1):
        print(f"  {i}. {obj}")

    print(f"\n--- Technology Stack in Scope ---")
    for t in bc.current_tech_stack:
        print(f"  • {t['name']:<20} [{t['category']:<22}] : {t['purpose']}")

    print(f"\n--- Workflows Evaluated ({len(project.workflows)}) ---")
    for w in project.workflows:
        print(f"  • [{w.process_id}] {w.name:<38} : {w.total_annual_manual_hours():,.1f} hrs/yr ({w.department})")

    print(f"\n--- Opportunities Cataloged ({len(project.opportunities)}) ---")
    for o in project.opportunities:
        print(f"  • [{o.id}] {o.title:<55} [{o.automation_type}]")
    print()


def cmd_map(args: argparse.Namespace) -> None:
    """Displays workflow process mapping and Mermaid diagram."""
    project = load_project_or_exit(args.file)
    target_wf = None
    if args.process_id:
        for w in project.workflows:
            if w.process_id.lower() == args.process_id.lower():
                target_wf = w
                break
        if not target_wf:
            print(f"Error: Process '{args.process_id}' not found. Available: {[w.process_id for w in project.workflows]}", file=sys.stderr)
            sys.exit(1)
    else:
        target_wf = project.workflows[0]

    analytics = ProcessMapper.analyze_process_bottlenecks(target_wf)
    mermaid_code = ProcessMapper.generate_mermaid(target_wf)

    print(f"\n========================================================")
    print(f"  WORKFLOW: {target_wf.name.upper()} ({target_wf.department})")
    print(f"========================================================")
    print(f"Process Owner     : {target_wf.owner}")
    print(f"Frequency / Count : {target_wf.frequency} ({target_wf.annual_frequency_count} runs/yr)")
    print(f"Manual Steps      : {analytics['manual_steps_count']}/{analytics['total_steps']} ({analytics['manual_ratio_pct']}%)")
    print(f"Manual Workload   : {analytics['total_manual_handling_mins_per_run']:.0f} mins/run -> {analytics['annual_manual_hours']:,.1f} annual hours")
    print(f"Error Rate        : {target_wf.current_error_rate_pct}%\n")

    print(f"--- Process Steps ---")
    for s in target_wf.steps:
        flag = "[Bottleneck ⚠️]" if s.bottleneck_identified else ""
        man = "[Manual ✍️]" if s.is_manual else "[Auto ⚡]"
        print(f"  Step {s.order}: {s.title:<40} {man} {s.handling_time_minutes:2.0f}m  {flag}")
        if s.bottleneck_notes:
            print(f"          ↳ Friction: {s.bottleneck_notes} ({s.evidence_level})")

    print(f"\n--- Mermaid Flowchart Definition ---")
    print(mermaid_code)
    print()

    if args.out:
        out_path = Path(args.out)
        out_path.write_text(mermaid_code, encoding="utf-8")
        print(f"Saved Mermaid chart to: {out_path}")


def cmd_score(args: argparse.Namespace) -> None:
    """Calculates transparent multi-criteria opportunity scores."""
    project = load_project_or_exit(args.file)
    engine = PrioritisationEngine(project.scoring_weights)
    ranked = engine.rank_opportunities(project.opportunities)
    opp_map = {o.id: o for o in project.opportunities}

    print(f"\n=========================================================================================================")
    print(f"  TRANSPARENT PRIORITISATION ENGINE: OPPORTUNITY RANKING")
    print(f"=========================================================================================================")
    print(f"{'Rank':<5} {'ID':<8} {'Score':<7} {'Tier':<22} {'Feasibility':<12} {'Human Gate':<18} {'Title'}")
    print(f"-" * 105)

    for s in ranked:
        opp = opp_map[s.opportunity_id]
        gate_str = opp.human_in_the_loop
        status_str = f"{s.final_score:.1f}" if not s.is_hard_stop_blocked else "BLOCKED"
        print(f"#{s.rank:<4} {s.opportunity_id:<8} {status_str:<7} {s.tier:<22} {opp.scoring_inputs.delivery_confidence}/5.0 {'':<4} {gate_str:<18} {opp.title}")

    print(f"\n--- Hard-Stop & Governance Review ---")
    blocked = [s for s in ranked if s.is_hard_stop_blocked]
    if blocked:
        for b in blocked:
            print(f"  ⛔ [{b.opportunity_id}] {b.opportunity_title}")
            print(f"     Reason: {b.hard_stop_reason}")
    else:
        print("  ✅ All scored initiatives cleared hard-stop safety filters.")
    print()


def cmd_financial(args: argparse.Namespace) -> None:
    """Calculates workload capacity, direct cash savings, payback, and ROI."""
    project = load_project_or_exit(args.file)
    scenario = FinancialScenario(args.scenario.lower())

    fin_results = [
        FinancialCalculator.calculate_opportunity(o, scenario)
        for o in project.opportunities
    ]
    portfolio = FinancialCalculator.calculate_portfolio_totals(fin_results)

    print(f"\n=========================================================================================================")
    print(f"  FINANCIAL & WORKLOAD ANALYSIS (SCENARIO: {scenario.value.upper()})")
    print(f"=========================================================================================================")
    print(f"{'ID':<8} {'Role Impacted':<24} {'Base Hrs':<10} {'Freed Hrs':<10} {'Capacity $':<12} {'Cash Sav $':<12} {'Impl Cost':<10} {'Payback'}")
    print(f"-" * 105)

    for f in fin_results:
        payback_str = f"{f.payback_period_months:.1f}m" if f.payback_period_months else "N/A"
        print(
            f"{f.opportunity_id:<8} {f.role_title:<24} {f.baseline_annual_hours:<10.0f} "
            f"{f.net_hours_saved_annual:<10.0f} ${f.capacity_released_value_usd:<11,.0f} "
            f"${f.direct_cash_savings_usd:<11,.0f} ${f.implementation_cost_usd:<9,.0f} {payback_str}"
        )

    print(f"-" * 105)
    print(f"PORTFOLIO TOTALS:")
    print(f"  • Total Baseline Workload in Scope : {portfolio['total_baseline_hours']:,.1f} hrs/yr (${portfolio['total_baseline_cost_usd']:,.0f} loaded internal cost)")
    print(f"  • Net Staff Capacity Released      : {portfolio['total_net_hours_saved']:,.1f} hrs/yr (${portfolio['total_capacity_released_usd']:,.0f}/yr value)")
    print(f"  • Direct Hard-Dollar Cash Savings  : ${portfolio['total_direct_cash_savings_usd']:,.0f}/yr")
    print(f"  • Combined Gross Annual Value      : ${portfolio['total_gross_annual_value_usd']:,.0f}/yr")
    print(f"  • Total Implementation Investment  : ${portfolio['total_implementation_cost_usd']:,.0f} (One-off)")
    print(f"  • Net First-Year Financial Benefit : ${portfolio['total_net_first_year_benefit_usd']:,.0f}")
    print(f"  • Portfolio Payback Horizon        : {portfolio['portfolio_payback_months']} months")
    print(f"  • 3-Year Estimated ROI             : {portfolio['portfolio_3yr_roi_pct']}%\n")


def cmd_risk(args: argparse.Namespace) -> None:
    """Evaluates security checklist and risk register."""
    project = load_project_or_exit(args.file)
    sec_summary = SecurityAssessmentEngine.evaluate_checklist_summary(project.security_checklist)
    risk_analysis = SecurityAssessmentEngine.analyze_risk_register(project.risk_register)

    print(f"\n========================================================")
    print(f"  SECURITY & DATA-READINESS ASSESSMENT")
    print(f"========================================================")
    print(f"Overall Data Readiness : {sec_summary['readiness_pct']}%")
    print(f"Passed Checks          : {sec_summary['pass_count']}/{sec_summary['total_items']}")
    print(f"Needs Attention        : {sec_summary['needs_attention_count']}")
    print(f"Failed Checks          : {sec_summary['fail_count']}\n")

    print("--- 8-Point Security Checklist ---")
    for c in project.security_checklist:
        badge = f"[{c.status}]"
        print(f"  • {c.id} {c.title:<45} {badge}")
        if c.remediation_action:
            print(f"    ↳ Remediation: {c.remediation_action}")

    print(f"\n--- Operational Risk Register ({len(project.risk_register)} Risks) ---")
    print(f"Average Inherent Risk: {risk_analysis['average_inherent_score']}/25 -> Residual: {risk_analysis['average_residual_score']}/25 ({risk_analysis['risk_reduction_pct']}% Risk Reduction)")
    for r in project.risk_register:
        print(f"  • [{r.risk_id}] {r.category:<35} Inherent: {r.inherent_risk_level:<8} -> Residual: {r.residual_risk_level:<8} (Owner: {r.owner})")
        print(f"    ↳ Mitigation: {r.mitigation_strategy}")
    print()


def cmd_roadmap(args: argparse.Namespace) -> None:
    """Displays 90-day phased roadmap initiatives."""
    project = load_project_or_exit(args.file)
    phases = RoadmapGenerator.organize_phases(project.roadmap)
    engine = PrioritisationEngine(project.scoring_weights)
    ranked = engine.rank_opportunities(project.opportunities)
    proto = RoadmapGenerator.select_first_prototype(ranked, project.opportunities)

    print(f"\n========================================================")
    print(f"  90-DAY IMPLEMENTATION ROADMAP")
    print(f"========================================================")
    if proto:
        print(f"⭐ RECOMMENDED FIRST PROTOTYPE: [{proto.id}] {proto.title}")
        print(f"   Rationale: High value, structured data APIs, internal review loop eliminates external risk.\n")

    for phase_name, inits in phases.items():
        print(f"--- {phase_name.upper()} ---")
        for init in inits:
            p_flag = " (⭐ PROTOTYPE)" if init.is_first_prototype else ""
            print(f"  🔹 {init.title}{p_flag}")
            print(f"     Owner: {init.responsible_role} | Effort: {init.estimated_effort_weeks} wks | Cost: ${init.estimated_cost_usd:,.0f}")
            print(f"     Gate : {init.go_no_go_gate}")
        print()


def cmd_report(args: argparse.Namespace) -> None:
    """Generates all reports and deliverable files."""
    project = load_project_or_exit(args.file)
    out_dir = args.output_dir or "outputs"
    rg = ReportGenerator()
    created = rg.export_all_deliverables(project, out_dir)

    print(f"\n========================================================")
    print(f"  REPORT GENERATION COMPLETE")
    print(f"========================================================")
    print(f"Deliverables exported to: '{out_dir}/'")
    for k, v in created.items():
        print(f"  • {k:<30} -> {v}")
    print("\nView live interactive dashboard with: ai-audit serve\n")


def cmd_serve(args: argparse.Namespace) -> None:
    """Launches the lightweight local web dashboard."""
    project = load_project_or_exit(args.file)
    start_server(project, file_path=args.file, port=args.port)


def build_parser() -> argparse.ArgumentParser:
    file_parent = argparse.ArgumentParser(add_help=False)
    file_parent.add_argument("--file", "-f", help="Path to project JSON file (defaults to data/sample_project.json)")

    parser = argparse.ArgumentParser(
        prog="ai-audit",
        description="AI Opportunity Audit & Automation Roadmap Toolkit",
        parents=[file_parent],
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # init
    p_init = subparsers.add_parser("init", help="Initialize a new audit project", parents=[file_parent])
    p_init.add_argument("name", nargs="?", help="Project or company name")
    p_init.add_argument("--sample", action="store_true", help="Initialize with sample case study data")
    p_init.add_argument("--force", action="store_true", help="Overwrite existing project file")

    # info
    p_info = subparsers.add_parser("info", help="Display business context, tech stack, and scope", parents=[file_parent])

    # map
    p_map = subparsers.add_parser("map", help="Inspect process map and Mermaid flowchart", parents=[file_parent])
    p_map.add_argument("process_id", nargs="?", help="Process ID to inspect (e.g., weekly_reporting, client_onboarding)")
    p_map.add_argument("--out", "-o", help="Write Mermaid source code to file")

    # score
    p_score = subparsers.add_parser("score", help="Calculate opportunity prioritisation scores", parents=[file_parent])

    # financial
    p_fin = subparsers.add_parser("financial", help="Run workload & financial ROI scenario analysis", parents=[file_parent])
    p_fin.add_argument("--scenario", "-s", default="expected", choices=["conservative", "expected", "optimistic"], help="Scenario to model")

    # risk
    p_risk = subparsers.add_parser("risk", help="Evaluate security checklist and risk register", parents=[file_parent])

    # roadmap
    p_road = subparsers.add_parser("roadmap", help="Display 90-day implementation roadmap", parents=[file_parent])

    # report
    p_rep = subparsers.add_parser("report", help="Generate all markdown and CSV deliverable reports", parents=[file_parent])
    p_rep.add_argument("--output-dir", "-o", default="outputs", help="Output directory for generated reports")

    # serve
    p_srv = subparsers.add_parser("serve", help="Launch local HTTP dashboard server", parents=[file_parent])
    p_srv.add_argument("--port", "-p", type=int, default=8080, help="Port to run web dashboard (default: 8080)")

    return parser


def main() -> None:
    parser = build_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()
    if args.command == "init":
        cmd_init(args)
    elif args.command == "info":
        cmd_info(args)
    elif args.command == "map":
        cmd_map(args)
    elif args.command == "score":
        cmd_score(args)
    elif args.command == "financial":
        cmd_financial(args)
    elif args.command == "risk":
        cmd_risk(args)
    elif args.command == "roadmap":
        cmd_roadmap(args)
    elif args.command == "report":
        cmd_report(args)
    elif args.command == "serve":
        cmd_serve(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
