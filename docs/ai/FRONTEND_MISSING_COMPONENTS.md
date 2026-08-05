# PAMSU Frontend: Missing Components Roadmap

Base sa pagsusuri ng **Backend 1.0.0 OpenAPI Contract** at sa mga kasalukuyang files sa `frontend/src/**/*.jsx`, narito ang roadmap ng mga missing components na kailangan pang gawan ng UI sa frontend.

---

## 1. Instructor Management & Grading (High Priority)
*(Backend files: `instructor.py`, `evaluation.py`)*

**Kasalukuyang UI:**
- `InstructorDashboard.jsx` (Pang-display lang ng list ng activities/classrooms)

**Mga Kailangan Pang Gawan (Missing):**
- [ ] **`CreateActivityModal.jsx` / `ActivityEditor.jsx`**
  - **Purpose:** Frontend UI para maka-create ang instructor ng coding tasks, description, at test cases.
  - **Endpoints:** `POST /instructors/tasks/` at `POST /instructors/tasks/{task_id}/test-cases`
- [ ] **`InstructorReviewQueue.jsx`**
  - **Purpose:** Page kung saan makikita ng instructor yung mga pending submissions na kailangan ng manual review/grading.
  - **Endpoint:** `GET /instructors/review-queue`
- [ ] **`InstructorGradebook.jsx`**
  - **Purpose:** Page para makita ang buong gradebook ng isang klase o classroom.
  - **Endpoint:** `GET /instructors/gradebook`
- [ ] **`GradingWorkspace.jsx` / `SubmissionReview.jsx`**
  - **Purpose:** Ang workspace ng instructor para mabasa ang source code ng student, makita ang AST/similarity indicators, at makapag-input ng official manual grade.
  - **Endpoint:** `PATCH /evaluation/submissions/{sub_id}/grade`

---

## 2. Classroom & Enrollment Management
*(Backend files: `classrooms.py`)*

**Kasalukuyang UI:**
- `CreateClassModal.jsx`, `JoinClassModal.jsx`, `ClassRosterView.jsx`

**Mga Kailangan Pang Gawan (Missing):**
- [ ] **`EditClassModal.jsx`**
  - **Purpose:** Para ma-update ng instructor ang classroom details gaya ng pangalan o schedule.
  - **Endpoint:** `PATCH /classrooms/{class_id}`
- [ ] **`EnrollmentManagement.jsx`**
  - **Purpose:** Component sa loob ng class roster para makapag-approve o reject ng pending students na gustong sumali.
  - **Endpoint:** `PATCH /classrooms/enrollments/{enrollment_id}/status`
- [ ] **`ClassroomCodeManager.jsx`**
  - **Purpose:** UI component para mag-regenerate ng invite code ng classroom kapag expired na o kailangan palitan.
  - **Endpoint:** `POST /classrooms/{class_id}/regenerate-code`

---

## 3. Notifications
*(Backend files: `notifications.py`)*

**Kasalukuyang UI:**
- `Navbar.jsx` (Dropdown container lang)

**Mga Kailangan Pang Gawan (Missing):**
- [ ] **`NotificationsPage.jsx`**
  - **Purpose:** Isang dedicated full page para mabasa ng user ang lahat ng read/unread notifications nila na may pagination, at "Mark all as read" button.
  - **Endpoints:** `GET /notifications/` at `PATCH /notifications/read-all`

---

## 4. Audit Records
*(Backend files: `audit_records.py`)*

**Kasalukuyang UI:**
- `Settings.jsx` at `InstructorSettings.jsx` (Ito ay kasalukuyang naka-block sa API contract dahil walang profile update endpoint).

**Mga Kailangan Pang Gawan (Missing):**
- [ ] **`AuditLogsPage.jsx`**
  - **Purpose:** Dedicated page o table layout para ma-display ang history/audit logs ng user system actions.
  - **Endpoint:** `GET /audit-records/`

---

## 5. Authentication & Registration (Kumpleto na ang base UI)
*(Backend files: `auth.py`, `registration.py`)*

**Kasalukuyang UI:**
- `Login.jsx`, `Register.jsx`, `AuthContext.jsx`
- *Note:* Walang major missing frontend files dito. Wala ding "Forgot Password" sa backend API kaya hindi kailangan gawan ng UI sa ngayon. API integration na lang ang kulang (Wiring).

---

## 6. Student Workspace & Execution (Kumpleto na ang base UI)
*(Backend files: `activities.py`, `submissions.py`, `execution.py`, `logs.py`)*

**Kasalukuyang UI:**
- `Workspace.jsx`, `MonacoEditorPane.jsx`, `BehaviorAlert.jsx`, `Submissions.jsx`
- *Note:* Walang major missing frontend files dito. Handa na ang layout para i-wire sa backend. API execution fetching na lang ang kailangan dito.

---

### Suggested Execution Order para sa Frontend Member:
1. **Unahin:** Instructor Management (`ActivityEditor`, `Gradebook`, at `ReviewQueue`) - dahil ito ang main pain point kung paano gagamitin ng guro ang system.
2. **Isunod:** `GradingWorkspace` para makapag-check na sila ng actual code.
3. **Pangatlo:** Tapusin ang mga missing modals sa Classroom (`EditClassModal`, `EnrollmentManagement`).
4. **Huli:** `NotificationsPage` at `AuditLogsPage`.
