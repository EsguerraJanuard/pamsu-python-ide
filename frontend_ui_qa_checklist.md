# Frontend UI QA Checklist (November 2026 UI, telemetry and MIS update)

This checklist covers everything pushed to `dev` from 2026-11-02 to 2026-11-04:

| Date | Commits | What |
|---|---|---|
| Nov 2 | `de6a600`, `5d7f903`, `fc5aecb`, `99c1c60` | UI polish, review indicators, telemetry paste counting, color thresholds |
| Nov 4 | `e18299c` | MIS queued enrollments: **Approve all ready** and **Sort by** |
| Nov 4 | `48606c1` | School IDs are 10 digits with no hyphen; placeholders on forms |
| Nov 4 | `045dd99` | Grading Bench card badges; dropdown focus ring; Live Monitoring filters |
| Nov 4 | `b8b3119` | Archived classes left out of the Grading Bench and the Overview counts |
| Nov 4 | `74430e2` | Icons on buttons across the app |
| Nov 4 | (maintenance fix) | Maintenance mode shows an amber notice instead of a server error |

Follow every step in order and tick each box. If a step fails, write it up with the report template at the end. Don't fix anything yourself.

The most important part is **Section 9, the real keyboard check**. Only a person in a real browser can do it.

---

## 0. Before you start

### Where and with what
- [ ] Open the app at **https://pamsu-python-ide.vercel.app**. Press **Ctrl+F5** once to make sure you have the latest version.
- [ ] Use **Google Chrome or Microsoft Edge on a Windows PC** (desktop or laptop, not a phone). Section 9 needs a real browser window, not a preview or embedded browser.
- [ ] Have **three separate browser sessions** ready:
  - **Window A (normal window):** the QA instructor account.
  - **Window B (InPrivate window in Edge, or Incognito in Chrome; Ctrl+Shift+N):** the QA student account.
  - **Window C (the other browser, e.g. Edge if A and B are Chrome):** the MIS admin account (Section 2 only).
  - Why: if you sign in as a different account in another tab of the *same* window, the first tab switches to that account too.
- [ ] Have **Notepad** open (Windows key, type "Notepad", Enter). You will copy text from it.
- [ ] Know how to open the browser console: press **F12**, then click the **Console** tab.

### Is the backend up to date? (decides which steps you can do)
The website (Vercel) updates by itself. The server (Render) updates only when Errol deploys it. Some new features need the updated server.
- [ ] Window C (MIS): sidebar **Students**, scroll down to the **"Queued class enrollments"** card.
  - If it shows a **"Sort by"** dropdown and an **"Approve all ready"** button, the server is updated: do every step.
  - If it does **not**, the server is not updated yet: mark the steps tagged **[needs server update]** as **N/A (server not deployed)** and do the rest.

### Accounts and data (QA only)
- [ ] A **QA instructor** account.
- [ ] A **QA student** account, enrolled in the QA instructor's class.
- [ ] An **MIS admin** account (Section 2). Ask the developer if you don't have one.
- [ ] A **QA class** owned by the QA instructor with:
  - [ ] at least one **published Laboratory activity** that the QA student has **submitted** and that is **not graded yet** (it shows "N to review" on the Grading Bench);
  - [ ] at least one **unpublished (draft) activity** with two test cases (one Sample, one Hidden);
  - [ ] (if possible) one **Homework** activity. The activity editor has no field for picking homework. If no homework activity exists, ask the developer to switch one QA activity to homework, or mark Section 8F as **N/A**.

### Test addresses for the MIS steps
Accounts you create get a real welcome email. Use only these made-up QA values (the emails will bounce, which is fine for a few):

| Use | Email | School ID | Name |
|---|---|---|---|
| Section 2D, queued then created | `qa.pending1@pampangastateu.edu.ph` | `2026000901` | QA Pending One |
| Section 2D, Approve all ready | `qa.pending2@pampangastateu.edu.ph` | `2026000902` | QA Pending Two |
| Section 2A, hyphen test (never created) | `qa.hyphen@pampangastateu.edu.ph` | `2026-00903` | QA Hyphen |

- [ ] **Do not use the defense demo files** (`demo_admin_students`, `demo_admin_faculty`, `demo_teacher_enrollment`) or their names and IDs. Those accounts must not exist before the defense.
- [ ] Write down every account and class you create in the **Sign-off** notes, so the developer can clean up.

### Safety rules
- [ ] Never test on real students' accounts or real classes.
- [ ] **Do not confirm destructive actions** on real data: Remove from class, Suspend account, Reset password, Delete test case. Open the menu or dialog, check it, then press **Esc** or click **Cancel**.
- [ ] Only save grades on QA submissions.
- [ ] **"Approve all ready" acts on every ready row in the whole system**, not only yours. Click it only when the Ready list shows **only QA rows** (Section 2D).

### Where things are
- **Theme switch:** bottom of the left sidebar: three small icons (sun = light, moon = dark, monitor = follow Windows). When the sidebar is collapsed, it is one button that switches Light → Dark → System each time you click it. Do the main pass in **Light**, then the dark pass in Section 11.
- **Sidebar collapse:** the small arrow button at the top of the sidebar.
- **Phone width:** press **F12**, then **Ctrl+Shift+M** (device toolbar) and type width **375**. Press **Ctrl+Shift+M** again to turn it off.

---

## 1. Global styles (any page)

### 1A. One focus ring on form fields
- [ ] Window A (instructor): left sidebar, **Classes**, then open the QA class (**Open roster**).
- [ ] Click inside the **"Search by name, ID or email…"** box.
- [ ] **Expect:** the box border turns maroon (gold in dark mode) with a soft glow around it. There is **only one ring**, with **no second outline** a few pixels outside it.
- [ ] Press **Tab** a few times. Every button or link you reach shows **one** clear outline.
- [ ] Repeat on the Grading Bench **Score** box and **Feedback** box (Section 7D): one ring each.
- [ ] Repeat on the **sign-in page** email and password boxes (use a fresh private window): the whole rounded box gets the ring, and there is no extra inner outline.

### 1B. Buttons: look and feel
- [ ] Find a **secondary button**: white, gray border, dark text, for example **"Bulk enroll"** or **"Class settings"** on the class page.
- [ ] Hover over it. **Expect:** the background gets slightly darker, the border darker, and a small shadow appears.
- [ ] Press and hold the mouse button on it. **Expect:** it shrinks very slightly (a "press" feel). Move the mouse off it before releasing, so nothing is triggered.
- [ ] Find a **primary button**: maroon with white text, for example **"New activity for this class"** on the class page's Activities tab. Hover makes it darker; press makes it shrink slightly.
- [ ] Find a **disabled button**, for example **"Create Activity"** in the Activity Editor before filling the form. **Expect:** it looks faded, does not change on hover and does not shrink on click.

### 1C. Buttons: icons (new, everywhere)
Each action button now has a small icon on the left of its label. For every button below, check:
- the icon sits **centered vertically** with the text, with an even **small gap** between icon and text;
- the icon's lines look **as thick as the letters** (bold enough, not thin and faint);
- the icon is the one listed.

