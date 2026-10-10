# AI Opportunity Audit & Automation Roadmap Toolkit

A comprehensive, portfolio-quality, zero-external-API toolkit designed for management consultants, operations leads, and technical advisors to assess a service business's operations, identify pragmatic AI and automation opportunities, prioritize them using transparent multi-criteria scoring, evaluate privacy and operational risks, and generate professional 90-day implementation roadmaps and executive deliverables.

---

## 🌟 Key Highlights & Design Philosophy

- **100% Local & Privacy-First:** Runs entirely locally using Python standard libraries and Jinja2 templates. No AI API keys, paid SaaS subscriptions, cloud databases, or Docker containers required.
- **Pragmatic Automation Filter:** Evaluates whether AI (LLM / RAG) is genuinely required or if deterministic rule-based automation (webhooks, APIs, scripts, OCR) is superior.
- **Transparent Multi-Criteria Scoring:** Documented mathematical formula ranking opportunities on Business Value, Data Readiness, Delivery Confidence, Implementation Effort, and Operational Risk.
- **Hard-Stop Safety Framework:** Enforces non-negotiable risk stops for unacceptable privacy, legal, or unsupervised brand-safety risks. High numerical scores **never** override a hard stop.
- **Workload vs Cash Separation:** Rigorously distinguishes internal staff capacity freed (hours redirected to client-facing billable advisory) from direct hard-dollar cash savings (contractor/tool reduction).
- **Three-Scenario Financial Modeling:** Generates Conservative, Expected, and Optimistic financial projections with payback horizons and 3-year ROI.
- **Automated Mermaid Flowcharting:** Generates GitHub-compatible Mermaid diagrams directly from structured process data with red bottleneck highlighting.
- **8-Point Security & Data-Readiness Checklist:** Evaluates PII scrubbing, Zero-Data-Retention (ZDR) terms, RBAC, secrets management, and failure recovery.
- **Complete 12-Section Executive Deliverables:** One-click generation of Executive Reports, Slide Decks, One-Page Briefs, CSV/JSON Registers, and 90-Day Roadmaps.
- **Dual Interface:** Full-featured command-line interface (`ai-audit`) and a built-in interactive local web dashboard (`ai-audit serve`).

---

## 📂 Project Structure

```
ai_opportunity_audit/
├── ai_audit/
│   ├── __init__.py          # Package exports and version metadata
│   ├── cli.py               # Full-featured CLI (init, info, map, score, financial, risk, roadmap, report, serve)
│   ├── models.py            # Typed domain data models & serialization
│   ├── process_map.py       # Process mapping, bottleneck detection & Mermaid generator
│   ├── scoring.py           # Transparent MCDA prioritisation engine & hard-stop checks
│   ├── financials.py        # Workload capacity, scenario modeling & payback calculator
│   ├── security.py          # 8-point security checklist & risk register engine
│   ├── roadmap.py           # 90-day phased roadmap & first prototype selector
│   ├── reporting.py         # Markdown/CSV/JSON report rendering & export pipeline
│   ├── project.py           # Project persistence & sample case study generator
│   ├── web/
│   │   ├── __init__.py
│   │   └── server.py        # Built-in lightweight HTTP dashboard & API server
│   └── templates/           # Jinja2 templates for all deliverables
│       ├── executive_report.md.j2
│       ├── presentation_outline.md.j2
│       ├── one_page_summary.md.j2
│       ├── roadmap_90day.md.j2
│       └── risk_register.md.j2
├── data/
│   ├── sample_project.json     # Seed dataset for "Apex Growth Partners" case study
│   ├── blank_template.json     # Clean template for new client audits
│   └── discovery_templates.md  # Consultant field kit & interview question packs
├── outputs/                    # Generated deliverables for sample project
│   ├── executive_report.md
│   ├── presentation_outline.md
│   ├── one_page_summary.md
│   ├── roadmap_90day.md
│   ├── risk_register.md
│   ├── risk_register.csv
│   ├── opportunity_register.csv
│   ├── opportunity_register.json
│   └── process_maps/
│       ├── client_onboarding.mmd
│       ├── weekly_reporting.mmd
│       ├── client_enquiry_triage.mmd
│       ├── proposal_preparation.mmd
│       └── invoice_processing.mmd
├── tests/                      # Automated test suite (20 unit tests)
│   ├── test_models.py
│   ├── test_scoring.py
│   ├── test_financials.py
│   ├── test_reporting.py
│   └── test_cli.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## 🚀 Quickstart Guide

### 1. Environment Setup

```bash
# Clone or navigate to the directory
cd /path/to/ai_opportunity_audit

