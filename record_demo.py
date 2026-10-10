"""Automated Screen Recorder & Demo Generator for AI Opportunity Audit Toolkit.

Records a professional, broadcast-quality demonstration of the web application
at 1280x720 (720p) @ 30 FPS, with visible mouse cursor, natural movements,
clicks, typing, live calculations, and exports a compressed H.264 MP4.
"""

import math
import os
import shutil
import socketserver
import subprocess
import threading
import time
from pathlib import Path

from ai_audit.project import ProjectManager
from ai_audit.web.server import DashboardRequestHandler
from playwright.sync_api import Page, sync_playwright

CURSOR_SCRIPT = """
(() => {
  // Create cursor element
  const cursor = document.createElement('div');
  cursor.id = 'demo-mouse-cursor';
  cursor.innerHTML = `
    <svg width="28" height="28" viewBox="0 0 28 28" fill="none" style="filter: drop-shadow(0 2px 4px rgba(0,0,0,0.6));">
      <path d="M4 4L11.5 22L15 14.5L22.5 11L4 4Z" fill="#3b82f6" stroke="#ffffff" stroke-width="2" stroke-linejoin="round"/>
      <circle cx="4" cy="4" r="2" fill="#ffffff" />
    </svg>
  `;
  cursor.style.position = 'fixed';
  cursor.style.top = '0px';
  cursor.style.left = '0px';
  cursor.style.width = '28px';
  cursor.style.height = '28px';
  cursor.style.pointerEvents = 'none';
  cursor.style.zIndex = '999999';
  cursor.style.transform = 'translate(-4px, -4px)';
  cursor.style.transition = 'opacity 0.2s ease';
  document.body.appendChild(cursor);

  // Click ripple container
  const rippleContainer = document.createElement('div');
  rippleContainer.id = 'demo-click-ripples';
  rippleContainer.style.position = 'fixed';
  rippleContainer.style.top = '0';
  rippleContainer.style.left = '0';
  rippleContainer.style.width = '100vw';
  rippleContainer.style.height = '100vh';
  rippleContainer.style.pointerEvents = 'none';
  rippleContainer.style.zIndex = '999998';
  document.body.appendChild(rippleContainer);

  window.__updateCursor = (x, y) => {
    cursor.style.left = `${x}px`;
    cursor.style.top = `${y}px`;
  };

  window.__showClickRipple = (x, y) => {
    const ripple = document.createElement('div');
    ripple.style.position = 'absolute';
    ripple.style.left = `${x}px`;
    ripple.style.top = `${y}px`;
    ripple.style.width = '30px';
    ripple.style.height = '30px';
    ripple.style.borderRadius = '50%';
    ripple.style.border = '3px solid #60a5fa';
    ripple.style.background = 'rgba(96, 165, 250, 0.35)';
    ripple.style.transform = 'translate(-50%, -50%) scale(0.3)';
    ripple.style.opacity = '1';
    ripple.style.transition = 'all 0.45s cubic-bezier(0.1, 0.8, 0.3, 1)';
    rippleContainer.appendChild(ripple);

    requestAnimationFrame(() => {
      ripple.style.transform = 'translate(-50%, -50%) scale(1.6)';
      ripple.style.opacity = '0';
    });

    setTimeout(() => {
      ripple.remove();
    }, 500);
  };
})();
"""