| Where to go | Button | Icon to expect |
|---|---|---|
| Window A, Classes, open the QA class (top right) | **Bulk enroll** | two people |
| same place | **Class settings** | gear |
| same page, **Activities** tab | **New activity for this class** | plus (+) |
| Window A, **Overview** (top right) | **New activity**, **Create class** | plus (+) |
| Window A, **Classes** (top right) | **Create class** | plus (+) |
| Window A, an activity's page (top right) | **Edit activity** | pencil |
| Window A, a draft activity, Test cases | **Add test case** | plus (+) |
| Window A, Activity Editor (bottom bar) | **Create Activity** / **Save Changes** | plus (+) / floppy disk |
| Window A, Grading Bench activity (top right) | **Export grades (CSV)** | download tray |
| Window A, Grading Bench, a student (bottom of the grade card) | **Save grade** | floppy disk |
| Window A, **Live Monitoring** (top right) | **Refresh now** | circular arrow |
| Window A, **Settings**, Change password | **Update password** | key |
| Class page, **Bulk enroll** dialog, Paste emails tab | **Enroll students** | person with + |
| Class page, **Class settings** dialog | **Save details** / **Generate new code** | floppy disk / circular arrow |
| Window C (MIS), Students, Create student account | **Create account** | person with + |
| Window C (MIS), Settings | **Save settings** | floppy disk |
| Window B (student), Dashboard | **Join a class** | plus (+) |
| Window B, an activity's **Session** tab (top toolbar) | **Check structure**, **Run**, **Submit** | check in a circle, play triangle, paper plane |

- [ ] Every row of the table above matches.
- [ ] **Small buttons** (for example **Refresh now** on Live Monitoring, **Generate new code**) have a slightly **smaller icon and a tighter gap** than normal buttons, and still look balanced.
- [ ] **While saving**, the icon is **replaced by a spinning circle**, then comes back. Check on **Save grade** (Section 7D) and **Update password** (only if you really change a QA password).
- [ ] **Plain buttons stay plain:** **Cancel**, **Close**, **OK** and **Done** have **no icon**. Check in: the Bulk enroll dialog (Cancel), the Create class dialog (Cancel, Done), the sign-out dialog (**Close** has no icon; **Sign Out** has an exit-arrow icon), the Activity Editor (**Cancel**).
- [ ] **Back buttons** have a **left arrow (←)**: **"All students"** on the Grading Bench at narrow width (Section 7D), **"Back to assignments"** / **"Back to modules"** on student error pages, the small back button at the top-left of the student workspace on a narrow window.

### 1D. Dropdowns (new style everywhere)
- [ ] Instructor: **Live Monitoring**, click the **Activity** dropdown.
- [ ] **Expect:** a floating white list appears directly under the box, the same width as the box, with a soft shadow. The current choice has a check mark.
- [ ] **While the list is open**, the box itself keeps a **maroon border with a soft maroon glow**, and the small **chevron (⌄) flips upward and turns maroon**.
- [ ] Press **↓** and **↑**: the highlight moves. **Enter** selects; **Esc** closes and keeps the old value.
- [ ] Press **Tab** to move onto the dropdown without opening it. **Expect** the same maroon border and glow (the focus ring).
- [ ] Hover over a closed dropdown: its border gets a little darker.
- [ ] Repeat on **Audit Logs**, the **"All events"** filter.
- [ ] Student (Window B): **Settings**, Editor, **Tab size** dropdown. Same style, choices "2 spaces" / "4 spaces".
- [ ] **No page** should show the plain gray, browser-built-in dropdown anymore.
- [ ] Dark mode is checked in Section 11 (the ring turns **gold** there).

### 1E. Placeholders (light gray example text in empty boxes)
Click into nothing; just look at the **empty** boxes.

| Where | Box | Expect this gray text |
|---|---|---|
| Window C (MIS), Students, **Create student account** | School ID | `e.g. 2026000001` |
| same form | First name / Middle name (optional) / Last name | `e.g. Juan` / `e.g. Dela Cruz` / `e.g. Santos` |
| Window C, **Faculty**, Create faculty account | First / Middle / Last name | same three as above (there is no School ID box for faculty) |
| Window C, Students, a student's **Edit** dialog | names and School ID | same as the create form (visible only if you clear a box) |
| Window A, class page, **Class settings** dialog | Class name / Subject code / Section | `e.g. Computer Programming 1` / `e.g. CCS101` / `e.g. BSCS 1A` (visible only if you clear a box) |
| Window A, a **draft** activity, new test case | Standard input (optional) / Expected output | `Values the program reads, one per line` / `Exactly what the program should print` |
| Any role, **Settings**, Change password | Current / New / Confirm new password | `Enter your current password` / `At least 8 characters` / `Type the new password again` |

- [ ] Every row matches. Note the School ID example is written **`e.g. 2026000001`** (no comma after "e.g."), the same style as all other examples in the app.
- [ ] The gray example text **disappears as soon as you type** and comes back if you clear the box.
- [ ] After checking a box, **clear anything you typed** and leave without saving.

---

## 2. MIS Admin (Window C)

### 2A. School ID: 10 digits, no hyphen
PSU School IDs are always 10 digits with no hyphen. The form and the server now refuse a hyphen.
- [ ] Window C: sidebar **Students**, card **"Create student account"**.
- [ ] School ID placeholder reads **`e.g. 2026000001`** (Section 1E).
- [ ] Type **12345678901** (11 digits) in School ID. **Expect:** the box **stops at 10 characters**.
- [ ] Fill in: University email `qa.hyphen@pampangastateu.edu.ph`, School ID **`2026-00903`**, First name `QA`, Last name `Hyphen`. Click **Create account**.
  - [ ] **Expect** a red message under School ID: **"Enter the 10-digit School ID with no hyphen, e.g. 2026000001."**
  - [ ] **Expect:** no account is created (the Student directory count does not change).
- [ ] Clear the form (delete what you typed).
- [ ] On a phone, the School ID box should bring up the **number keypad** (optional: check on a real phone).
- [ ] **[needs server update]** Masterlist upload with a hyphen:
  - [ ] In Notepad, type these two lines and save as `qa_hyphen.csv` (File, Save as, "All files", UTF-8):
    ```
    email,school_id,first_name,last_name
    qa.hyphen@pampangastateu.edu.ph,2026-00903,QA,Hyphen
    ```
  - [ ] Card **"Bulk register from masterlist"**, **Choose a masterlist file**, pick `qa_hyphen.csv`.
  - [ ] **Expect** a gold message **"0 accounts created, 0 already existed, 1 row failed."** and under it **"Row 2 (qa.hyphen@pampangastateu.edu.ph): School ID must be exactly 10 digits with no hyphen, for example 2026000001."**

