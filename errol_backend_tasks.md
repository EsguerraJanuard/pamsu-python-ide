# Backend Development Tasks (Errol)

This document contains the official backend requirements based on the signed Capstone Panel Recommendations. Please process these with your AI agent to update the FastAPI backend.

## 1. Core Evaluation Logic Restructuring
The panel explicitly requested a separation between structural checking (AST) and behavioral checking (Telemetry).

* **AST-Based Auto-Grading:**
  * Update the grading algorithm: If a student's code satisfies all required AST rules (e.g., loops, functions, specific syntax), the system MUST automatically award the corresponding full score for the structural portion.
  * Stop relying purely on input/output matching. The AST is now the primary basis for the code authenticity score.
* **Telemetry & Behavioral Indicators:**
  * Telemetry data (paste events, tab switches, idle time) should **NO LONGER** automatically deduct points from the student's grade.
  * Instead, expose these telemetry flags via a separate API endpoint for the instructor.
  * The instructor will use this data as a basis for **manual review and manual point deduction**.

## 2. Smart Activity Creation (AI/Algorithm)
The panel requested that the system automatically identify the difficulty and required constructs when an instructor creates an activity.

* **Create a new endpoint:** `POST /instructors/tasks/analyze-solution`
* **Input:** The reference solution (Python code) provided by the instructor.
* **Logic Requirements:**
  * Use Python's built-in `ast` module to parse the provided reference code.
  * Auto-detect the presence of `For`, `While`, `FunctionDef`, `ClassDef`, `With` (file handling), etc.
  * **Difficulty Algorithm:** 
    * Return `beginner` if only basic operations/variables/prints are used.
    * Return `intermediate` if loops or basic functions are used.
    * Return `expert` if file handling, classes, or recursive functions are used.
* **Output:** A JSON response containing the detected `difficulty_level` and a list of `suggested_ast_rules` that the frontend can auto-populate.

## 3. Authentication & Super Admin Provisioning
The panel requested the complete removal of open student registration and emphasized centralized system management.

* **Role-Based Access Control (RBAC):**
  * Add a new `superadmin` or `mis` role to the database.
* **Faculty Provisioning:**
  * Create an endpoint for the Super Admin to register instructors directly. Instructors can no longer sign up publicly.
  * The endpoint must strictly validate emails to follow the official university format (e.g., `@pampangastateu.edu.ph`).
* **Student Invitation Codes / Class Roster:**
  * Create backend logic for instructors to generate unique "Invitation Codes" or "Class Links" for their classrooms.
  * Students will use this code to join a class, or the MIS can batch-upload a CSV of official students.
* **Guest Account:**
  * Create a temporary provisioning endpoint for "Guest Accounts" as requested by Panel 3.

## 4. Security & Refactoring
* **Hide API Keys:** Ensure zero API keys (if any are used for external AI or services) are sent to the client. Keep them strictly in the backend `.env`.
* **Password Encryption:** Double-check that all provisioning endpoints hash passwords using bcrypt before saving to the database.
* **Data Privacy:** Ensure the backend does not expose unnecessary sensitive account information in standard API calls.