class DemoRecorder:
    def __init__(self, page: Page):
        self.page = page
        self.cur_x = 100
        self.cur_y = 100

    def init_cursor(self):
        self.page.evaluate(CURSOR_SCRIPT)
        self.set_cursor(self.cur_x, self.cur_y)

    def set_cursor(self, x: float, y: float):
        self.cur_x = x
        self.cur_y = y
        self.page.evaluate(f"window.__updateCursor({x}, {y})")

    def move_to(self, target_x: float, target_y: float, duration_ms: int = 400, steps: int = 20):
        start_x = self.cur_x
        start_y = self.cur_y
        dt = duration_ms / steps / 1000.0

        # Curved Bézier control point for natural human-like curve
        mid_x = (start_x + target_x) / 2.0 + (target_y - start_y) * 0.08
        mid_y = (start_y + target_y) / 2.0 + (target_x - start_x) * -0.08

        for i in range(1, steps + 1):
            t = i / float(steps)
            # Cubic ease out
            ease_t = 1 - math.pow(1 - t, 3)

            # Quadratic Bezier formula
            x = (1 - ease_t) * (1 - ease_t) * start_x + 2 * (1 - ease_t) * ease_t * mid_x + ease_t * ease_t * target_x
            y = (1 - ease_t) * (1 - ease_t) * start_y + 2 * (1 - ease_t) * ease_t * mid_y + ease_t * ease_t * target_y

            self.set_cursor(x, y)
            self.page.mouse.move(x, y)
            time.sleep(dt)

        self.set_cursor(target_x, target_y)
        self.page.mouse.move(target_x, target_y)

    def move_to_selector(self, selector: str, offset_x: float = 0, offset_y: float = 0, duration_ms: int = 450):
        box = self.page.locator(selector).first.bounding_box()
        if not box:
            return
        target_x = box["x"] + box["width"] / 2.0 + offset_x
        target_y = box["y"] + box["height"] / 2.0 + offset_y
        self.move_to(target_x, target_y, duration_ms)

    def click_selector(self, selector: str, offset_x: float = 0, offset_y: float = 0):
        self.move_to_selector(selector, offset_x, offset_y)
        time.sleep(0.1)
        self.page.evaluate(f"window.__showClickRipple({self.cur_x}, {self.cur_y})")
        self.page.click(selector)
        time.sleep(0.2)

    def click_current(self):
        self.page.evaluate(f"window.__showClickRipple({self.cur_x}, {self.cur_y})")
        self.page.mouse.click(self.cur_x, self.cur_y)
        time.sleep(0.2)

    def type_text(self, selector: str, text: str, delay_ms: int = 50):
        self.click_selector(selector)
        self.page.fill(selector, "")
        for char in text:
            self.page.type(selector, char, delay=delay_ms)
            time.sleep(delay_ms / 1000.0)
        time.sleep(0.15)