### 2B. Name placeholders and Edit dialog
- [ ] Section 1E rows for the create forms and the Edit dialog all match.
- [ ] In a QA student's **Edit** dialog, change the School ID to **`2026-00999`** and click **Save changes**. **Expect** the same red "Enter the 10-digit School ID with no hyphen…" message. Click **Cancel**. Nothing is saved.

### 2C. MIS admin tables
- [ ] **Students** tab: each row has an avatar, a School ID chip, a status pill, an **"Edit"** button and a **⋮** button.
- [ ] Click **⋮** on a QA student. **Expect:** "Re-apply pending enrollments", "Reset password", a divider, then "Suspend account" in red (or "Activate account" in green). Each item has a small explanation under it. Press **Esc**. **Do not click any item.**
- [ ] **Faculty** tab: ⋮ shows "Reset password" and "Suspend account". Press **Esc**.
- [ ] **Audit trail** tab: the **Event**, **Outcome** and **Role** filters and **"Rows per page"** use the new dropdown (Section 1D).
- [ ] Open **Event**. **Expect:** the list **floats over** the edge of the white card and is not cut off. It scrolls when you hold **↓**, and the highlighted item stays visible.
- [ ] Pick an event and check that the table filters. Set it back to "All events".

### 2D. Queued class enrollments (pending students)
**How it works:** when an instructor enrolls an email that has **no account yet**, it is saved in a queue that only MIS sees. When MIS **creates the account**, the student **joins the class automatically**; no extra approval is needed. **"Approve all ready"** is for rows that are left over, for example when the class was archived at the moment the account was created.

**Part 1: an address with no account goes to "Waiting"**
- [ ] Window A (instructor): open the QA class, click **Bulk enroll**, tab **Paste emails**.
- [ ] Paste these two lines and click **Enroll students**:
  ```
  qa.pending1@pampangastateu.edu.ph
  qa.pending2@pampangastateu.edu.ph
  ```
- [ ] **Expect** the result tile **PENDING (NO ACCOUNT) 2** in gold, and a gold note that the addresses have no student account yet. Click **Done**.
- [ ] Window C (MIS): **Students**, scroll to **"Queued class enrollments"**. Click the **"Waiting"** button at the top of the card.
- [ ] **Expect** two rows, one per address. Each row shows:
  - [ ] the **email** in bold;
  - [ ] under it, one gray line: **class name · subject code · section · instructor's name · queued (date)**;
  - [ ] a gold pill **"No account yet"** and a red **"Remove"** button on the right.

**Part 2: Sort by [needs server update]**
- [ ] Above the list there is a **"Sort by"** dropdown (new dropdown style, Section 1D) with exactly these choices: **Newest queued**, **Oldest queued**, **Class (A–Z)**, **Instructor (A–Z)**, **Student email (A–Z)**.
- [ ] Choose **Oldest queued**: `qa.pending1` is above `qa.pending2`. Choose **Newest queued**: the order flips.
- [ ] Choose **Student email (A–Z)**: `qa.pending1` is first.
- [ ] Choose **Class (A–Z)** and **Instructor (A–Z)**: if there are other rows, they regroup by class name / by instructor name in alphabetical order. Rows of the same class stay together.
- [ ] Set it back to **Newest queued**.

**Part 3: creating the account completes the enrollment**
- [ ] Window C, card **"Create student account"**: email `qa.pending1@pampangastateu.edu.ph`, School ID `2026000901`, First name `QA`, Middle name empty, Last name `Pending One`. Click **Create account**.
- [ ] **Expect** a green message: **"Account created for qa.pending1@pampangastateu.edu.ph. …"** ending with **"Added to 1 class that had queued this email."**
- [ ] Queued class enrollments, **Waiting**: `qa.pending1` is **gone**. **Ready to apply** does not list it either. This is correct: it was enrolled at once.
- [ ] Window A: the QA class roster (Students tab) now lists **QA Pending One**.

**Part 4: Approve all ready [needs server update]**
To get a "ready" row, the class must be archived when the account is created, then unarchived.
- [ ] Window A: **Classes**, **Create class**: Class name `QA Queue Test`, Subject code `QA 101`, Section `QA 1-A` (all three are required). Click **Create class**, then **Done**.
- [ ] Open **QA Queue Test**, **Bulk enroll**, **Paste emails**: `qa.pending2@pampangastateu.edu.ph`, **Enroll students**. Expect **PENDING (NO ACCOUNT) 1**. (It is now queued for two classes: the QA class and QA Queue Test.)
- [ ] Back on **Classes**, on the **QA Queue Test** card click **Archive**, then confirm. **Expect** "QA Queue Test was archived. Find it under Archived."
- [ ] Window C: create the account: email `qa.pending2@pampangastateu.edu.ph`, School ID `2026000902`, First name `QA`, Last name `Pending Two`, **Create account**.
  - [ ] **Expect** the green message to say it was **added to 1 class**, and **"1 queued class is inactive or could not be joined and stays pending."**
- [ ] Queued class enrollments, **Waiting**: `qa.pending2` (now shown with the name **QA Pending Two** in bold) for **QA Queue Test**, with a gray pill **"Class archived"**.
- [ ] Window A: **Classes**, tab **Archived**, on **QA Queue Test** click **Unarchive** and confirm.
- [ ] Window C: reload the page (F5), scroll to Queued class enrollments. The **"Ready to apply"** view is selected.
  - [ ] **Expect** a row for **QA Pending Two** / QA Queue Test with a green pill **"Ready"**, an **"Apply"** button and a **"Remove"** button.
  - [ ] The small gray badge at the top says **"1 ready enrollment"**.
  - [ ] The maroon button **"Approve all ready (1)"** (check-in-circle icon) is on the right, above the list.
- [ ] **Safety check:** the Ready list shows **only QA rows**. If any other student is listed, **stop**: click **Apply** on the QA row instead, skip the next three steps and report it.
- [ ] Click **"Approve all ready (1)"**. **Expect** a dialog **"Approve all ready enrollments?"** that says how many enrollments are ready and that addresses with no account are not affected. Buttons: **Cancel** and **Approve all**.
- [ ] Click **Cancel** first: nothing changes. Then click the button again and **Approve all**.
  - [ ] While it works, the button says **"Approving…"** with a spinning icon.
  - [ ] **Expect** a green message: **"Approved 1 queued enrollment for 1 student."**
  - [ ] The Ready view now shows **"Nothing to apply"**, the badge says **"0 ready enrollments"**, and the button is **faded and can't be clicked** (hover: "No queued enrollment is ready to apply").
- [ ] Click **Waiting**: the **"Approve all ready"** button is **not shown** in this view (it only appears in Ready to apply).
- [ ] Window A: open **QA Queue Test**: its roster lists **QA Pending Two**.
- [ ] Write the two QA accounts and the QA Queue Test class in the Sign-off notes.

