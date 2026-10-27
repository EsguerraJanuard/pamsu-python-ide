"""Automatic activity difficulty: the analyzer, the shared levels and the
create/update validation.

Levels (lowest at which a rule may be required) are defined once per side:
RULE_LEVELS in app/services/ast_analyzer.py and the groups in
frontend/src/utils/astRules.js. A test below keeps the two identical.
"""

import re
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.models.domain_models import Classroom, Task, User
from app.services.ast_analyzer import (DESCRIPTION_PATTERNS, RULE_LEVELS,
                                       SOLUTION_SUGGESTIBLE_RULES,
                                       analyze_activity, rules_above_level)
from app.services.ast_evaluator import SUPPORTED_AST_RULES

DOMAIN = "@pampangastateu.edu.ph"
ASTRULES_JS = Path(__file__).resolve().parents[2] / "frontend" / "src" / "utils" / "astRules.js"


# ---------------------------------------------------------------- levels


def test_rule_levels_cover_every_evaluator_rule():
    canonical = {name for name in SUPPORTED_AST_RULES if name not in ("require_function", "require_class")}
    assert set(RULE_LEVELS) == canonical
    assert set(SOLUTION_SUGGESTIBLE_RULES) <= set(RULE_LEVELS)
    assert set(DESCRIPTION_PATTERNS) <= set(RULE_LEVELS)


@pytest.mark.skipif(not ASTRULES_JS.exists(), reason="frontend checkout not present")
def test_rule_levels_match_the_activity_editor_groups():
    source = ASTRULES_JS.read_text(encoding="utf-8")
    groups = source.split("export const AST_GROUPS", 1)[1].split("];", 1)[0]
    editor_levels = {}
    for block in re.findall(r"levels:\s*\[([^\]]*)\],\s*rules:\s*\[(.*?)\]", groups, re.S):
        lowest = re.findall(r'"(\w+)"', block[0])[0]
        for rule in re.findall(r'id:\s*"(\w+)"', block[1]):
            editor_levels[rule] = lowest
    assert editor_levels == RULE_LEVELS


def test_seed_activities_meet_their_rule_levels():
    # seed.py writes these straight to the database, past the API check.
    import seed_content

    too_low = {
        key: rules_above_level(template.difficulty, template.rules)
        for key, template in seed_content.ACTIVITIES.items()
        if rules_above_level(template.difficulty, template.rules)
    }
    assert too_low == {}


# ---------------------------------------------------------------- analyzer


@pytest.mark.parametrize(
    "text",
    [
        "Ask the user for a number. If the number is negative, display 'Invalid input'. Otherwise print its square.",
        "Write a program that raises a number to the power of 2 and prints the result.",
        "Library fines: ask for the number of days a book is late and print the fine.",
        "In this module you will practice conditionals. Ask for a grade and print Passed or Failed.",
        "Define a variable named total, add the two numbers the user enters, and print the total.",
        "Use a for loop to print the numbers 1 to 10. Save your file as lab3.py.",
    ],
)
def test_everyday_beginner_wording_stays_beginner(text):
    assert analyze_activity(description=text)["difficulty_level"] == "beginner"


@pytest.mark.parametrize(
    ("text", "rule", "level"),
    [
        ("Import the math module and print the square root.", "require_import", "expert"),
        ("Use the random module to pick a number.", "require_import", "expert"),
        ("Raise a ValueError when the age is negative.", "require_raise_statement", "expert"),
        ("Read the names from a text file and count them.", "require_open_call", "intermediate"),
        ("Write the results to a file named scores.txt.", "require_open_call", "intermediate"),
        ("Handle errors so the program runs without crashing.", "require_try_except", "expert"),
    ],
)
def test_explicit_wording_is_still_detected(text, rule, level):
    result = analyze_activity(description=text)
    assert rule in result["suggested_ast_rules"]
    assert result["difficulty_level"] == level


@pytest.mark.parametrize(
    ("code", "level", "rule"),
    [
        ("scores = [90, 85]\nfor s in scores:\n    print(s)\n", "intermediate", "require_list"),
        ("seen = {1, 2}\nprint(3 in seen)\n", "intermediate", "require_set"),
        ("x = 5\nassert x > 0\nprint(x)\n", "expert", "require_assert_statement"),
        ("async def main():\n    await other()\n", "expert", "require_async_function"),
    ],
)
def test_solution_constructs_set_the_level(code, level, rule):
    result = analyze_activity(reference_code=code)
    assert result["difficulty_level"] == level
    assert rule in result["suggested_ast_rules"]


def test_noise_constructs_do_not_raise_the_level():
    # Calls, tuples (a, b = b, a) and a standard-library import appear in
    # beginner work, so they do not count.
    code = "import math\na, b = 1, 2\na, b = b, a\nprint(math.sqrt(a + b))\n"
    result = analyze_activity(reference_code=code)
    assert result["difficulty_level"] == "beginner"
    assert result["suggested_ast_rules"] == {}


def test_analyzer_level_matches_its_own_suggestions():
    # The difficulty is the highest level among the suggested rules, so
    # applying the suggestions never leaves the checklist above the level.
    code = "def total(xs):\n    return sum(xs)\nprint(total([1, 2]))\n"
    result = analyze_activity(reference_code=code)
    levels = {RULE_LEVELS[rule] for rule in result["suggested_ast_rules"]}
    assert result["difficulty_level"] == "intermediate"
    assert "intermediate" in levels and "expert" not in levels


# ---------------------------------------------------------------- API


