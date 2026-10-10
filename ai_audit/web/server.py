"""Lightweight Built-in Local Web Dashboard and API Server.

Provides a standalone HTTP dashboard using Python standard library http.server.
Allows interactive process inspection, live score recalculation, scenario switching,
and deliverable generation without external frontend build tools or dependencies.
"""

from __future__ import annotations

import http.server
import json
import socketserver
import urllib.parse
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional

from ai_audit.financials import FinancialCalculator, FinancialScenario
from ai_audit.models import AuditProject, ScoringInputs, ScoringWeights
from ai_audit.process_map import ProcessMapper
from ai_audit.project import ProjectManager
from ai_audit.reporting import ReportGenerator
from ai_audit.roadmap import RoadmapGenerator
from ai_audit.scoring import PrioritisationEngine
from ai_audit.security import SecurityAssessmentEngine

HTML_DASHBOARD = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Opportunity Audit & Automation Roadmap</title>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <style>
    :root {
      --bg: #0f172a;
      --card-bg: #1e293b;
      --card-border: #334155;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --primary: #3b82f6;
      --primary-hover: #2563eb;
      --success: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
      --accent: #8b5cf6;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
    body { background: var(--bg); color: var(--text); min-height: 100vh; display: flex; flex-direction: column; }
    header { background: #0b1120; border-bottom: 1px solid var(--card-border); padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; }
    .brand { display: flex; align-items: center; gap: 0.75rem; }
    .brand h1 { font-size: 1.25rem; font-weight: 700; color: #fff; }
    .brand span { background: #1e3a8a; color: #60a5fa; font-size: 0.75rem; font-weight: 600; padding: 0.2rem 0.6rem; border-radius: 9999px; }
    .header-actions { display: flex; gap: 0.75rem; align-items: center; }
    .btn { background: var(--primary); color: #fff; border: none; padding: 0.5rem 1rem; border-radius: 6px; font-weight: 600; cursor: pointer; font-size: 0.875rem; transition: background 0.15s; }
    .btn:hover { background: var(--primary-hover); }
    .btn-secondary { background: #334155; color: #cbd5e1; }
    .btn-secondary:hover { background: #475569; color: #fff; }
    .btn-danger { background: var(--danger); }
    .btn-sm { padding: 0.25rem 0.5rem; font-size: 0.75rem; }
    
    /* Navigation Tabs */
    nav { background: #131c2e; border-bottom: 1px solid var(--card-border); padding: 0 2rem; display: flex; gap: 1rem; overflow-x: auto; }
    nav button { background: none; border: none; color: var(--text-muted); padding: 0.875rem 0.5rem; font-size: 0.9rem; font-weight: 600; cursor: pointer; border-bottom: 2px solid transparent; transition: all 0.15s; }
    nav button:hover { color: #fff; }
    nav button.active { color: #60a5fa; border-bottom-color: #60a5fa; }

    main { padding: 2rem; flex: 1; max-width: 1440px; margin: 0 auto; width: 100%; }
    .tab-content { display: none; }
    .tab-content.active { display: block; }

    /* Cards & Grids */
    .grid-4 { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1.25rem; margin-bottom: 1.5rem; }
    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 1.5rem; }
    .card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 8px; padding: 1.25rem; }
    .card-title { font-size: 0.875rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; }
    .card-value { font-size: 1.75rem; font-weight: 700; color: #fff; }
    .card-sub { font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem; }

    /* Tables */
    table { width: 100%; border-collapse: collapse; margin-top: 1rem; font-size: 0.875rem; }
    th { text-align: left; padding: 0.75rem 1rem; background: #172033; color: var(--text-muted); font-weight: 600; border-bottom: 1px solid var(--card-border); }
    td { padding: 0.75rem 1rem; border-bottom: 1px solid #293548; color: #e2e8f0; vertical-align: middle; }
    tr:hover td { background: #223049; }

    /* Badges */
    .badge { display: inline-block; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
    .badge-quickwin { background: #064e3b; color: #6ee7b7; border: 1px solid #059669; }
    .badge-strategic { background: #1e3a8a; color: #93c5fd; border: 1px solid #2563eb; }
    .badge-higheffort { background: #78350f; color: #fcd34d; border: 1px solid #d97706; }
    .badge-blocked { background: #7f1d1d; color: #fca5a5; border: 1px solid #dc2626; }
    .badge-pass { background: #064e3b; color: #6ee7b7; }
    .badge-attention { background: #78350f; color: #fcd34d; }
    .badge-fail { background: #7f1d1d; color: #fca5a5; }

    /* Forms & Inputs */
    .scenario-selector { display: flex; gap: 0.5rem; background: #0b1120; padding: 0.25rem; border-radius: 6px; border: 1px solid var(--card-border); }
    .scenario-btn { background: none; border: none; color: var(--text-muted); padding: 0.35rem 0.75rem; font-size: 0.8rem; font-weight: 600; border-radius: 4px; cursor: pointer; }
    .scenario-btn.active { background: var(--primary); color: #fff; }

    .mermaid-box { background: #111827; border: 1px solid var(--card-border); border-radius: 8px; padding: 1.5rem; margin-top: 1rem; overflow-x: auto; text-align: center; }
    .pre-box { background: #0b1120; padding: 1rem; border-radius: 6px; font-family: monospace; font-size: 0.85rem; overflow-x: auto; max-height: 500px; white-space: pre-wrap; color: #cbd5e1; border: 1px solid var(--card-border); }

    /* Modal */
    .modal { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 1000; align-items: center; justify-content: center; padding: 1rem; }
    .modal.open { display: flex; }
    .modal-content { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 8px; width: 100%; max-width: 600px; max-height: 90vh; overflow-y: auto; padding: 1.5rem; }
    .form-group { margin-bottom: 1rem; }
    .form-group label { display: block; font-size: 0.8rem; color: var(--text-muted); font-weight: 600; margin-bottom: 0.25rem; }
    .form-control { width: 100%; background: #0f172a; border: 1px solid var(--card-border); padding: 0.5rem; border-radius: 4px; color: #fff; font-size: 0.875rem; }
  </style>
</head>
<body>

  <header>
    <div class="brand">
      <h1>AI Opportunity Audit & Roadmap</h1>
      <span id="clientNameBadge">Loading...</span>
    </div>
    <div class="header-actions">
      <div class="scenario-selector">
        <button class="scenario-btn" onclick="setScenario('conservative')" id="scen-conservative">Conservative</button>
        <button class="scenario-btn active" onclick="setScenario('expected')" id="scen-expected">Expected</button>
        <button class="scenario-btn" onclick="setScenario('optimistic')" id="scen-optimistic">Optimistic</button>
      </div>
      <button class="btn btn-secondary btn-sm" onclick="exportDeliverables()">Export Deliverables</button>
    </div>
  </header>

  <nav>
    <button class="active" onclick="switchTab('dashboard')">Executive Dashboard</button>
    <button onclick="switchTab('opportunities')">Opportunity Register & Scorer</button>
    <button onclick="switchTab('workflows')">Process Maps & Bottlenecks</button>
    <button onclick="switchTab('financials')">Workload & Financial ROI</button>
    <button onclick="switchTab('security')">Security & Risk Register</button>
    <button onclick="switchTab('roadmap')">90-Day Roadmap</button>
    <button onclick="switchTab('reports')">Report Deliverables</button>
  </nav>

  <main>
    <!-- TAB 1: EXECUTIVE DASHBOARD -->
    <section id="tab-dashboard" class="tab-content active">
      <div class="grid-4" id="kpiGrid">
        <div class="card">
          <div class="card-title">Baseline In-Scope Hours</div>
          <div class="card-value" id="kpiBaselineHours">-</div>
          <div class="card-sub" id="kpiBaselineCost">-</div>
        </div>
        <div class="card">
          <div class="card-title">Net Capacity Freed</div>
          <div class="card-value" style="color: #60a5fa;" id="kpiNetHours">-</div>
          <div class="card-sub" id="kpiCapacityValue">-</div>
        </div>
        <div class="card">
          <div class="card-title">Direct Cash Savings</div>
          <div class="card-value" style="color: #34d399;" id="kpiDirectCash">-</div>
          <div class="card-sub">Software & contractor cost reduction</div>
        </div>
        <div class="card">
          <div class="card-title">Payback Horizon</div>
          <div class="card-value" style="color: #fcd34d;" id="kpiPayback">-</div>
          <div class="card-sub" id="kpiRoi3yr">-</div>
        </div>
      </div>

      <div class="grid-2">
        <div class="card">
          <h2 style="font-size: 1.1rem; margin-bottom: 0.75rem; color: #fff;">Client Organization Context</h2>
          <p style="font-size: 0.875rem; color: #cbd5e1; line-height: 1.5; margin-bottom: 1rem;" id="orgOverview">-</p>
          <div class="card-title" style="margin-top: 1rem;">Core Strategic Objectives</div>
          <ul style="padding-left: 1.25rem; font-size: 0.85rem; color: #94a3b8; line-height: 1.6;" id="orgObjectives"></ul>
        </div>
        <div class="card">
          <h2 style="font-size: 1.1rem; margin-bottom: 0.75rem; color: #fff;">Technology Stack in Scope</h2>
          <table id="techStackTable">
            <thead><tr><th>System</th><th>Category</th><th>Role in Operations</th></tr></thead>
            <tbody></tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- TAB 2: OPPORTUNITY REGISTER & SCORER -->
    <section id="tab-opportunities" class="tab-content">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
        <div>
          <h2 style="font-size: 1.25rem; color: #fff;">Prioritised Opportunity Register</h2>
          <p style="font-size: 0.85rem; color: var(--text-muted);">Multi-factor scoring with hard-stop risk guardrails.</p>
        </div>
      </div>
      <div class="card" style="padding: 0; overflow-x: auto;">
        <table id="opportunityTable">
          <thead>
            <tr>
              <th>Rank</th>
              <th>ID</th>
              <th>Initiative Title</th>
              <th>Type</th>
              <th>Score</th>
              <th>Tier</th>
              <th>Delivery Conf</th>
              <th>Human Gate</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </section>

    <!-- TAB 3: WORKFLOWS & PROCESS MAPS -->
    <section id="tab-workflows" class="tab-content">
      <div style="display: flex; gap: 1rem; align-items: center; margin-bottom: 1rem;">
        <h2 style="font-size: 1.25rem; color: #fff;">Process Workflow Mapping</h2>
        <select id="workflowSelect" class="form-control" style="width: auto;" onchange="renderSelectedWorkflow()"></select>
      </div>
      <div class="card" style="margin-bottom: 1.5rem;" id="workflowInfoCard"></div>
      <div class="mermaid-box" id="mermaidContainer"></div>
    </section>

    <!-- TAB 4: FINANCIALS & WORKLOAD -->
    <section id="tab-financials" class="tab-content">
      <div style="margin-bottom: 1rem;">
        <h2 style="font-size: 1.25rem; color: #fff;">Workload Capacity & Financial Impact Analysis</h2>
        <p style="font-size: 0.85rem; color: var(--text-muted);">Distinguishes released staff capacity from direct hard-dollar cash savings.</p>
      </div>
      <div class="card" style="padding: 0; overflow-x: auto;">
        <table id="financialTable">
          <thead>
            <tr>
              <th>ID</th>
              <th>Opportunity</th>
              <th>Impacted Role</th>
              <th>Baseline Hrs/Yr</th>
              <th>Net Hrs Freed</th>
              <th>Capacity Value</th>
              <th>Direct Cash</th>
              <th>Gross Value</th>
              <th>Impl Cost</th>
              <th>Payback</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </section>

    <!-- TAB 5: SECURITY & RISK REGISTER -->
    <section id="tab-security" class="tab-content">
      <div class="grid-2">
        <div class="card">
          <h2 style="font-size: 1.1rem; margin-bottom: 0.75rem; color: #fff;">8-Point Security & Data Readiness Checklist</h2>
          <table id="securityChecklistTable">
            <thead><tr><th>ID</th><th>Dimension</th><th>Status</th><th>Action</th></tr></thead>
            <tbody></tbody>
          </table>
        </div>
        <div class="card">
          <h2 style="font-size: 1.1rem; margin-bottom: 0.75rem; color: #fff;">Operational Risk Register</h2>
          <table id="riskRegisterTable">
            <thead><tr><th>Risk ID</th><th>Category</th><th>Inherent</th><th>Residual</th><th>Owner</th></tr></thead>
            <tbody></tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- TAB 6: 90-DAY ROADMAP -->
    <section id="tab-roadmap" class="tab-content">
      <div style="margin-bottom: 1rem;">
        <h2 style="font-size: 1.25rem; color: #fff;">90-Day Phased Implementation Roadmap</h2>
        <p style="font-size: 0.85rem; color: var(--text-muted);">Sequenced in 30-day agile sprints with stage-gate criteria.</p>
      </div>
      <div id="roadmapContainer"></div>
    </section>

    <!-- TAB 7: REPORT DELIVERABLES -->
    <section id="tab-reports" class="tab-content">
      <div style="display: flex; gap: 1rem; align-items: center; margin-bottom: 1rem;">
        <h2 style="font-size: 1.25rem; color: #fff;">Generated Deliverables Viewer</h2>
        <select id="reportSelect" class="form-control" style="width: auto;" onchange="loadReportDeliverable()">
          <option value="executive_report">Executive Report (12 Sections Markdown)</option>
          <option value="presentation_outline">Presentation Outline (Slide Deck)</option>
          <option value="one_page_summary">One-Page Executive Brief</option>
          <option value="roadmap_90day">90-Day Implementation Roadmap</option>
          <option value="risk_register">Security & Risk Register</option>
          <option value="opportunity_register_csv">Opportunity Register CSV</option>
        </select>
      </div>
      <div class="pre-box" id="reportPreviewBox">Loading report...</div>
    </section>
  </main>

  <!-- EDIT OPPORTUNITY MODAL -->
  <div class="modal" id="editModal">
    <div class="modal-content">
      <h2 style="font-size: 1.1rem; margin-bottom: 1rem; color: #fff;" id="modalTitle">Edit Opportunity Scores</h2>
      <input type="hidden" id="editOppId">
      <div class="form-group">
        <label>Business Value (1.0 to 5.0)</label>
        <input type="number" step="0.1" min="1" max="5" id="inputBV" class="form-control">
      </div>
      <div class="form-group">
        <label>Data Readiness (1.0 to 5.0)</label>
        <input type="number" step="0.1" min="1" max="5" id="inputDR" class="form-control">
      </div>
      <div class="form-group">
        <label>Delivery Confidence (1.0 to 5.0)</label>
        <input type="number" step="0.1" min="1" max="5" id="inputDC" class="form-control">
      </div>
      <div class="form-group">
        <label>Implementation Effort (1.0 to 5.0)</label>
        <input type="number" step="0.1" min="1" max="5" id="inputIE" class="form-control">
      </div>
      <div class="form-group">
        <label>Operational Risk (1.0 to 5.0)</label>
        <input type="number" step="0.1" min="1" max="5" id="inputOR" class="form-control">
      </div>
      <div class="form-group" style="background: #0f172a; padding: 0.75rem; border-radius: 4px; border: 1px solid var(--card-border);">
        <label style="color: #fca5a5; display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
          <input type="checkbox" id="inputHardStop"> Flag Hard-Stop Risk (Block Deployment)
        </label>
        <input type="text" id="inputHardStopReason" placeholder="Reason for hard stop risk..." class="form-control" style="margin-top: 0.5rem;">
      </div>
      <div style="display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 1.5rem;">
        <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button class="btn" onclick="saveOpportunityModal()">Save & Recalculate</button>
      </div>
    </div>
  </div>

  <script>
    mermaid.initialize({ startOnLoad: false, theme: 'dark' });

    let projectData = null;
    let currentScenario = 'expected';

    async function fetchProject() {
      const res = await fetch(`/api/project?scenario=${currentScenario}`);
      projectData = await res.json();
      renderAll();
    }

    function switchTab(tabId) {
      document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      event.target.classList.add('active');
      document.getElementById(`tab-${tabId}`).classList.add('active');
      if (tabId === 'workflows') {
        renderSelectedWorkflow();
      } else if (tabId === 'reports') {
        loadReportDeliverable();
      }
    }

    function setScenario(scen) {
      currentScenario = scen;
      document.querySelectorAll('.scenario-btn').forEach(b => b.classList.remove('active'));
      document.getElementById(`scen-${scen}`).classList.add('active');
      fetchProject();
    }

    function renderAll() {
      if (!projectData) return;
      document.getElementById('clientNameBadge').textContent = projectData.project.business_context.company_name;

      // KPI Grid
      const p = projectData.portfolio;
      document.getElementById('kpiBaselineHours').textContent = `${p.total_baseline_hours.toLocaleString()} hrs/yr`;
      document.getElementById('kpiBaselineCost').textContent = `$${Math.round(p.total_baseline_cost_usd).toLocaleString()}/yr internal cost`;
      document.getElementById('kpiNetHours').textContent = `${Math.round(p.total_net_hours_saved).toLocaleString()} hrs/yr`;
      document.getElementById('kpiCapacityValue').textContent = `$${Math.round(p.total_capacity_released_usd).toLocaleString()}/yr freed capacity`;
      document.getElementById('kpiDirectCash').textContent = `$${Math.round(p.total_direct_cash_savings_usd).toLocaleString()}/yr`;
      document.getElementById('kpiPayback').textContent = `${p.portfolio_payback_months} mos`;
      document.getElementById('kpiRoi3yr').textContent = `3-Year ROI: ${p.portfolio_3yr_roi_pct}%`;

      // Business Context
      const bc = projectData.project.business_context;
      document.getElementById('orgOverview').textContent = bc.business_overview;
      const objList = document.getElementById('orgObjectives');
      objList.innerHTML = bc.strategic_objectives.map(o => `<li>${o}</li>`).join('');

      const techTable = document.querySelector('#techStackTable tbody');
      techTable.innerHTML = bc.current_tech_stack.map(t => `
        <tr><td><strong>${t.name}</strong></td><td>${t.category}</td><td>${t.purpose}</td></tr>
      `).join('');

      // Opportunity Table
      const oppTable = document.querySelector('#opportunityTable tbody');
      oppTable.innerHTML = projectData.ranked_scores.map(s => {
        const opp = projectData.opp_map[s.opportunity_id];
        let tierBadge = `<span class="badge badge-strategic">${s.tier}</span>`;
        if (s.tier === 'Quick Win') tierBadge = `<span class="badge badge-quickwin">Quick Win</span>`;
        else if (s.tier === 'Blocked') tierBadge = `<span class="badge badge-blocked">Blocked</span>`;
        else if (s.tier === 'High-Effort Project') tierBadge = `<span class="badge badge-higheffort">High Effort</span>`;

        const statusBadge = s.is_hard_stop_blocked 
          ? `<span class="badge badge-blocked">⛔ Hard Stop</span>` 
          : `<span class="badge badge-pass">✅ Active</span>`;

        return `
          <tr>
            <td><strong>#${s.rank}</strong></td>
            <td><code>${s.opportunity_id}</code></td>
            <td><strong>${opp.title}</strong></td>
            <td>${opp.automation_type}</td>
            <td><strong>${s.final_score}</strong></td>
            <td>${tierBadge}</td>
            <td>${opp.scoring_inputs.delivery_confidence}/5</td>
            <td>${opp.human_in_the_loop}</td>
            <td>${statusBadge}</td>
            <td><button class="btn btn-secondary btn-sm" onclick="openEditModal('${s.opportunity_id}')">Edit</button></td>
          </tr>
        `;
      }).join('');

      // Workflows Select
      const wfSelect = document.getElementById('workflowSelect');
      wfSelect.innerHTML = projectData.project.workflows.map(w => `
        <option value="${w.process_id}">${w.name} (${w.department})</option>
      `).join('');

      // Financials Table
      const finTable = document.querySelector('#financialTable tbody');
      finTable.innerHTML = projectData.financial_results.map(f => `
        <tr>
          <td><code>${f.opportunity_id}</code></td>
          <td><strong>${f.opportunity_title}</strong></td>
          <td>${f.role_title}</td>
          <td>${Math.round(f.baseline_annual_hours).toLocaleString()}</td>
          <td><strong>${Math.round(f.net_hours_saved_annual).toLocaleString()}</strong></td>
          <td>$${Math.round(f.capacity_released_value_usd).toLocaleString()}</td>
          <td>$${Math.round(f.direct_cash_savings_usd).toLocaleString()}</td>
          <td><strong>$${Math.round(f.total_gross_annual_value_usd).toLocaleString()}</strong></td>
          <td>$${Math.round(f.implementation_cost_usd).toLocaleString()}</td>
          <td>${f.payback_period_months ? f.payback_period_months + 'm' : 'N/A'}</td>
        </tr>
      `).join('');

      // Security Checklist
      const secTable = document.querySelector('#securityChecklistTable tbody');
      secTable.innerHTML = projectData.project.security_checklist.map(c => `
        <tr>
          <td><code>${c.id}</code></td>
          <td><strong>${c.title}</strong></td>
          <td><span class="badge ${c.status === 'PASS' ? 'badge-pass' : 'badge-attention'}">${c.status}</span></td>
          <td>${c.remediation_action || c.notes}</td>
        </tr>
      `).join('');

      // Risk Register
      const riskTable = document.querySelector('#riskRegisterTable tbody');
      riskTable.innerHTML = projectData.project.risk_register.map(r => `
        <tr>
          <td><code>${r.risk_id}</code></td>
          <td><strong>${r.category}</strong></td>
          <td><span class="badge ${r.inherent_risk_level === 'High' || r.inherent_risk_level === 'Critical' ? 'badge-blocked' : 'badge-higheffort'}">${r.inherent_risk_level} (${r.inherent_risk_score})</span></td>
          <td><span class="badge badge-pass">${r.residual_risk_level} (${r.residual_risk_score})</span></td>
          <td>${r.owner}</td>
        </tr>
      `).join('');

      // Roadmap
      const rmContainer = document.getElementById('roadmapContainer');
      let rmHtml = '';
      for (const [phase, inits] of Object.entries(projectData.roadmap_phases)) {
        rmHtml += `<div class="card" style="margin-bottom: 1.5rem;"><h3 style="font-size: 1.1rem; color: #60a5fa; margin-bottom: 1rem;">${phase}</h3>`;
        inits.forEach(init => {
          const protoBadge = init.is_first_prototype ? '<span class="badge badge-quickwin">⭐ First Prototype</span>' : '';
          rmHtml += `
            <div style="background: #111827; border: 1px solid var(--card-border); padding: 1rem; border-radius: 6px; margin-bottom: 0.75rem;">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="font-size: 1rem; color: #fff;">${init.title} ${protoBadge}</h4>
                <span style="font-size: 0.8rem; color: var(--text-muted);">${init.estimated_effort_weeks} wks | $${init.estimated_cost_usd.toLocaleString()}</span>
              </div>
              <p style="font-size: 0.85rem; color: #cbd5e1; margin: 0.5rem 0;">${init.objective}</p>
              <div style="font-size: 0.8rem; color: var(--text-muted);"><strong>Decision Gate:</strong> ${init.go_no_go_gate}</div>
            </div>
          `;
        });
        rmHtml += '</div>';
      }
      rmContainer.innerHTML = rmHtml;
    }

    async function renderSelectedWorkflow() {
      if (!projectData) return;
      const wfId = document.getElementById('workflowSelect').value;
      const wf = projectData.project.workflows.find(w => w.process_id === wfId);
      if (!wf) return;

      document.getElementById('workflowInfoCard').innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <h3 style="font-size: 1.1rem; color: #fff;">${wf.name} (${wf.department})</h3>
          <span style="font-size: 0.85rem; color: var(--text-muted);">Owner: ${wf.owner} | Frequency: ${wf.frequency}</span>
        </div>
        <p style="font-size: 0.85rem; color: #cbd5e1; margin-top: 0.5rem;"><strong>Systems:</strong> ${wf.systems_involved.join(', ')}</p>
      `;

      const mermaidCode = projectData.mermaid_maps[wfId];
      const container = document.getElementById('mermaidContainer');
      container.removeAttribute('data-processed');
      container.innerHTML = `<pre class="mermaid">${mermaidCode}</pre>`;
      mermaid.run({ nodes: container.querySelectorAll('.mermaid') });
    }

    async function loadReportDeliverable() {
      const name = document.getElementById('reportSelect').value;
      const res = await fetch(`/api/deliverables/${name}`);
      const text = await res.text();
      document.getElementById('reportPreviewBox').textContent = text;
    }

    function openEditModal(oppId) {
      const opp = projectData.opp_map[oppId];
      document.getElementById('editOppId').value = oppId;
      document.getElementById('modalTitle').textContent = `Edit Scoring: [${oppId}] ${opp.title}`;
      document.getElementById('inputBV').value = opp.scoring_inputs.business_value;
      document.getElementById('inputDR').value = opp.scoring_inputs.data_readiness;
      document.getElementById('inputDC').value = opp.scoring_inputs.delivery_confidence;
      document.getElementById('inputIE').value = opp.scoring_inputs.implementation_effort;
      document.getElementById('inputOR').value = opp.scoring_inputs.operational_risk;
      document.getElementById('inputHardStop').checked = opp.scoring_inputs.hard_stop_triggered;
      document.getElementById('inputHardStopReason').value = opp.scoring_inputs.hard_stop_reason || '';
      document.getElementById('editModal').classList.add('open');
    }

    function closeModal() {
      document.getElementById('editModal').classList.remove('open');
    }

    async function saveOpportunityModal() {
      const oppId = document.getElementById('editOppId').value;
      const payload = {
        opportunity_id: oppId,
        business_value: parseFloat(document.getElementById('inputBV').value),
        data_readiness: parseFloat(document.getElementById('inputDR').value),
        delivery_confidence: parseFloat(document.getElementById('inputDC').value),
        implementation_effort: parseFloat(document.getElementById('inputIE').value),
        operational_risk: parseFloat(document.getElementById('inputOR').value),
        hard_stop_triggered: document.getElementById('inputHardStop').checked,
        hard_stop_reason: document.getElementById('inputHardStopReason').value,
      };

      const res = await fetch('/api/opportunity/update-score', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        closeModal();
        fetchProject();
      } else {
        alert('Failed to update opportunity score.');
      }
    }

    async function exportDeliverables() {
      const res = await fetch('/api/export', { method: 'POST' });
      if (res.ok) {
        alert('Deliverables exported successfully to outputs/ directory!');
      } else {
        alert('Error exporting deliverables.');
      }
    }

    fetchProject();
  </script>
</body>
</html>
"""


class DashboardRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler serving the dashboard UI and JSON API endpoints."""

    project_instance: Optional[AuditProject] = None
    project_file_path: Optional[str] = None

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_DASHBOARD.encode("utf-8"))
            return

        if path == "/api/project":
            scenario_name = query.get("scenario", ["expected"])[0]
            try:
                scenario = FinancialScenario(scenario_name.lower())
            except ValueError:
                scenario = FinancialScenario.EXPECTED

            rg = ReportGenerator()
            context = rg.prepare_context(self.project_instance)
            # Recompute financials for requested scenario
            fin_results = [
                FinancialCalculator.calculate_opportunity(o, scenario)
                for o in self.project_instance.opportunities
            ]
            portfolio = FinancialCalculator.calculate_portfolio_totals(fin_results)

            payload = {
                "project": self.project_instance.to_dict(),
                "ranked_scores": [asdict(s) for s in context["ranked_scores"]],
                "opp_map": {o.id: o.to_dict() for o in self.project_instance.opportunities},
                "financial_results": [asdict(f) for f in fin_results],
                "portfolio": portfolio,
                "mermaid_maps": context["mermaid_maps"],
                "security_summary": context["security_summary"],
                "risk_analysis": context["risk_analysis"],
                "roadmap_phases": {
                    k: [i.to_dict() for i in v] for k, v in context["roadmap_phases"].items()
                },
                "scenario": scenario.value,
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return

        if path.startswith("/api/deliverables/"):
            name = path.replace("/api/deliverables/", "")
            rg = ReportGenerator()
            if name == "executive_report":
                content = rg.generate_executive_report(self.project_instance)
                mime = "text/markdown; charset=utf-8"
            elif name == "presentation_outline":
                content = rg.generate_presentation_outline(self.project_instance)
                mime = "text/markdown; charset=utf-8"
            elif name == "one_page_summary":
                content = rg.generate_one_page_summary(self.project_instance)
                mime = "text/markdown; charset=utf-8"
            elif name == "roadmap_90day":
                content = rg.generate_roadmap_markdown(self.project_instance)
                mime = "text/markdown; charset=utf-8"
            elif name == "risk_register":
                content = rg.generate_risk_register_markdown(self.project_instance)
                mime = "text/markdown; charset=utf-8"
            elif name == "opportunity_register_csv":
                content = rg.export_opportunities_csv(self.project_instance)
                mime = "text/csv; charset=utf-8"
            else:
                self.send_response(404)
                self.end_headers()
                return

            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/opportunity/update-score":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len)
            data = json.loads(body.decode("utf-8"))

            opp_id = data.get("opportunity_id")
            for opp in self.project_instance.opportunities:
                if opp.id == opp_id:
                    opp.scoring_inputs.business_value = float(data.get("business_value", opp.scoring_inputs.business_value))
                    opp.scoring_inputs.data_readiness = float(data.get("data_readiness", opp.scoring_inputs.data_readiness))
                    opp.scoring_inputs.delivery_confidence = float(data.get("delivery_confidence", opp.scoring_inputs.delivery_confidence))
                    opp.scoring_inputs.implementation_effort = float(data.get("implementation_effort", opp.scoring_inputs.implementation_effort))
                    opp.scoring_inputs.operational_risk = float(data.get("operational_risk", opp.scoring_inputs.operational_risk))
                    opp.scoring_inputs.hard_stop_triggered = bool(data.get("hard_stop_triggered", False))
                    opp.scoring_inputs.hard_stop_reason = data.get("hard_stop_reason") if opp.scoring_inputs.hard_stop_triggered else None
                    break

            if self.project_file_path:
                ProjectManager.save_project(self.project_instance, self.project_file_path)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))
            return

        if path == "/api/export":
            rg = ReportGenerator()
            rg.export_all_deliverables(self.project_instance, "outputs")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "exported", "dir": "outputs"}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()


def start_server(project: AuditProject, file_path: Optional[str] = None, port: int = 8080) -> None:
    """Starts the lightweight HTTP server."""
    DashboardRequestHandler.project_instance = project
    DashboardRequestHandler.project_file_path = file_path

    class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True

    with ThreadedHTTPServer(("", port), DashboardRequestHandler) as httpd:
        print(f"🚀 AI Opportunity Audit Dashboard running at: http://localhost:{port}")
        print("Press Ctrl+C to stop server.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nDashboard server stopped.")