### 2E. Maintenance mode notice (new)
**Warning:** maintenance mode blocks **every real student** from signing in. Do this part only at a time the team agrees on (not during a class or a deadline), and turn it off again right away. Ten minutes is enough.
- [ ] Window B (student): make sure the QA student is **signed in** and on the Dashboard.
- [ ] Window C (MIS): **Settings**, switch **"Maintenance mode"** on ("Blocks student sign-in. Instructors and MIS keep access."), click **Save settings**. The banner at the top changes to **"Maintenance mode on"**.
- [ ] **Already signed-in student:** Window B, click **Assignments** (or reload the page).
  - [ ] **Expect** an **amber** panel with a **wrench** icon: **"Maintenance in progress"** and "The platform is currently undergoing maintenance. Student access is temporarily paused. Please check back later." with a **Try again** button.
  - [ ] **Not OK:** a **red** panel that says "Server error" or "The server ran into a problem".
- [ ] **Student sign-in:** Window B, sign out, then sign in again with the QA student.
  - [ ] **Expect** an **amber** box above the email field, with a **wrench** icon, saying **"The platform is currently undergoing maintenance. Student access is temporarily paused."** and under it "Please check back later. Instructors and MIS staff can still sign in."
  - [ ] **Not OK:** the **red** box "The server ran into a problem. Please try again shortly."
- [ ] **Guest:** on the same sign-in page click **Continue as Guest Student**. **Expect** the same amber box (not "Guest access is temporarily unavailable").
- [ ] **Wrong password still says so:** type the QA student's email with a wrong password. **Expect** the red **"Invalid email or password."** (maintenance does not hide a wrong password).
- [ ] **Instructor still gets in:** Window A, sign out and sign in again with the QA instructor. It works normally.
- [ ] Window C: switch **Maintenance mode** off, **Save settings**. The banner says **"All services open"**.
- [ ] Window B: sign in with the QA student. It works again.

---

## 3. Instructor: Overview (Window A)
- [ ] Sidebar, **Overview**. **Expect three tiles:** ACTIVE CLASSES, AWAITING REVIEW and PUBLISHED ACTIVITIES. Each has a large number, a small gray caption and a small icon in the top-right corner.
- [ ] **AWAITING REVIEW** caption reads **"In active classes, not yet graded"**, and the tile is tinted **gold** when the number is above 0.
- [ ] Click **anywhere on a tile** (not just the label). **Expect:** it opens Classes or the Grading Bench.
- [ ] Press **Tab** onto a tile. **Expect:** a ring around the **whole tile**.
- [ ] Right side, **"Latest submissions"**: lists up to 5 recent submissions from **active** classes only.
- [ ] Top right: **New activity** and **Create class** have a **+** icon (Section 1C).
- [ ] The archived-class behavior of AWAITING REVIEW is tested in Section 7A.

---

## 4. Instructor: Classes and class page (Window A)

### 4A. Class roster
- [ ] **Classes**, open the QA class, **Students** tab.
- [ ] Top right: **Bulk enroll** (people icon) and **Class settings** (gear icon) look like a matching pair (Section 1C).
- [ ] **Expect in each row:**
  - [ ] a round **avatar with initials** (for example "JD") before the name, with the email under the name;
  - [ ] the **School ID** in a small gray rounded box;
  - [ ] an **Enrollment** badge (Active in green, Paused in gold);
  - [ ] **Session**: "Online" with a green dot, or "Offline";
  - [ ] on the right: a **"Grades"** button with a small chart icon, and a **⋮ (three vertical dots)** button.
- [ ] Above the table, on the right: the count, for example **"9 students"**. While typing in the search box it shows, for example, **"2 of 9 students"**. If someone is online it adds **"· 1 online now"**.
- [ ] The search box has a **magnifying-glass icon** inside on the left.

**⋮ row menu**
- [ ] Click **⋮** on a QA student's row. **Expect** a floating menu with two items:
  - [ ] **"Copy email address"**, with the student's email in small gray text under it;
  - [ ] a thin divider, then **"Remove from class"** in red, with "Their submissions stay on record." under it.
- [ ] Press **Esc**. The menu closes.
- [ ] Keyboard: press **Tab** until the ⋮ button is focused, then press **Enter**. The menu opens with the first item focused. **↓ / ↑** move between items. **Esc** closes it and focus returns to ⋮.
- [ ] Open ⋮ again and click **"Copy email address"**. **Expect** a green message at the top: **"Copied (email)."** Paste in Notepad (Ctrl+V): the email appears.
- [ ] Open ⋮ again and click **"Remove from class"**. **Expect** a confirmation dialog. Click **Cancel**. Do not remove.
- [ ] Scroll the page while the menu is open. **Expect:** the menu closes, so it doesn't float away from its row.

**Sticky header**
- [ ] Make the browser window short (or zoom to 150% with Ctrl and +) so the student list scrolls.
- [ ] Scroll down. **Expect:** the gray header row (STUDENT, SCHOOL ID, ENROLLMENT, SESSION, ACTIONS) **stays pinned at the very top** of the content area. No student rows show above it.
- [ ] Reset the zoom with **Ctrl+0**.

**Phone width (folded columns, no sideways scrolling)**
- [ ] Turn on phone width (Section 0, "Where things are").
- [ ] **Expect:**
  - [ ] **no sideways scrolling**;
  - [ ] the School ID, the Enrollment badge and Online/Offline appear **under the student's name**;
  - [ ] the **Grades** button shows **only the chart icon**.
- [ ] Turn phone width off again.

**Grades dialog**
- [ ] Click **"Grades"** on a QA student who has submitted. **Expect** a dialog with the student's name and a table:
  - [ ] columns **Activity / Status / Grade / Review**;
  - [ ] the grade shown as a large number with "/ 100", and "Released" in green or "Not released" in gray under it;
  - [ ] an **"Open bench"** button with an arrow icon.
- [ ] At phone width: the status badge moves under the activity name and "Open bench" shows only the arrow icon.
- [ ] Close the dialog with **Esc**.

### 4B. Bulk enroll result tiles ("Not a student" label)
- [ ] On the class page click **"Bulk enroll"**, then the **"Paste emails"** tab.
- [ ] Paste these addresses, one per line:
  - the QA student's email (already in the class);
  - **your own QA instructor email** (a faculty account, so not a student).
- [ ] Click **"Enroll students"** (person-with-+ icon).
- [ ] **Expect** a green "Enrollment processed." message and result **tiles**:
  - [ ] **ENROLLED 0**, **PENDING (NO ACCOUNT) 0** and **INVALID 0** in neutral gray;
  - [ ] **ALREADY IN CLASS 1** in neutral gray;
  - [ ] **NOT A STUDENT 1**, tinted **gold**. The label says exactly **"Not a student"**, not "Not a student account".
- [ ] **Expect:** the big numbers in the same row line up at the same height.
- [ ] Under the tiles, a gold note explains the address that belongs to a faculty, admin or guest account.
- [ ] **Done** and **Enroll more** have no icon (plain buttons).

