# QA AI Handoff & Testing Checklist
**Project:** Pampanga State University (PSU) Python IDE
**Target Branch:** `dev`

Hello QA! Please review and verify the following major architectural and UI changes that have been implemented and pushed to the `dev` branch.

## 1. Universal Theme & Contrast Polish (Dark/Light Mode)
* **Dynamic Brand Text:** Replaced hardcoded Tailwind colors with native CSS variables (`--text-brand-accent`) in `index.css`. The system now reliably swaps text colors (PSU Maroon `#701d0b` for Light Mode, and PSU Gold `#eeb319` for Dark Mode) to guarantee WCAG compliance.
* **Component De-hardcoding:** Stripped all residual `#10b981` (Emerald) and `#3b82f6` (Blue) hex colors from SVG strokes, borders, and hover states across the application. These now hook directly into the PSU Maroon, Red, and Gold theme variables.
* **Avatar Contrast Standardized:** Fixed a bug where the user initials disappeared in Light Mode. Both Instructor and Student avatars now strictly use a solid `bg-psu-maroon` with `text-white` to ensure high visibility across both themes.

## 2. Instructor Dashboard Overhaul (`InstructorDashboard.jsx`)
* **Decluttering:** Completely removed the "System Audit Trail" panel as requested by the panel to reduce technical clutter and focus on learning metrics.
* **New 'Needs Grading' Panel:** Injected an actionable review list in the right sidebar. It dynamically fetches `reviewQueue.slice(0, 5)` and renders:
  * Student Name and Task Title.
  * A "New" badge for recent submissions.
  * Smart Alerts: Highlights whether the student passed the structural AST rules (Green) or was flagged for high similarity (Red).
  * A "Grade Now" button routing directly to `/instructor/submissions/:id`.

## 3. Smart Activity Creation (Backend & Frontend)
* **Backend AST Engine (`ast_analyzer.py`):** Built a Python AST traversal service that parses an instructor's reference solution. It accurately counts `For`, `While`, `FunctionDef`, `ClassDef`, `With` blocks, and comprehensions.
* **FastAPI Endpoint (`/instructors/tasks/analyze-solution`):** Integrated the analyzer into a secure POST endpoint that returns a computed `difficulty_level` (beginner, intermediate, expert) and a dictionary of `suggested_ast_rules`.
* **Activity Editor UI (`ActivityEditor.jsx`):** 
  * Added the "Smart Activity Generator" component above the starter code.
  * Instructors can paste their reference solution, click "Analyze Solution", and the frontend will automatically populate the AST Compliance Checklist and update the difficulty dropdown based on the API response.
  * Changed the generic "Description" label to "Problem Context / Real-world Scenario" to enforce better pedagogical framing as recommended by the panel.

## Recommended QA Testing Scenarios
1. **Toggle Light/Dark Mode:** Verify that the "MANAGEMENT" category texts and paragraph texts swap correctly between Maroon and Gold without refreshing the page. Verify the initials in the bottom-left avatar remain visible in both modes.
2. **Dashboard State:** Log in as an instructor. Verify that the right sidebar displays the "Needs Grading" list and properly routes to the grading bench.
3. **Smart Activity Generator:** Navigate to Author New Activity. Paste a code block containing a `try/except` or `class` definition. Click Analyze. Verify the difficulty sets itself to "expert" and the corresponding AST rules auto-check themselves.
