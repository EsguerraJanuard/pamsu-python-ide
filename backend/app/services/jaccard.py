import builtins
import io
import keyword
import re
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

PRESERVED_BUILTIN_NAMES = frozenset(dir(builtins))
MAX_SHARED_FEATURES_IN_RESPONSE = 50

FALLBACK_TOKEN_PATTERN = re.compile(
    r"[A-Za-z_]\w*"
    r"|\d+(?:\.\d+)?"
    r"|==|!=|<=|>=|:=|\*\*|//|<<|>>"
    r"|[()[\]{}:,.+\-*/%=<>]"
)


def _normalize_python_token_sequence(
    raw_code: str,
    normalize_identifiers: bool = True,
    normalize_literals: bool = True,
) -> list[str]:
    if not isinstance(raw_code, str) or not raw_code.strip():
        return []

    normalized_tokens: list[str] = []

    try:
        token_stream = tokenize.generate_tokens(io.StringIO(raw_code).readline)

        for current_token in token_stream:
            token_type = current_token.type
            token_value = current_token.string

            if token_type in IGNORED_TOKEN_TYPES:
                continue

            if token_type == tokenize.ERRORTOKEN:
                if token_value.isspace():
                    continue

                normalized_tokens.append(token_value)
                continue

            if not token_value:
                continue

            if token_type == tokenize.NAME:
                if keyword.iskeyword(token_value):
                    normalized_tokens.append(token_value)
                elif (
                    normalize_identifiers and token_value not in PRESERVED_BUILTIN_NAMES
                ):
                    normalized_tokens.append("IDENTIFIER")
                else:
                    normalized_tokens.append(token_value)

            elif token_type == tokenize.NUMBER:
                normalized_tokens.append(
                    "NUMBER_LITERAL" if normalize_literals else token_value
                )

            elif token_type == tokenize.STRING:
                normalized_tokens.append(
                    "STRING_LITERAL" if normalize_literals else token_value
                )

            else:
                normalized_tokens.append(token_value)

    except (tokenize.TokenError, IndentationError, SyntaxError):
        # Keep any valid tokens produced before the tokenization error.
        # Syntax validity is handled separately by the AST evaluator.
        if not normalized_tokens:
            normalized_tokens.extend(sorted(fallback_tokenize(raw_code)))

    return normalized_tokens


def tokenize_python_code(
    raw_code: str,
    normalize_identifiers: bool = True,
    normalize_literals: bool = True,
) -> set[str]:
    """
    Return unique normalized Python tokens.

    This public function keeps the original set-based behavior for
    compatibility with existing services and tests.
    """

    return set(
        _normalize_python_token_sequence(
            raw_code=raw_code,
            normalize_identifiers=normalize_identifiers,
            normalize_literals=normalize_literals,
        )
    )


def fallback_tokenize(raw_code: str) -> set[str]:
    if not isinstance(raw_code, str) or not raw_code.strip():
        return set()

    return set(FALLBACK_TOKEN_PATTERN.findall(raw_code))


def _create_features(
    normalized_tokens: list[str],
    shingle_size: int,
) -> set[str]:
    if shingle_size < 1:
        raise ValueError("shingle_size must be at least 1.")

    if not normalized_tokens:
        return set()

    if shingle_size == 1:
        return set(normalized_tokens)

    if len(normalized_tokens) < shingle_size:
        return set(normalized_tokens)

    return {
        "\x1f".join(normalized_tokens[index : index + shingle_size])
        for index in range(len(normalized_tokens) - shingle_size + 1)
    }


def _display_feature(feature: str) -> str:
    return " ".join(feature.split("\x1f"))


def calculate_jaccard_score(
    code_a: str,
    code_b: str,
    normalize_identifiers: bool = True,
    normalize_literals: bool = True,
    shingle_size: int = 1,
) -> float:
    details = calculate_jaccard_details(
        code_a=code_a,
        code_b=code_b,
        normalize_identifiers=normalize_identifiers,
        normalize_literals=normalize_literals,
        shingle_size=shingle_size,
    )

    return float(details["score"])


