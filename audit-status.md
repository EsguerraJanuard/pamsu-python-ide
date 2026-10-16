# PAMS(U) IDE — Frontend Audit Status

_Last updated: 2026-10-16 · Branch: `dev` · Base commit: `b5f111f`_

## Overall progress

**Frontend: nearly production-ready.** The repository-wide frontend audit and hardening pass is complete. What remains is mostly backend work (see "Backend blockers").

- `npm run lint`: PASS (0 problems)
- `npm run build`: PASS. Pages are now loaded per route, which shrank the main bundle from 757 kB to 294 kB and removed the >500 kB warning.
- `git diff --check`: PASS
- Tested in the browser against the local backend with the seeded student, instructor and admin accounts, at desktop width and 375 px.

### Root cause of "Failed to load data"
The backend wasn't running. Once it was started, every student endpoint returned 200. The frontend turned every failure into one generic message, or into a misleading empty state. Pages now tell these apart:
- loading
- empty (no records)
- server unreachable
- timeout
- session expired (401 → back to sign-in with a notice)
- forbidden (403)
- not found (404)
- server error (5xx)

### Key fixes (P0: actions that silently did nothing)
- **Grading bench:** the workspace never found a submission, and grades never saved (it looked up `id` where the data has `student_id`). It also showed a grade suggestion calculated in the browser and a false "Perfect Structure" when no AST data existed. Rebuilt; it saves grades through `PUT` and shows real AST findings, indicators and submitted code.
- **Activity details:** adding a test case always failed with 422 (wrong field names). Delete called `/test-cases/undefined`. The paste toggle sent a field that doesn't exist.
- **Login:** admin accounts were sent to Access Denied. Guest sign-in called a path that doesn't exist (`/auth/guest`).
- **Notifications:** always empty (items were cleared right after loading). Wrong field names. "Mark as read" claimed success even when it failed.
- **Instructor settings:** password change used `POST`, which the backend rejects (405). Fields that were never saved (department, default course, alert toggles) have been removed.
- **Student gradebook modal:** always showed "no records".
- **Class details:** showed a made-up classroom ("Dr. Maria Santos") whenever loading failed.
- **Submission details:** links used the activity id instead of the submission id; every page showed a false "AST FAILED".
- **Submissions:** released grades were fetched but never shown.
- **Class roster:** removing a student took them off the list even when the API call failed. The submissions column was hard-coded to 0.
- **Activity editor:** "Publish immediately" was ignored.
- **Admin dashboard:** the Faculty tab was misplaced and there was no mobile navigation. Fake zero stats were shown when the API failed. Search would crash on a field the API doesn't send.
- **Workspace:** a WebSocket that never worked, Fibonacci placeholder code, no submit confirmation, and misleading sandbox messages.
- **Behaviour tracking hook:** called a route that returns 404 every 5 seconds.

### Native browser UI
`alert()` went from 4 to 0, `confirm()` from 2 to 0, and forms without `noValidate` from 4 to 0. All validation is now shown by the app next to each field, linked for screen readers.

### Theme
- The app is light-only with PSU branding. Tailwind's `dark:` classes followed the computer's dark-mode setting rather than the in-app toggle, so pages were half dark for some users.
- The code editor keeps its own light/dark switch.
- Colours are defined once in `frontend/src/index.css`, together with shared button, card, input and badge styles.

## Files modified (tracked)
```
frontend/src/App.jsx
frontend/src/index.css
frontend/src/services/api.js
frontend/src/hooks/useBehaviorTracking.js
frontend/src/hooks/useEditorSettings.js
frontend/src/components/layout/InstructorSidebar.jsx
frontend/src/components/layout/Sidebar.jsx
frontend/src/components/layout/SignOutModal.jsx
frontend/src/components/layout/Statusbar.jsx
frontend/src/components/modals/AlertModal.jsx
frontend/src/components/modals/BulkEnrollModal.jsx
frontend/src/components/modals/ConfirmationModal.jsx
frontend/src/components/modals/CreateClassModal.jsx
frontend/src/components/modals/EditClassModal.jsx
frontend/src/components/modals/JoinClassModal.jsx
frontend/src/components/modals/StudentGradebookModal.jsx
frontend/src/components/ui/CustomSelect.jsx
frontend/src/features/admin/AdminDashboard.jsx
frontend/src/features/assignments/Assignments.jsx
frontend/src/features/auth/AuthContext.jsx
frontend/src/features/auth/ForgotPassword.jsx
frontend/src/features/auth/Login.jsx
frontend/src/features/auth/ProtectedRoute.jsx
frontend/src/features/auth/Register.jsx
frontend/src/features/auth/RoleRoute.jsx
frontend/src/features/classes/ClassDetails.jsx
frontend/src/features/classes/MyClasses.jsx
frontend/src/features/dashboard/Analytics.jsx
frontend/src/features/dashboard/ClassRosterView.jsx
frontend/src/features/dashboard/InstructorDashboard.jsx
frontend/src/features/dashboard/StudentDashboard.jsx
frontend/src/features/instructor/ActivityDetails.jsx
frontend/src/features/instructor/ActivityEditor.jsx
frontend/src/features/instructor/ClassManagement.jsx
frontend/src/features/instructor/LiveMonitoring.jsx
frontend/src/features/instructor/PracticeModuleManager.jsx
frontend/src/features/instructor/grading/GradingBenchRoot.jsx
frontend/src/features/instructor/grading/GradingClassView.jsx
frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx
frontend/src/features/practice/PracticeWorkspace.jsx
frontend/src/features/practice/SoloPractice.jsx
frontend/src/features/settings/EditorSettings.jsx
frontend/src/features/settings/InstructorSettings.jsx
frontend/src/features/settings/Settings.jsx
frontend/src/features/submissions/SubmissionDetails.jsx
frontend/src/features/submissions/Submissions.jsx
frontend/src/features/theme/ThemeContext.jsx
frontend/src/features/theme/ThemeToggle.jsx
frontend/src/features/workspace/Workspace.jsx
frontend/src/pages/AuditLogsPage.jsx
frontend/src/pages/NotFound.jsx
frontend/src/pages/NotificationsPage.jsx
frontend/src/pages/Unauthorized.jsx
```

## Files created
```
audit-status.md
frontend/src/components/ErrorBoundary.jsx
frontend/src/components/layout/AppSidebar.jsx
frontend/src/components/layout/PageShell.jsx
frontend/src/components/ui/Modal.jsx
frontend/src/components/ui/StateViews.jsx
frontend/src/features/settings/AccountSections.jsx
frontend/src/features/student/ActivityCard.jsx
frontend/src/features/student/studentData.js
frontend/src/features/submissions/submissionData.js
frontend/src/utils/format.js
```
`.claude/launch.json` (local dev-server config) was also created. It is **not** meant to be committed.

## Files deleted (unused; recoverable from git history)
```
frontend/src/App.css
frontend/src/assets/hero.png
frontend/src/assets/react.svg
frontend/src/assets/vite.svg
frontend/src/components/layout/InstructorLayout.jsx
frontend/src/components/layout/Navbar.jsx
```

## Pending tasks / next steps

### Backend blockers (not changed in this pass)
1. `backend/app/main.py` imports `admin` but never calls `app.include_router(admin.router)`, so every `/admin/*` endpoint returns 404. The admin dashboard shows "Administration service unavailable" until this is fixed.
2. `POST /guest` returns 500 with `ModuleNotFoundError: app.core.utils` (in `routers/auth.py`, `login_guest`).
3. `backend/app/routers/users.py` assigns `router` twice, so `PATCH /users/me/integrity` is never registered (404). The frontend no longer calls it.
4. There is no "allow retake" endpoint. The frontend retake buttons were removed rather than left broken.
5. The sign-in response doesn't include `ast_strictness_level`, so instructor settings can't show the saved level until the instructor saves one. A `GET /users/me` endpoint would fix this.
6. Locally, Redis isn't running. Every authenticated request takes 4–8 seconds, execution requests stay queued, and `POST /submissions/` blocks for more than 40 seconds even though the submission is recorded.

### Frontend follow-ups
- Test real code execution, structure checks and grading in a staging environment with Redis and the execution worker running.
- Fully rebuild `PracticeModuleManager.jsx` and `ActivityEditor.jsx` on `PageShell` and the shared form styles; so far they were only patched.
- Remove the unused dependencies `xlsx` and `react-intersection-observer` from `package.json`. Removing them will change `package-lock.json`.
- Decide whether to restore dark mode for the whole app. It is now light-only by design.
- Optional: a toast system for short success messages. Inline alerts are used today.

### Local test data created during QA (seeded QA accounts only)
- Submission #3 for activity 7 by `qa.student`, graded 92 (not released) by `qa.instructor`.
- Two queued "run" execution requests for activity 7.
