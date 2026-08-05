### 6. `EditClassModal.jsx` (Classroom Settings)
* **Purpose:** Modal/dialog box for updating classroom details.
* **UI Requirements:**
  * Form inputs for `class_name` (Text) and `schedule` (Text).
  * "Save Changes" and "Cancel" buttons.
  * "Regenerate Invite Code" action button.
* **Backend API Target:** `PATCH /classrooms/{class_id}`

### 7. `EnrollmentManagement.jsx` (Student Approvals)
* **Purpose:** Component mounted inside `ClassRosterView.jsx` (e.g., as a "Pending Requests" tab) to manage students joining via invite code.
* **UI Requirements:**
  * Table/List displaying Student Name and Email.
  * Action buttons per row: **Approve** and **Reject**.
* **Backend API Target:** `PATCH /classrooms/enrollments/{enrollment_id}/status` *(Payload: `{"status": "approved" | "rejected"}`)*

### 8. `NotificationsPage.jsx` (System Alerts)
* **Purpose:** Standalone page (`/notifications`) for viewing all read/unread system alerts.
* **UI Requirements:**
  * Clean list view of notifications.
  * Unread state highlighting (`is_read = false`).
  * "Mark all as read" button at the top.
  * Pagination or "Load more" functionality.
* **Backend API Targets:** `GET /notifications/` and `PATCH /notifications/read-all`

### 9. `AuditLogsPage.jsx` (Security History)
* **Purpose:** Standalone page (`/audit-logs`) tracking account history and system actions.
* **UI Requirements:**
  * Data table with columns: **Action**, **Resource**, **IP Address**, and **Timestamp**.
  * Search bar / Filter dropdown (e.g., filter by action type).
* **Backend API Target:** `GET /audit-records/`
