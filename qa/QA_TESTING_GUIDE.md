# PAMS(U) IDE: QA Testing Guide

This guide is for the two QA testers of the PAMS(U) Python IDE. You'll run your own private copy of the system on your computer, use it the way a real admin, instructor and student would, and write down:

- **bugs and logical errors:** something works wrong, shows wrong numbers, lets the wrong person do something, or loses data;
- **UI and usability problems:** confusing, ugly, hard to read, or broken on a phone screen;
- **suggestions:** anything that would make it clearer, faster or friendlier.

You don't need to know how to code. Follow the steps in order and copy the commands exactly.

**Time needed:** about 45 minutes for the one-time setup, then about 3–4 hours of testing.
**Questions or blockers:** message Januard.

---

## 0. Golden rules (read before anything else)

1. **Test only on your own copy**, at `http://localhost:5174`.
   - **Never** test on the live site (`pamsu-python-ide.vercel.app`) or any link ending in `.vercel.app`. Those use the **real** database and real accounts.
2. **Use only the fake QA accounts and made-up data.**
   - No real names, real student numbers, real email addresses or your own passwords.
   - Every email you type must end in `@pampangastateu.edu.ph`, but make it up, for example `qa.test5@pampangastateu.edu.ph`.
3. **Don't change the code, and don't commit or push anything.** If you think the code should change, write it in your report.
4. **Report everything,** even if you're not sure it's a bug. Januard decides what's important.
5. Keep screenshots inside the team. Don't post them publicly.

---

## 1. Install the tools (one time)

You need four programs. If you already have one, skip it.

| Program | Why | Download |
|---|---|---|
| **Git** | Downloads the project | https://git-scm.com/download/win |
| **Python 3.13** | Runs the backend (server) | https://www.python.org/downloads/ (choose a **3.13.x** version) |
| **Node.js (LTS)** | Runs the frontend (website) | https://nodejs.org (click the **LTS** button) |
| **Google Chrome** | For testing | https://www.google.com/chrome |

### 1.1 Git
1. Download from the link above and run the installer.
2. Click **Next** on every screen (the default options are fine), then **Install**.

### 1.2 Python 3.13
1. On the Python downloads page, find a **Python 3.13.x** release (not 3.14, not 3.12), then choose **Windows installer (64-bit)**.
2. Run it. **On the first screen, tick ☑ "Add python.exe to PATH"**, then click **Install Now**.

### 1.3 Node.js
1. On nodejs.org, download the **LTS** version (22.12 or newer).
2. Run the installer and click **Next** on every screen.

### 1.4 Check that everything installed
1. Press the **Windows key**, type `PowerShell`, and open **Windows PowerShell**.
   - **All commands in this guide go into PowerShell.** To paste, **right-click** inside the window, then press **Enter**.
2. Run these one at a time. Each should print a version number:
   ```powershell
   git --version
   ```
   ```powershell
   py -3.13 --version
   ```
   ```powershell
   node -v
   ```
   - `py -3.13 --version` should print `Python 3.13.x`.
   - `node -v` should print `v22.12` or higher.

   If you see "is not recognized", close PowerShell, open it again, and retry. If it still fails, see **Troubleshooting** at the end.

---

## 2. Download the project (one time)

In PowerShell:
```powershell
cd $HOME\Documents
```
```powershell
git clone https://github.com/EsguerraJanuard/pamsu-python-ide.git
```
```powershell
cd pamsu-python-ide
```
```powershell
git checkout dev
```
The project is now in **Documents\pamsu-python-ide**. From now on, every command assumes you are in that folder. If you open a new PowerShell window, go there first:
```powershell
cd $HOME\Documents\pamsu-python-ide
```

---

## 3. Install the project's parts (one time)

### 3.1 Backend (about 5–10 minutes)
Run these one at a time and wait for each to finish:
```powershell
py -3.13 -m venv backend\venv
```
```powershell
.\backend\venv\Scripts\python.exe -m pip install --upgrade pip
```
```powershell
.\backend\venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```
The last one prints a lot of text. It's done when you see `Successfully installed ...` and the prompt comes back.

### 3.2 Frontend (about 3–5 minutes)
```powershell
cd frontend
```
```powershell
npm ci
```
```powershell
cd ..
```
Warnings in yellow are normal. Red `ERR!` lines are not; see Troubleshooting.

