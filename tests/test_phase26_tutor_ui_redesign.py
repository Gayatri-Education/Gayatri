"""Tests for Phase 26 — Tutor UI Redesign.

Verifies:
- Tutor CSS & JS asset existence (tutor.css, tutor.js)
- CSS layout rules (3-pane layout, intelligent composer, learning context panel, response action bar, AI status indicator)
- Tutor JS controller functions (toggleLearningContext, triggerResponseAction, updateAIStatus, updateLearningContext)
- Python backend TutorUIController, TutorUIState, TruthfulAIStatusData, and LearningContextPanelData
"""
import pytest
from pathlib import Path

from central_platform.ui.tutor import (
    LearningContextPanelData,
    TruthfulAIStatusData,
    TutorActionType,
    TutorUIController,
    TutorUIState,
)


@pytest.fixture
def tutor_paths():
    root = Path(__file__).resolve().parent.parent
    ds_dir = root / "app" / "ui" / "design_system"
    return {
        "tutor_css": ds_dir / "tutor.css",
        "tutor_js": ds_dir / "tutor.js",
    }


def test_tutor_files_exist(tutor_paths):
    assert tutor_paths["tutor_css"].exists()
    assert tutor_paths["tutor_js"].exists()


def test_tutor_css_rules(tutor_paths):
    css = tutor_paths["tutor_css"].read_text(encoding="utf-8")

    # Verify key Tutor UI components in CSS
    assert ".tutor-layout" in css
    assert ".conversation-area" in css
    assert ".learning-context-panel" in css
    assert ".response-action-bar" in css
    assert ".tutor-composer" in css
    assert ".ai-status-indicator" in css
    assert ".context-collapsed" in css


def test_tutor_js_controller(tutor_paths):
    js = tutor_paths["tutor_js"].read_text(encoding="utf-8")

    # Verify JS controller functions
    assert "toggleLearningContext" in js
    assert "triggerResponseAction" in js
    assert "updateAIStatus" in js
    assert "updateLearningContext" in js


def test_python_tutor_actions():
    actions = TutorUIController.get_supported_actions()
    assert len(actions) == 6
    action_types = {a["type"] for a in actions}
    assert "explain_simpler" in action_types
    assert "give_hint" in action_types
    assert "practice" in action_types
    assert "copy" in action_types
    assert "show_sources" in action_types


def test_truthful_ai_status_defaults():
    status = TruthfulAIStatusData()
    d = status.to_dict()
    assert d["provider_name"] == "local_gguf"
    assert d["zero_leakage_enforced"] is True
    assert d["latency_ms"] == 120.0


def test_learning_context_panel_data():
    panel = LearningContextPanelData(
        topic_name="Equilibrium",
        mastery_score=0.85,
        sources=[{"citation": "NCERT (p. 190)", "text": "Le Chatelier principle"}]
    )
    d = panel.to_dict()
    assert d["topic_name"] == "Equilibrium"
    assert d["mastery_score"] == 0.85
    assert len(d["sources"]) == 1


def test_tutor_ui_state():
    state = TutorUIState(student_id="s1", course_id="c1")
    d = state.to_dict()
    assert d["student_id"] == "s1"
    assert d["course_id"] == "c1"
    assert d["context_panel_collapsed"] is False
