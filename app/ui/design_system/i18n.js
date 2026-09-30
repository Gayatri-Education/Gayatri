/**
 * Gayatri AI Platform — Client-side i18n Controller (Phase 33)
 * Manages translation dictionaries, language switching, DOM translation,
 * and AI language prompt integration.
 */

window.GayatriI18n = (function () {
  'use strict';

  let currentLang = 'en';

  const dictionaries = {
    en: {
      app_title: 'Gayatri AI Platform',
      welcome: 'Welcome back',
      dashboard: 'Dashboard',
      curriculum: 'Curriculum',
      learning_graph: 'Learning Graph',
      progress: 'Progress',
      review_queue: 'Review Queue',
      assignments: 'Assignments',
      assessments: 'Assessments',
      activity: 'Activity',
      profile: 'Profile',
      notifications: 'Notifications',
      class_overview: 'Class Overview',
      students: 'Students',
      learning_health: 'Learning Health',
      interventions: 'Interventions',
      teacher_instructions: 'Teacher Instructions',
      ai_copilot: 'AI Copilot',
      child_progress: 'Child Progress',
      attendance: 'Attendance',
      teacher_updates: 'Teacher Updates',
      recommendations: 'Recommendations',
      fees: 'Fees & Payments',
      fee_setup: 'Fee Setup',
      monthly_billing: 'Monthly Billing',
      student_accounts: 'Student Fee Accounts',
      record_payment: 'Record Payment',
      receipts: 'Receipts Ledger',
      outstanding_reports: 'Outstanding Reports',
    },
    hi: {
      app_title: 'गायत्री एआई प्लेटफॉर्म',
      welcome: 'पुनः स्वागत है',
      dashboard: 'डैशबोर्ड',
      curriculum: 'पाठ्यक्रम',
      learning_graph: 'शिक्षण ग्राफ',
      progress: 'प्रगति',
      review_queue: 'समीक्षा कतार',
      assignments: 'असाइनमेंट',
      assessments: 'मूल्यांकन',
      activity: 'गतिविधि',
      profile: 'प्रोफ़ाइल',
      notifications: 'सूचनाएं',
      class_overview: 'कक्षा अवलोकन',
      students: 'छात्र',
      learning_health: 'शिक्षण स्वास्थ्य',
      interventions: 'हस्तक्षेप',
      teacher_instructions: 'शिक्षक निर्देश',
      ai_copilot: 'एआई सह-पायलट',
      child_progress: 'बच्चे की प्रगति',
      attendance: 'उपस्थिति',
      teacher_updates: 'शिक्षक अपडेट',
      recommendations: 'सिफारिशें',
      fees: 'शुल्क और भुगतान',
      fee_setup: 'शुल्क व्यवस्था',
      monthly_billing: 'मासिक बिलिंग',
      student_accounts: 'छात्र शुल्क खाते',
      record_payment: 'भुगतान दर्ज करें',
      receipts: 'रसीद खाता',
      outstanding_reports: 'बकाया रिपोर्ट',
    },
  };

  // 1. Get Translated String
  function t(key, fallback = '') {
    const dict = dictionaries[currentLang] || dictionaries.en;
    return dict[key] || dictionaries.en[key] || fallback || key;
  }

  // 2. Set Language
  function setLanguage(langCode) {
    if (!['en', 'hi', 'sa', 'ta', 'te', 'kn', 'mr', 'bn'].includes(langCode)) {
      langCode = 'en';
    }
    currentLang = langCode;
    document.documentElement.setAttribute('lang', langCode);
    translateDOM();

    if (window.GayatriUI) {
      window.GayatriUI.showToast(`Language set to ${langCode.toUpperCase()}`, 'info');
    }
  }

  // 3. Get Current Language
  function getLanguage() {
    return currentLang;
  }

  // 4. Translate DOM Elements with [data-i18n]
  function translateDOM() {
    const elements = document.querySelectorAll('[data-i18n]');
    elements.forEach((el) => {
      const key = el.getAttribute('data-i18n');
      if (key) {
        el.textContent = t(key, el.textContent);
      }
    });
  }

  return {
    t,
    setLanguage,
    getLanguage,
    translateDOM,
  };
})();
