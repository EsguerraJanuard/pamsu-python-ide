import io
import json
import keyword
import tokenize
from typing import Any


IGNORED_TOKEN_TYPES = {
    tokenize.ENCODING,
    tokenize.ENDMARKER,
    tokenize.NEWLINE,
    tokenize.NL,
    tokenize.INDENT,
    tokenize.DEDENT,
    tokenize.COMMENT,
}


def tokenize_python_code(
    raw_code: str,
    normalize_identifiers: bool = True,
    normalize_literals: bool = True,
) -> set[str]:
    if not isinstance(raw_code, str):
        return set()

    if not raw_code.strip():
        return set()

    tokens: set[str] = set()

    try:
        token_stream = tokenize.generate_tokens(io.StringIO(raw_code).readline)

        for token in token_stream:
            token_type = token.type
            token_value = token.string.strip()

            if token_type in IGNORED_TOKEN_TYPES:
                continue

            if not token_value:
                continue

            if token_type == tokenize.NAME:
                if keyword.iskeyword(token_value):
                    tokens.add(token_value)
                elif normalize_identifiers:
                    tokens.add("IDENTIFIER")
                else:
                    tokens.add(token_value)

            elif token_type == tokenize.NUMBER:
                if normalize_literals:
                    tokens.add("NUMBER_LITERAL")
                else:
                    tokens.add(token_value)

            elif token_type == tokenize.STRING:
                if normalize_literals:
                    tokens.add("STRING_LITERAL")
                else:
                    tokens.add(token_value)

            else:
                tokens.add(token_value)

    except tokenize.TokenError:
        return fallback_tokenize(raw_code)

    return tokens


def fallback_tokenize(raw_code: str) -> set[str]:
    if not isinstance(raw_code, str):
        return set()

    separators = [
        "(",
        ")",
        "[",
        "]",
        "{",
        "}",
        ":",
        ",",
        ".",
        "+",
        "-",
        "*",
        "/",
        "%",
        "=",
        "==",
        "!=",
        "<",
        ">",
        "<=",
        ">=",
        "\n",
        "\t",
    ]

    cleaned_code = raw_code

    for separator in separators:
        cleaned_code = cleaned_code.replace(separator, " ")

    return {token.strip() for token in cleaned_code.split() if token.strip()}


def calculate_jaccard_score(
    code_a: str,
    code_b: str,
    normalize_identifiers: bool = True,
    normalize_literals: bool = True,
) -> float:
    details = calculate_jaccard_details(
        code_a=code_a,
        code_b=code_b,
        normalize_identifiers=normalize_identifiers,
        normalize_literals=normalize_literals,
    )

    return float(details["score"])


def calculate_jaccard_details(
    code_a: str,
    code_b: str,
    normalize_identifiers: bool = True,
    normalize_literals: bool = True,
) -> dict[str, Any]:
    tokens_a = tokenize_python_code(
        raw_code=code_a,
        normalize_identifiers=normalize_identifiers,
        normalize_literals=normalize_literals,
    )

    tokens_b = tokenize_python_code(
        raw_code=code_b,
        normalize_identifiers=normalize_identifiers,
        normalize_literals=normalize_literals,
    )

    if not tokens_a and not tokens_b:
        return {
            "score": 0.0,
            "intersection_count": 0,
            "union_count": 0,
            "tokens_a_count": 0,
            "tokens_b_count": 0,
            "shared_tokens": [],
        }

    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)

    if not union:
        score = 0.0
    else:
        score = round((len(intersection) / len(union)) * 100, 2)

    return {
        "score": score,
        "intersection_count": len(intersection),
        "union_count": len(union),
        "tokens_a_count": len(tokens_a),
        "tokens_b_count": len(tokens_b),
        "shared_tokens": sorted(intersection),
    }


def find_highest_similarity(
    target_code: str,
    comparison_submissions: dict[int, str],
    normalize_identifiers: bool = True,
    normalize_literals: bool = True,
) -> dict[str, Any]:
    highest_score = 0.0
    highest_match_sub_id = None
    all_results: list[dict[str, Any]] = []

    for sub_id, comparison_code in comparison_submissions.items():
        score = calculate_jaccard_score(
            code_a=target_code,
            code_b=comparison_code,
            normalize_identifiers=normalize_identifiers,
            normalize_literals=normalize_literals,
        )

        result = {
            "sub_id": sub_id,
            "score": score,
        }

        all_results.append(result)

        if score > highest_score:
            highest_score = score
            highest_match_sub_id = sub_id

    return {
        "highest_score": highest_score,
        "highest_match_sub_id": highest_match_sub_id,
        "comparisons": all_results,
    }


if __name__ == "__main__":
    student_code_a = """
def solve():
    for i in range(5):
        print(i)

solve()
"""

    student_code_b = """
def answer():
    for number in range(5):
        print(number)

answer()
"""

    student_code_c = """
name = input("Enter name: ")
print("Hello", name)
"""

    same_code_result = calculate_jaccard_details(student_code_a, student_code_b)
    different_code_result = calculate_jaccard_details(student_code_a, student_code_c)

    comparison_result = find_highest_similarity(
        target_code=student_code_a,
        comparison_submissions={
            2: student_code_b,
            3: student_code_c,
        },
    )

    print("Similar Code Result:")
    print(json.dumps(same_code_result, indent=4))

    print("\nDifferent Code Result:")
    print(json.dumps(different_code_result, indent=4))

    print("\nHighest Similarity Result:")
    print(json.dumps(comparison_result, indent=4))
