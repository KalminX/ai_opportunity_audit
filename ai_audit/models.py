"""Domain data models for AI Opportunity Audit & Automation Roadmap Toolkit.

These data models represent service business context, discovery findings,
process maps, automation opportunities, scoring criteria, financial estimates,
security checklists, risk registers, and implementation roadmaps.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class EvidenceLevel(str, Enum):
    MEASURED = "MEASURED"  # Directly verified from system logs / analytics / time tracking
    OBSERVED_INTERVIEW = "OBSERVED_INTERVIEW"  # Stated during stakeholder interviews
    HYPOTHESIS_NEEDS_VALIDATION = "HYPOTHESIS_NEEDS_VALIDATION"  # Assumption requiring validation


class AutomationType(str, Enum):
    RULE_BASED = "RULE_BASED"  # Deterministic automation (Zapier, Make, scripts, webhooks)
    AI_LLM = "AI_LLM"  # Generative AI / LLM / NLP reasoning
    HYBRID = "HYBRID"  # Deterministic pipeline with AI step for unstructured data/drafting
    PROCESS_IMPROVEMENT_NO_TECH = "PROCESS_IMPROVEMENT_NO_TECH"  # Operational streamlining without tech


class HumanInTheLoop(str, Enum):
    MANDATORY_REVIEW = "MANDATORY_REVIEW"  # Human must approve before execution/dispatch
    EXCEPTION_ONLY = "EXCEPTION_ONLY"  # Auto-executed unless confidence score is below threshold
    PERIODIC_AUDIT = "PERIODIC_AUDIT"  # Background execution with weekly/monthly sampling
    AUTONOMOUS = "AUTONOMOUS"  # Fully automated without human intervention


class ChecklistStatus(str, Enum):
    PASS = "PASS"
    NEEDS_ATTENTION = "NEEDS_ATTENTION"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


@dataclass
class ProcessStep:
    step_id: str
    order: int
    title: str
    actor: str
    system: str
    description: str
    is_manual: bool = True
    is_decision: bool = False
    is_approval: bool = False
    handoff_to: Optional[str] = None
    next_step_ids: List[str] = field(default_factory=list)
    handling_time_minutes: float = 0.0
    bottleneck_identified: bool = False
    bottleneck_notes: str = ""
    evidence_level: str = EvidenceLevel.OBSERVED_INTERVIEW.value

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProcessStep:
        return cls(**data)


@dataclass
class ProcessWorkflow:
    process_id: str
    name: str
    owner: str
    department: str
    frequency: str  # e.g., "Weekly", "Per Client", "Daily", "Monthly"
    annual_frequency_count: float
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    systems_involved: List[str] = field(default_factory=list)
    pain_points: List[str] = field(default_factory=list)
    current_error_rate_pct: float = 0.0
    steps: List[ProcessStep] = field(default_factory=list)

    def total_manual_handling_time_minutes(self) -> float:
        return sum(s.handling_time_minutes for s in self.steps if s.is_manual)

    def total_annual_manual_hours(self) -> float:
        return (self.total_manual_handling_time_minutes() * self.annual_frequency_count) / 60.0

    def bottleneck_steps(self) -> List[ProcessStep]:
        return [s for s in self.steps if s.bottleneck_identified]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProcessWorkflow:
        steps_data = data.pop("steps", [])
        steps = [ProcessStep.from_dict(s) for s in steps_data]
        return cls(steps=steps, **data)


@dataclass
class FinancialAssumptions:
    role_title: str = "Consultant / Specialist"
    hourly_rate_usd: float = 65.0  # Fully loaded internal cost per hour
    annual_volume: float = 52.0  # Units or executions per year
    handling_time_hours: float = 10.0  # Hours per unit currently spent
    automation_coverage_pct: float = 0.70  # Expected share of task addressable by automation (0.0 - 1.0)
    human_review_overhead_pct: float = 0.15  # Human review / supervision allowance as fraction of automated work
    implementation_cost_usd: float = 6000.0  # Upfront dev, setup & integration cost
    annual_recurring_cost_usd: float = 1200.0  # Subscriptions, API tokens, hosting, maintenance
    direct_cash_savings_usd: float = 0.0  # Direct software/contractor cost elimination
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FinancialAssumptions:
        return cls(**data)


@dataclass
class ScoringInputs:
    business_value: float = 3.0  # 1 (Low) to 5 (Transformative)
    data_readiness: float = 3.0  # 1 (Scattered/Unstructured) to 5 (Clean APIs/Structured docs)
    delivery_confidence: float = 3.0  # 1 (High technical uncertainty) to 5 (Proven off-the-shelf/straightforward)
    implementation_effort: float = 3.0  # 1 (Very Low/Days) to 5 (High/Months)
    operational_risk: float = 2.0  # 1 (Negligible/Internal) to 5 (Severe regulatory/client exposure)
    hard_stop_triggered: bool = False
    hard_stop_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ScoringInputs:
        return cls(**data)


@dataclass
class ScoringWeights:
    business_value: float = 0.30
    data_readiness: float = 0.20
    delivery_confidence: float = 0.20
    implementation_effort: float = 0.15
    operational_risk: float = 0.15

    def validate(self) -> bool:
        total = (
            self.business_value
            + self.data_readiness
            + self.delivery_confidence
            + self.implementation_effort
            + self.operational_risk
        )
        return abs(total - 1.0) < 1e-4

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ScoringWeights:
        return cls(**data)


@dataclass
class Opportunity:
    id: str
    title: str
    description: str
    workflow_id: str
    problem_statement: str
    proposed_solution: str
    automation_type: str = AutomationType.HYBRID.value
    why_ai_or_why_not: str = ""
    human_in_the_loop: str = HumanInTheLoop.MANDATORY_REVIEW.value
    responsible_owner: str = "Operations Lead"
    data_readiness_notes: str = ""
    dependencies: List[str] = field(default_factory=list)
    required_integrations: List[str] = field(default_factory=list)
    evidence_level: str = EvidenceLevel.OBSERVED_INTERVIEW.value
    assumptions: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    scoring_inputs: ScoringInputs = field(default_factory=ScoringInputs)
    financial_inputs: FinancialAssumptions = field(default_factory=FinancialAssumptions)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Opportunity:
        scoring_data = data.pop("scoring_inputs", {})
        financial_data = data.pop("financial_inputs", {})
        scoring = ScoringInputs.from_dict(scoring_data) if scoring_data else ScoringInputs()
        financial = FinancialAssumptions.from_dict(financial_data) if financial_data else FinancialAssumptions()
        return cls(scoring_inputs=scoring, financial_inputs=financial, **data)


@dataclass
class SecurityChecklistItem:
    id: str
    category: str
    title: str
    requirement: str
    status: str = ChecklistStatus.NEEDS_ATTENTION.value
    notes: str = ""
    evidence_level: str = EvidenceLevel.OBSERVED_INTERVIEW.value
    remediation_action: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SecurityChecklistItem:
        return cls(**data)


@dataclass
class RiskRegisterItem:
    risk_id: str
    category: str
    description: str
    likelihood: int  # 1 to 5
    severity: int  # 1 to 5
    mitigation_strategy: str
    residual_likelihood: int  # 1 to 5
    residual_severity: int  # 1 to 5
    owner: str = "Lead Consultant / CTO"

    @property
    def inherent_risk_score(self) -> int:
        return self.likelihood * self.severity

    @property
    def inherent_risk_level(self) -> str:
        score = self.inherent_risk_score
        if score >= 15:
            return RiskLevel.CRITICAL.value
        elif score >= 10:
            return RiskLevel.HIGH.value
        elif score >= 5:
            return RiskLevel.MEDIUM.value
        return RiskLevel.LOW.value

    @property
    def residual_risk_score(self) -> int:
        return self.residual_likelihood * self.residual_severity

    @property
    def residual_risk_level(self) -> str:
        score = self.residual_risk_score
        if score >= 15:
            return RiskLevel.CRITICAL.value
        elif score >= 10:
            return RiskLevel.HIGH.value
        elif score >= 5:
            return RiskLevel.MEDIUM.value
        return RiskLevel.LOW.value

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["inherent_risk_score"] = self.inherent_risk_score
        d["inherent_risk_level"] = self.inherent_risk_level
        d["residual_risk_score"] = self.residual_risk_score
        d["residual_risk_level"] = self.residual_risk_level
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RiskRegisterItem:
        # Strip computed properties if present
        data.pop("inherent_risk_score", None)
        data.pop("inherent_risk_level", None)
        data.pop("residual_risk_score", None)
        data.pop("residual_risk_level", None)
        return cls(**data)


@dataclass
class RoadmapInitiative:
    phase: str  # "Phase 1: Days 1-30", "Phase 2: Days 31-60", "Phase 3: Days 61-90"
    opportunity_id: str
    title: str
    objective: str
    business_justification: str
    deliverables: List[str]
    responsible_role: str
    dependencies: List[str]
    estimated_effort_weeks: float
    estimated_cost_usd: float
    risks_and_mitigations: List[Dict[str, str]]
    success_metrics: List[str]
    baseline_requirements: List[str]
    acceptance_criteria: List[str]
    go_no_go_gate: str
    is_first_prototype: bool = False
    prototype_rationale: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RoadmapInitiative:
        return cls(**data)


@dataclass
class BusinessContext:
    company_name: str
    industry: str
    size_employees: int
    annual_revenue_usd: float
    business_overview: str
    strategic_objectives: List[str] = field(default_factory=list)
    team_structure: Dict[str, Any] = field(default_factory=dict)
    current_tech_stack: List[Dict[str, str]] = field(default_factory=list)
    confidentiality_requirements: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BusinessContext:
        return cls(**data)


@dataclass
class InterviewFinding:
    interviewee_role: str
    interviewee_name: str
    department: str
    key_quotes: List[str] = field(default_factory=list)
    reported_pain_points: List[str] = field(default_factory=list)
    time_sinks_identified: List[str] = field(default_factory=list)
    sentiment_towards_ai: str = "Cautiously Optimistic"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> InterviewFinding:
        return cls(**data)


@dataclass
class AuditProject:
    project_id: str
    project_name: str
    audit_date: str
    consultant_name: str
    client_contact: str
    business_context: BusinessContext
    interviews: List[InterviewFinding] = field(default_factory=list)
    workflows: List[ProcessWorkflow] = field(default_factory=list)
    opportunities: List[Opportunity] = field(default_factory=list)
    security_checklist: List[SecurityChecklistItem] = field(default_factory=list)
    risk_register: List[RiskRegisterItem] = field(default_factory=list)
    roadmap: List[RoadmapInitiative] = field(default_factory=list)
    scoring_weights: ScoringWeights = field(default_factory=ScoringWeights)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "audit_date": self.audit_date,
            "consultant_name": self.consultant_name,
            "client_contact": self.client_contact,
            "business_context": self.business_context.to_dict(),
            "interviews": [i.to_dict() for i in self.interviews],
            "workflows": [w.to_dict() for w in self.workflows],
            "opportunities": [o.to_dict() for o in self.opportunities],
            "security_checklist": [s.to_dict() for s in self.security_checklist],
            "risk_register": [r.to_dict() for r in self.risk_register],
            "roadmap": [rm.to_dict() for rm in self.roadmap],
            "scoring_weights": self.scoring_weights.to_dict(),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AuditProject:
        data = dict(data)
        bc = BusinessContext.from_dict(data.pop("business_context", {}))
        interviews = [InterviewFinding.from_dict(i) for i in data.pop("interviews", [])]
        workflows = [ProcessWorkflow.from_dict(w) for w in data.pop("workflows", [])]
        opportunities = [Opportunity.from_dict(o) for o in data.pop("opportunities", [])]
        sec_checklist = [SecurityChecklistItem.from_dict(s) for s in data.pop("security_checklist", [])]
        risk_reg = [RiskRegisterItem.from_dict(r) for r in data.pop("risk_register", [])]
        roadmap = [RoadmapInitiative.from_dict(rm) for rm in data.pop("roadmap", [])]
        weights_data = data.pop("scoring_weights", {})
        scoring_weights = ScoringWeights.from_dict(weights_data) if weights_data else ScoringWeights()

        return cls(
            business_context=bc,
            interviews=interviews,
            workflows=workflows,
            opportunities=opportunities,
            security_checklist=sec_checklist,
            risk_register=risk_reg,
            roadmap=roadmap,
            scoring_weights=scoring_weights,
            **data,
        )

    @classmethod
    def from_json(cls, json_str: str) -> AuditProject:
        return cls.from_dict(json.loads(json_str))