# Create and activate a Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install package in editable mode with dependencies
pip install -e .
```

### 2. Verify Installation & Run Automated Tests

```bash
pytest -v
```

### 3. Inspect the Included Fictional Case Study

```bash
# View company overview, tech stack, and scope
ai-audit info

# Calculate transparent opportunity scores
ai-audit score

# Run financial ROI and workload capacity analysis (Expected scenario)
ai-audit financial --scenario expected

# Inspect process map and Mermaid flowchart for weekly reporting
ai-audit map weekly_reporting

# Review security & operational risk register
ai-audit risk

# Review 90-day implementation roadmap
ai-audit roadmap

# Export all markdown reports, CSVs, and Mermaid files
ai-audit report --output-dir outputs
```

### 4. Launch the Interactive Local Web Dashboard

```bash
ai-audit serve --port 8080
```
Open **http://localhost:8080** in your browser to interactively explore live Mermaid flowcharts, adjust scoring parameters in real time, toggle hard-stop risks, switch between Conservative/Expected/Optimistic scenarios, and download deliverables!

---

## 📊 The Fictional Case Study: "Apex Growth Partners"

The toolkit includes a rich, realistic service-business case study with clearly labeled assumptions:

- **Company Profile:** 25-person boutique B2B performance marketing and growth consultancy with $4.8M annual revenue and 30+ retainer clients ($8k–$20k/mo).
- **Core Problem:** Experienced consultants spending 14+ hours per week copy-pasting ad metrics across Meta, Google Ads, and Looker Studio; 14-day client onboarding cycles; 20 hours spent reconstructing customized pitch decks; and 35+ hours/month manually matching contractor invoices.
- **Evaluated Workflows:**
  1. `weekly_reporting` (1,456 runs/yr, 75 mins manual handling per report, 12% calculation error rate)
  2. `client_onboarding` (36 new clients/yr, 480 mins manual handling, 14-day cycle time)
  3. `client_enquiry_triage` (350 inbound leads/yr, 35 mins research latency)
  4. `proposal_preparation` (60 custom pitches/yr, 20 hrs per proposal)
  5. `invoice_processing` (540 contractor invoices/yr, 45 mins manual 3-way match)

### 9 Realistic Opportunities Cataloged

| ID | Title | Technology Approach | Human Gate | Status |
| :--- | :--- | :--- | :--- | :--- |
| **OPP-01** | Automated Cross-Channel Performance Report Generator & Narrative Draft | **HYBRID** (API pull + LLM draft) | Mandatory Review | ✅ Approved (Quick Win) |
| **OPP-02** | Client Onboarding Orchestrator & Automated Asset Collection Hub | **RULE_BASED** (Webhooks + Drive/Asana) | Exception Only | ✅ Approved (⭐ 1st Prototype) |
| **OPP-03** | Smart Inbound Lead Enrichment & Slack Routing Card | **HYBRID** (Clearbit API + LLM intent) | Mandatory Review | ✅ Approved (Quick Win) |
| **OPP-04** | Proposal Knowledge Retrieval & Modular Slide Drafter | **AI_LLM** (RAG over past decks) | Mandatory Review | ✅ Approved (Strategic Bet) |
| **OPP-05** | Contractor Timesheet & Invoice Automated 3-Way Reconciliation | **HYBRID** (OCR + Asana/QuickBooks API) | Mandatory Review | ✅ Approved (Quick Win) |
| **OPP-06** | Client Meeting Intelligence & Action Item Synchronizer | **AI_LLM** (Transcript NLP to Asana) | Mandatory Review | ✅ Approved |
| **OPP-07** | Internal SOP & Playbook Co-pilot for Junior Analysts | **AI_LLM** (Internal Slack RAG) | Exception Only | ✅ Approved |
| **OPP-08** | Autonomous Direct-to-Client Live Campaign Auto-Publisher | **AI_LLM** (Unsupervised spend modify) | Autonomous | ⛔ **BLOCKED (Hard Stop)** |
| **OPP-09** | Automated Monthly Client Health & Retention Risk Predictor | **RULE_BASED** (Asana/CRM heuristics) | Exception Only | ✅ Approved (Strategic Bet) |

---

## 🧮 Transparent Prioritisation Scoring Formula

The prioritisation engine uses a multi-criteria decision analysis (MCDA) model. Every dimension is evaluated on a standard 1.0 to 5.0 scale:

### Factor Weights (Default)
- **Business Value ($w_V = 0.30$):** Revenue impact, client retention, time saved, strategic upside.
- **Data Readiness ($w_D = 0.20$):** Clean APIs, structured spreadsheets, standardized documentation.
- **Delivery Confidence ($w_C = 0.20$):** Technical feasibility, proven integration patterns, vendor stability.
- **Implementation Effort Penalty ($w_E = 0.15$):** Development weeks, custom engineering, training friction.
- **Operational Risk Penalty ($w_R = 0.15$):** Error impact, client exposure, privacy risk.

### Composite Score Math (0 to 100 Scale)
$$\text{Norm}(x) = \frac{x - 1.0}{4.0}, \quad \text{InvNorm}(x) = \frac{5.0 - x}{4.0}$$

$$\text{Composite Score} = \left( w_V \cdot \text{Norm}(V) + w_D \cdot \text{Norm}(D) + w_C \cdot \text{Norm}(C) + w_E \cdot \text{InvNorm}(E) + w_R \cdot \text{InvNorm}(R) \right) \times 100$$

### Hard-Stop Governance Override
If an opportunity involves unvetted PII leakage or unsupervised high-stakes execution (e.g., `OPP-08` modifying live client ad budgets autonomously):
- `final_score` = **`0.0`**
- `tier` = **`Blocked`**
- A high mathematical score **never** overrides a hard-stop risk gate.

---

## 💰 Financial & Workload Sizing Methodology

$$\text{Baseline Annual Hours} = \text{Annual Volume} \times \text{Handling Time (Hours)}$$
$$\text{Baseline Cost} = \text{Baseline Annual Hours} \times \text{Hourly Loaded Rate (\$/hr)}$$
$$\text{Net Hours Saved} = \text{Baseline Annual Hours} \times \text{Coverage \%} \times (1 - \text{Human Review Overhead \%})$$
$$\text{Capacity Released Value} = \text{Net Hours Saved} \times \text{Hourly Loaded Rate}$$
$$\text{Total Gross Annual Value} = \text{Capacity Released Value} + \text{Direct Cash Savings}$$
$$\text{Net Annual Ongoing Benefit} = \text{Total Gross Annual Value} - \text{Annual Recurring Costs}$$
$$\text{Net First-Year Benefit} = \text{Net Annual Ongoing Benefit} - \text{Implementation Investment}$$
$$\text{Payback Period (Months)} = \frac{\text{Implementation Investment}}{\text{Net Annual Ongoing Benefit} / 12}$$

### Multi-Scenario Assumptions Table

| Dimension | Conservative Scenario | Expected Scenario (Baseline) | Optimistic Scenario |
| :--- | :---: | :---: | :---: |
| **Automation Coverage** | Base $\times 0.75$ | Base (e.g. 70%) | Base $\times 1.20$ |
| **Human Review Overhead** | Base $\times 1.50$ | Base (e.g. 15%) | Base $\times 0.65$ |
| **Implementation Cost** | Base $\times 1.25$ (+25% overrun) | Base Cost | Base $\times 0.85$ (-15% efficiency) |
| **Direct Cash Savings** | Base $\times 0.80$ | Base Savings | Base $\times 1.10$ |

---

## 🔒 Security & Data Readiness 8-Point Checklist

1. **`SEC-01` Personal & Confidential Data:** Identification of client financials and automated regex tokenization before LLM processing.
2. **`SEC-02` Access Controls & Least Privilege:** Role-based access control (RBAC), scoped service accounts, and mandatory MFA.
3. **`SEC-03` Data Retention & Deletion:** 24-month retention windows and right-to-be-forgotten deletion workflows.
4. **`SEC-04` Vendor Terms & Model Training:** Zero-Data-Retention (ZDR) contractual enforcement prohibiting foundation model training.
5. **`SEC-05` Data Residency & Jurisdiction:** US/EU regional data center storage compliance.
6. **`SEC-06` Human Review & Escalation Guardrails:** Mandatory human approval for client communications and financial transactions.
7. **`SEC-07` Auditability, Reliability & Telemetry:** Centralized immutable execution logs and error telemetry sinks.
8. **`SEC-08` Secrets Management & Credential Isolation:** Centralized secrets vault (e.g. 1Password / AWS Secrets Manager) and 90-day rotation.

---

## 🗺️ 90-Day Phased Implementation Structure

- **Phase 1: Days 1–30 (Foundations, Security & First Prototype):**
  - Security lockdown, Zero-Data-Retention agreements, API credential vaulting.
  - Recommended First Prototype: **Client Onboarding Orchestrator** or **Automated Performance Reporter** (internal consultant review, high data availability, zero external client exposure).
  - *Gate 1:* Security signoff and prototype review by Head of Client Services.
- **Phase 2: Days 31–60 (Core Workflow Automation & System Integration):**
  - Client Onboarding Hub & Inbound Lead Triage assistant.
  - *Gate 2:* Tested on 50 live submissions with 100% routing accuracy.
- **Phase 3: Days 61–90 (Scaling, Advanced AI Drafting & Continuous Optimization):**
  - Proposal Knowledge Retrieval & Contractor Invoice 3-Way Reconciliation.
  - *Gate 3:* Executive sign-off and 3-month ROI measurement.

---

## 🛠️ How to Create a New Audit from Scratch

1. **Initialize a new audit project:**
   ```bash
   ai-audit init "Client Company Name" --file data/my_client_audit.json
   ```
2. **Conduct Discovery & Interviews:**
   - Use `data/discovery_templates.md` as your interview guide with founders, practice leads, and operations staff.
3. **Record Workflows & Opportunities:**
   - Edit `data/my_client_audit.json` or launch `ai-audit serve --file data/my_client_audit.json` to enter process steps, handling times, bottlenecks, and candidate opportunities.
4. **Calculate Scores & Model Scenarios:**
   ```bash
   ai-audit score --file data/my_client_audit.json
   ai-audit financial --file data/my_client_audit.json --scenario expected
   ```
5. **Generate All Deliverables:**
   ```bash
   ai-audit report --file data/my_client_audit.json --output-dir client_deliverables
   ```

---

## 📄 Deliverables Included

When you run `ai-audit report`, the toolkit exports:
- `executive_report.md` — Complete 12-section consulting executive report.
- `presentation_outline.md` — Slide-by-slide executive briefing presentation deck.
- `one_page_summary.md` — C-suite 1-page executive brief.
- `roadmap_90day.md` — Standalone 90-day implementation roadmap with stage gates.
- `risk_register.md` and `risk_register.csv` — Security checklist and operational risk register.
- `opportunity_register.csv` and `opportunity_register.json` — Prioritised register with scores, tiers, and financial metrics.
- `process_maps/*.mmd` — Mermaid flowchart definitions for all mapped workflows.

---
*Built with Python 3.13, Jinja2, and pytest.*