### 3.3 Create your test database and accounts
```powershell
.\backend\venv\Scripts\python.exe qa\qa_setup.py
```
It prints four test accounts:

| Role | Email |
|---|---|
| Admin (MIS) | `qa.admin@pampangastateu.edu.ph` |
| Instructor | `qa.instructor@pampangastateu.edu.ph` |
| Student 1 | `qa.student1@pampangastateu.edu.ph` |
| Student 2 | `qa.student2@pampangastateu.edu.ph` |

- **The passwords are random**, different on each computer. They're printed on screen and saved in a file. To open the file:
  ```powershell
  notepad qa\.qa-data\accounts.txt
  ```
- This database lives only on your computer (`qa\.qa-data\qa.db`). You can't break anything real.

---

## 4. Start the system (every testing session)

You need **two PowerShell windows** open side by side. Keep both open while you test.

**Window 1: the backend (server)**
```powershell
cd $HOME\Documents\pamsu-python-ide
```
```powershell
.\backend\venv\Scripts\python.exe qa\run_backend.py
```
Wait until you see `Application startup complete.` Leave this window open.

**Window 2: the frontend (website)**
1. Open a **second** PowerShell window (Windows key → `PowerShell`).
2. Run:
   ```powershell
   cd $HOME\Documents\pamsu-python-ide
   ```
   ```powershell
   .\backend\venv\Scripts\python.exe qa\run_frontend.py
   ```
3. Wait until you see `Local: http://localhost:5174/`.

**Open the app:** in Chrome, go to **http://localhost:5174**.

**To stop:** click each PowerShell window and press **Ctrl + C**. Closing the windows also works.

**Tip: two people at once.**
- To be the instructor and a student at the same time, use a normal Chrome window for one and an **Incognito window** (**Ctrl + Shift + N**) for the other. Microsoft Edge also works as a third.
- Each window keeps its own sign-in.

**Red text in Window 1 is often normal.** Lines about **Redis** or the **execution queue** are expected on a local copy (see section 6). Real problems appear as an error in the website.

---

## 5. Before each session: get the latest version

Stop both windows (Ctrl + C), then in one window:
```powershell
cd $HOME\Documents\pamsu-python-ide
```
```powershell
git pull
```
```powershell
.\backend\venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```
```powershell
cd frontend
```
```powershell
npm ci
```
```powershell
cd ..
```
Then start the system again (section 4).

**Starting over with an empty database:**
1. Stop Window 1.
2. Run:
   ```powershell
   .\backend\venv\Scripts\python.exe qa\qa_setup.py --reset
   ```
3. Your old test data is gone, and the **passwords change**. Check `accounts.txt` again.

---

## 6. What does NOT work on your local copy (don't report these)

Some parts need outside services that only the live server has. **Don't report these as bugs:**

| You'll see | Why |
|---|---|
| **Run** in the workspace says "The execution queue is unavailable…" | The code runner (Judge0) and Redis aren't on your computer |
| **Practice → Run & check** says "The code runner is unavailable right now…" | Same reason |
| On the instructor's grading page: similarity "Not computed", "No structure analysis has been recorded" | That runs in a background worker that isn't on your computer. The **Check structure** button in the workspace *does* work |
| **No emails arrive** ("Forgot password?" says a code was sent, but nothing comes) | Email sending is switched off locally on purpose |
| Live monitoring always shows students as **Offline** | Online status needs Redis |
| Audit-trail times are **8 hours behind** | A quirk of the local test database only |
| You're asked to sign in again after **30 minutes** | Normal: sessions expire after 30 minutes |
| "Too many sign-in attempts" after about 10 wrong passwords in a minute; Guest refused after 2 tries in a minute | Normal protection. Wait a minute |

