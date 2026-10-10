"""Unit tests for financial and workload calculator."""

import pytest
from ai_audit.financials import FinancialCalculator, FinancialScenario
from ai_audit.models import FinancialAssumptions, Opportunity, ScoringInputs


def test_basic_financial_calculation():
    opp = Opportunity(
        id="OPP-01",
        title="Weekly Report Auto",
        description="Desc",
        workflow_id="wf1",
        problem_statement="Prob",
        proposed_solution="Sol",
        financial_inputs=FinancialAssumptions(
            role_title="Senior Consultant",
            hourly_rate_usd=100.0,
            annual_volume=100.0,
            handling_time_hours=10.0,  # 1,000 baseline hours ($100k cost)
            automation_coverage_pct=0.70,  # 700 hours gross auto
            human_review_overhead_pct=0.10,  # 70 hours review overhead
            implementation_cost_usd=10000.0,
            annual_recurring_cost_usd=2000.0,
            direct_cash_savings_usd=5000.0,
        ),
    )

    res = FinancialCalculator.calculate_opportunity(opp, FinancialScenario.EXPECTED)
    assert res.is_valid_data is True
    assert res.baseline_annual_hours == 1000.0
    assert res.baseline_annual_cost_usd == 100000.0

    # Net hours saved = 700 - 70 = 630.0 hours
    assert res.gross_hours_automated == 700.0
    assert res.human_review_hours_overhead == 70.0
    assert res.net_hours_saved_annual == 630.0

    # Capacity released value = 630 hrs * $100 = $63,000
    assert res.capacity_released_value_usd == 63000.0
    assert res.direct_cash_savings_usd == 5000.0
    assert res.total_gross_annual_value_usd == 68000.0

    # Net annual ongoing = 68000 - 2000 = 66000
    assert res.net_annual_ongoing_benefit_usd == 66000.0
    # Net first year = 66000 - 10000 = 56000
    assert res.net_first_year_benefit_usd == 56000.0

    # Payback period: 10000 / (66000 / 12) = 1.818 months -> 1.8 months
    assert res.payback_period_months == 1.8


def test_scenario_multipliers():
    opp = Opportunity(
        id="OPP-01",
        title="Weekly Report Auto",
        description="Desc",
        workflow_id="wf1",
        problem_statement="Prob",
        proposed_solution="Sol",
        financial_inputs=FinancialAssumptions(
            role_title="Senior Consultant",
            hourly_rate_usd=100.0,
            annual_volume=100.0,
            handling_time_hours=10.0,
            automation_coverage_pct=0.70,
            human_review_overhead_pct=0.15,
            implementation_cost_usd=10000.0,
            annual_recurring_cost_usd=2000.0,
            direct_cash_savings_usd=5000.0,
        ),
    )

    expected = FinancialCalculator.calculate_opportunity(opp, FinancialScenario.EXPECTED)
    conservative = FinancialCalculator.calculate_opportunity(opp, FinancialScenario.CONSERVATIVE)
    optimistic = FinancialCalculator.calculate_opportunity(opp, FinancialScenario.OPTIMISTIC)

    # Conservative should save fewer hours and cost more to implement
    assert conservative.net_hours_saved_annual < expected.net_hours_saved_annual
    assert conservative.implementation_cost_usd > expected.implementation_cost_usd
    assert conservative.net_first_year_benefit_usd < expected.net_first_year_benefit_usd

    # Optimistic should save more hours and cost less to implement
    assert optimistic.net_hours_saved_annual > expected.net_hours_saved_annual
    assert optimistic.implementation_cost_usd < expected.implementation_cost_usd
    assert optimistic.net_first_year_benefit_usd > expected.net_first_year_benefit_usd


def test_missing_data_handling():
    opp = Opportunity(
        id="OPP-MISSING",
        title="Incomplete Opp",
        description="Desc",
        workflow_id="wf1",
        problem_statement="Prob",
        proposed_solution="Sol",
        financial_inputs=FinancialAssumptions(
            annual_volume=0.0,  # Missing volume
            handling_time_hours=5.0,
        ),
    )

    res = FinancialCalculator.calculate_opportunity(opp, FinancialScenario.EXPECTED)
    assert res.is_valid_data is False
    assert res.data_gap_warning is not None
    assert "Missing or non-positive" in res.data_gap_warning
    assert res.net_hours_saved_annual == 0.0
    assert res.payback_period_months is None
