"""Standalone HTTP Web Server for Teacher Portal and Central Platform API.

Comprehensive Teacher Command Center & Cohort Learning Analytics Engine.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from central_platform.db import PlatformDatabase
from central_platform.models.schema import Organization, User, UserRole
from central_platform.sync.manager import SyncEvent, SyncManager
from central_platform.teacher.copilot import CopilotCitation, CopilotResponse, TeacherCopilot
from central_platform.teacher.instruction import TeacherInstruction, TeacherInstructionEngine
from central_platform.teacher.intervention import (
    AlertSeverity,
    AlertStatus,
    TeacherAlert,
    TeacherInterventionEngine,
)
from central_platform.teacher.portal import TeacherPortalService

# Persistent or configurable database path
DB_PATH = os.environ.get("GAYATRI_DB_PATH", ":memory:")
db = PlatformDatabase(DB_PATH)

# Seed default organization and demo roles
org = Organization(id="org-dsa", name="Delhi Science Academy", slug="dsa")
db.create_organization(org)

teacher_user = User(
    id="tchr-101",
    email="teacher@dsa.edu",
    full_name="Dr. Sunita Sharma",
    role=UserRole.TEACHER,
    organization_id=org.id,
)
db.create_user(teacher_user)

# Central Services
portal = TeacherPortalService()
instruction_engine = TeacherInstructionEngine()
intervention_engine = TeacherInterventionEngine()
copilot = TeacherCopilot()
sync_manager = SyncManager()

# Seed Cohort Students in Chemistry 101
cohort = [
    {
        "id": "stu-202",
        "name": "Rahul Kumar",
        "mastery": 0.85,
        "needs_attention": False,
        "misconceptions": [],
        "hints": 2,
        "retention": 0.90,
        "recent": "Solved Hess's Law formation enthalpy",
        "chapters": {"Thermodynamics": 0.88, "Chemical Bonding": 0.84, "Coordination Chemistry": 0.80, "Periodic Trends": 0.90},
    },
    {
        "id": "stu-203",
        "name": "Priya Sharma",
        "mastery": 0.94,
        "needs_attention": False,
        "misconceptions": [],
        "hints": 0,
        "retention": 0.96,
        "recent": "Calculated Gibbs free energy at non-standard T",
        "chapters": {"Thermodynamics": 0.95, "Chemical Bonding": 0.92, "Coordination Chemistry": 0.94, "Periodic Trends": 0.95},
    },
    {
        "id": "stu-204",
        "name": "Amit Patel",
        "mastery": 0.42,
        "needs_attention": True,
        "misconceptions": ["THERMO_SIGN_CONVENTION"],
        "hints": 7,
        "retention": 0.60,
        "recent": "Failed sign convention in expansion work (ΔU)",
        "chapters": {"Thermodynamics": 0.36, "Chemical Bonding": 0.52, "Coordination Chemistry": 0.38, "Periodic Trends": 0.58},
    },
    {
        "id": "stu-205",
        "name": "Ananya Roy",
        "mastery": 0.67,
        "needs_attention": False,
        "misconceptions": ["BOND_ORBITAL_HYBRIDIZATION"],
        "hints": 4,
        "retention": 0.78,
        "recent": "Struggled with sp3d axial/equatorial bond angles",
        "chapters": {"Thermodynamics": 0.70, "Chemical Bonding": 0.62, "Coordination Chemistry": 0.65, "Periodic Trends": 0.76},
    },
    {
        "id": "stu-206",
        "name": "Vikram Seth",
        "mastery": 0.52,
        "needs_attention": True,
        "misconceptions": ["THERMO_REVERSIBLE_WORK"],
        "hints": 5,
        "retention": 0.68,
        "recent": "Confused isothermal reversible with adiabatic work",
        "chapters": {"Thermodynamics": 0.46, "Chemical Bonding": 0.58, "Coordination Chemistry": 0.50, "Periodic Trends": 0.64},
    },
]

for s in cohort:
    user = User(
        id=s["id"],
        email=f"{s['id']}@dsa.edu",
        full_name=s["name"],
        role=UserRole.STUDENT,
        organization_id=org.id,
    )
    db.create_user(user)
    sync_manager.bind_device(f"device-{s['id']}", s["id"])
    portal.register_student_snapshot(
        student_id=s["id"],
        name=s["name"],
        course_id="crs-chem-101",
        mastery=s["mastery"],
        needs_attention=s["needs_attention"],
        misconceptions=s["misconceptions"],
        hint_count=s["hints"],
        retention_rate=s["retention"],
        chapter_mastery=s["chapters"],
        recent_activity=s["recent"],
    )

# Seed Active Alerts
intervention_engine.raise_alert(
    TeacherAlert(
        alert_id="alt-001",
        student_id="stu-204",
        course_id="crs-chem-101",
        alert_type="repeated_failure",
        severity=AlertSeverity.CRITICAL,
        message="Amit Patel failed thermodynamic expansion work sign convention 3 times consecutively.",
    )
)
intervention_engine.raise_alert(
    TeacherAlert(
        alert_id="alt-002",
        student_id="stu-205",
        course_id="crs-chem-101",
        alert_type="prerequisite_weakness",
        severity=AlertSeverity.WARNING,
        message="Ananya Roy requested Tier 4 hint twice for VSEPR orbital geometry in PCl5.",
    )
)
intervention_engine.raise_alert(
    TeacherAlert(
        alert_id="alt-003",
        student_id="stu-206",
        course_id="crs-chem-101",
        alert_type="mastery_regression",
        severity=AlertSeverity.WARNING,
        message="Vikram Seth experienced a 15% mastery drop in Reversible Expansion Work.",
    )
)
intervention_engine.raise_alert(
    TeacherAlert(
        alert_id="alt-004",
        student_id="stu-203",
        course_id="crs-chem-101",
        alert_type="advancement_ready",
        severity=AlertSeverity.INFO,
        message="Priya Sharma exceeded 90% mastery across all topics. Ready for JEE Advanced problem set.",
    )
)

# Seed Initial Pedagogical Instructions
instruction_engine.add_instruction(
    TeacherInstruction(
        instruction_id="inst-001",
        teacher_id=teacher_user.id,
        student_id="all",
        course_id="crs-chem-101",
        concept_scope="THERMODYNAMICS",
        instruction_text="Emphasize IUPAC sign conventions: expansion work done BY the system must always be taken as -w.",
        priority=2,
    )
)
instruction_engine.add_instruction(
    TeacherInstruction(
        instruction_id="inst-002",
        teacher_id=teacher_user.id,
        student_id="stu-204",
        course_id="crs-chem-101",
        concept_scope="THERMO_SIGN_CONVENTION",
        instruction_text="Guide Amit through the microscopic piston cylinder model before asking for numerical calculation of ΔU.",
        priority=3,
    )
)
instruction_engine.add_instruction(
    TeacherInstruction(
        instruction_id="inst-003",
        teacher_id=teacher_user.id,
        student_id="stu-205",
        course_id="crs-chem-101",
        concept_scope="BOND_ORBITAL_HYBRIDIZATION",
        instruction_text="Have Ananya compare axial vs equatorial bond repulsions in trigonal bipyramidal molecules.",
        priority=2,
    )
)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gayatri AI — Teacher Command Center & Cohort Intelligence</title>
    <style>
        :root {
            --bg: #0b0d1b;
            --card-bg: #13172e;
            --card-border: #22274c;
            --accent: #9b59b6;
            --accent-hover: #8e44ad;
            --text-main: #f0f2f8;
            --text-sub: #9ca3af;
            --green: #27c93f;
            --yellow: #f5a623;
            --red: #ff5f56;
            --blue: #3b82f6;
            --cyan: #00d2d3;
        }
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: var(--bg);
            color: var(--text-main);
            margin: 0;
            padding: 24px;
            line-height: 1.5;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        
        /* Top Navigation Header */
        .top-bar {
            background: linear-gradient(135deg, #181d3d 0%, #291a45 100%);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 24px 30px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
        }
        .top-title h1 { margin: 0 0 6px 0; font-size: 24px; color: #fff; display: flex; align-items: center; gap: 10px; }
        .top-title p { margin: 0; color: var(--text-sub); font-size: 13px; }
        .top-badge {
            background: rgba(155, 89, 182, 0.2);
            color: #d8b4e2;
            border: 1px solid var(--accent);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        .badge-dot {
            width: 8px; height: 8px; border-radius: 50%; background: var(--green);
            box-shadow: 0 0 8px var(--green);
        }
        
        /* KPI Cards Grid */
        .grid-kpi {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }
        .kpi-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 18px;
        }
        .kpi-lbl { font-size: 11px; font-weight: 700; color: var(--text-sub); text-transform: uppercase; letter-spacing: 0.6px; }
        .kpi-val { font-size: 28px; font-weight: 800; margin: 6px 0; }
        .kpi-sub { font-size: 12px; color: var(--text-sub); }

        /* Mastery Breakdown Bar */
        .card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 14px;
            padding: 22px;
            margin-bottom: 24px;
        }
        .card h2 { margin: 0 0 16px 0; font-size: 18px; color: #fff; display: flex; align-items: center; gap: 10px; }
        .section-desc { font-size: 13px; color: var(--text-sub); margin-top: -8px; margin-bottom: 16px; }

        .progress-bar-container {
            height: 18px;
            background: #090b16;
            border-radius: 9px;
            overflow: hidden;
            display: flex;
            margin: 12px 0 16px 0;
            border: 1px solid #23274c;
        }
        .progress-seg { height: 100%; transition: width 0.3s; }
        .progress-legend { display: flex; gap: 20px; font-size: 13px; flex-wrap: wrap; }
        .legend-item { display: flex; align-items: center; gap: 6px; }
        .legend-dot { width: 10px; height: 10px; border-radius: 50%; }

        /* Chapter Performance Grid */
        .chapter-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 14px;
            margin-top: 14px;
        }
        .chapter-box {
            background: #181d38;
            border: 1px solid var(--card-border);
            border-radius: 10px;
            padding: 16px;
        }
        .chapter-name { font-weight: 600; font-size: 14px; color: #fff; margin-bottom: 8px; }
        .chapter-pct { font-size: 22px; font-weight: 700; color: var(--cyan); margin-bottom: 6px; }
        .chapter-bar { height: 6px; background: #0c0e1e; border-radius: 3px; overflow: hidden; }
        .chapter-bar-fill { height: 100%; background: var(--cyan); }

        /* Tables */
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }
        th { text-align: left; padding: 12px 14px; background: #1a1e3d; color: #adb5bd; border-bottom: 2px solid var(--card-border); font-weight: 600; }
        td { padding: 12px 14px; border-bottom: 1px solid var(--card-border); vertical-align: middle; }
        tr:hover td { background: rgba(255,255,255,0.02); }
        
        .status-pill {
            padding: 3px 8px;
            border-radius: 10px;
            font-size: 11px;
            font-weight: 700;
            display: inline-block;
        }
        .pill-good { background: rgba(39, 201, 63, 0.15); color: #27c93f; }
        .pill-warn { background: rgba(245, 166, 35, 0.15); color: #f5a623; }
        .pill-crit { background: rgba(255, 95, 86, 0.15); color: #ff5f56; }
        .pill-info { background: rgba(59, 130, 246, 0.15); color: #60a5fa; }
        
        .misc-pill {
            background: rgba(255, 95, 86, 0.15);
            color: #ff8580;
            border: 1px solid rgba(255, 95, 86, 0.3);
            border-radius: 6px;
            padding: 2px 6px;
            font-size: 11px;
            font-family: monospace;
            display: inline-block;
            margin: 2px;
        }

        /* Alert Center Cards */
        .alert-card {
            background: #171b36;
            border-left: 4px solid var(--accent);
            padding: 14px 18px;
            border-radius: 0 8px 8px 0;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 14px;
        }
        .alert-critical { border-left-color: var(--red); }
        .alert-warning { border-left-color: var(--yellow); }
        .alert-info { border-left-color: var(--blue); }

        /* Form elements */
        .form-row { display: flex; gap: 12px; margin-top: 14px; flex-wrap: wrap; }
        input[type="text"], select {
            background: #0c0e1e;
            border: 1px solid #2d325a;
            border-radius: 8px;
            padding: 10px 14px;
            color: #fff;
            font-size: 13px;
            outline: none;
        }
        input[type="text"]:focus, select:focus { border-color: var(--accent); }
        button, input[type="submit"] {
            background: var(--accent);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 18px;
            font-size: 13px;
            font-weight: 700;
            cursor: pointer;
            transition: opacity 0.2s;
        }
        button:hover, input[type="submit"]:hover { opacity: 0.88; }
        .btn-small { padding: 6px 12px; font-size: 12px; border-radius: 6px; }
        .btn-resolve { background: #233446; color: #64b5f6; }
        .btn-resolve:hover { background: #1e88e5; color: #fff; }
        .btn-toggle { background: #2a203f; color: #d8b4e2; }
        .btn-toggle:hover { background: var(--accent); color: #fff; }

        /* Copilot Briefing Box */
        .copilot-box {
            background: linear-gradient(135deg, #181d3d 0%, #201736 100%);
            border: 1px solid #3c2a63;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 24px;
        }
        .copilot-header { display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 16px; color: #e0b0ff; margin-bottom: 10px; }
        .copilot-body { font-size: 13px; color: #d1d5db; line-height: 1.6; }
        .copilot-rec { background: rgba(155, 89, 182, 0.15); border-left: 3px solid var(--accent); padding: 8px 12px; border-radius: 4px; margin-top: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <!-- Top Banner Header -->
        <div class="top-bar">
            <div class="top-title">
                <h1>👩‍🏫 Gayatri AI — Teacher Command Center</h1>
                <p>Course: Class 11 &amp; 12 NCERT Chemistry (<code>crs-chem-101</code>) • Instructor: Dr. Sunita Sharma</p>
            </div>
            <div class="top-badge">
                <span class="badge-dot"></span>
                Central Platform Live &amp; Synced
            </div>
        </div>

        <!-- KPI Summary Cards -->
        <div class="grid-kpi">
            <div class="kpi-card">
                <div class="kpi-lbl">Class Health</div>
                <div class="kpi-val" style="color: __HEALTH_COLOR__;">__HEALTH_STATUS__</div>
                <div class="kpi-sub">Overall Cohort State</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-lbl">Class Average</div>
                <div class="kpi-val" style="color: var(--cyan);">__AVG_MASTERY__%</div>
                <div class="kpi-sub">Across All Concepts</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-lbl">Mastered (&gt;80%)</div>
                <div class="kpi-val" style="color: var(--green);">__MASTERED_COUNT__</div>
                <div class="kpi-sub">Exceeding Benchmark</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-lbl">In Progress (50-80%)</div>
                <div class="kpi-val" style="color: var(--yellow);">__PROGRESSING_COUNT__</div>
                <div class="kpi-sub">Steady Progression</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-lbl">Critical / At Risk</div>
                <div class="kpi-val" style="color: var(--red);">__CRITICAL_COUNT__</div>
                <div class="kpi-sub">Requires Intervention</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-lbl">Active Directives</div>
                <div class="kpi-val" style="color: var(--accent);">__TOTAL_INSTRUCTIONS__</div>
                <div class="kpi-sub">AI Tutor Pedagogies</div>
            </div>
        </div>

        <!-- Mastery Distribution Bar -->
        <div class="card">
            <h2><span>📈</span> Cohort Mastery Distribution</h2>
            <div class="section-desc">Empirical student mastery tier grouping for Class 11 &amp; 12 Chemistry.</div>
            <div class="progress-bar-container">
                <div class="progress-seg" style="width: __MASTERED_PCT__%; background: var(--green);" title="Mastered"></div>
                <div class="progress-seg" style="width: __PROGRESSING_PCT__%; background: var(--yellow);" title="In Progress"></div>
                <div class="progress-seg" style="width: __CRITICAL_PCT__%; background: var(--red);" title="Critical"></div>
            </div>
            <div class="progress-legend">
                <div class="legend-item"><div class="legend-dot" style="background: var(--green);"></div> Mastered (&ge;80%): <strong>__MASTERED_COUNT__ Students (__MASTERED_PCT__%)</strong></div>
                <div class="legend-item"><div class="legend-dot" style="background: var(--yellow);"></div> In Progress (50-79%): <strong>__PROGRESSING_COUNT__ Students (__PROGRESSING_PCT__%)</strong></div>
                <div class="legend-item"><div class="legend-dot" style="background: var(--red);"></div> Attention Needed (&lt;50%): <strong>__CRITICAL_COUNT__ Students (__CRITICAL_PCT__%)</strong></div>
            </div>

            <!-- Chapter Mastery Grid -->
            <div class="chapter-grid">
                __CHAPTER_BOXES__
            </div>
        </div>

        <!-- AI Teacher Copilot Briefing -->
        <div class="copilot-box">
            <div class="copilot-header">
                <span>🤖</span> Teacher AI Copilot — Cohort Intelligence &amp; Gap Analysis
            </div>
            <div class="copilot-body">
                <strong>Empirical Session Analysis:</strong>
                Based on continuous interaction telemetry across __TOTAL_STUDENTS__ students, the primary learning bottleneck is centered on <em>IUPAC Thermodynamic Sign Conventions (Expansion Work ΔU)</em> and <em>VSEPR Orbital Hybridization</em>.
                <div class="copilot-rec">
                    <strong>💡 Copilot Pedagogical Recommendation:</strong>
                    Inject a Tier-1 conceptual directive for students attempting expansion work calculations to ask whether the system did work on surroundings or vice-versa before formulas are computed.
                </div>
            </div>
        </div>

        <!-- Actionable Alerts & Intervention Queue -->
        <div class="card">
            <h2><span>🚨</span> Real-Time Teacher Alert Queue (__ACTIVE_ALERTS_COUNT__)</h2>
            <div class="section-desc">Automated alerts raised when students encounter repeated errors, prerequisite gaps, or score drops.</div>
            __ALERT_CARDS__
        </div>

        <!-- Monitored Students Roster & Deep Dive -->
        <div class="card">
            <h2><span>👥</span> Student Performance Roster &amp; Misconception Diagnostics</h2>
            <div class="section-desc">Detailed learning evidence including hint dependencies, retention rate, and diagnosed misconceptions.</div>
            <table>
                <thead>
                    <tr>
                        <th>Student</th>
                        <th>Course</th>
                        <th>Mastery</th>
                        <th>Diagnosed Misconceptions</th>
                        <th>Hints</th>
                        <th>Retention</th>
                        <th>Recent Interaction</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    __STUDENT_ROWS__
                </tbody>
            </table>
        </div>

        <!-- Targeted Pedagogical Directives (Teacher Instructions) -->
        <div class="card">
            <h2><span>🎯</span> Inject Targeted Pedagogical Directive</h2>
            <div class="section-desc">Instruct the student's local Gayatri AI Tutor to emphasize specific derivations, sign conventions, or teaching styles.</div>
            <form method="POST" action="/instruction">
                <div class="form-row">
                    <select name="student_id" style="min-width: 170px;">
                        <option value="all">Entire Class (crs-chem-101)</option>
                        __STUDENT_OPTIONS__
                    </select>
                    <select name="concept_scope" style="min-width: 160px;">
                        <option value="ALL">All Concepts</option>
                        <option value="THERMODYNAMICS">Thermodynamics</option>
                        <option value="CHEMICAL_BONDING">Chemical Bonding</option>
                        <option value="COORDINATION">Coordination Chemistry</option>
                        <option value="PERIODIC">Periodic Trends</option>
                    </select>
                    <input type="text" name="instruction" placeholder="e.g. Always require sign reasoning before evaluating ΔU = q + w..." style="flex: 1; min-width: 280px;" required>
                    <select name="priority" style="min-width: 110px;">
                        <option value="1">Normal (1)</option>
                        <option value="2" selected>High (2)</option>
                        <option value="3">Urgent (3)</option>
                    </select>
                    <input type="submit" value="Inject Directive">
                </div>
            </form>

            <h3 style="margin-top: 24px; font-size: 15px; color: #fff;">Active Directives for AI Tutors</h3>
            <div style="margin-top: 10px;">
                __INSTRUCTION_ITEMS__
            </div>
        </div>

        <!-- Course Assessments & Diagnostics -->
        <div class="card">
            <h2><span>📝</span> Course Assessments &amp; Diagnostic Quizzes</h2>
            <div class="section-desc">Manage calibrated diagnostic quizzes and track student completion.</div>
            <table>
                <thead>
                    <tr>
                        <th>Assessment Title</th>
                        <th>Concept Scope</th>
                        <th>Questions</th>
                        <th>Status</th>
                        <th>Class Avg Score</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>Thermodynamics &amp; Enthalpy Diagnostic</strong></td>
                        <td>First Law of Thermodynamics</td>
                        <td>5 Items</td>
                        <td><span class="status-pill pill-good">Completed</span></td>
                        <td><strong>78%</strong></td>
                        <td><button class="btn-small btn-resolve">View Breakdown</button></td>
                    </tr>
                    <tr>
                        <td><strong>Chemical Bonding &amp; VSEPR Drill</strong></td>
                        <td>Molecular Geometry &amp; Hybridization</td>
                        <td>10 Items</td>
                        <td><span class="status-pill pill-info">Active</span></td>
                        <td><strong>72%</strong></td>
                        <td><button class="btn-small btn-resolve">View Live</button></td>
                    </tr>
                    <tr>
                        <td><strong>Coordination Chemistry Speed Check</strong></td>
                        <td>IUPAC Naming &amp; Isomerism</td>
                        <td>8 Items</td>
                        <td><span class="status-pill pill-warn">Scheduled</span></td>
                        <td><strong>--</strong></td>
                        <td><button class="btn-small btn-toggle">Deploy Now</button></td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""


class TeacherPortalHTTPHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for Teacher Dashboard and Central Sync API."""

    def log_message(self, format: str, *args) -> None:
        """Suppress noisy default logging."""
        return

    def _send_json(self, data: dict, status: int = 200) -> None:
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self) -> None:
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        try:
            parsed = urlparse(self.path)
            path = parsed.path

            if path in ("/", "/teacher", "/dashboard"):
                overview = portal.get_dashboard_overview("crs-chem-101")
                students = portal.get_all_students("crs-chem-101")
                instructions = instruction_engine.get_all_instructions()
                alerts = intervention_engine.get_all_alerts("crs-chem-101")

                # Health Color
                health_color = "var(--green)"
                if overview.class_health_status == "Attention Needed":
                    health_color = "var(--yellow)"
                elif overview.class_health_status == "Critical":
                    health_color = "var(--red)"

                # Distribution percentages
                total = max(1, overview.total_students)
                mastered_pct = int((overview.mastered_count / total) * 100)
                progressing_pct = int((overview.progressing_count / total) * 100)
                critical_pct = 100 - mastered_pct - progressing_pct

                # Chapter boxes
                chapter_boxes = []
                for ch_name, ch_avg in overview.chapter_averages.items():
                    pct = int(ch_avg * 100)
                    chapter_boxes.append(
                        f"<div class='chapter-box'>"
                        f"  <div class='chapter-name'>{ch_name}</div>"
                        f"  <div class='chapter-pct'>{pct}%</div>"
                        f"  <div class='chapter-bar'><div class='chapter-bar-fill' style='width: {pct}%;'></div></div>"
                        f"</div>"
                    )

                # Student Rows
                student_rows = []
                student_options = []
                for s in students:
                    status_pill = (
                        '<span class="status-pill pill-warn">Attention Needed</span>'
                        if s["needs_attention"]
                        else '<span class="status-pill pill-good">On Track</span>'
                    )
                    misc_badges = (
                        "".join(f"<span class='misc-pill'>{m}</span>" for m in s.get("misconceptions", []))
                        if s.get("misconceptions")
                        else "<span style='color: var(--text-sub);'>None</span>"
                    )
                    student_rows.append(
                        f"<tr>"
                        f"<td><strong>{s['name']}</strong><br><code style='color: var(--text-sub); font-size: 11px;'>{s['id']}</code></td>"
                        f"<td>{s['course_id']}</td>"
                        f"<td><strong style='font-size: 14px;'>{int(s['mastery'] * 100)}%</strong></td>"
                        f"<td>{misc_badges}</td>"
                        f"<td>{s.get('hint_count', 0)}</td>"
                        f"<td>{int(s.get('retention_rate', 0.85) * 100)}%</td>"
                        f"<td style='font-size: 12px; color: var(--text-sub);'>{s.get('recent_activity', 'Active')}</td>"
                        f"<td>{status_pill}</td>"
                        f"</tr>"
                    )
                    student_options.append(f"<option value='{s['id']}'>{s['name']} ({s['id']})</option>")

                # Alert Cards
                alert_cards = []
                active_alerts = [a for a in alerts if a.status != AlertStatus.RESOLVED]
                for a in active_alerts:
                    card_class = "alert-info"
                    severity_badge = '<span class="status-pill pill-info">Info</span>'
                    if a.severity == AlertSeverity.CRITICAL:
                        card_class = "alert-critical"
                        severity_badge = '<span class="status-pill pill-crit">Critical</span>'
                    elif a.severity == AlertSeverity.WARNING:
                        card_class = "alert-warning"
                        severity_badge = '<span class="status-pill pill-warn">Warning</span>'

                    alert_cards.append(
                        f"<div class='alert-card {card_class}'>"
                        f"  <div>"
                        f"    <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 4px;'>"
                        f"      {severity_badge}"
                        f"      <span style='font-weight: 700; color: #fff;'>Student: {a.student_id}</span>"
                        f"      <span style='font-size: 11px; color: var(--text-sub);'>({a.alert_type})</span>"
                        f"    </div>"
                        f"    <div style='font-size: 13px; color: #e5e7eb;'>{a.message}</div>"
                        f"  </div>"
                        f"  <form method='POST' action='/alert/resolve' style='margin: 0;'>"
                        f"    <input type='hidden' name='alert_id' value='{a.alert_id}'>"
                        f"    <button type='submit' class='btn-small btn-resolve'>✓ Resolve</button>"
                        f"  </form>"
                        f"</div>"
                    )

                # Instruction Items
                instruction_items = []
                for inst in instructions:
                    status_badge = (
                        "<span style='color: var(--green); font-weight: 600;'>● Active</span>"
                        if inst.is_active
                        else "<span style='color: var(--text-sub);'>Inactive</span>"
                    )
                    toggle_label = "Deactivate" if inst.is_active else "Activate"
                    instruction_items.append(
                        f"<div class='alert-card' style='border-left-color: var(--accent);'>"
                        f"  <div>"
                        f"    <div style='font-size: 14px; font-weight: 600; color: #fff;'>\"{inst.instruction_text}\"</div>"
                        f"    <div style='font-size: 12px; color: var(--text-sub); margin-top: 4px;'>"
                        f"      Target: <code>{inst.student_id}</code> | Scope: <strong>{inst.concept_scope or 'ALL'}</strong> | Priority: {inst.priority} | Created: {inst.created_at[:19]}"
                        f"    </div>"
                        f"  </div>"
                        f"  <div style='display: flex; align-items: center; gap: 10px;'>"
                        f"    {status_badge}"
                        f"    <form method='POST' action='/instruction/toggle' style='margin: 0;'>"
                        f"      <input type='hidden' name='instruction_id' value='{inst.instruction_id}'>"
                        f"      <button type='submit' class='btn-small btn-toggle'>{toggle_label}</button>"
                        f"    </form>"
                        f"  </div>"
                        f"</div>"
                    )

                content = (
                    HTML_TEMPLATE
                    .replace("__HEALTH_STATUS__", overview.class_health_status)
                    .replace("__HEALTH_COLOR__", health_color)
                    .replace("__AVG_MASTERY__", str(int(overview.average_mastery * 100)))
                    .replace("__TOTAL_STUDENTS__", str(overview.total_students))
                    .replace("__MASTERED_COUNT__", str(overview.mastered_count))
                    .replace("__PROGRESSING_COUNT__", str(overview.progressing_count))
                    .replace("__CRITICAL_COUNT__", str(overview.critical_count))
                    .replace("__MASTERED_PCT__", str(mastered_pct))
                    .replace("__PROGRESSING_PCT__", str(progressing_pct))
                    .replace("__CRITICAL_PCT__", str(critical_pct))
                    .replace("__TOTAL_INSTRUCTIONS__", str(len([i for i in instructions if i.is_active])))
                    .replace("__ACTIVE_ALERTS_COUNT__", str(len(active_alerts)))
                    .replace("__CHAPTER_BOXES__", "\n".join(chapter_boxes))
                    .replace("__ALERT_CARDS__", "\n".join(alert_cards) if alert_cards else "<div style='color: var(--text-sub); padding: 10px;'>No active alerts. All students progressing stably.</div>")
                    .replace("__STUDENT_ROWS__", "\n".join(student_rows) if student_rows else "<tr><td colspan='8'>No students registered yet</td></tr>")
                    .replace("__STUDENT_OPTIONS__", "\n".join(student_options))
                    .replace("__INSTRUCTION_ITEMS__", "\n".join(instruction_items) if instruction_items else "<div style='color: var(--text-sub); padding: 10px;'>No directives added yet.</div>")
                )

                payload = content.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            elif path == "/api/health":
                overview = portal.get_dashboard_overview("crs-chem-101")
                self._send_json({
                    "status": "HEALTHY",
                    "service": "TeacherPortalServer",
                    "students_monitored": overview.total_students,
                    "active_instructions": len(instruction_engine.get_all_instructions()),
                    "active_alerts": len([a for a in intervention_engine.get_all_alerts("crs-chem-101") if a.status != AlertStatus.RESOLVED]),
                })

            elif path == "/api/teacher/dashboard":
                query = parse_qs(parsed.query)
                course_id = query.get("course_id", ["crs-chem-101"])[0]
                overview = portal.get_dashboard_overview(course_id)
                students = portal.get_all_students(course_id)
                alerts = [
                    {
                        "alert_id": a.alert_id,
                        "student_id": a.student_id,
                        "severity": a.severity.value,
                        "alert_type": a.alert_type,
                        "message": a.message,
                        "status": a.status.value,
                        "created_at": a.created_at,
                    }
                    for a in intervention_engine.get_all_alerts(course_id)
                ]
                self._send_json({
                    "ok": True,
                    "course_id": course_id,
                    "total_students": overview.total_students,
                    "students_needing_attention": overview.students_needing_attention,
                    "average_mastery": overview.average_mastery,
                    "active_alerts_count": overview.active_alerts_count,
                    "class_health_status": overview.class_health_status,
                    "mastered_count": overview.mastered_count,
                    "progressing_count": overview.progressing_count,
                    "critical_count": overview.critical_count,
                    "chapter_averages": overview.chapter_averages,
                    "top_misconceptions": overview.top_misconceptions,
                    "students": students,
                    "alerts": alerts,
                })

            elif path == "/api/teacher/instructions":
                query = parse_qs(parsed.query)
                student_id = query.get("student_id", [None])[0]
                course_id = query.get("course_id", ["crs-chem-101"])[0]

                if student_id:
                    active = instruction_engine.get_instructions_for_student(student_id, course_id)
                else:
                    active = [i for i in instruction_engine.get_all_instructions() if i.is_active]

                serialized = [
                    {
                        "instruction_id": i.instruction_id,
                        "teacher_id": i.teacher_id,
                        "student_id": i.student_id,
                        "course_id": i.course_id,
                        "concept_scope": i.concept_scope,
                        "instruction_text": i.instruction_text,
                        "priority": i.priority,
                        "created_at": i.created_at,
                    }
                    for i in active
                ]
                self._send_json({"ok": True, "instructions": serialized})

            else:
                self.send_error(404, "Page Not Found")
        except Exception as e:
            self._send_json({"ok": False, "error": str(e)}, status=500)

    def do_POST(self) -> None:
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8") if length > 0 else ""

            if path == "/instruction":
                params = parse_qs(body)
                inst_text = params.get("instruction", [""])[0].strip()
                student_id = params.get("student_id", ["all"])[0]
                scope = params.get("concept_scope", ["ALL"])[0]
                priority = int(params.get("priority", [2])[0])

                if inst_text:
                    new_inst = TeacherInstruction(
                        instruction_id=f"inst-{uuid.uuid4().hex[:6]}",
                        teacher_id=teacher_user.id,
                        student_id=student_id,
                        course_id="crs-chem-101",
                        concept_scope=scope if scope != "ALL" else None,
                        instruction_text=inst_text,
                        priority=priority,
                    )
                    instruction_engine.add_instruction(new_inst)

                self.send_response(HTTPStatus.SEE_OTHER)
                self.send_header("Location", "/")
                self.end_headers()

            elif path == "/instruction/toggle":
                params = parse_qs(body)
                inst_id = params.get("instruction_id", [""])[0]
                if inst_id:
                    instruction_engine.toggle_instruction(inst_id)

                self.send_response(HTTPStatus.SEE_OTHER)
                self.send_header("Location", "/")
                self.end_headers()

            elif path == "/alert/resolve":
                params = parse_qs(body)
                alert_id = params.get("alert_id", [""])[0]
                if alert_id:
                    intervention_engine.resolve_alert(alert_id)

                self.send_response(HTTPStatus.SEE_OTHER)
                self.send_header("Location", "/")
                self.end_headers()

            elif path == "/api/teacher/instruction":
                data = json.loads(body)
                text = data.get("instruction", "").strip()
                if not text:
                    self._send_json({"ok": False, "error": "Instruction text is required"}, status=400)
                    return

                new_inst = TeacherInstruction(
                    instruction_id=data.get("instruction_id", f"inst-{uuid.uuid4().hex[:6]}"),
                    teacher_id=data.get("teacher_id", teacher_user.id),
                    student_id=data.get("student_id", "all"),
                    course_id=data.get("course_id", "crs-chem-101"),
                    concept_scope=data.get("concept_scope"),
                    instruction_text=text,
                    priority=int(data.get("priority", 2)),
                )
                instruction_engine.add_instruction(new_inst)
                self._send_json({"ok": True, "instruction_id": new_inst.instruction_id})

            elif path == "/api/teacher/alert/resolve":
                data = json.loads(body)
                aid = data.get("alert_id")
                if aid and intervention_engine.resolve_alert(aid):
                    self._send_json({"ok": True, "message": "Alert resolved"})
                else:
                    self._send_json({"ok": False, "error": "Alert not found"}, status=404)

            elif path == "/api/student/snapshot":
                data = json.loads(body)
                sid = data.get("student_id", "stu-202")
                name = data.get("student_name", "Student")
                course_id = data.get("course_id", "crs-chem-101")
                mastery = float(data.get("mastery", 0.75))
                needs_attention = bool(data.get("needs_attention", False))

                portal.register_student_snapshot(
                    student_id=sid,
                    name=name,
                    course_id=course_id,
                    mastery=mastery,
                    needs_attention=needs_attention,
                    misconceptions=data.get("misconceptions", []),
                    hint_count=int(data.get("hint_count", 0)),
                    retention_rate=float(data.get("retention_rate", 0.85)),
                )
                self._send_json({"ok": True, "message": "Snapshot updated"})

            elif path == "/api/sync/events":
                data = json.loads(body)
                events_data = data.get("events", [])
                for ev in events_data:
                    event = SyncEvent(
                        event_id=ev["event_id"],
                        student_id=ev["student_id"],
                        device_id=ev["device_id"],
                        event_type=ev["event_type"],
                        payload=ev.get("payload", {}),
                    )
                    sync_manager.queue_offline_event(event)

                result = sync_manager.process_sync()
                self._send_json({"ok": True, "sync_result": result})

            else:
                self.send_error(404, "Endpoint Not Found")
        except Exception as e:
            self._send_json({"ok": False, "error": str(e)}, status=500)


def run_server(port: int = 8000) -> None:
    server_address = ("0.0.0.0", port)
    httpd = HTTPServer(server_address, TeacherPortalHTTPHandler)
    print(f"[ONLINE] Gayatri Teacher Portal HTTP Server running at http://localhost:{port}")
    httpd.serve_forever()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    run_server(port)
