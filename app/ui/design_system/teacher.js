/**
 * Gayatri AI Platform — Teacher Portal UI Controller (Phase 28)
 * Controls tab switching for Class Overview, Students, Learning Health,
 * Student Profile, Interventions, Assessments, Teacher Instructions, and AI Copilot.
 */

window.GayatriTeacher = (function () {
  'use strict';

  let currentTab = 'class_overview';

  // 1. Switch Tab
  function switchTeacherTab(tabName) {
    const validTabs = [
      'class_overview', 'students', 'learning_health', 'student_profile',
      'interventions', 'assessments', 'teacher_instructions', 'ai_copilot'
    ];
    if (!validTabs.includes(tabName)) return;

    currentTab = tabName;

    // Update tab buttons
    const buttons = document.querySelectorAll('.teacher-tab-btn');
    buttons.forEach((btn) => {
      if (btn.getAttribute('data-tab') === tabName) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    // Update view panels
    const views = document.querySelectorAll('.teacher-view-panel');
    views.forEach((panel) => {
      if (panel.id === `teacher-view-${tabName}`) {
        panel.style.display = 'block';
      } else {
        panel.style.display = 'none';
      }
    });
  }

  // 2. Render Functions
  function renderClassOverview(data) {
    const container = document.querySelector('.class-overview-grid');
    if (!container || !data) return;

    container.innerHTML = `
      <div class="cohort-stat-card">
        <div class="stat-value">${data.enrolled_count || 0}</div>
        <div class="stat-label">Enrolled Students</div>
      </div>
      <div class="cohort-stat-card">
        <div class="stat-value">${data.average_mastery_pct || 0}%</div>
        <div class="stat-label">Average Cohort Mastery</div>
      </div>
      <div class="cohort-stat-card">
        <div class="stat-value">${data.at_risk_count || 0}</div>
        <div class="stat-label">At-Risk Students</div>
      </div>
      <div class="cohort-stat-card">
        <div class="stat-value">${data.active_interventions || 0}</div>
        <div class="stat-label">Active Interventions</div>
      </div>
    `;
  }

  function triggerCopilotAnalysis() {
    if (window.GayatriUI) {
      window.GayatriUI.showToast("AI Copilot analyzing cohort learning health...", "info");
    }
  }

  return {
    switchTeacherTab,
    renderClassOverview,
    triggerCopilotAnalysis,
  };
})();
