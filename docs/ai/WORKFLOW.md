# PAMSU Python IDE — Canonical AI Workflow

## Communication
- Use professional casual Taglish.
- Address the user as **bro**.
- Be exact, calm, and beginner-friendly.
- Work one file or one tightly related module at a time.
- State the exact file path, action, working directory, PowerShell commands, expected result, and one next file.
- When the user says `g`, `ggg`, `go`, `next`, or `proceed`, continue the agreed next step without broad repetitive questions.

## File Rule
Before replacing a complex current file, inspect that file. Ask for only one file at a time when repository access is unavailable. Provide the complete replacement unless a small exact edit is safer.

## Standard Format
```text
Bro, [brief assessment].

File:
backend/app/...

Action:
Replace the entire file.

[complete code]

Run from:
C:\Users\ACER\Documents\Codes\pamsu-python-ide\backend

Commands:
[exact PowerShell commands]

Expected:
[expected output]

Next file:
[one exact path]
```

## Validation Order
From `backend`:
```powershell
.\venv\Scripts\python.exe -m compileall -q app
.\venv\Scripts\python.exe -m pytest tests\<focused_test>.py -q
.\venv\Scripts\python.exe -m pytest -q
```

Distinguish compile/import checks, focused tests, pillar tests, and full regression. Do not claim success without the user's actual output.

## Error Workflow
Classify the error first: command/quoting, syntax, import, schema, database, authorization, response validation, stale test, or application bug. Give one exact correction and rerun the smallest relevant check. Do not move to another pillar while failures remain.

## Test Decision Rule
A failure may indicate a stale test or incorrect application behavior. Compare both against `PROJECT_CONTEXT.md`, `ROADMAP.md`, current models, and current API contracts. Never weaken security, privacy, immutability, ownership, or grading boundaries just to make a test green.

## Git Workflow
From repository root:
```powershell
git switch dev
git pull --ff-only origin dev
git switch -c <local-branch>
```

Never push the local branch. Before commit:
```powershell
git branch --show-current
git status --short
git diff --stat
```

Stage exact files; avoid `git add .`. Commit only after tests pass. Merge locally:
```powershell
git switch dev
git merge --no-ff <local-branch> -m "merge: <description>"
git push origin dev
```

Push only `dev`. Confirm:
```powershell
git status
git log --oneline -5
```

## Completion Gate
A pillar is complete only when implementation, authorization, privacy, transactions, tests, OpenAPI, version, roadmap, handoff, commit, local merge, `dev` push, and clean working tree are all confirmed.
