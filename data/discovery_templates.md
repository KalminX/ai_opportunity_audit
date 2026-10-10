# AI Opportunity Audit: Discovery & Process Inventory Toolkit
**Consultant Field Kit & Reusable Interview Question Packs**

---

## 1. Business Overview & Architecture Worksheet

| Dimension | Discovery Questions & Prompts | Client Response / Findings |
| :--- | :--- | :--- |
| **Organization & Scale** | - Company Name, Primary Industry, Target Market.<br>- Total Full-Time & Part-Time Headcount by Department.<br>- Annual Turnover / Revenue Run-Rate ($ USD).<br>- Key growth targets over the next 12–24 months. | *[Record company background and strategic context]* |
| **Core Value Proposition** | - What are your flagship client services or deliverables?<br>- What is your typical engagement model (retainer, fixed-fee project, hourly)?<br>- What is your current gross margin target? | *[Record service structure and pricing model]* |
| **Existing Technology Stack** | - CRM & Sales Pipeline tools (e.g. HubSpot, Salesforce)?<br>- Project Management & Ticketing (e.g. Asana, ClickUp, Jira)?<br>- Document Collaboration & Storage (e.g. Google Workspace, M365)?<br>- Accounting & Billing (e.g. QuickBooks, Xero)?<br>- Specialized operational tools, BI tools, and ad platforms? | *[Catalog all current software, licenses, and API availability]* |
| **Data Confidentiality & Policy** | - What customer PII, financial data, or proprietary IP is handled?<br>- Are there contractual Non-Disclosure Agreements (NDAs) or regulatory mandates (GDPR, CCPA, SOC-2)?<br>- Does leadership enforce Zero-Data-Retention policies for external AI APIs? | *[Record compliance and confidentiality boundaries]* |

---

## 2. Reusable Stakeholder Interview Guides

### A. Executive Leadership & Founders
**Goal:** Align on high-level strategic objectives, commercial bottlenecks, risk tolerance, and gross margin goals.

1. **Strategic Scaling Goals:**
   - *"What is preventing your firm from doubling its client roster or revenue over the next 18 months?"*
   - *"Which departments or service lines are currently the most margin-compressed or staffing-constrained?"*
2. **Consultant Time & High-Value Focus:**
   - *"What percentage of your senior strategists' and directors' time is spent on administrative coordination vs high-value client advisory?"*
3. **AI Vision & Governance:**
   - *"What is your executive stance on AI automation? Where would you welcome AI assistance, and where is human oversight strictly non-negotiable?"*
4. **Investment & Payback Expectations:**
   - *"What payback period or ROI benchmark does leadership require for technology modernization investments?"*

---

### B. Practice Leads & Department Heads (Client Services, Media, Operations)
**Goal:** Uncover operational handoff delays, quality variances, recurring firefighting, and departmental friction.

1. **Operational Workload & Bottlenecks:**
   - *"Walk me through a typical week. Which recurring tasks consume the largest number of team hours?"*
   - *"Where do deliverables sit waiting for input, approval, or data extraction?"*
2. **Handoffs & Error Rates:**
   - *"When a project moves between sales, account management, and specialists, where do details get lost or re-entered?"*
   - *"What is the estimated error or rework rate on client deliverables (e.g., reporting, proposals, billing)?"*
3. **Tool & Data Friction:**
   - *"Are team members frequently copy-pasting numbers from one dashboard or spreadsheet into another?"*
   - *"How easily accessible is historical company knowledge (past pitch decks, client benchmark results, SOPs)?"*

---

### C. Operational Staff, Analysts & Specialists (Frontline Execution)
**Goal:** Measure exact task handling times, repetitive cognitive toil, manual spreadsheets, and daily workarounds.

1. **Day-in-the-Life Task Inventory:**
   - *"Which tasks do you perform daily or weekly that feel tedious, repetitive, or robotic?"*
   - *"How long does it take you to complete one run of this task (in minutes or hours)?"*
   - *"How many times per week/month do you perform it?"*
