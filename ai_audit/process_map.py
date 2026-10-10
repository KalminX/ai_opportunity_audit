"""Process Mapping and Mermaid Flowchart Generator.

Transforms structured process workflow data into clear Mermaid diagrams,
highlights bottlenecks and manual toil, and tags findings with evidence levels.
"""

from __future__ import annotations

import html
import re
from typing import Dict, List, Optional

from ai_audit.models import EvidenceLevel, ProcessStep, ProcessWorkflow


class ProcessMapper:
    """Generates Mermaid flowchart definitions and bottleneck diagnostics from workflows."""

    @staticmethod
    def sanitize_label(text: str) -> str:
        """Sanitizes text for safe inclusion in Mermaid node labels."""
        # Replace newlines with <br/> and escape quotes
        clean = text.replace('"', "'").replace("\n", "<br/>")
        return clean

    @classmethod
    def generate_mermaid(
        cls,
        workflow: ProcessWorkflow,
        direction: str = "TD",
        highlight_bottlenecks: bool = True,
    ) -> str:
        """Generates clean, GitHub-compatible Mermaid flowchart syntax."""
        lines = [f"flowchart {direction}"]

        # Subgraph for workflow context
        safe_workflow_name = cls.sanitize_label(workflow.name)
        lines.append(f'  subgraph SG1 ["Workflow: {safe_workflow_name} ({workflow.department})"]')

        # Start Node
        start_node_id = f"{workflow.process_id}_start"
        lines.append(f'    {start_node_id}(["Start: {safe_workflow_name} Trigger"])')

        # Node definitions
        prev_node_id = start_node_id
        bottleneck_nodes = []
        manual_toil_nodes = []

        for step in sorted(workflow.steps, key=lambda s: s.order):
            step_node_id = step.step_id
            badge = ""
            if step.is_manual:
                badge += " ✍️ [Manual]"
                manual_toil_nodes.append(step_node_id)
            else:
                badge += " ⚡ [Auto]"

            if step.bottleneck_identified:
                badge += " ⚠️ [Bottleneck]"
                bottleneck_nodes.append(step_node_id)

            label_parts = [
                f"<b>Step {step.order}: {cls.sanitize_label(step.title)}</b>",
                f"Actor: {cls.sanitize_label(step.actor)} | System: {cls.sanitize_label(step.system)}",
                f"Time: {step.handling_time_minutes:.0f} mins | Status: {badge}",
            ]
            if step.bottleneck_notes:
                label_parts.append(f"<i>Bottleneck: {cls.sanitize_label(step.bottleneck_notes)}</i>")

            label = "<br/>".join(label_parts)

            # Shape selection
            if step.is_decision:
                lines.append(f'    {step_node_id}{{"{label}"}}')
            elif step.is_approval:
                lines.append(f'    {step_node_id}{{"🛡️ Approval Gate: {label}"}}')
            else:
                lines.append(f'    {step_node_id}["{label}"]')

        lines.append("  end")

        # Edge definitions
        if workflow.steps:
            first_step = sorted(workflow.steps, key=lambda s: s.order)[0]
            lines.append(f"  {start_node_id} --> {first_step.step_id}")

            for step in sorted(workflow.steps, key=lambda s: s.order):
                if step.next_step_ids:
                    for target_id in step.next_step_ids:
                        if step.is_decision or step.is_approval:
                            lines.append(f'  {step.step_id} -->|"Next / Approved"| {target_id}')
                        else:
                            lines.append(f"  {step.step_id} --> {target_id}")
                else:
                    # Look up next sequential step
                    next_steps = [s for s in workflow.steps if s.order == step.order + 1]
                    if next_steps:
                        target = next_steps[0]
                        lines.append(f"  {step.step_id} --> {target.step_id}")
                    else:
                        end_node_id = f"{workflow.process_id}_end"
                        lines.append(f'    {end_node_id}(["End: Workflow Complete"])')
                        lines.append(f"  {step.step_id} --> {end_node_id}")

        # Highlight styling
        if highlight_bottlenecks and bottleneck_nodes:
            for bn in bottleneck_nodes:
                lines.append(f"  style {bn} fill:#fee2e2,stroke:#ef4444,stroke-width:2px,color:#991b1b")

        return "\n".join(lines)

    @classmethod
    def analyze_process_bottlenecks(cls, workflow: ProcessWorkflow) -> Dict[str, Any]:
        """Analyzes process for manual toil, friction, and bottleneck evidence."""
        total_steps = len(workflow.steps)
        manual_steps = [s for s in workflow.steps if s.is_manual]
        manual_ratio = (len(manual_steps) / total_steps) if total_steps > 0 else 0.0
        total_manual_time = workflow.total_manual_handling_time_minutes()
        annual_hours = workflow.total_annual_manual_hours()

        bottlenecks = []
        for s in workflow.steps:
            if s.bottleneck_identified or s.handling_time_minutes >= 30.0:
                bottlenecks.append(
                    {
                        "step_id": s.step_id,
                        "title": s.title,
                        "actor": s.actor,
                        "system": s.system,
                        "handling_time_minutes": s.handling_time_minutes,
                        "is_approval": s.is_approval,
                        "notes": s.bottleneck_notes or "High manual handling time.",
                        "evidence_level": s.evidence_level,
                    }
                )

        return {
            "process_id": workflow.process_id,
            "name": workflow.name,
            "total_steps": total_steps,
            "manual_steps_count": len(manual_steps),
            "manual_ratio_pct": round(manual_ratio * 100.0, 1),
            "total_manual_handling_mins_per_run": total_manual_time,
            "annual_manual_hours": round(annual_hours, 1),
            "bottlenecks": bottlenecks,
        }
