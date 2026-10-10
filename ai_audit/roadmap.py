"""Ninety-Day Implementation Roadmap Generator.

Builds a structured, three-phase implementation roadmap (Days 1-30, Days 31-60, Days 61-90)
prioritising security foundations, quick-win prototypes, and phased rollout with go/no-go gates.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from ai_audit.models import Opportunity, RoadmapInitiative
from ai_audit.scoring import PrioritisationEngine, ScoreBreakdown


class RoadmapGenerator:
    """Generates and structures 90-day implementation initiatives."""

    @classmethod
    def select_first_prototype(
        cls,
        ranked_scores: List[ScoreBreakdown],
        opportunities: List[Opportunity],
    ) -> Optional[Opportunity]:
        """Selects the ideal first prototype initiative.

        Criteria:
          - Non-blocked.
          - High Business Value (>= 3.5).
          - High Delivery Confidence (>= 4.0).
          - Low/Medium Implementation Effort (<= 3.0).
          - Low Operational Risk (<= 2.0).
          - Clear internal-only human review feedback loop.
        """
        opp_by_id = {o.id: o for o in opportunities}
        for score in ranked_scores:
            if score.is_hard_stop_blocked:
                continue
            opp = opp_by_id.get(score.opportunity_id)
            if not opp:
                continue
            si = opp.scoring_inputs
            if si.delivery_confidence >= 4.0 and si.implementation_effort <= 3.0 and si.operational_risk <= 2.0:
                return opp

        # Fallback to top non-blocked if strict criteria not met
        for score in ranked_scores:
            if not score.is_hard_stop_blocked:
                return opp_by_id.get(score.opportunity_id)

        return None

    @classmethod
    def organize_phases(
        cls,
        initiatives: List[RoadmapInitiative],
    ) -> Dict[str, List[RoadmapInitiative]]:
        """Groups roadmap initiatives into Phase 1 (1-30), Phase 2 (31-60), and Phase 3 (61-90)."""
        phases = {
            "Phase 1: Days 1–30 (Foundations, Security & First Prototype)": [],
            "Phase 2: Days 31–60 (Core Workflow Automation & System Integration)": [],
            "Phase 3: Days 61–90 (Scaling, Advanced AI Drafting & Continuous Optimization)": [],
        }

        for init in initiatives:
            phase_name = init.phase.lower()
            if "phase 1" in phase_name or "1–30" in phase_name or "1-30" in phase_name:
                phases["Phase 1: Days 1–30 (Foundations, Security & First Prototype)"].append(init)
            elif "phase 2" in phase_name or "31–60" in phase_name or "31-60" in phase_name:
                phases["Phase 2: Days 31–60 (Core Workflow Automation & System Integration)"].append(init)
            else:
                phases["Phase 3: Days 61–90 (Scaling, Advanced AI Drafting & Continuous Optimization)"].append(init)

        return phases

    @classmethod
    def calculate_roadmap_resource_summary(
        cls, initiatives: List[RoadmapInitiative]
    ) -> Dict[str, Any]:
        """Calculates total effort weeks, costs, and prototype count across roadmap."""
        total_weeks = sum(i.estimated_effort_weeks for i in initiatives)
        total_cost = sum(i.estimated_cost_usd for i in initiatives)
        prototypes = [i for i in initiatives if i.is_first_prototype]

        return {
            "total_initiatives": len(initiatives),
            "total_effort_weeks": round(total_weeks, 1),
            "total_estimated_cost_usd": round(total_cost, 2),
            "first_prototype": prototypes[0].title if prototypes else "None designated",
        }
