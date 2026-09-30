/**
 * Gayatri AI Platform — Socratic Tutor UI Controller (Phase 26)
 * Controls conversation rendering, response actions, learning context panel,
 * intelligent composer, and truthful AI status indicator.
 */

window.GayatriTutor = (function () {
  'use strict';

  // 1. Learning Context Panel Toggle
  function toggleLearningContext() {
    const layout = document.querySelector('.tutor-layout');
    if (layout) {
      layout.classList.toggle('context-collapsed');
      const isCollapsed = layout.classList.contains('context-collapsed');
      localStorage.setItem('gayatri_tutor_context_collapsed', isCollapsed ? 'true' : 'false');
    }
  }

  // 2. Trigger Response Actions
  function triggerResponseAction(actionType, messageId) {
    const actions = {
      explain_simpler: "Could you explain that more simply with an intuitive analogy?",
      give_hint: "Can you give me a small hint without revealing the direct answer?",
      practice: "Can you generate a practice problem to test my understanding?",
      ask_question: "What is another question related to this concept?",
      show_sources: "Please highlight the exact textbook sources for this explanation.",
      copy: null,
    };

    if (actionType === 'copy') {
      const msgBubble = document.querySelector(`[data-message-id="${messageId}"] .chat-message-bubble`);
      if (msgBubble) {
        navigator.clipboard.writeText(msgBubble.innerText);
        if (window.GayatriUI) {
          window.GayatriUI.showToast("Copied to clipboard", "success");
        }
      }
      return;
    }

    const promptText = actions[actionType];
    if (promptText) {
      const composerInput = document.querySelector('.composer-input');
      if (composerInput) {
        composerInput.value = promptText;
        composerInput.focus();
      }
    }
  }

  // 3. Update AI Status
  function updateAIStatus(statusObj) {
    const modelLabel = document.querySelector('.ai-status-model');
    const latencyLabel = document.querySelector('.ai-status-latency');

    if (modelLabel && statusObj.model) {
      modelLabel.innerText = `${statusObj.provider || 'Local'}: ${statusObj.model}`;
    }
    if (latencyLabel && statusObj.latency_ms !== undefined) {
      latencyLabel.innerText = `${statusObj.latency_ms}ms`;
    }
  }

  // 4. Update Learning Context Panel
  function updateLearningContext(contextData) {
    const topicEl = document.querySelector('.context-topic-name');
    const masteryEl = document.querySelector('.context-mastery-score');
    const sourcesContainer = document.querySelector('.sources-list');

    if (topicEl && contextData.topic) {
      topicEl.innerText = contextData.topic;
    }
    if (masteryEl && contextData.mastery !== undefined) {
      const pct = Math.round(contextData.mastery * 100);
      masteryEl.innerText = `${pct}%`;
    }
    if (sourcesContainer && Array.isArray(contextData.sources)) {
      sourcesContainer.innerHTML = contextData.sources.map(src => `
        <div class="source-card-item">
          <strong>${window.GayatriUI ? window.GayatriUI.escapeHtml(src.citation) : src.citation}</strong>
          <p>${window.GayatriUI ? window.GayatriUI.escapeHtml(src.text.slice(0, 100)) : src.text.slice(0, 100)}...</p>
        </div>
      `).join('');
    }
  }

  // Auto-init on DOMContentLoaded
  document.addEventListener('DOMContentLoaded', () => {
    const collapsed = localStorage.getItem('gayatri_tutor_context_collapsed') === 'true';
    const layout = document.querySelector('.tutor-layout');
    if (layout && collapsed) {
      layout.classList.add('context-collapsed');
    }
  });

  return {
    toggleLearningContext,
    triggerResponseAction,
    updateAIStatus,
    updateLearningContext,
  };
})();