**Not built yet (don't report as missing):**
- AI tutor and hints;
- retakes;
- dark mode on admin and login pages (light only by design);
- creating more admins from the app.

**Do report:**
- if any of the messages above are **confusing**;
- if the page **freezes** or shows a blank screen;
- if a **submission is lost** (Submit should still save even though Run can't execute).

---

## 7. Who tests what

| Tester | Main area (about 2.5 hours) | Then swap (about 45 minutes) |
|---|---|---|
| **Tester A** | Admin (section 8A) + Instructor (8B) | Quick pass of 8C and 8D |
| **Tester B** | Student (8C) + Guest (8D) + Everything else (8E) | Quick pass of 8A and 8B |

Many tests need two roles, for example the instructor publishes and the student sees it. Use the normal + Incognito trick from section 4. Coordinate in your group chat if you test together.

---

## 8. Test checklists

For each item: **do it, compare with "should"**, then tick ☑ or write a report (section 10). The **"should"** describes what the design intends. If it behaves differently, that's a finding.

### 8A. Admin / MIS (sign in as `qa.admin`)
- [ ] **A1 Overview.** The counts of instructors, students and classrooms match what you created. Re-check after each step below.
- [ ] **A2 Create a faculty account** (Faculty tab).
  - Use a made-up email like `qa.teacher2@pampangastateu.edu.ph`.
  - Try a `@gmail.com` email, empty fields, and the same email twice.
  - **Should:** bad input is refused with a clear message, and the temporary password is shown once.
  - Then sign in as that instructor in Incognito.
- [ ] **A3 Create a student account** (Students tab).
  - Try wrong school IDs (`123`, `abcd`, `2026-1`), a duplicate email, and a duplicate school ID.
  - **Should:** valid formats are 10 digits or `####-#####`, and duplicates are refused.
- [ ] **A4 Masterlist import.**
  1. Open **Notepad** and paste this:
     ```
     email,school_id,name
     qa.mlist1@pampangastateu.edu.ph,2026000101,QA Masterlist One
     qa.mlist2@pampangastateu.edu.ph,2026000102,QA Masterlist Two
     qa.mlist3@gmail.com,2026000103,Wrong Domain
     qa.mlist4@pampangastateu.edu.ph,12345,Bad School ID
     qa.mlist2@pampangastateu.edu.ph,2026000105,Duplicate Email
     ,2026000106,Missing Email
     ```
  2. **File → Save As**:
     - set "Save as type" to **All files**;
     - name it `qa-masterlist.csv`;
     - set Encoding to **UTF-8**.
  3. Upload it in **Students → Bulk register from masterlist**.
  4. **Should:**
     - `qa.mlist1` is created;
     - every other row fails with a reason and its row number (both `qa.mlist2` rows fail, because the email appears twice);
     - no password is shown or emailed.
  5. Upload the **same file again**. **Should:** `qa.mlist1` is reported as "already existed", not duplicated.
- [ ] **A5 Reset password** on a student row, then sign in as that student with the new password.
- [ ] **A6 Suspend** a student. **Should:** they can't sign in ("This account is inactive."). **Activate** them again; they can sign in.
- [ ] **A7 Settings → Maintenance mode ON.** **Should:** students can't sign in, instructors can. Turn it **OFF** again.
- [ ] **A8 Settings → Default AST strictness.** Change it, save, and reload the page. **Should:** your choice is kept.
- [ ] **A9 Settings → Change password.**
  - **Should:** you're signed out, the new password works, and the old one doesn't.
  - Write the new password in `accounts.txt` so you don't lose it.
- [ ] **A10 Audit trail.** Your sign-ins and failed sign-ins appear.
- [ ] **A11 Search and Export CSV** on the Students tab. The file opens in Excel with the right people.

### 8B. Instructor (sign in as `qa.instructor`)
- [ ] **B1 Dashboard.** The numbers (classes, awaiting review, published activities) are correct after each step below.
- [ ] **B2 Create a class.** Then try **Class settings** (edit name and section), **Copy** the enrollment code, and **Archive** a test class.
  - **Should:** archived classes stop accepting new students.
- [ ] **B3 Bulk enroll → Paste emails.** Paste:
  ```
  qa.student2@pampangastateu.edu.ph
  qa.newkid@pampangastateu.edu.ph
  qa.instructor@pampangastateu.edu.ph
  notanemail
  ```
  - **Should:**
    - student2 is enrolled;
    - `qa.newkid` is "pending" (no account yet);
    - the instructor is "not a student account";
    - the bad line is invalid.
  - **Then:** as **admin**, create a student with email `qa.newkid@…`. **Should:** they're automatically added to the class.
- [ ] **B4 Create an activity** (New Activity).
  - Try saving with required fields empty.
  - Choose a difficulty: the AST checklist unlocks.
  - Try **Publish immediately** on and off, a **scheduled publish date** a few minutes ahead, a **due date** in the past and in the future, and both paste policies.
  - **Should:** students see it only when it's published.
- [ ] **B5 Test cases** on the activity page: add, edit and delete visible and hidden cases. **Should:** you must unpublish before editing them.
- [ ] **B6 Practice modules:** create a module, add tasks, edit, reorder, delete. **Should:** students see them under Solo Practice.
- [ ] **B7 Grading bench.**
  1. Open a student's submission.
  2. Try scores of `-1`, `101`, `abc` and blank. **Should:** refused.
  3. Save **without** "Release". **Should:** the **student does NOT see the grade**.
  4. Save **with** "Release". **Should:** the student sees the grade and gets a notification.
  5. Also try **Export grades (CSV)**.
- [ ] **B8 Roster:** **Remove** a student from a class. **Should:** they lose access to the class activities. Also try the **Grades** button.
- [ ] **B9 Settings:** change your AST strictness and your password; switch the theme Light / Dark / System.
- [ ] **B10 Notifications and Audit logs pages** load and make sense.
- [ ] **B11 Unpublish** an activity a student already submitted to. What does the student see? Is anything lost?

### 8C. Student (sign in as `qa.student1`; use `qa.student2` as the second student)
- [ ] **C1 Join a class** with the enrollment code (Dashboard → Join a class).
  - Try a wrong code and a code you already joined.
  - **Should:** clear messages each time.
- [ ] **C2 Dashboard, Assignments, My classes, Class details.** Activities, due dates and counts are correct. Check the **filters**.
- [ ] **C3 Workspace** (open an activity):
  - write code, then try **Check structure** (should list found and missing structures) and **Run** (expected message, see section 6);
  - **Submit** and confirm, then submit **again**. **Should:** the newest attempt becomes "official";
  - try pasting from outside when the activity blocks pasting. **Should:** blocked, with a message;
  - reload the page. Is your code still there? Note what happens;
  - try the editor settings (font size, word wrap).
- [ ] **C4 Submissions** list and details. **Should:** the grade appears only after the instructor releases it.
- [ ] **C5 Notifications:** read, unread, mark all as read.
- [ ] **C6 Solo Practice:** open a module, read the lesson, start the challenge, and see whether later tasks unlock in order.
- [ ] **C7 Analytics:** the numbers make sense compared with what you did.
- [ ] **C8 Settings:** change your password (you're signed out, and the new one works). Profile details are read-only.
- [ ] **C9 Dark mode:** switch Light / Dark / System with the sidebar buttons, and visit **every** student page in dark mode. Look for unreadable text, white boxes and invisible icons.
- [ ] **C10 Late work:** ask the instructor to set a due date in the past. What happens when you try to submit? Is the message clear?

### 8D. Guest
- [ ] **D1** On the sign-in page, click **Continue as Guest Student**.
  - **Should:** you land in the "Guest Sandbox Classroom" only.
- [ ] **D2** As a guest, try to **join a real class** with its code. **Should:** refused, with a clear reason.
- [ ] **D3** Visit every page a guest can see. Is anything confusing, or does it show things that only make sense for real students?

### 8E. Everyone: checks across the whole system
- [ ] **E1 Wrong-role pages.**
  - Signed in as a **student**, type these into the address bar: `http://localhost:5174/instructor/dashboard` and `http://localhost:5174/admin/dashboard`.
  - As an **instructor**, try `/admin/dashboard`.
  - **Should:** blocked ("Unauthorized"), with **no** private data shown, not even for a second.
- [ ] **E2 Sign out, then press the browser Back button.** **Should:** no private page or data is shown.
- [ ] **E3 Phone size.**
  1. Press **F12**, then **Ctrl + Shift + M**.
  2. Choose **iPhone SE** at the top.
  3. Visit every page.
  - **Should:** no cut-off text, no sideways scrolling, no overlapping buttons, and menus reachable.
- [ ] **E4 Keyboard only.** Use only **Tab**, **Shift + Tab**, **Enter** and **Esc** on sign-in, dialogs and forms. Can you always see where you are? Do dialogs close with Esc?
- [ ] **E5 Server down.**
  1. Stop Window 1 (Ctrl + C) while using the app.
  2. Click around. **Should:** clear "server unavailable" messages, never a blank white page.
  3. Start Window 1 again. **Should:** the app recovers with **Retry** or a reload.
- [ ] **E6 Strange input** everywhere you can type:
  - very long text (paste 300+ characters);
  - emoji 😀;
  - accents (`Peña`, `José`);
  - spaces before or after text;
  - HTML like `<b>hi</b>` (it should show as plain text, not bold);
  - very long code (500+ lines).
- [ ] **E7 Double-click** Create, Save and Submit buttons quickly. **Should:** nothing gets created twice.
- [ ] **E8 Refresh** (F5) in the middle of filling a form or a dialog. What happens?
- [ ] **E9 Browser zoom 200%** (Ctrl + +). Is the layout still usable?
- [ ] **E10 Words.** Spelling, grammar, the same thing called by different names, unclear buttons, missing "Are you sure?" before destructive actions.

---

## 9. What counts as a "logical error"? Some ideas

- A number that doesn't match reality (a count, score, attempt number or date).
- Someone can see or do something they shouldn't. For example:
  - a student seeing an unreleased grade;
  - a student seeing another class;
  - a guest joining a real class.
- An action says "success" but nothing changed, or the change disappears after a reload.
- An action changed something it shouldn't have, like the wrong student or class.
- Steps in a strange order break things (unpublish after submissions, remove a student who has a grade, archive a class with activities).
- Two windows disagree, for example an instructor change that the student never sees, even after a reload.
- Time-related problems: due dates, scheduled publishing, "late" labels.

**UI suggestions are welcome too:**
- confusing wording;
- too many clicks;
- important information hidden;
- missing empty states or confirmations;
- text that's hard to read (contrast, size);
- layouts that feel cluttered.

---

## 10. How to report

Make **one file per tester**, named for example `QA-findings-YourName.md` (a Word or Google Doc is fine too), and send it to Januard. **Don't put it in the project folder or commit it.**

Take screenshots with **Windows + Shift + S** and paste them into your document, or save them with clear names like `BUG-03.png`.

### Bug template
```
### BUG-01: <short title, e.g. "Unreleased grade visible to student">
- Account/role: student (qa.student1)
- Page (URL): http://localhost:5174/student/submissions
- Steps:
  1. ...
  2. ...
- Should happen:
- Actually happened:
- Severity: P0 / P1 / P2 / P3   (see the table below)
- Every time? Yes / Sometimes / Only once
- Screenshot: BUG-01.png
- Server error (if any): copy the last ~20 red lines from Window 1
```

### UI suggestion template
```
### UI-01: <short title>
- Page (URL):
- What's confusing or hard now:
- Suggestion:
- How important: High / Medium / Low
```

### Severity
| Level | Meaning | Example |
|---|---|---|
| **P0 Critical** | Data lost or wrong, a security or permission problem, or the app crashes | A student sees another student's grade; a submission disappears |
| **P1 Major** | A main feature doesn't work and there's no workaround | Can't create a class; the grade doesn't save |
| **P2 Minor** | Works, but wrong, misleading or confusing | Wrong count on the dashboard; unclear error message |
| **P3 Cosmetic** | Looks off but works | Misaligned button; typo; poor contrast |

**If you find a P0, message Januard right away.** Don't wait for the final report.

---

## 11. Troubleshooting

| Problem | Fix |
|---|---|
| `git`, `py` or `node` "is not recognized" | Close PowerShell and open it again. If it still fails, reinstall that program; for Python, tick **"Add python.exe to PATH"** |
| `py -3.13` says no such version | Install **Python 3.13** (section 1.2). Other versions may fail to install the packages |
| `pip install` shows red errors | Make sure the venv was made with `py -3.13` (section 3.1). If needed, delete the `backend\venv` folder and redo section 3.1 |
| `npm ci` shows `ERR!` about the Node version | Install the current **Node.js LTS** (22.12 or newer) and retry |
| "No QA database yet" | Run section 3.3 |
| "The frontend packages are not installed yet" | Run section 3.2 |
| "address already in use" or "Port 5174 is in use" | Another window is already running it. Close all PowerShell windows, or restart the PC, then start again |
| Website says "Cannot reach the server" | Window 1 (backend) isn't running or has stopped. Start it again (section 4) |
| "Invalid email or password" with a QA account | Check `notepad qa\.qa-data\accounts.txt`. After `--reset` the passwords change |
| Blank white page | Press **F12** → **Console**, screenshot the red text, and report it as a bug |
| `git pull` complains about local changes | Run `git stash`, then `git pull` again. You weren't supposed to change files, so this is safe |

---

## 12. When you're done

1. Press **Ctrl + C** in both PowerShell windows.
2. Send your findings file and screenshots to Januard.
3. Leave the project folder as it is. **Don't commit or push.**

Thank you for testing! 🙏
