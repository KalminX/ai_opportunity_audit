"""Transparent Prioritisation Engine for AI and Automation Opportunities.

Implements documented, multi-criteria decision analysis (MCDA) scoring
with configurable weights, hard-stop risk gates, and transparent score breakdowns.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from ai_audit.models import Opportunity, ScoringInputs, ScoringWeights


@dataclass
class ScoreBreakdown:
    opportunity_id: str
    opportunity_title: str
    business_value_score: float
    data_readiness_score: float
    delivery_confidence_score: float
    implementation_effort_score: float
    operational_risk_score: float
    raw_composite_score: float  # 0 to 100
    final_score: float  # 0 to 100 (0 if hard stop triggered)
    is_hard_stop_blocked: bool
    hard_stop_reason: Optional[str]
    tier: str  # "Quick Win", "Strategic Bet", "High-Effort Project", "Deferred / Deprioritised", "Blocked"
    rank: int = 0
    explanation: str = ""

    def summary_line(self) -> str:
        if self.is_hard_stop_blocked:
            return f"[{self.opportunity_id}] {self.opportunity_title} -> BLOCKED (Hard-Stop: {self.hard_stop_reason})"
        return f"[{self.opportunity_id}] {self.opportunity_title} -> Score: {self.final_score:.1f}/100 | Tier: {self.tier} (Rank #{self.rank})"


class PrioritisationEngine:
    """Calculates transparent prioritisation scores based on multi-factor weighted scoring.

    Formula:
      Positive contributions (higher is better, scale 1-5):
        - Business Value (normalized: (V - 1) / 4)
        - Data Readiness (normalized: (D - 1) / 4)
        - Delivery Confidence (normalized: (C - 1) / 4)
      Negative penalties (lower is better, scale 1-5):
        - Implementation Effort (inverted normalized: (5 - E) / 4)
        - Operational Risk (inverted normalized: (5 - R) / 4)

      Composite Score = (w_V * norm(V) + w_D * norm(D) + w_C * norm(C)
                        + w_E * inv_norm(E) + w_R * inv_norm(R)) * 100

      When a Hard-Stop Risk is flagged, the final score is set to 0.0 and tier is BLOCKED.
    """

    def __init__(self, weights: Optional[ScoringWeights] = None):
        self.weights = weights or ScoringWeights()
        if not self.weights.validate():
            raise ValueError(f"Scoring weights must sum to 1.0 (got {asdict(self.weights)})")

    def score_inputs(
        self,
        inputs: ScoringInputs,
        opp_id: str = "OPP-000",
        opp_title: str = "Untitled Opportunity",
    ) -> ScoreBreakdown:
        # Validate input ranges
        for name, val in [
            ("business_value", inputs.business_value),
            ("data_readiness", inputs.data_readiness),
            ("delivery_confidence", inputs.delivery_confidence),
            ("implementation_effort", inputs.implementation_effort),
            ("operational_risk", inputs.operational_risk),
        ]:
            if not (1.0 <= val <= 5.0):
                raise ValueError(f"Score input '{name}' must be between 1.0 and 5.0 (got {val})")

        # Normalized components (0.0 to 1.0)
        norm_v = (inputs.business_value - 1.0) / 4.0
        norm_d = (inputs.data_readiness - 1.0) / 4.0
        norm_c = (inputs.delivery_confidence - 1.0) / 4.0
        norm_e_inv = (5.0 - inputs.implementation_effort) / 4.0
        norm_r_inv = (5.0 - inputs.operational_risk) / 4.0

        raw_score = (
            (self.weights.business_value * norm_v)
            + (self.weights.data_readiness * norm_d)
            + (self.weights.delivery_confidence * norm_c)
            + (self.weights.implementation_effort * norm_e_inv)
            + (self.weights.operational_risk * norm_r_inv)
        ) * 100.0

        # Hard-Stop check
        is_blocked = bool(inputs.hard_stop_triggered)
        hard_stop_reason = inputs.hard_stop_reason if is_blocked else None

        if is_blocked:
            final_score = 0.0
            tier = "Blocked"
            explanation = (
                f"HARD-STOP TRIGGERED: {hard_stop_reason}. "
                f"Despite a raw mathematical score of {raw_score:.1f}/100, this opportunity cannot proceed "
                f"without fundamental risk mitigation and human governance safeguards."
            )
        else:
            final_score = round(raw_score, 1)
            # Determine Tier
            if final_score >= 70.0 and inputs.implementation_effort <= 3.0 and inputs.operational_risk <= 2.5:
                tier = "Quick Win"
                explanation = "High business value with strong data readiness, proven delivery model, and low operational friction."
            elif final_score >= 60.0:
                tier = "Strategic Bet"
                explanation = "Substantial strategic upside; may require moderate integration effort or foundational data prep."
            elif final_score >= 45.0:
                tier = "High-Effort Project"
                explanation = "Positive potential but hindered by higher implementation effort, technical complexity, or risk profile."
            else:
                tier = "Deferred / Deprioritised"
                explanation = "Lower relative return on investment or excessive delivery hurdles compared to higher-ranked alternatives."

        return ScoreBreakdown(
            opportunity_id=opp_id,
            opportunity_title=opp_title,
            business_value_score=inputs.business_value,
            data_readiness_score=inputs.data_readiness,
            delivery_confidence_score=inputs.delivery_confidence,
            implementation_effort_score=inputs.implementation_effort,
            operational_risk_score=inputs.operational_risk,
            raw_composite_score=round(raw_score, 1),
            final_score=final_score,
            is_hard_stop_blocked=is_blocked,
            hard_stop_reason=hard_stop_reason,
            tier=tier,
            explanation=explanation,
        )

    def score_opportunity(self, opp: Opportunity) -> ScoreBreakdown:
        return self.score_inputs(opp.scoring_inputs, opp.id, opp.title)

    def rank_opportunities(self, opportunities: List[Opportunity]) -> List[ScoreBreakdown]:
        """Scores and ranks opportunities.

        Rank ordering:
          1. Non-blocked items sorted descending by final score.
          2. Tie-breakers: Business value (descending), Delivery confidence (descending), Implementation effort (ascending).
          3. Blocked items placed at the bottom.
        """
        scored_items = [self.score_opportunity(opp) for opp in opportunities]

        def sort_key(item: ScoreBreakdown) -> Tuple[int, float, float, float, float]:
            if item.is_hard_stop_blocked:
                return (0, 0.0, 0.0, 0.0, 0.0)
            return (
                1,
                item.final_score,
                item.business_value_score,
                item.delivery_confidence_score,
                -item.implementation_effort_score,
            )

        ranked = sorted(scored_items, key=sort_key, reverse=True)
        for i, item in enumerate(ranked, start=1):
            item.rank = i

        return ranked