def calculate_jaccard_details(
    code_a: str,
    code_b: str,
    normalize_identifiers: bool = True,
    normalize_literals: bool = True,
    shingle_size: int = 1,
) -> dict[str, Any]:
    tokens_a_sequence = _normalize_python_token_sequence(
        raw_code=code_a,
        normalize_identifiers=normalize_identifiers,
        normalize_literals=normalize_literals,
    )
    tokens_b_sequence = _normalize_python_token_sequence(
        raw_code=code_b,
        normalize_identifiers=normalize_identifiers,
        normalize_literals=normalize_literals,
    )

    tokens_a = set(tokens_a_sequence)
    tokens_b = set(tokens_b_sequence)

    features_a = _create_features(
        normalized_tokens=tokens_a_sequence,
        shingle_size=shingle_size,
    )
    features_b = _create_features(
        normalized_tokens=tokens_b_sequence,
        shingle_size=shingle_size,
    )

    if not features_a and not features_b:
        return {
            "score": 0.0,
            "intersection_count": 0,
            "union_count": 0,
            "tokens_a_count": 0,
            "tokens_b_count": 0,
            "token_sequence_a_count": 0,
            "token_sequence_b_count": 0,
            "shared_tokens": [],
            "shared_tokens_truncated": False,
            "shingle_size": shingle_size,
        }

    intersection = features_a.intersection(features_b)
    union = features_a.union(features_b)

    score = round((len(intersection) / len(union)) * 100, 2) if union else 0.0

    shared_features = sorted(intersection)
    displayed_shared_features = [
        _display_feature(feature)
        for feature in shared_features[:MAX_SHARED_FEATURES_IN_RESPONSE]
    ]

    return {
        "score": score,
        "intersection_count": len(intersection),
        "union_count": len(union),
        "tokens_a_count": len(tokens_a),
        "tokens_b_count": len(tokens_b),
        "token_sequence_a_count": len(tokens_a_sequence),
        "token_sequence_b_count": len(tokens_b_sequence),
        "shared_tokens": displayed_shared_features,
        "shared_tokens_truncated": (
            len(shared_features) > MAX_SHARED_FEATURES_IN_RESPONSE
        ),
        "shingle_size": shingle_size,
    }


def find_highest_similarity(
    target_code: str,
    comparison_submissions: dict[int, str],
    normalize_identifiers: bool = True,
    normalize_literals: bool = True,
    shingle_size: int = 1,
) -> dict[str, Any]:
    highest_score = 0.0
    highest_match_sub_id: int | None = None
    all_results: list[dict[str, Any]] = []

    for sub_id in sorted(comparison_submissions):
        comparison_code = comparison_submissions[sub_id]

        details = calculate_jaccard_details(
            code_a=target_code,
            code_b=comparison_code,
            normalize_identifiers=normalize_identifiers,
            normalize_literals=normalize_literals,
            shingle_size=shingle_size,
        )

        score = float(details["score"])

        all_results.append(
            {
                "sub_id": sub_id,
                "score": score,
                "intersection_count": details["intersection_count"],
                "union_count": details["union_count"],
            }
        )

        is_better_score = score > highest_score
        is_preferred_tie = (
            score > 0
            and score == highest_score
            and (highest_match_sub_id is None or sub_id < highest_match_sub_id)
        )

        if is_better_score or is_preferred_tie:
            highest_score = score
            highest_match_sub_id = sub_id

    all_results.sort(
        key=lambda result: (
            -float(result["score"]),
            int(result["sub_id"]),
        )
    )

    return {
        "highest_score": highest_score,
        "highest_match_sub_id": highest_match_sub_id,
        "comparisons": all_results,
        "shingle_size": shingle_size,
    }


# REVIEW BOUNDARY:
# Jaccard similarity is an automated review indicator only. It must never
# automatically declare plagiarism, copying, cheating, or misconduct, and
# must never calculate the official instructor-assigned grade.

# ANALYSIS BOUNDARY:
# This module tokenizes source code as text only. It must never execute
# submitted Python code.

# PARTNER INTEGRATION:
# The isolated worker may call this module for analysis, but execution and
# resource enforcement remain under the partner-owned sandbox.
