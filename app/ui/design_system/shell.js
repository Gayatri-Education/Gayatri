/**
 * Gayatri AI Platform — Application Shell Controller (Phase 25)
 * Handles sidebar toggling, user menu dropdown, portal navigation,
 * theme selection, and multi-language switching.
 */

window.GayatriShell = (function () {
  'use strict';

  let currentLanguage = 'en';
  const supportedLanguages = [
    { code: 'en', name: 'English' },
    { code: 'hi', name: 'Hindi (हिंदी)' },
    { code: 'sa', name: 'Sanskrit (संस्कृतम्)' },
    { code: 'ta', name: 'Tamil (தமிழ்)' },
    { code: 'te', name: 'Telugu (తెలుగు)' },
    { code: 'kn', name: 'Kannada (கன்னட)' },
    { code: 'mr', name: 'Marathi (मराठी)' },
    { code: 'bn', name: 'Bengali (বাংলা)' },
  ];

  // 1. Sidebar Toggle
  function toggleSidebar() {
    const sidebar = document.querySelector('.app-sidebar');
    if (sidebar) {
      sidebar.classList.toggle('collapsed');
      const isCollapsed = sidebar.classList.contains('collapsed');
      localStorage.setItem('gayatri_sidebar_collapsed', isCollapsed ? 'true' : 'false');
    }
  }

  // 2. User Menu Dropdown
  function toggleUserMenu() {
    const menu = document.querySelector('.user-menu-dropdown');
    if (menu) {
      menu.classList.toggle('active');
    }
  }

  // Close dropdown on outside click
  document.addEventListener('click', (e) => {
    const wrapper = document.querySelector('.user-menu-wrapper');
    if (wrapper && !wrapper.contains(e.target)) {
      const menu = document.querySelector('.user-menu-dropdown');
      if (menu) menu.classList.remove('active');
    }
  });

  // 3. Language Selector
  function setLanguage(langCode) {
    const valid = supportedLanguages.some((l) => l.code === langCode) ? langCode : 'en';
    currentLanguage = valid;
    document.documentElement.setAttribute('lang', valid);
    localStorage.setItem('gayatri_language', valid);
    
    // Update select element if present
    const langSelect = document.querySelector('.language-selector');
    if (langSelect) langSelect.value = valid;
  }

  function getLanguage() {
    return currentLanguage;
  }

  // 4. Portal Navigation
  function navigateToPortal(portalName) {
    const validPortals = ['student', 'teacher', 'parent', 'admin'];
    if (!validPortals.includes(portalName)) return;

    window.location.href = `${portalName}_portal.html`;
  }

  // Auto-init on DOMContentLoaded
  document.addEventListener('DOMContentLoaded', () => {
    // Restore sidebar state
    const collapsed = localStorage.getItem('gayatri_sidebar_collapsed') === 'true';
    const sidebar = document.querySelector('.app-sidebar');
    if (sidebar && collapsed) {
      sidebar.classList.add('collapsed');
    }

    // Restore language state
    const savedLang = localStorage.getItem('gayatri_language') || 'en';
    setLanguage(savedLang);
  });

  return {
    toggleSidebar,
    toggleUserMenu,
    setLanguage,
    getLanguage,
    navigateToPortal,
    supportedLanguages,
  };
})();
