"""Financial and Workload Analysis for AI & Automation Initiatives.

Calculates workload capacity, labor hours redirected, direct cash savings,
implementation ROI, payback periods, and multi-scenario projections
(Conservative, Expected, Optimistic).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from ai_audit.models import FinancialAssumptions, Opportunity


class FinancialScenario(str, Enum):
    CONSERVATIVE = "conservative"
    EXPECTED = "expected"
    OPTIMISTIC = "optimistic"


@dataclass
class FinancialAnalysisResult:
    opportunity_id: str
    opportunity_title: str
    scenario: FinancialScenario
    is_valid_data: bool
    data_gap_warning: Optional[str]

    # Baseline metrics
    role_title: str
    hourly_rate_usd: float
    annual_volume: float
    handling_time_hours: float
    baseline_annual_hours: float
    baseline_annual_cost_usd: float

    # Automation parameters applied
    automation_coverage_pct: float
    human_review_overhead_pct: float
    net_efficiency_gain_pct: float

    # Hours saved & capacity
    gross_hours_automated: float
    human_review_hours_overhead: float
    net_hours_saved_annual: float
    capacity_released_value_usd: float  # Value of freed internal hours (redeployable)
    direct_cash_savings_usd: float  # Hard-dollar cost reduction (software/contractors)
    total_gross_annual_value_usd: float  # Capacity + Direct cash

    # Costs & ROI
    implementation_cost_usd: float
    annual_recurring_cost_usd: float
    net_annual_ongoing_benefit_usd: float  # Gross value - Recurring costs
    net_first_year_benefit_usd: float  # Net annual - Implementation cost
    payback_period_months: Optional[float]
    three_year_roi_pct: Optional[float]
    summary_notes: str

    def format_summary(self) -> str:
        if not self.is_valid_data:
            return f"[{self.opportunity_id}] INSUFFICIENT DATA: {self.data_gap_warning}"
        payback_str = f"{self.payback_period_months:.1f} months" if self.payback_period_months else "N/A"
        return (
            f"[{self.opportunity_id}] {self.opportunity_title} ({self.scenario.value.title()})\n"
            f"  - Baseline Workload: {self.baseline_annual_hours:,.1f} hrs/yr (${self.baseline_annual_cost_usd:,.2f})\n"
            f"  - Net Hours Saved: {self.net_hours_saved_annual:,.1f} hrs/yr ({self.role_title})\n"
            f"  - Capacity Released Value: ${self.capacity_released_value_usd:,.2f}/yr\n"
            f"  - Direct Cash Savings: ${self.direct_cash_savings_usd:,.2f}/yr\n"
            f"  - Total Gross Annual Value: ${self.total_gross_annual_value_usd:,.2f}/yr\n"
            f"  - Net First Year Benefit: ${self.net_first_year_benefit_usd:,.2f}\n"
            f"  - Estimated Payback: {payback_str}"
        )


class FinancialCalculator:
    """Calculates financial and workload impact for opportunities."""

    @staticmethod
    def adjust_assumptions_for_scenario(
        base: FinancialAssumptions,
        scenario: FinancialScenario = FinancialScenario.EXPECTED,
    ) -> FinancialAssumptions:
        """Applies scenario multipliers to create conservative or optimistic projections."""
        if scenario == FinancialScenario.EXPECTED:
            return base

        if scenario == FinancialScenario.CONSERVATIVE:
            # Lower automation coverage, higher human review overhead, higher dev cost, lower cash savings
            coverage = max(0.20, base.automation_coverage_pct * 0.75)
            review_overhead = min(0.40, base.human_review_overhead_pct * 1.5)
            impl_cost = base.implementation_cost_usd * 1.25
            recurring = base.annual_recurring_cost_usd * 1.15
            cash_savings = base.direct_cash_savings_usd * 0.80
            return FinancialAssumptions(
                role_title=base.role_title,
                hourly_rate_usd=base.hourly_rate_usd,
                annual_volume=base.annual_volume,
                handling_time_hours=base.handling_time_hours,
                automation_coverage_pct=round(coverage, 3),
                human_review_overhead_pct=round(review_overhead, 3),
                implementation_cost_usd=round(impl_cost, 2),
                annual_recurring_cost_usd=round(recurring, 2),
                direct_cash_savings_usd=round(cash_savings, 2),
                notes=f"Conservative scenario adjusted: Coverage -25%, Review Overhead +50%, Impl Cost +25%.",
            )

        if scenario == FinancialScenario.OPTIMISTIC:
            # Higher automation coverage, streamlined review overhead, lower dev cost, higher cash savings
            coverage = min(0.95, base.automation_coverage_pct * 1.20)
            review_overhead = max(0.05, base.human_review_overhead_pct * 0.65)
            impl_cost = base.implementation_cost_usd * 0.85
            recurring = base.annual_recurring_cost_usd * 0.90
            cash_savings = base.direct_cash_savings_usd * 1.15
            return FinancialAssumptions(
                role_title=base.role_title,
                hourly_rate_usd=base.hourly_rate_usd,
                annual_volume=base.annual_volume,
                handling_time_hours=base.handling_time_hours,
                automation_coverage_pct=round(coverage, 3),
                human_review_overhead_pct=round(review_overhead, 3),
                implementation_cost_usd=round(impl_cost, 2),
                annual_recurring_cost_usd=round(recurring, 2),
                direct_cash_savings_usd=round(cash_savings, 2),
                notes=f"Optimistic scenario adjusted: Coverage +20%, Review Overhead -35%, Impl Cost -15%.",
            )

        return base

    @classmethod
    def calculate_opportunity(
        cls,
        opp: Opportunity,
        scenario: FinancialScenario = FinancialScenario.EXPECTED,
    ) -> FinancialAnalysisResult:
        """Calculates workload and financial metrics for a single opportunity."""
        raw_fa = opp.financial_inputs
        fa = cls.adjust_assumptions_for_scenario(raw_fa, scenario)

        # Missing data validation
        is_valid = True
        gap_warning = None
        if fa.annual_volume <= 0 or fa.handling_time_hours <= 0:
            is_valid = False
            gap_warning = "Missing or non-positive annual volume or handling time hours."
        elif fa.hourly_rate_usd <= 0:
            is_valid = False
            gap_warning = "Hourly rate must be positive for financial capacity calculations."

        if not is_valid:
            return FinancialAnalysisResult(
                opportunity_id=opp.id,
                opportunity_title=opp.title,
                scenario=scenario,
                is_valid_data=False,
                data_gap_warning=gap_warning,
                role_title=fa.role_title,
                hourly_rate_usd=fa.hourly_rate_usd,
                annual_volume=fa.annual_volume,
                handling_time_hours=fa.handling_time_hours,
                baseline_annual_hours=0.0,
                baseline_annual_cost_usd=0.0,
                automation_coverage_pct=fa.automation_coverage_pct,
                human_review_overhead_pct=fa.human_review_overhead_pct,
                net_efficiency_gain_pct=0.0,
                gross_hours_automated=0.0,
                human_review_hours_overhead=0.0,
                net_hours_saved_annual=0.0,
                capacity_released_value_usd=0.0,
                direct_cash_savings_usd=0.0,
                total_gross_annual_value_usd=0.0,
                implementation_cost_usd=fa.implementation_cost_usd,
                annual_recurring_cost_usd=fa.annual_recurring_cost_usd,
                net_annual_ongoing_benefit_usd=0.0,
                net_first_year_benefit_usd=0.0,
                payback_period_months=None,
                three_year_roi_pct=None,
                summary_notes="Insufficient evidence to estimate financial returns reliably.",
            )

        baseline_hours = fa.annual_volume * fa.handling_time_hours
        baseline_cost = baseline_hours * fa.hourly_rate_usd

        gross_hours_auto = baseline_hours * fa.automation_coverage_pct
        review_overhead_hours = gross_hours_auto * fa.human_review_overhead_pct
        net_hours_saved = max(0.0, gross_hours_auto - review_overhead_hours)

        net_efficiency = (net_hours_saved / baseline_hours) if baseline_hours > 0 else 0.0

        capacity_released_val = net_hours_saved * fa.hourly_rate_usd
        direct_cash = fa.direct_cash_savings_usd
        total_gross_annual = capacity_released_val + direct_cash

        net_annual_ongoing = total_gross_annual - fa.annual_recurring_cost_usd
        net_first_year = net_annual_ongoing - fa.implementation_cost_usd

        # Payback period in months
        payback_months: Optional[float] = None
        if net_annual_ongoing > 0:
            monthly_benefit = net_annual_ongoing / 12.0
            payback_months = round(fa.implementation_cost_usd / monthly_benefit, 1)

        # 3-Year ROI %
        # 3-Year gross benefits = 3 * total_gross_annual
        # 3-Year total costs = implementation_cost + 3 * recurring_cost
        three_year_gross = 3.0 * total_gross_annual
        three_year_costs = fa.implementation_cost_usd + (3.0 * fa.annual_recurring_cost_usd)
        three_year_roi: Optional[float] = None
        if three_year_costs > 0:
            net_three_year = three_year_gross - three_year_costs
            three_year_roi = round((net_three_year / three_year_costs) * 100.0, 1)

        notes = (
            f"Frees ~{net_hours_saved:,.0f} hours/yr of {fa.role_title} capacity. "
            f"Distinguishes ${capacity_released_val:,.0f}/yr capacity release from ${direct_cash:,.0f}/yr cash savings."
        )

        return FinancialAnalysisResult(
            opportunity_id=opp.id,
            opportunity_title=opp.title,
            scenario=scenario,
            is_valid_data=True,
            data_gap_warning=None,
            role_title=fa.role_title,
            hourly_rate_usd=fa.hourly_rate_usd,
            annual_volume=fa.annual_volume,
            handling_time_hours=fa.handling_time_hours,
            baseline_annual_hours=round(baseline_hours, 1),
            baseline_annual_cost_usd=round(baseline_cost, 2),
            automation_coverage_pct=fa.automation_coverage_pct,
            human_review_overhead_pct=fa.human_review_overhead_pct,
            net_efficiency_gain_pct=round(net_efficiency * 100.0, 1),
            gross_hours_automated=round(gross_hours_auto, 1),
            human_review_hours_overhead=round(review_overhead_hours, 1),
            net_hours_saved_annual=round(net_hours_saved, 1),
            capacity_released_value_usd=round(capacity_released_val, 2),
            direct_cash_savings_usd=round(direct_cash, 2),
            total_gross_annual_value_usd=round(total_gross_annual, 2),
            implementation_cost_usd=round(fa.implementation_cost_usd, 2),
            annual_recurring_cost_usd=round(fa.annual_recurring_cost_usd, 2),
            net_annual_ongoing_benefit_usd=round(net_annual_ongoing, 2),
            net_first_year_benefit_usd=round(net_first_year, 2),
            payback_period_months=payback_months,
            three_year_roi_pct=three_year_roi,
            summary_notes=notes,
        )

    @classmethod
    def calculate_portfolio_totals(
        cls,
        results: List[FinancialAnalysisResult],
    ) -> Dict[str, float]:
        """Aggregates portfolio-level financial outcomes."""
        valid_results = [r for r in results if r.is_valid_data]
        total_baseline_hours = sum(r.baseline_annual_hours for r in valid_results)
        total_baseline_cost = sum(r.baseline_annual_cost_usd for r in valid_results)
        total_net_hours_saved = sum(r.net_hours_saved_annual for r in valid_results)
        total_capacity_released = sum(r.capacity_released_value_usd for r in valid_results)
        total_direct_cash = sum(r.direct_cash_savings_usd for r in valid_results)
        total_gross_annual = sum(r.total_gross_annual_value_usd for r in valid_results)
        total_impl_cost = sum(r.implementation_cost_usd for r in valid_results)
        total_recurring_cost = sum(r.annual_recurring_cost_usd for r in valid_results)
        total_net_annual_ongoing = sum(r.net_annual_ongoing_benefit_usd for r in valid_results)
        total_net_first_year = sum(r.net_first_year_benefit_usd for r in valid_results)

        portfolio_payback: Optional[float] = None
        if total_net_annual_ongoing > 0:
            portfolio_payback = round(total_impl_cost / (total_net_annual_ongoing / 12.0), 1)

        three_year_gross = 3.0 * total_gross_annual
        three_year_costs = total_impl_cost + (3.0 * total_recurring_cost)
        three_year_roi: Optional[float] = None
        if three_year_costs > 0:
            three_year_roi = round(((three_year_gross - three_year_costs) / three_year_costs) * 100.0, 1)

        return {
            "total_baseline_hours": round(total_baseline_hours, 1),
            "total_baseline_cost_usd": round(total_baseline_cost, 2),
            "total_net_hours_saved": round(total_net_hours_saved, 1),
            "total_capacity_released_usd": round(total_capacity_released, 2),
            "total_direct_cash_savings_usd": round(total_direct_cash, 2),
            "total_gross_annual_value_usd": round(total_gross_annual, 2),
            "total_implementation_cost_usd": round(total_impl_cost, 2),
            "total_annual_recurring_cost_usd": round(total_recurring_cost, 2),
            "total_net_annual_ongoing_benefit_usd": round(total_net_annual_ongoing, 2),
            "total_net_first_year_benefit_usd": round(total_net_first_year, 2),
            "portfolio_payback_months": portfolio_payback or 0.0,
            "portfolio_3yr_roi_pct": three_year_roi or 0.0,
        }