2. **Data & System Friction:**
   - *"Which screens, tabs, and applications do you keep open simultaneously to complete this task?"*
   - *"What manual checks or formula verifications do you perform to avoid mistakes?"*
3. **Ideal Automation Wishlist:**
   - *"If you had a virtual assistant that could do 70% of the first draft for this task, what would you want it to hand you?"*

---

## 3. Business Process Inventory & Step Mapping Template

For every workflow identified during discovery, complete the following structured inventory:

### Process Metadata
- **Process Name:** *[e.g., Weekly Client Performance Reporting]*
- **Department / Function:** *[e.g., Paid Media]*
- **Process Owner (Role):** *[e.g., Senior Paid Media Consultant]*
- **Frequency:** *[e.g., Daily, Weekly, Monthly, Per Client Onboarding, Per Inbound Lead]*
- **Annual Run Volume:** *[e.g., 52 weeks × 28 clients = 1,456 executions/yr]*
- **Current Error / Rework Rate (%):** *[e.g., 12%]*

### Process Step Detail Table
| Step # | Step Title | Actor / Role | System / Software | Action Description | Manual? (Y/N) | Decision / Gate? | Handling Time (Mins) | Bottleneck Identified? | Evidence Level (Measured / Interview / Hypothesis) |
| :---: | :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **1** | Extract Data | Junior Analyst | Ad Platform | Download weekly CSV | Yes | No | 15 mins | No | Measured |
| **2** | Aggregate Data | Junior Analyst | Google Sheets | Paste CSVs & check CAC | Yes | No | 20 mins | Yes (Formula breaks) | Measured |
| **3** | Draft Commentary | Senior Consultant| Google Docs | Write narrative trends | Yes | No | 25 mins | Yes (Repetitive toil) | Observed Interview |
| **4** | Director Review | Account Director | Google Docs | Review & approve | Yes | Yes (Approval) | 10 mins | No | Observed Interview |
| **5** | Send to Client | Junior Analyst | Gmail / Slack | PDF export & email | Yes | No | 5 mins | No | Measured |

---

## 4. Opportunity Identification & Scoring Worksheet

For each proposed automation initiative, gather the following 5 evaluation parameters (1 to 5 scale):

1. **Business Value (1-5):** Revenue enablement, client satisfaction, turnaround speed, and hours saved.
2. **Data Readiness (1-5):** Availability of structured APIs, clean documentation, or standardized past examples.
3. **Delivery Confidence (1-5):** Technical clarity, proven off-the-shelf integration patterns, low architecture risk.
4. **Implementation Effort (1-5):** Estimated development weeks, custom code required, and change management friction.
5. **Operational Risk (1-5):** Potential impact of errors, client-facing exposure, and regulatory/privacy sensitivity.

### Hard-Stop Governance Gate
- [ ] Does this initiative transmit sensitive PII or confidential client financials to unvetted public AI models?
- [ ] Does this initiative allow an unsupervised AI agent to make irreversible financial commitments or publish external communications without human review?
- *If YES to either: Flag as **BLOCKED (Hard Stop)** until mandatory human review guardrails and Zero-Data-Retention agreements are established.*

---

## 5. Financial & Workload Sizing Formula Guide

$$\text{Baseline Annual Hours} = \text{Annual Volume} \times \text{Handling Time (Hours)}$$
$$\text{Baseline Cost} = \text{Baseline Annual Hours} \times \text{Hourly Loaded Rate (\$/hr)}$$
$$\text{Net Hours Saved} = \text{Baseline Annual Hours} \times \text{Coverage \%} \times (1 - \text{Human Review Overhead \%})$$
$$\text{Capacity Value Released} = \text{Net Hours Saved} \times \text{Hourly Loaded Rate}$$
$$\text{Total Gross Annual Value} = \text{Capacity Value Released} + \text{Direct Cash Savings}$$
$$\text{Payback Period (Months)} = \frac{\text{Implementation Cost}}{\text{Total Gross Annual Value} - \text{Annual Recurring Cost}} \times 12$$

---
*Discovery template provided by the AI Opportunity Audit and Automation Roadmap Toolkit.*
