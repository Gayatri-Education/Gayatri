/**
 * Gayatri AI Platform — Student Portal UI Controller (Phase 27)
 * Controls tab switching for Dashboard, Curriculum, Learning Graph, Progress,
 * Review Queue, Assignments, Assessments, Activity Stream, Profile, and Notifications.
 */

window.GayatriStudent = (function () {
  'use strict';

  let currentTab = 'dashboard';

  // 1. Switch Tab
  function switchStudentTab(tabName) {
    const validTabs = [
      'dashboard', 'curriculum', 'learning_graph', 'progress',
      'review_queue', 'assignments', 'assessments', 'activity',
      'profile', 'notifications'
    ];
    if (!validTabs.includes(tabName)) return;

    currentTab = tabName;

    // Update tab buttons
    const buttons = document.querySelectorAll('.student-tab-btn');
    buttons.forEach((btn) => {
      if (btn.getAttribute('data-tab') === tabName) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    // Update view panels
    const views = document.querySelectorAll('.student-view-panel');
    views.forEach((panel) => {
      if (panel.id === `view-${tabName}`) {
        panel.style.display = 'block';
      } else {
        panel.style.display = 'none';
      }
    });
  }

  // 2. Render Functions
  function renderDashboardStats(stats) {
    const container = document.querySelector('.student-dashboard-grid');
    if (!container || !stats) return;

    container.innerHTML = `
      <div class="stat-card">
        <div class="stat-value">${stats.mastery_pct || 0}%</div>
        <div class="stat-label">Overall Concept Mastery</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">${stats.review_due_count || 0}</div>
        <div class="stat-label">Review Items Due</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">${stats.assignments_pending || 0}</div>
        <div class="stat-label">Pending Assignments</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">${stats.streak_days || 0} Days</div>
        <div class="stat-label">Learning Streak</div>
      </div>
    `;
  }

  function renderReviewQueue(items) {
    const list = document.querySelector('.review-queue-list');
    if (!list || !Array.isArray(items)) return;

    if (items.length === 0) {
      list.innerHTML = `<div class="empty-state"><div class="empty-state-title">No review items due!</div></div>`;
      return;
    }

    list.innerHTML = items.map(item => `
      <div class="review-item-card">
        <div>
          <strong>${window.GayatriUI ? window.GayatriUI.escapeHtml(item.concept_name) : item.concept_name}</strong>
          <div class="caption">Retainability: ${Math.round(item.retainability * 100)}%</div>
        </div>
        <button class="btn btn-primary btn-sm" onclick="window.GayatriStudent.startReview('${item.concept_id}')">Review Now</button>
      </div>
    `).join('');
  }

  function startReview(conceptId) {
    if (window.GayatriUI) {
      window.GayatriUI.showToast(`Starting review for ${conceptId}`, 'info');
    }
  }

  return {
    switchStudentTab,
    renderDashboardStats,
    renderReviewQueue,
    startReview,
  };
})();
