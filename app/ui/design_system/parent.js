/**
 * Gayatri AI Platform — Parent Portal UI Controller (Phase 29)
 * Controls child selection, tab navigation (Progress, Attendance, Assignments,
 * Assessments, Teacher Updates, Recommendations, Fees, Notifications).
 */

window.GayatriParent = (function () {
  'use strict';

  let currentChildId = 'child-01';
  let currentTab = 'progress';

  // 1. Select Child
  function selectChild(childId) {
    currentChildId = childId;
    const pills = document.querySelectorAll('.child-pill');
    pills.forEach((p) => {
      if (p.getAttribute('data-child-id') === childId) {
        p.classList.add('active');
      } else {
        p.classList.remove('active');
      }
    });

    if (window.GayatriUI) {
      window.GayatriUI.showToast(`Switched view to child: ${childId}`, 'info');
    }
  }

  // 2. Switch Tab
  function switchParentTab(tabName) {
    const validTabs = [
      'progress', 'attendance', 'assignments', 'assessments',
      'teacher_updates', 'recommendations', 'fees', 'notifications'
    ];
    if (!validTabs.includes(tabName)) return;

    currentTab = tabName;

    // Update tab buttons
    const buttons = document.querySelectorAll('.parent-tab-btn');
    buttons.forEach((btn) => {
      if (btn.getAttribute('data-tab') === tabName) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    // Update view panels
    const views = document.querySelectorAll('.parent-view-panel');
    views.forEach((panel) => {
      if (panel.id === `parent-view-${tabName}`) {
        panel.style.display = 'block';
      } else {
        panel.style.display = 'none';
      }
    });
  }

  return {
    selectChild,
    switchParentTab,
  };
})();