def make_user(db: Session, *, email: str, role: str, school_id: str) -> User:
    user = User(
        name="Test User",
        email=email,
        role=role,
        school_id=school_id,
        password_hash=get_password_hash("Original#2026"),
        email_verified=True,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def instructor(db_session):
    user = make_user(db_session, email=f"faculty{DOMAIN}", role="instructor", school_id="9000000002")
    classroom = Classroom(
        instructor_id=user.user_id,
        name="Programming 1",
        subject_code="CCS101",
        section="BSIT 1A",
        class_code="CLASSA01",
        is_active=True,
    )
    db_session.add(classroom)
    db_session.commit()
    return {
        "headers": {"Authorization": f"Bearer {create_access_token({'sub': str(user.user_id)})}"},
        "class_id": classroom.class_id,
    }


def create(client, instructor, **fields):
    payload = {"title": "Loops", "class_ids": [instructor["class_id"]], **fields}
    return client.post("/instructors/tasks/", headers=instructor["headers"], json=payload)


def stored_difficulty(db_session, task_id: int) -> str:
    db_session.expire_all()
    return db_session.get(Task, task_id).difficulty


@pytest.mark.parametrize(
    ("rules", "expected"),
    [
        ({}, "beginner"),
        ({"require_for_loop": {"required": True, "min_count": 2}}, "beginner"),
        ({"require_for_loop": True, "require_function_def": 1}, "intermediate"),
        ({"require_class": True}, "expert"),
        ({"require_class_def": {"required": False}}, "beginner"),
    ],
)
def test_create_without_difficulty_sets_it_from_the_rules(client, db_session, instructor, rules, expected):
    response = create(client, instructor, required_ast_rules=rules)
    assert response.status_code == 201, response.text
    task = response.json()[0]
    assert task["difficulty"] == expected
    assert stored_difficulty(db_session, task["task_id"]) == expected


def test_create_keeps_a_higher_difficulty_chosen_by_hand(client, db_session, instructor):
    response = create(client, instructor, difficulty="expert", required_ast_rules={"require_for_loop": True})
    assert response.status_code == 201, response.text
    assert stored_difficulty(db_session, response.json()[0]["task_id"]) == "expert"


def test_create_refuses_a_difficulty_below_the_rules(client, db_session, instructor):
    response = create(
        client,
        instructor,
        difficulty="beginner",
        required_ast_rules={"require_for_loop": True, "require_class_def": True, "require_dict": True},
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "class definition (Expert)" in detail and "dictionary literal (Intermediate)" in detail
    assert "Set the difficulty to Expert" in detail
    assert db_session.query(Task).count() == 0


@pytest.mark.parametrize(
    ("rules", "message"),
    [
        ({"require_goto": True}, "not a supported AST rule"),
        ({"require_for_loop": "yes"}, "must be a boolean, integer, or dictionary"),
        ({"require_for_loop": {"required": True, "min_count": -1}}, "non-negative integer"),
        ({"require_for_loop": {"required": True, "min_count": 21}}, "at most 20"),
    ],
)
def test_create_refuses_rules_the_evaluator_cannot_grade(client, db_session, instructor, rules, message):
    response = create(client, instructor, difficulty="expert", required_ast_rules=rules)
    assert response.status_code == 422
    assert message in response.text
    assert db_session.query(Task).count() == 0


def test_update_checks_the_resulting_difficulty_and_rules(client, db_session, instructor):
    task_id = create(
        client, instructor, difficulty="intermediate", required_ast_rules={"require_function_def": True}
    ).json()[0]["task_id"]
    url = f"/instructors/tasks/{task_id}"

    lowered = client.patch(url, headers=instructor["headers"], json={"difficulty": "beginner"})
    assert lowered.status_code == 422
    assert "function definition (Intermediate)" in lowered.json()["detail"]

    raised_rules = client.patch(url, headers=instructor["headers"], json={"required_ast_rules": {"require_lambda": True}})
    assert raised_rules.status_code == 422
    assert "lambda expression (Expert)" in raised_rules.json()["detail"]
    assert stored_difficulty(db_session, task_id) == "intermediate"

    both = client.patch(
        url,
        headers=instructor["headers"],
        json={"difficulty": "expert", "required_ast_rules": {"require_lambda": {"required": True, "min_count": 1}}},
    )
    assert both.status_code == 200, both.text
    assert both.json()["difficulty"] == "expert"
    assert stored_difficulty(db_session, task_id) == "expert"

    lowered_with_rules = client.patch(
        url,
        headers=instructor["headers"],
        json={"difficulty": "beginner", "required_ast_rules": {"require_for_loop": True}},
    )
    assert lowered_with_rules.status_code == 200, lowered_with_rules.text
    assert stored_difficulty(db_session, task_id) == "beginner"


def test_other_edits_leave_an_older_inconsistent_activity_alone(client, db_session, instructor):
    # Activities saved before this check (and some seed data) may require
    # rules above their difficulty. Editing the title must still work.
    task_id = create(client, instructor, difficulty="expert", required_ast_rules={"require_import": True}).json()[0]["task_id"]
    task = db_session.get(Task, task_id)
    task.difficulty = "intermediate"
    db_session.commit()

    response = client.patch(f"/instructors/tasks/{task_id}", headers=instructor["headers"], json={"title": "Renamed"})
    assert response.status_code == 200, response.text
    assert stored_difficulty(db_session, task_id) == "intermediate"


@pytest.mark.parametrize("field", ["difficulty", "required_ast_rules", "title", "starter_code"])
def test_update_refuses_null_for_required_columns(client, db_session, instructor, field):
    task_id = create(client, instructor, difficulty="beginner").json()[0]["task_id"]
    response = client.patch(f"/instructors/tasks/{task_id}", headers=instructor["headers"], json={field: None})
    assert response.status_code == 422
    assert "cannot be empty" in response.text