### 4C. Class settings dialog
- [ ] Class page, **Class settings**. The three boxes show the class's current name, subject code and section.
- [ ] Clear the **Class name** box: the gray example **`e.g. Computer Programming 1`** appears. Do the same for Subject code (`e.g. CCS101`) and Section (`e.g. BSCS 1A`).
- [ ] **Close the dialog without saving** (Esc). Reopen it: the real values are back.
- [ ] **Save details** has a floppy-disk icon; **Generate new code** has a circular-arrow icon. **Do not generate a new code** on a class real students use.

### 4D. Audit Logs and Notifications
- [ ] Sidebar, **Audit Logs**. **Expect** a table: **WHEN / EVENT / RESOURCE / OUTCOME**. The resource is a small gray chip (for example "User #1"); the outcome is a colored badge.
- [ ] The **Refresh** button (top right) has a circular-arrow icon that **spins** while "Refreshing…".
- [ ] If there are more than 15 events: the footer says **"Showing 1–15 of N events"**, with **‹** and **›** arrow buttons and "Page 1 of X". Click **›**: it says "Showing 16–30…".
- [ ] At phone width: WHEN and RESOURCE move under the event name; no sideways scrolling.
- [ ] Sidebar, **Notifications**. With more than 10 notifications, the footer shows **"Showing 1–10 of N notifications"** with arrow buttons. **Mark all as read** has a check-mark icon.

---

## 5. Instructor: Activity Editor (Window A)
Use the QA class only. Click **Cancel** at the end unless you mean to create the activity.

- [ ] Sidebar, **New Activity**. **Expect:**
  - [ ] the normal left sidebar and the thin status bar at the bottom of the screen, like other pages;
  - [ ] a header with the small maroon word **"MANAGEMENT"**, the title **"Create New Activity"** and a gray description;
  - [ ] white rounded cards: **Activity Details**, **Starter Code Template** and **Options & Controls**.
- [ ] Every text box and text area has the **same style as other forms** (rounded, gray border) and **one focus ring** when clicked (Section 1A).
- [ ] Code boxes (**Reference solution**, **Expected Output**, **Starter Code Template**) use a **monospace (code) font**.

**Floating save bar**
- [ ] At the bottom of the screen there is a **white bar with a shadow** that stays visible while you scroll.
- [ ] On an empty form it shows a **gold dot** and **"Add a title, a classroom and a difficulty level to continue."** **"Create Activity"** (with a **+** icon) is faded and can't be clicked.
- [ ] Type a title, tick the QA class and pick a difficulty (Beginner). **Expect:** a **green dot** and **"Ready to create."**, and **"Create Activity"** becomes active (maroon).
- [ ] Scroll to the very bottom. **Expect:** the bar sits **below** the last card and does **not cover** the deadline fields.
- [ ] **"Cancel"** is a plain text button with **no icon** and takes you back.

**Keyboard focus on switches**
- [ ] Press **Tab** until you reach **"Publish immediately"** and **"Allow workspace clipboard paste"**. **Expect:** a **visible ring** around the little switch. **Space** turns it on and off.
- [ ] Pick a difficulty first (the AST checklist is locked until you do). Then open any group under **"AST Checklist Requirements"** (click its row) and Tab to a rule switch: same ring.
- [ ] Tab to a classroom in **"Target Classroom(s)"**: a ring around the class row.

**Edit mode**
- [ ] Open an existing QA activity, then **Edit activity** (pencil icon). **Expect:** the title **"Edit Activity"**, the class name in the small header line, the bar saying **"Ready to save."** and the button **"Save Changes"** with a **floppy-disk** icon. Click **Cancel**.

---

## 6. Instructor: Activity Details, test cases and structures (Window A)
- [ ] Open the **draft (unpublished)** QA activity with test cases.
- [ ] Top right: **Edit activity** has a **pencil** icon.
- [ ] Each test case box shows:
  - [ ] a small **number** (1, 2, …) and the case name;
  - [ ] a badge: **"Sample"** with an **eye** icon, or **"Hidden"** with a **crossed-out eye** icon;
  - [ ] two **code panels** side by side, **INPUT** and **EXPECTED OUTPUT**, each with a gray header bar and a **"Copy"** button on the right;
  - [ ] a **"Delete"** button with a trash icon on the right. It appears on draft activities only.
- [ ] Click **Copy** on an Expected output. **Expect:** it changes to a green check and **"Copied"** for about 2 seconds. Paste in Notepad: the exact output appears.
- [ ] A case with no input shows **"(no input)"** in gray italics, and its Copy button is faded and can't be clicked.
- [ ] Click **Delete**. A confirmation appears. Click **Cancel**.
- [ ] **Add a test case form** (draft activities): the empty boxes show the gray examples **"e.g. Small input"** (name), **"Values the program reads, one per line"** and **"Exactly what the program should print"**. The **Add test case** button has a **+** icon. Don't add a case unless you delete it afterwards.
- [ ] Open a **published** activity: the Delete buttons are **not shown**, and a light note under the cases says **"Unpublish the activity to add or delete test cases."**
- [ ] **Required structures** card (right side, or below on narrow screens): each requirement is a **pill** with a small **"<>"** icon. Rules needed more than once show a small maroon **"×2"** (or ×3…) bubble.

---

## 7. Instructor: Grading Bench (Window A)

### 7A. Archived classes are left out (new)
An archived class means its term is over, so it is not part of grading anymore.
- [ ] Sidebar, **Grading Bench**. Write down the header sentence, for example **"3 submissions awaiting review across your active classes."**, and the **"N to review"** number on the QA class card.
- [ ] Sidebar, **Overview**: write down the **AWAITING REVIEW** number.
- [ ] Sidebar, **Classes**: on the **QA class** card click **Archive**, then confirm.
- [ ] **Grading Bench** again:
  - [ ] the **QA class card is gone**;
  - [ ] the header number went **down by the QA class's "N to review"**;
  - [ ] **no card anywhere says "Archived"**.
- [ ] **Overview**: AWAITING REVIEW went down by the same amount, and **Latest submissions** no longer lists the QA class's submissions.
- [ ] Only if the QA instructor has **no other active class**: the Grading Bench shows **"No active classes"**, the text "All your classes are archived, so nothing is waiting on the Grading Bench. Unarchive a class from Classes to grade it here again." and a **Go to classes** button, and the header says **"No active classes to review."**
- [ ] **Classes**, tab **Archived**, on the QA class click **Unarchive** and confirm. (Or click **Undo** in the green message right after archiving.)
- [ ] **Grading Bench** and **Overview**: the QA class card and both numbers are **back** to what you wrote down.

### 7B. Grading Bench home: class cards
- [ ] Each class card shows:
  - [ ] the subject and section badges (for example **"CC 102"** and **"Section BSCS 1-A"**) on the left;
  - [ ] a gold **"N to review"** pill **in the top-right corner** when submissions are waiting;
  - [ ] a **"Submissions reviewed X of Y"** line with a thin maroon progress bar (or "No submissions yet.");
  - [ ] **"Review activities →"** at the bottom. The arrow moves slightly right on hover.
