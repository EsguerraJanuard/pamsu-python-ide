# UI Development Tasks (Items 6-9)

Here are the remaining UI components that need to be developed. Please ensure they match the uniform dark theme design of the system (using `bg-[#0f1117]`, `slate-900/50`, etc.) and handle their own layout wrappers as established.

### 6. Student Classes List (`/student/classes`)
- **Description:** A page where students can view their enrolled classes and join new ones.
- **Key Features:**
  - A form/input field to enter a 6-character instructor code to join a classroom.
  - A grid or list view of currently enrolled classes.
- **API Endpoints (Reference):**
  - `POST /classrooms/join`
  - `GET /classrooms/mine`

### 7. Student Classroom Details (`/student/classes/:id`)
- **Description:** The detailed view of a specific classroom for a student.
- **Key Features:**
  - Display the class name, subject code, and instructor details.
  - A list of active laboratory activities and announcements specific to this class.
- **API Endpoints (Reference):**
  - `GET /classrooms/{id}`
  - `GET /activities/` (filtered by class)

### 8. Student Solo Practice (`/student/practice`)
- **Description:** An independent coding sandbox for students to practice Python without it being graded.
- **Key Features:**
  - A code editor interface (similar to the Workspace but simplified).
  - Ability to run code and see output directly.
  - No AST monitoring or strict requirements checking.

### 9. Student Submission Details (`/student/submissions/:id`)
- **Description:** A page for students to review a past graded submission.
- **Key Features:**
  - Read-only view of their submitted code.
  - Display AST feedback, passed/failed test cases, and execution output.
  - Display the final instructor grade and feedback (if available).
- **API Endpoints (Reference):**
  - `GET /submissions/{id}`

---
*(Note: An additional Placeholder exists for `/instructor/classes` - Class Management, which may also need to be built if not already handled).*
