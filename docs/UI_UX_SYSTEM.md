# Shared UI Design System & UX Specification — Gayatri AI Platform

## 1. Design Tokens & Theme Engine

The Gayatri UI System utilizes CSS Custom Properties defined in `app/ui/design_system/tokens.css` to drive complete visual consistency and seamless theme switching.

```css
:root {
  /* Surface & Background Tokens */
  --bg-primary: #0f172a;
  --bg-surface: #1e293b;
  --bg-surface-raised: #334155;
  --bg-surface-hover: #475569;

  /* Typography & Border Tokens */
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --text-tertiary: #64748b;
  --border-subtle: #334155;
  --border-strong: #475569;

  /* Brand & Status Tokens */
  --brand-primary: #6366f1;
  --brand-hover: #4f46e5;
  --status-success: #10b981;
  --status-warning: #f59e0b;
  --status-error: #ef4444;
  --status-info: #3b82f6;
}

[data-theme="light"] {
  --bg-primary: #f8fafc;
  --bg-surface: #ffffff;
  --bg-surface-raised: #f1f5f9;
  --text-primary: #0f172a;
  --text-secondary: #475569;
  --border-subtle: #e2e8f0;
}
```

---

## 2. Shared Component Library (`components.css` & `components.js`)

1. **Typography & Layout**: Standardized heading hierarchy (`h1`–`h6`), body text, code blocks, containers.
2. **Buttons & Controls**: Primary, secondary, ghost, icon buttons, loading states, and size variants.
3. **Form Inputs**: Text fields, select dropdowns, textareas, checkboxes, radio buttons with error validation.
4. **Cards & Containers**: Stat cards, summaries, progress bars, timeline widgets, data tables.
5. **Overlay UI**: Accessible modals, slide-out drawers, tooltips, toast notifications, skeleton loaders.
6. **Chat UI**: Bubble messages, socratic hint pills, citation cards, truthful AI status indicators.

---

## 3. Application Shell & Responsiveness

### Shell Architecture (`app/ui/design_system/shell.css` & `shell.js`)
- **Desktop Layout**: Collapsible sidebar (~260px expanded, 64px collapsed), top header with portal navigation, theme toggle, user avatar dropdown, and i18n language picker.
- **Mobile Responsive Layout**: Breakpoint `< 768px` converts sidebar into a touch-friendly slide-out drawer, turns context panels into bottom sheets, and scales tables with horizontal scroll wrappers.

---

## 4. Multi-Portal UI Breakdown

- **Tutor UI (`tutor.css`, `tutor.js`)**:
  - 3-pane responsive layout: Navigation sidebar, central conversation stream with composer, right-hand collapsible learning context panel.
  - Truthful AI status indicator ("Searching course material...", "Evaluating answer...", "Updating learning graph...").
- **Student Portal (`student.css`, `student.js`)**:
  - 10 sub-views: Dashboard summary, curriculum tree, learning graph DAG visualizer, progress analytics, review queue, assignments, assessments, activity stream, profile, and notifications.
- **Teacher Portal (`teacher.css`, `teacher.js`)**:
  - 8 sub-views: Class overview grid, student roster table with health risk indicators, detailed student profiles, intervention builder, assessment authoring, teacher instructions, and AI Copilot.
- **Parent Portal (`parent.css`, `parent.js`)**:
  - 8 sub-views: Child switcher, academic progress summary, attendance status grid, assignments list, assessment performance, teacher update cards, recommendations feed, and fee payment details.
- **Fee Administration UI (`fee_admin.css`, `fee_admin.js`)**:
  - 6 tabs: Overview stats, fee structures setup, monthly billing batch generator, student fee accounts, receipt viewer/printer, and outstanding fee report exporter.

---

## 5. Internationalization (i18n)

Client-side controller `app/ui/design_system/i18n.js` coupled with `central_platform/i18n/registry.py`:
- 8 Supported Languages: English (`en`), Hindi (`hi`), Sanskrit (`sa`), Tamil (`ta`), Telugu (`te`), Kannada (`kn`), Marathi (`mr`), Bengali (`bn`).
- Automatic DOM translation via `data-i18n` attribute scanning.
- English fallback guaranteed for missing key definitions.