- [ ] Right after the page loads, the bar area may show a gray shimmer for a moment, then the numbers.
- [ ] **Badge layout:** slowly make the browser window narrower (drag its right edge), then switch to phone width.
  - [ ] When the badges run out of room, the **subject and section badges wrap onto a second line on the left**, with an even gap between the lines.
  - [ ] The **"N to review"** pill **always stays in the top-right corner**, on the first line. It never drops to a line of its own.
  - [ ] No badge text is split across two lines inside its pill.

### 7C. Class activity list
- [ ] Click the QA class card. Each **published** activity shows:
  - [ ] a gold **"N to review"** pill when submissions are waiting;
  - [ ] **"Students submitted X of Y"** with a progress bar;
  - [ ] a maroon **"Review submissions"** button.
- [ ] A **draft** activity shows **"Publish to receive submissions"** instead and no bar.

### 7D. Activity bench (review page)
Use a window at least **1024 px wide** (maximized on a laptop) so the student list and the review show side by side.

- [ ] Click **"Review submissions"** on the QA Laboratory activity.
- [ ] **Export grades (CSV)** button (top right):
  - [ ] it has a **download-tray icon**; on hover the little arrow **moves down slightly**;
  - [ ] click it: a small spinner and **"Exporting…"**, then a CSV file downloads. Open it to confirm it has the grades.

**Student list (left)**
- [ ] A search box **"Search name or ID…"** with a magnifying-glass icon. Typing filters the list.
- [ ] Filter chips: **All / To review / Graded / Not submitted**, each with a count.
- [ ] Click **"To review"**. **Expect:** that chip turns **solid maroon with white text**, and the list shows only students waiting for review.
- [ ] Each student row has an **initials avatar**, the name, the ID and a status badge.
- [ ] At a window narrower than 1024 px, after picking a student, an **"All students"** button with a **← arrow** takes you back to the list.

**Review indicators (stat tiles)**
- [ ] Click a QA student who submitted. The **Review indicators** card shows **four tiles**:
  - [ ] **SIMILARITY**: a large number with a small "%", a thin maroon bar and "Highest match with a classmate". It is **never colored**, whatever the number;
  - [ ] **TAB SWITCHES**, **BLOCKED PASTES** and **POINTER EXITS**: a large number, a small icon in a rounded square (top right) and a short gray caption.
- [ ] Under the tiles, click **"How the colors are set"**. **Expect** it to expand and list:
  - Tab switches: **4** and **10** (not colored for homework)
  - Blocked pastes: **1** and **3**
  - Pointer exits: **10** and **25** (not colored for homework)
  - "Similarity is never colored…"
- [ ] (The colors themselves are tested in Section 8.)

**Structure check (AST)**
- [ ] Each required structure is a row: the name, "N found · M needed", and a pill on the right:
  - [ ] **"✓ Found"** (green);
  - [ ] **"× Missing"** (gold);
  - [ ] the header line on the right says, for example, **"3 of 4 found"**.

