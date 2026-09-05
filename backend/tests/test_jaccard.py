from app.services.jaccard import (
    calculate_jaccard_details,
    calculate_jaccard_score,
    find_highest_similarity,
)


def test_identical_code_returns_full_similarity():
    code = "for number in range(5):\n    print(number)"

    score = calculate_jaccard_score(code, code)

    assert score == 100.0


def test_renamed_identifiers_are_normalized():
    code_a = """
def solve():
    for number in range(5):
        print(number)
"""

    code_b = """
def answer():
    for value in range(5):
        print(value)
"""

    score = calculate_jaccard_score(code_a, code_b)

    assert score == 100.0


def test_empty_code_returns_zero_similarity():
    details = calculate_jaccard_details("", "")

    assert details["score"] == 0.0
    assert details["intersection_count"] == 0
    assert details["union_count"] == 0


def test_highest_similarity_match_is_identified():
    target_code = "for number in range(5):\n    print(number)"

    comparisons = {
        2: "name = input('Name: ')\nprint(name)",
        3: "for value in range(5):\n    print(value)",
    }

    result = find_highest_similarity(
        target_code=target_code,
        comparison_submissions=comparisons,
    )

    assert result["highest_match_sub_id"] == 3
    assert result["highest_score"] == 100.0