def run_recording():
    temp_dir = Path("temp_video")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    # 1. Start test dashboard server
    sample = ProjectManager.create_sample_project()
    DashboardRequestHandler.project_instance = sample
    DashboardRequestHandler.project_file_path = "data/sample_project.json"

    port = 8990
    httpd = socketserver.TCPServer(("", port), DashboardRequestHandler)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(1)

    print("🎬 Starting Playwright browser recording (1280x720 @ 30FPS)...")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-gpu",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--window-size=1280,720",
            ],
        )

        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=str(temp_dir),
            record_video_size={"width": 1280, "height": 720},
        )

        page = context.new_page()
        rec = DemoRecorder(page)

        # Navigate to Dashboard
        page.goto(f"http://localhost:{port}")
        page.wait_for_selector("#kpiBaselineHours")
        rec.init_cursor()
        time.sleep(1.0)

        # =========================================================================
        # SCENE 1: Executive Dashboard & Scenario Toggling (0:00 - 0:15)
        # =========================================================================
        print("▶️ Recording Scene 1: Executive Dashboard & Scenario Toggling...")
        rec.move_to(640, 360, duration_ms=400)
        time.sleep(0.5)

        # Hover over KPI Cards
        rec.move_to_selector("#kpiBaselineHours", duration_ms=400)
        time.sleep(0.8)
        rec.move_to_selector("#kpiNetHours", duration_ms=400)
        time.sleep(0.8)
        rec.move_to_selector("#kpiDirectCash", duration_ms=400)
        time.sleep(0.8)
        rec.move_to_selector("#kpiPayback", duration_ms=400)
        time.sleep(0.8)

        # Hover over Tech Stack & Objectives
        rec.move_to_selector("#orgObjectives", duration_ms=450)
        time.sleep(0.8)
        rec.move_to_selector("#techStackTable", duration_ms=450)
        time.sleep(0.8)

        # Toggle Scenario Switcher in Header (Conservative -> Optimistic -> Expected)
        rec.click_selector("#scen-conservative")
        time.sleep(1.2)
        rec.click_selector("#scen-optimistic")
        time.sleep(1.2)
        rec.click_selector("#scen-expected")
        time.sleep(1.2)

        # =========================================================================
        # SCENE 2: Opportunity Register & Live Scorer (0:15 - 0:35)
        # =========================================================================
        print("▶️ Recording Scene 2: Opportunity Register & Scorer...")
        rec.click_selector('nav button:has-text("Opportunity Register")')
        page.wait_for_selector("#opportunityTable tbody tr")
        time.sleep(1.0)

        # Hover over ranked items & tiers
        rec.move_to_selector("#opportunityTable tbody tr:nth-child(1)", duration_ms=400)
        time.sleep(0.8)
        rec.move_to_selector("#opportunityTable tbody tr:nth-child(2)", duration_ms=400)
        time.sleep(0.8)
        rec.move_to_selector("#opportunityTable tbody tr:nth-child(4)", duration_ms=400)
        time.sleep(0.8)

        # Hover over hard-stop blocked initiative (OPP-08)
        rec.move_to_selector("#opportunityTable tbody tr:has-text('OPP-08')", duration_ms=450)
        time.sleep(1.2)

        # Open Edit Modal on OPP-01
        rec.click_selector("#opportunityTable tbody tr:has-text('OPP-01') button:has-text('Edit')")
        page.wait_for_selector("#editModal.open")
        time.sleep(0.8)

        # Edit Business Value and Delivery Confidence in Modal
        rec.type_text("#inputBV", "5.0")
        time.sleep(0.4)
        rec.type_text("#inputDC", "4.8")
        time.sleep(0.4)

        # Save and recalculate
        rec.click_selector("#editModal button:has-text('Save & Recalculate')")
        time.sleep(1.5)

        # =========================================================================
        # SCENE 3: Process Maps & Bottleneck Diagnostics (0:35 - 0:52)
        # =========================================================================
        print("▶️ Recording Scene 3: Process Maps & Bottlenecks...")
        rec.click_selector('nav button:has-text("Process Maps")')
        page.wait_for_selector("#workflowSelect")
        time.sleep(1.5)

        # Inspect weekly reporting Mermaid diagram & bottlenecks
        rec.move_to(640, 420, duration_ms=500)
        time.sleep(1.5)

        # Change dropdown to Client Onboarding
        rec.click_selector("#workflowSelect")
        page.select_option("#workflowSelect", "client_onboarding")
        page.evaluate("renderSelectedWorkflow()")
        time.sleep(2.0)
        rec.move_to(640, 440, duration_ms=450)
        time.sleep(1.5)

        # Change dropdown to Invoice Processing
        rec.click_selector("#workflowSelect")
        page.select_option("#workflowSelect", "invoice_processing")
        page.evaluate("renderSelectedWorkflow()")
        time.sleep(2.0)
        rec.move_to(640, 400, duration_ms=450)
        time.sleep(1.5)

        # =========================================================================
        # SCENE 4: Workload & Financial ROI Analysis (0:52 - 1:06)
        # =========================================================================
        print("▶️ Recording Scene 4: Financial ROI & Workload Capacity...")
        rec.click_selector('nav button:has-text("Workload & Financial ROI")')
        page.wait_for_selector("#financialTable tbody tr")
        time.sleep(1.0)

        rec.move_to_selector("#financialTable tbody tr:nth-child(1)", duration_ms=400)
        time.sleep(0.8)
        rec.move_to_selector("#financialTable tbody tr:nth-child(2)", duration_ms=400)
        time.sleep(0.8)
        rec.move_to_selector("#financialTable tbody tr:nth-child(5)", duration_ms=400)
        time.sleep(0.8)

        # Toggle conservative vs optimistic to show table updates
        rec.click_selector("#scen-conservative")
        time.sleep(1.2)
        rec.click_selector("#scen-expected")
        time.sleep(1.0)

        # =========================================================================
        # SCENE 5: Security & Risk Register (1:06 - 1:18)
        # =========================================================================
        print("▶️ Recording Scene 5: Security & Risk Register...")
        rec.click_selector('nav button:has-text("Security & Risk Register")')
        page.wait_for_selector("#securityChecklistTable tbody tr")
        time.sleep(1.0)

        # Inspect 8-point checklist
        rec.move_to_selector("#securityChecklistTable tbody tr:nth-child(1)", duration_ms=400)
        time.sleep(0.8)
        rec.move_to_selector("#securityChecklistTable tbody tr:nth-child(4)", duration_ms=400)
        time.sleep(0.8)

        # Inspect Risk Register
        rec.move_to_selector("#riskRegisterTable tbody tr:nth-child(1)", duration_ms=400)
        time.sleep(0.8)
        rec.move_to_selector("#riskRegisterTable tbody tr:nth-child(2)", duration_ms=400)
        time.sleep(0.8)

        # =========================================================================
        # SCENE 6: 90-Day Implementation Roadmap (1:18 - 1:30)
        # =========================================================================
        print("▶️ Recording Scene 6: 90-Day Implementation Roadmap...")
        rec.click_selector('nav button:has-text("90-Day Roadmap")')
        page.wait_for_selector("#roadmapContainer .card")
        time.sleep(1.0)

        # Hover over Phase 1, First Prototype, Phase 2, Phase 3
        rec.move_to_selector("#roadmapContainer .card:nth-child(1)", duration_ms=450)
        time.sleep(1.2)
        rec.move_to_selector("#roadmapContainer .card:nth-child(2)", duration_ms=450)
        time.sleep(1.0)
        rec.move_to_selector("#roadmapContainer .card:nth-child(3)", duration_ms=450)
        time.sleep(1.0)

        # =========================================================================
        # SCENE 7: Report Deliverables & Export Action (1:30 - 1:44)
        # =========================================================================
        print("▶️ Recording Scene 7: Report Deliverables & Export...")
        rec.click_selector('nav button:has-text("Report Deliverables")')
        page.wait_for_selector("#reportPreviewBox")
        time.sleep(1.2)

        # Switch to Presentation Outline
        page.select_option("#reportSelect", "presentation_outline")
        page.evaluate("loadReportDeliverable()")
        time.sleep(1.5)
        rec.move_to_selector("#reportPreviewBox", duration_ms=400)
        time.sleep(1.0)

        # Switch to One-Page Summary
        page.select_option("#reportSelect", "one_page_summary")
        page.evaluate("loadReportDeliverable()")
        time.sleep(1.5)
        rec.move_to_selector("#reportPreviewBox", duration_ms=400)
        time.sleep(1.0)

        # Click Export Deliverables in Header
        rec.click_selector("button:has-text('Export Deliverables')")
        time.sleep(2.0)

        # Return to Dashboard for final view
        rec.click_selector('nav button:has-text("Executive Dashboard")')
        time.sleep(1.5)
        rec.move_to(640, 360, duration_ms=400)
        time.sleep(1.0)

        # Close browser to finalize video file
        page.close()
        context.close()
        browser.close()

    httpd.shutdown()
    print("✅ Raw browser recording complete.")

    # 2. Find generated video file and convert with FFmpeg to H.264 MP4 (1280x720, 30fps)
    video_files = list(temp_dir.glob("*.webm"))
    if not video_files:
        raise RuntimeError("No raw video file found in temp_video directory.")

    raw_video = video_files[0]
    final_output = Path("ai_opportunity_audit_demo_720p.mp4")

    print(f"🎬 Transcoding raw video '{raw_video}' to '{final_output}' via FFmpeg...")
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-i", str(raw_video),
        "-vf", "scale=1280:720,fps=30",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        "-crf", "22",
        "-movflags", "+faststart",
        str(final_output),
    ]

    subprocess.run(ffmpeg_cmd, check=True)

    # Clean up temp webm
    shutil.rmtree(temp_dir)
    print(f"🎉 Final demonstration video saved successfully at: {final_output.resolve()}")

    # 3. Probe final video metadata
    probe_cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration,size:stream=width,height,r_frame_rate,codec_name",
        "-of", "json",
        str(final_output),
    ]
    res = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
    print("📊 Video Metadata:\n", res.stdout)


if __name__ == "__main__":
    run_recording()
