"""Unit tests for transparent prioritisation scoring engine."""

import pytest
from ai_audit.models import Opportunity, ScoringInputs, ScoringWeights
from ai_audit.scoring import PrioritisationEngine


def test_perfect_score_calculation():
    engine = PrioritisationEngine()
    inputs = ScoringInputs(
        business_value=5.0,
        data_readiness=5.0,
        delivery_confidence=5.0,
        implementation_effort=1.0,  # Minimum effort (best)
        operational_risk=1.0,  # Minimum risk (best)
        hard_stop_triggered=False,
    )
    res = engine.score_inputs(inputs)
    assert res.final_score == 100.0
    assert res.tier == "Quick Win"
    assert not res.is_hard_stop_blocked


def test_worst_score_calculation():
    engine = PrioritisationEngine()
    inputs = ScoringInputs(
        business_value=1.0,
        data_readiness=1.0,
        delivery_confidence=1.0,
        implementation_effort=5.0,  # Maximum effort (worst)
        operational_risk=5.0,  # Maximum risk (worst)
        hard_stop_triggered=False,
    )
    res = engine.score_inputs(inputs)
    assert res.final_score == 0.0
    assert res.tier == "Deferred / Deprioritised"


def test_hard_stop_overrides_high_numerical_score():
    engine = PrioritisationEngine()
    # High value, high readiness, low effort -> mathematically would be ~90+
    inputs = ScoringInputs(
        business_value=5.0,
        data_readiness=4.8,
        delivery_confidence=4.8,
        implementation_effort=1.5,
        operational_risk=5.0,
        hard_stop_triggered=True,
        hard_stop_reason="Unsupervised autonomous ad spend modifications violate brand safety and liability rules.",
    )
    res = engine.score_inputs(inputs)

    assert res.is_hard_stop_blocked is True
    assert res.final_score == 0.0
    assert res.tier == "Blocked"
    assert "HARD-STOP TRIGGERED" in res.explanation
    assert res.raw_composite_score > 60.0  # Raw score exists but is suppressed


def test_ranking_and_tie_breaking():
    engine = PrioritisationEngine()
    opp1 = Opportunity(
        id="OPP-01",
        title="High Score Quick Win",
        description="Desc",
        workflow_id="wf1",
        problem_statement="Prob",
        proposed_solution="Sol",
        scoring_inputs=ScoringInputs(
            business_value=4.5,
            data_readiness=4.5,
            delivery_confidence=4.5,
            implementation_effort=2.0,
            operational_risk=1.5,
        ),
    )
    opp2 = Opportunity(
        id="OPP-02",
        title="Blocked High Score",
        description="Desc",
        workflow_id="wf1",
        problem_statement="Prob",
        proposed_solution="Sol",
        scoring_inputs=ScoringInputs(
            business_value=5.0,
            data_readiness=5.0,
            delivery_confidence=5.0,
            implementation_effort=1.0,
            operational_risk=5.0,
            hard_stop_triggered=True,
            hard_stop_reason="Severe compliance violation",
        ),
    )
    opp3 = Opportunity(
        id="OPP-03",
        title="Moderate Strategic Bet",
        description="Desc",
        workflow_id="wf1",
        problem_statement="Prob",
        proposed_solution="Sol",
        scoring_inputs=ScoringInputs(
            business_value=4.0,
            data_readiness=3.5,
            delivery_confidence=3.5,
            implementation_effort=3.0,
            operational_risk=2.0,
        ),
    )

    ranked = engine.rank_opportunities([opp2, opp3, opp1])
    assert ranked[0].opportunity_id == "OPP-01"
    assert ranked[1].opportunity_id == "OPP-03"
    # Blocked item must be ranked at the bottom despite highest raw inputs
    assert ranked[2].opportunity_id == "OPP-02"
    assert ranked[2].is_hard_stop_blocked is True


def test_invalid_scoring_input_bounds():
    engine = PrioritisationEngine()
    with pytest.raises(ValueError):
        engine.score_inputs(ScoringInputs(business_value=6.0))
    with pytest.raises(ValueError):
        engine.score_inputs(ScoringInputs(operational_risk=0.5))