**Grade and feedback card**
- [ ] The header **"Grade and feedback"** has a status chip on the right: **"Not graded yet"**, **"Saved, not released"** (gold) or **"Released to student"** (green).
- [ ] If not graded yet: a box with a **gold left border** and a lightbulb icon: **"Suggested score: X / 100"** and a short explanation.
- [ ] **Score** box: a large number with **"/ 100"** inside the box on the right. (It has no gray example number on purpose, so it can't be mistaken for a grade.)
- [ ] **Feedback** box: placeholder "What went well, and what to improve next time…" and a counter **"0 / 5,000"** that goes up as you type.
- [ ] The bottom bar (light gray) has the **"Release grade to the student"** switch with a hint under it, and the **"Save grade"** button with a **floppy-disk** icon.
- [ ] On a QA submission: type feedback, turn Release on, click **Save grade**. **Expect:** the icon is replaced by a **spinner** while saving, then a green message, and the chip changes to **"Released to student"**.

### 7E. Code viewer: no console error when switching students
- [ ] Press **F12**, open **Console**, and click the 🚫 (clear) button.
- [ ] Click student **A** (who submitted) and wait until the **"Submitted code"** viewer shows code (left: starter code, right: submitted code).
- [ ] Click student **B**, wait for the code, then **A**, then **B** again.
- [ ] Click **"Back to (class name)"** at the top.
- [ ] **Expect:** **no red error** in the Console that says **"TextModel got disposed before DiffEditorWidget model got reset"**. (Before the Nov 2 update, that error appeared on every switch.)
- [ ] If the window is narrower than 1024 px, use the **"All students"** button to go back to the list between switches. The result must be the same.

---

## 8. Instructor: Live Monitoring and telemetry colors (Windows A and B)

### 8A. Filter dropdowns (new look)
- [ ] Window A: sidebar, **Live Monitoring**.
- [ ] **Labels:** "Activity" and "Class" above the two dropdowns are in **smaller gray text** (quieter than form labels elsewhere).
- [ ] **Dropdowns:** the two boxes are **tall** (about the height of the sign-in boxes), with rounded corners, a light shadow and a **⌄ chevron** on the right. They are the new dropdown (Section 1D), not the browser's plain one.
- [ ] Click **Activity**. **Expect:** a **maroon border and glow** while the list is open; the chevron flips up and turns maroon; choices are "All active sessions" and each activity.
- [ ] Pick an activity. **Expect:** the **Class** dropdown disappears (it only shows with "All active sessions"). Pick **"All active sessions"** again: Class comes back.
- [ ] Desktop: the two dropdowns sit **side by side**. Phone width: they **stack**, full width, Activity above Class.

### 8B. The color rules you are checking

| Indicator | No color (normal) | **Gold, "Above typical"** | **Red, "Well above typical"** | Homework activity |
|---|---|---|---|---|
| Blocked pastes | 0 | 1–2 | 3 or more | Same as laboratory |
| Tab switches | 0–3 | 4–9 | 10 or more | Never colored |
| Pointer exits | 0–9 | 10–24 | 25 or more | Never colored |
| Similarity | always | never | never | never |
| Runs (Live Monitoring) | always | never | never | never |

- [ ] **Every colored tile also shows the words** "Above typical" or "Well above typical", with a small colored dot under the number. **Color is never shown without the words.**

### 8C. Make counts with the QA student (Window B)
- [ ] Window B (student): open the **Laboratory** activity, then **"Start coding"** (Session tab).
- [ ] Open the student's own counts: on smaller screens click **"Indicators"** in the editor toolbar; on very wide screens the **"Session indicators"** panel is already on the right. It lists **Tab switches, Blocked pastes, Pointer left window, Runs this session**. Write down the starting numbers.
- [ ] Counts are sent to the server about every **5 seconds**. Wait 10 seconds before checking the instructor side.

### 8D. Live Monitoring colors (Window A)
- [ ] Window A: **Live Monitoring**. The QA student's card shows **"Live"** while Window B has the workspace open. The page refreshes every 10 seconds (or click **Refresh now**).
- [ ] The card has three small tiles: **TAB SWITCHES, BLOCKED PASTES, RUNS**.
- [ ] **Tab switches.** In Window B, switch to another browser tab and back (or minimize and restore the window) until the student's Tab switches total is **4**.
  - [ ] Window A, after about 10 seconds: TAB SWITCHES is **gold** with **"Above typical"**.
- [ ] Continue to a total of **10**.
  - [ ] TAB SWITCHES is **red** with **"Well above typical"**.
- [ ] **Blocked pastes.** In Window B, do one **outside paste** (Section 9C, step C2).
  - [ ] BLOCKED PASTES is **gold "Above typical"** at 1–2 and **red "Well above typical"** at 3.
- [ ] **RUNS** is **never colored**, however many times you click Run.

### 8E. Grading Bench colors (Window A)
The bench shows the counts of the coding session linked to the submission. The student must have **submitted** the activity at least once.

- [ ] Window A: Grading Bench, the QA class, the Laboratory activity, then the QA student. **Reload the page (F5)** after making new counts.
- [ ] **Expect** the same colors and words as Live Monitoring for **TAB SWITCHES** and **BLOCKED PASTES**.
- [ ] **Pointer exits.** In Window B, move the mouse **out of the browser window** (for example down onto the Windows taskbar) and back in. Repeat until "Pointer left window" is **10**.
  - [ ] Window A (reload): POINTER EXITS is **gold "Above typical"**.
  - [ ] Continue to **25**: POINTER EXITS is **red "Well above typical"**.
  - [ ] Note: moving the mouse up to the browser's own tab bar also counts as leaving the page.
- [ ] **SIMILARITY** stays uncolored.

### 8F. Homework activity
Needs a Homework activity (Section 0). If there is none, mark this part **N/A**.
- [ ] Confirm the activity is homework: on the class page, **Activities** tab, its badge says **"Homework"**.
- [ ] Window B (student): open the homework activity, **Start coding**, then make **10+ tab switches**, **25+ pointer exits** and **1 outside paste**. Submit once.
- [ ] Window A, **Live Monitoring**, the student's card for the homework activity:
  - [ ] TAB SWITCHES shows the number with **no color and no words**, even at 10 or more;
  - [ ] BLOCKED PASTES **is still colored** (gold at 1);
  - [ ] under "Last activity …", the card says **"Homework: tab switches are not colored."** (Live Monitoring does not show pointer exits.)
- [ ] Window A, **Grading Bench**, the homework activity, the student:
  - [ ] TAB SWITCHES and POINTER EXITS have **no color**, even at 10+ / 25+;
  - [ ] BLOCKED PASTES **is still colored**;
  - [ ] under the tiles: **"This is a homework activity, done outside class, so tab switches and pointer exits are shown without color."**

---

## 9. Student Workspace: REAL KEYBOARD CHECK (critical)

**Why this matters:** this is the copy/paste logic. Automated tools cannot press real Ctrl+C / Ctrl+V, so a person must check it in a real browser.

**Setup**
- [ ] Use **real Chrome or Edge on Windows** (Window B, the student).
- [ ] The activity's paste policy must be **"Workspace clipboard only"**. To check: Window A, Activity Details, **Settings** card, **Paste policy**. This is the normal setting.
- [ ] Window B: open the activity, then **"Start coding"**.
- [ ] Open the student's counts ("Indicators" button, or the panel on the right). Write down **Blocked pastes = N**.

### 9A. The student's own copy and paste must work and must NOT count
- [ ] **A1.** Click in the editor and type on a new line:
  ```python
  a = int(input())
  ```
- [ ] **A2.** Select that whole line (drag over it with the mouse, or press **Home** then **Shift+End**).
- [ ] **A3.** Press **Ctrl+C**. **Expect** a short notice: **"Copied to the workspace clipboard."**
- [ ] **A4.** Press **End**, then **Enter** to start a new line, then **Ctrl+V**.
  - [ ] **Expect:** `a = int(input())` is pasted on the new line.
  - [ ] **Expect:** **no** "blocked" message.
  - [ ] **Expect:** Blocked pastes is **still N**.
- [ ] **A5.** Press **Ctrl+V** three more times. The line is pasted each time, and Blocked pastes is **still N**.
- [ ] **A6.** **Cut:** select one of the pasted lines and press **Ctrl+X**.
  - [ ] **Expect:** the line disappears and the notice says **"Moved to the workspace clipboard."**
  - [ ] Press **Ctrl+V**: the line comes back. Blocked pastes is **still N**.
- [ ] **A7.** **Toolbar buttons:** select some code and click the **"Copy"** button in the editor toolbar.
  - [ ] Then press **Ctrl+V** somewhere else: it pastes, and Blocked pastes is **still N**.
  - [ ] Click the toolbar **"Paste"** button: it also pastes, still N.
- [ ] **A8.** **Shift+Insert** (another paste shortcut), after copying inside the editor: it pastes, still N.
- [ ] **A9.** **Moving code by dragging inside the editor:** select a word, then click and drag it to another spot in the same editor.
  - [ ] **Expect:** it moves. Blocked pastes is **still N**.
- [ ] **A10.** Wait 10 seconds. In Window A (Live Monitoring), the student's BLOCKED PASTES has **not gone up**.

### 9B. Code must NOT leave the workspace (no copy-out)
- [ ] **B1.** In the editor, select a line of code and press **Ctrl+C**.
- [ ] **B2.** Switch to **Notepad**, click inside it and press **Ctrl+V**.
  - [ ] **Expect:** **nothing is pasted** (Notepad stays empty, or nothing new appears).
  - [ ] **Not OK:** if the code appears in Notepad, the code leaked out. Report it as a **critical** failure.
- [ ] **B3.** Repeat B1–B2 with the toolbar **"Copy"** button instead of Ctrl+C. Nothing pastes in Notepad.
- [ ] **B4.** Press **Ctrl+F** in the editor (the find box opens with the selected text in it). In the find box press **Ctrl+A** then **Ctrl+C**, then paste in Notepad.
  - [ ] **Expect:** nothing (no code) is pasted.

### 9C. Text from OUTSIDE must be blocked and counted
- [ ] **C1.** In **Notepad**, type:
  ```python
  print("copied from outside")
  ```
  Select it and press **Ctrl+C**.
- [ ] **C2.** Go back to the browser, click in the editor and press **Ctrl+V**.
  - [ ] **Expect:** the text is **NOT inserted**.
  - [ ] **Expect:** the notice says **"Pasting from outside the workspace is blocked. Copying and pasting inside the editor still works."**
  - [ ] **Expect:** Blocked pastes becomes **N + 1**.
- [ ] **C3.** Press **Shift+Insert** with the same Notepad text on the clipboard: blocked, **+1** again.
- [ ] **C4.** If right-clicking in the editor shows a browser menu with **"Paste"**, click it: blocked and counted, like Ctrl+V. (If no menu appears, write "no menu".)
- [ ] **C5.** Copy text from **another website** (any page in another tab), then press **Ctrl+V** in the editor: blocked, **+1**.
- [ ] **C6.** **Problem tab text:** switch to the **Problem** tab, select a sentence of the description, press **Ctrl+C**. Go back to **Session** and press **Ctrl+V**.
  - [ ] **Expected today:** blocked and counted (**+1**). Text from the Problem tab is treated like any outside text.
  - [ ] Write down whether this feels unfair to students; it is a product decision, not a bug.
- [ ] **C7.** **After an outside copy, the student's own copy works again:** copy a line inside the editor with **Ctrl+C**, then **Ctrl+V**. It pastes and is **not** counted. The new inside copy replaces the outside text.

### 9D. Dragging text from outside must be blocked and counted
- [ ] **D1.** In **Notepad**, select some text and **drag it with the mouse** into the editor in the browser.
  - [ ] **Expect:** the text is **NOT inserted**.
  - [ ] **Expect:** the notice says **"Dropping text from outside the workspace is blocked."**
  - [ ] **Expect:** Blocked pastes goes up by **1**.

### 9E. The find box accepts outside text (allowed)
- [ ] **E1.** Copy a word in Notepad. In the editor press **Ctrl+F**, click in the find box and press **Ctrl+V**.
  - [ ] **Expect:** the word appears in the **find box** (searching is allowed). It is **not** put into the code, and Blocked pastes does **not** go up.

### 9F. "No pasting" policy
Only on a QA activity. Set it back afterwards.
- [ ] **F1.** Window A: Activity Details, **Paste policy**, choose **"No pasting"**. **Expect** "Paste policy updated."
- [ ] **F2.** Window B: reload the workspace, then **Start coding**.
  - [ ] **Expect:** the toolbar **"Paste"** button is faded. Its tooltip says "Pasting is turned off for this activity".
- [ ] **F3.** Copy a line inside the editor (**Ctrl+C**) and press **Ctrl+V**.
  - [ ] **Expect:** nothing is pasted, and the notice says **"Pasting is turned off for this activity."**
  - [ ] **Expect:** Blocked pastes does **NOT** go up (it was the student's own code).
- [ ] **F4.** Copy text in Notepad and press **Ctrl+V** in the editor.
  - [ ] **Expect:** blocked, and Blocked pastes goes up by **1**.
- [ ] **F5.** Window A: set the Paste policy back to **"Workspace clipboard only"**.

### 9G. Final count check
- [ ] Add up the counted actions you did in Section 9: C2, C3, C5, C6, D1 and F4 (plus C4 if a menu appeared).
- [ ] The student's **Blocked pastes** should equal **N + that number**. Nothing from 9A, 9B, 9E, F3 or C7 should have counted.
- [ ] Window A (Live Monitoring, and the Grading Bench after a reload) shows the **same number**.

### 9H. Optional: Firefox
- [ ] If any computer lab uses **Firefox**, repeat 9A, 9B and 9C in Firefox and note the results separately.

---

## 10. Student Workspace: Problem tab and toolbar (Window B)
- [ ] Open an activity. It opens on the **Problem** tab (reading view: description, instructions, required structures, sample cases).
- [ ] **Expect on the Problem tab:**
  - [ ] the **code editor is not shown**;
  - [ ] the **"Check structure"**, **"Run"** and **"Submit"** buttons at the top are **faded and cannot be clicked**;
  - [ ] hovering over them shows **"Open the Session tab to run and submit your code."**
- [ ] The three toolbar buttons each have an icon: **Check structure** (check in a circle), **Run** (play triangle), **Submit** (paper plane). They line up evenly.
- [ ] Click **"Start coding"** (or the **Session** tab at the top). The editor appears and the buttons become active.
- [ ] Type some code, switch to **Problem**, then back to **Session**. **Expect:** your code is still there. The editor footer says "draft saved in this browser".
- [ ] Keyboard: click the **Problem** tab button, then press **End**: it switches to Session. Press **Home**: it switches to Problem.
- [ ] Narrow window (below laptop width): a small **← back button** appears at the top left of the workspace; it has an arrow icon and goes back to Assignments.
- [ ] Student **Dashboard**: **Join a class** has a **+** icon. If you have no classes, the empty card's **Enter class code** button has one too.

---

## 11. Dark mode and phone width (quick pass)
- [ ] Switch the theme to **Dark** (bottom of the sidebar) in Windows A and B.
- [ ] **Dropdowns (Live Monitoring, Audit Logs filter):** focused or open, the dropdown now shows a **gold border and gold glow**, clearly visible on the dark background. (Before, the ring was dark maroon and almost invisible.) The open list's selected item is gold.
- [ ] **Button icons** are as visible as the button text in dark mode (Overview, class page, Grading Bench).
- [ ] Grading Bench: the tiles are readable; **gold "Above typical"** and **red "Well above typical"** are clearly readable on the dark background.
- [ ] Grading Bench home: class card badges and the gold **"N to review"** pill are readable, and the pill stays top-right (Section 7B).
- [ ] Class roster: the ⋮ menu, avatars and chips are readable, and the open ⋮ button is highlighted, not a bright white square.
- [ ] Activity Editor: the floating save bar is readable.
- [ ] At **phone width**, Grading Bench student review:
  - [ ] the four tiles are **2 × 2**;
  - [ ] labels wrap onto two lines instead of being cut off (no "TAB SWITC…");
  - [ ] the small icons are hidden;
  - [ ] the big numbers in a row line up.
- [ ] At **phone width**, Live Monitoring: the Activity and Class dropdowns are stacked (Section 8A).
- [ ] Window C (MIS) is always light; at **phone width**, Queued class enrollments: **Sort by** and **Approve all ready** stack full-width above the list.
- [ ] Switch the theme back to what you prefer.

---

## Report template (one entry per problem)

```
Section / step:      (e.g. 9C, step C2)
Page / URL:
Browser + version:   (e.g. Edge 130, Windows 11)
Theme:               Light / Dark
Window size:         Desktop / phone width
Server updated?      Yes / No (Section 0)
What I did:
What I expected:
What happened:
Screenshot / console error:
```

## Sign-off

| Section | Pass / Fail / N/A | Tester | Date | Notes |
|---|---|---|---|---|
| 1. Global styles, icons, dropdowns, placeholders | | | | |
| 2. MIS Admin (School ID, queued enrollments, maintenance notice) | | | | |
| 3. Instructor Overview | | | | |
| 4. Classes and class page | | | | |
| 5. Activity Editor | | | | |
| 6. Activity Details | | | | |
| 7. Grading Bench (incl. archived classes, card badges) | | | | |
| 8. Live Monitoring and telemetry colors | | | | |
| 9. Real keyboard check (critical) | | | | |
| 10. Workspace Problem tab and toolbar | | | | |
| 11. Dark mode and phone width | | | | |

**QA data created (for cleanup):** accounts `qa.pending1`, `qa.pending2`; class `QA Queue Test`; anything else:
