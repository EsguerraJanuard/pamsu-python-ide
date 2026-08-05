# SYSTEM MAPPING: Backend to Frontend
**Target Audience:** Frontend Developer & AI Assistant
**Goal:** A clean, 1-to-1 mapping of backend endpoints to their required frontend components to easily identify what needs to be built and wired.

---
## Authentication & Registration (✅ UI Complete, Missing API Wiring)
**Backend File(s):** `auth.py`, `registration.py`

| Status | Endpoint | Frontend File | Description |
|---|---|---|---|
| ✅ Existing | `POST /login` | `frontend/src/features/auth/Login.jsx` | Login Form |
| ✅ Existing | `POST /registration/start` | `frontend/src/features/auth/Register.jsx` | Register Step 1 (Request OTP) |
| ✅ Existing | `POST /registration/verify` | `frontend/src/features/auth/Register.jsx` | Register Step 2 (Verify OTP) |
| ✅ Existing | `POST /registration/resend` | `frontend/src/features/auth/Register.jsx` | Resend OTP button |
| ✅ Existing | `N/A (Global State)` | `frontend/src/features/auth/AuthContext.jsx` | JWT Session Storage & Provider |

## Classroom Management
**Backend File(s):** `classrooms.py`

| Status | Endpoint | Frontend File | Description |
|---|---|---|---|
| ✅ Existing | `GET /classrooms/` | `frontend/src/features/dashboard/InstructorDashboard.jsx` | List instructor classrooms |
| ✅ Existing | `POST /classrooms/` | `frontend/src/components/modals/CreateClassModal.jsx` | Create a new classroom |
| ✅ Existing | `GET /classrooms/mine` | `frontend/src/features/dashboard/StudentDashboard.jsx` | List enrolled classrooms |
| ✅ Existing | `POST /classrooms/join` | `frontend/src/components/modals/JoinClassModal.jsx` | Student joins classroom using code |
| ✅ Existing | `GET /classrooms/{class_id}` | `frontend/src/features/dashboard/ClassRosterView.jsx` | View classroom details |
| ❌ Missing | `PATCH /classrooms/{class_id}` | `frontend/src/components/modals/EditClassModal.jsx` | Edit classroom name/schedule |
| ✅ Existing | `GET /classrooms/{class_id}/members` | `frontend/src/features/dashboard/ClassRosterView.jsx` | List students and instructors in class |
| ❌ Missing | `PATCH /classrooms/enrollments/{enrollment_id}/status` | `frontend/src/features/dashboard/EnrollmentManagement.jsx` | Approve/Reject pending students |
| ❌ Missing | `POST /classrooms/{class_id}/regenerate-code` | `frontend/src/features/dashboard/ClassroomCodeManager.jsx` | Regenerate invite code |

## Instructor Activities & Evaluation (🚨 Major Missing UI)
**Backend File(s):** `instructor.py`, `evaluation.py`

| Status | Endpoint | Frontend File | Description |
|---|---|---|---|
| ✅ Existing | `GET /instructors/tasks/` | `frontend/src/features/dashboard/InstructorDashboard.jsx` | List instructor's created activities |
| ❌ Missing | `POST /instructors/tasks/` | `frontend/src/features/assignments/ActivityEditor.jsx` | Create a new coding activity |
| ❌ Missing | `PATCH /instructors/tasks/{task_id}` | `frontend/src/features/assignments/ActivityEditor.jsx` | Update existing activity |
| ❌ Missing | `PATCH /instructors/tasks/{task_id}/publication` | `frontend/src/features/assignments/ActivityEditor.jsx` | Publish/Unpublish activity |
| ❌ Missing | `POST /instructors/tasks/{task_id}/test-cases` | `frontend/src/features/assignments/ActivityEditor.jsx` | Create activity test cases |
| ❌ Missing | `DELETE /instructors/test-cases/{test_case_id}` | `frontend/src/features/assignments/ActivityEditor.jsx` | Delete a test case |
| ❌ Missing | `GET /instructors/review-queue` | `frontend/src/features/dashboard/InstructorReviewQueue.jsx` | List submissions waiting for manual grading |
| ❌ Missing | `GET /instructors/gradebook` | `frontend/src/features/dashboard/InstructorGradebook.jsx` | Class gradebook view |
| ❌ Missing | `GET /evaluation/submissions/{sub_id}` | `frontend/src/features/submissions/GradingWorkspace.jsx` | View specific student submission code & AST |
| ❌ Missing | `PATCH /evaluation/submissions/{sub_id}/grade` | `frontend/src/features/submissions/GradingWorkspace.jsx` | Input official manual grade |
| ❌ Missing | `PATCH /evaluation/submissions/{sub_id}/status` | `frontend/src/features/submissions/GradingWorkspace.jsx` | Update review status |

## Student Activities & Execution
**Backend File(s):** `activities.py`, `submissions.py`, `execution.py`

| Status | Endpoint | Frontend File | Description |
|---|---|---|---|
| ✅ Existing | `GET /activities/` | `frontend/src/features/dashboard/StudentDashboard.jsx` | List available activities for student |
| ✅ Existing | `GET /activities/{task_id}` | `frontend/src/features/assignments/Assignments.jsx` | View activity details |
| ✅ Existing | `GET /activities/{task_id}/sample-test-cases` | `frontend/src/features/workspace/Workspace.jsx` | Load public test cases |
| ✅ Existing | `POST /activities/coding-sessions/` | `frontend/src/features/workspace/Workspace.jsx` | Start coding session |
| ✅ Existing | `PATCH /activities/coding-sessions/{session_id}/activity` | `frontend/src/features/workspace/Workspace.jsx` | Update coding telemetry (keystrokes, etc) |
| ✅ Existing | `POST /execution/requests/` | `frontend/src/features/workspace/Workspace.jsx` | Run code in sandbox (Execution) |
| ✅ Existing | `GET /execution/requests/{execution_id}` | `frontend/src/features/workspace/Workspace.jsx` | Poll execution status |
| ✅ Existing | `POST /submissions/` | `frontend/src/features/workspace/Workspace.jsx` | Submit code for grading |
| ✅ Existing | `GET /submissions/` | `frontend/src/features/submissions/Submissions.jsx` | List my past submissions |
| ✅ Existing | `GET /activities/released-grades` | `frontend/src/features/dashboard/StudentDashboard.jsx` | List grades released by instructor |

## Notifications & Audit
**Backend File(s):** `notifications.py`, `audit_records.py`

| Status | Endpoint | Frontend File | Description |
|---|---|---|---|
| ❌ Missing | `GET /notifications/` | `frontend/src/pages/NotificationsPage.jsx` | List all notifications (Read/Unread) |
| ✅ Existing | `GET /notifications/unread-count` | `frontend/src/components/layout/Navbar.jsx` | Notification badge count |
| ❌ Missing | `PATCH /notifications/read-all` | `frontend/src/pages/NotificationsPage.jsx` | Mark all as read |
| ❌ Missing | `GET /audit-records/` | `frontend/src/pages/AuditLogsPage.jsx` | List user account audit trails |

## Reports & Telemetry
**Backend File(s):** `reporting.py`, `logs.py`

| Status | Endpoint | Frontend File | Description |
|---|---|---|---|
| ✅ Existing | `GET /reports/students/me/progress` | `frontend/src/features/dashboard/Analytics.jsx` | Student progress stats |
| ❌ Missing | `GET /reports/classrooms/{class_id}/gradebook.csv` | `frontend/src/features/dashboard/InstructorGradebook.jsx` | Download gradebook CSV |
| ✅ Existing | `POST /logs/behavioral/` | `frontend/src/hooks/useBehaviorTracking.js` | Send behavioral events (Paste, Tab switch) |
