from __future__ import annotations

import pytest

from app.core.pagination import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    MIN_PAGE,
    MIN_PAGE_SIZE,
    DEFAULT_PAGINATION_BOUNDS,
    PaginationBounds,
    PaginationError,
    PaginationMetadata,
    PaginationRequest,
    SortConfigurationError,
    SortField,
    build_deterministic_sort,
    build_pagination_metadata,
    calculate_item_range,
    calculate_total_pages,
    normalize_sort_direction,
    validate_pagination,
)


def test_default_pagination_constants_are_bounded():
    assert MIN_PAGE == 1
    assert DEFAULT_PAGE == 1

    assert MIN_PAGE_SIZE == 1
    assert DEFAULT_PAGE_SIZE == 25
    assert MAX_PAGE_SIZE == 100


def test_default_pagination_bounds_match_global_limits():
    assert DEFAULT_PAGINATION_BOUNDS == PaginationBounds(
        minimum_page=1,
        minimum_page_size=1,
        maximum_page_size=100,
    )


@pytest.mark.parametrize(
    "minimum_page",
    (
        0,
        -1,
        -100,
    ),
)
def test_pagination_bounds_reject_invalid_minimum_page(
    minimum_page: int,
):
    with pytest.raises(
        PaginationError,
        match="minimum_page must be at least 1",
    ):
        PaginationBounds(
            minimum_page=minimum_page,
        )


@pytest.mark.parametrize(
    "minimum_page_size",
    (
        0,
        -1,
    ),
)
def test_pagination_bounds_reject_invalid_minimum_page_size(
    minimum_page_size: int,
):
    with pytest.raises(
        PaginationError,
        match="minimum_page_size must be at least 1",
    ):
        PaginationBounds(
            minimum_page_size=minimum_page_size,
        )


def test_pagination_bounds_reject_maximum_below_minimum():
    with pytest.raises(
        PaginationError,
        match=("maximum_page_size must be greater than or equal to minimum_page_size"),
    ):
        PaginationBounds(
            minimum_page_size=20,
            maximum_page_size=10,
        )


def test_pagination_bounds_reject_maximum_above_global_limit():
    with pytest.raises(
        PaginationError,
        match=("maximum_page_size must not exceed the global maximum"),
    ):
        PaginationBounds(
            maximum_page_size=MAX_PAGE_SIZE + 1,
        )


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    (
        ("minimum_page", True),
        ("minimum_page_size", False),
        ("maximum_page_size", 10.5),
        ("maximum_page_size", "100"),
    ),
)
def test_pagination_bounds_reject_non_integer_values(
    field_name: str,
    field_value: object,
):
    values = {
        "minimum_page": 1,
        "minimum_page_size": 1,
        "maximum_page_size": 100,
    }

    values[field_name] = field_value

    with pytest.raises(
        PaginationError,
        match=f"{field_name} must be an integer",
    ):
        PaginationBounds(
            **values,
        )


def test_validate_pagination_returns_validated_request():
    result = validate_pagination(
        page=3,
        page_size=20,
    )

    assert result == PaginationRequest(
        page=3,
        page_size=20,
    )


def test_pagination_request_derives_offset():
    pagination = PaginationRequest(
        page=4,
        page_size=25,
    )

    assert pagination.offset == 75


@pytest.mark.parametrize(
    "page",
    (
        0,
        -1,
    ),
)
def test_validate_pagination_rejects_page_below_minimum(
    page: int,
):
    with pytest.raises(
        PaginationError,
        match=("page must be greater than or equal to 1"),
    ):
        validate_pagination(
            page=page,
            page_size=25,
        )


@pytest.mark.parametrize(
    "page_size",
    (
        0,
        101,
    ),
)
def test_validate_pagination_rejects_page_size_outside_bounds(
    page_size: int,
):
    with pytest.raises(
        PaginationError,
        match="page_size must be between 1 and 100",
    ):
        validate_pagination(
            page=1,
            page_size=page_size,
        )


@pytest.mark.parametrize(
    ("page", "page_size", "field_name"),
    (
        (True, 25, "page"),
        (1.5, 25, "page"),
        (1, False, "page_size"),
        (1, "25", "page_size"),
    ),
)
def test_validate_pagination_rejects_non_integer_values(
    page: object,
    page_size: object,
    field_name: str,
):
    with pytest.raises(
        PaginationError,
        match=f"{field_name} must be an integer",
    ):
        validate_pagination(
            page=page,
            page_size=page_size,
        )


def test_validate_pagination_supports_endpoint_specific_bounds():
    bounds = PaginationBounds(
        minimum_page=1,
        minimum_page_size=5,
        maximum_page_size=50,
    )

    result = validate_pagination(
        page=2,
        page_size=50,
        bounds=bounds,
    )

    assert result.page == 2
    assert result.page_size == 50
    assert result.offset == 50


@pytest.mark.parametrize(
    ("total_items", "page_size", "expected"),
    (
        (0, 25, 0),
        (1, 25, 1),
        (25, 25, 1),
        (26, 25, 2),
        (63, 25, 3),
        (100, 10, 10),
    ),
)
def test_calculate_total_pages(
    total_items: int,
    page_size: int,
    expected: int,
):
    assert (
        calculate_total_pages(
            total_items=total_items,
            page_size=page_size,
        )
        == expected
    )


def test_calculate_total_pages_rejects_negative_total():
    with pytest.raises(
        PaginationError,
        match=("total_items must be greater than or equal to 0"),
    ):
        calculate_total_pages(
            total_items=-1,
            page_size=25,
        )


@pytest.mark.parametrize(
    "page_size",
    (
        0,
        -1,
    ),
)
def test_calculate_total_pages_rejects_invalid_page_size(
    page_size: int,
):
    with pytest.raises(
        PaginationError,
        match=("page_size must be greater than or equal to 1"),
    ):
        calculate_total_pages(
            total_items=10,
            page_size=page_size,
        )


def test_calculate_total_pages_rejects_boolean_total_items():
    with pytest.raises(
        PaginationError,
        match="total_items must be an integer",
    ):
        calculate_total_pages(
            total_items=True,
            page_size=25,
        )


def test_calculate_item_range_for_first_page():
    pagination = PaginationRequest(
        page=1,
        page_size=25,
    )

    assert calculate_item_range(
        pagination=pagination,
        total_items=63,
    ) == (
        1,
        25,
    )


def test_calculate_item_range_for_middle_page():
    pagination = PaginationRequest(
        page=2,
        page_size=25,
    )

    assert calculate_item_range(
        pagination=pagination,
        total_items=63,
    ) == (
        26,
        50,
    )


def test_calculate_item_range_for_partial_last_page():
    pagination = PaginationRequest(
        page=3,
        page_size=25,
    )

    assert calculate_item_range(
        pagination=pagination,
        total_items=63,
    ) == (
        51,
        63,
    )


def test_calculate_item_range_for_empty_collection():
    pagination = PaginationRequest(
        page=1,
        page_size=25,
    )

    assert calculate_item_range(
        pagination=pagination,
        total_items=0,
    ) == (
        0,
        0,
    )


def test_calculate_item_range_for_page_past_last_item():
    pagination = PaginationRequest(
        page=10,
        page_size=25,
    )

    assert calculate_item_range(
        pagination=pagination,
        total_items=63,
    ) == (
        0,
        0,
    )


def test_calculate_item_range_rejects_negative_total():
    pagination = PaginationRequest(
        page=1,
        page_size=25,
    )

    with pytest.raises(
        PaginationError,
        match=("total_items must be greater than or equal to 0"),
    ):
        calculate_item_range(
            pagination=pagination,
            total_items=-1,
        )


def test_build_pagination_metadata():
    pagination = PaginationRequest(
        page=2,
        page_size=25,
    )

    result = build_pagination_metadata(
        pagination=pagination,
        total_items=63,
    )

    assert result == PaginationMetadata(
        page=2,
        page_size=25,
        total_items=63,
        total_pages=3,
        from_item=26,
        to_item=50,
    )


def test_build_empty_pagination_metadata():
    pagination = PaginationRequest(
        page=1,
        page_size=25,
    )

    result = build_pagination_metadata(
        pagination=pagination,
        total_items=0,
    )

    assert result == PaginationMetadata(
        page=1,
        page_size=25,
        total_items=0,
        total_pages=0,
        from_item=0,
        to_item=0,
    )


@pytest.mark.parametrize(
    ("direction", "expected"),
    (
        ("asc", "asc"),
        ("ASC", "asc"),
        (" desc ", "desc"),
        ("DESC", "desc"),
    ),
)
def test_normalize_sort_direction(
    direction: str,
    expected: str,
):
    assert normalize_sort_direction(direction) == expected


@pytest.mark.parametrize(
    "direction",
    (
        "",
        "ascending",
        "descending",
        "random",
    ),
)
def test_normalize_sort_direction_rejects_invalid_value(
    direction: str,
):
    with pytest.raises(
        SortConfigurationError,
        match=("sort direction must be either 'asc' or 'desc'"),
    ):
        normalize_sort_direction(direction)


@pytest.mark.parametrize(
    "direction",
    (
        None,
        1,
        True,
    ),
)
def test_normalize_sort_direction_rejects_non_string(
    direction: object,
):
    with pytest.raises(
        SortConfigurationError,
        match="sort direction must be a string",
    ):
        normalize_sort_direction(direction)


def test_build_deterministic_sort_adds_tie_breaker():
    result = build_deterministic_sort(
        primary_field="created_at",
        tie_breaker_field="notification_id",
        direction="DESC",
    )

    assert result == (
        SortField(
            field_name="created_at",
            direction="desc",
        ),
        SortField(
            field_name="notification_id",
            direction="desc",
        ),
    )


def test_build_deterministic_sort_avoids_duplicate_field():
    result = build_deterministic_sort(
        primary_field="notification_id",
        tie_breaker_field="notification_id",
        direction="asc",
    )

    assert result == (
        SortField(
            field_name="notification_id",
            direction="asc",
        ),
    )


def test_build_deterministic_sort_trims_field_names():
    result = build_deterministic_sort(
        primary_field=" created_at ",
        tie_breaker_field=" notification_id ",
        direction=" desc ",
    )

    assert result == (
        SortField(
            field_name="created_at",
            direction="desc",
        ),
        SortField(
            field_name="notification_id",
            direction="desc",
        ),
    )


@pytest.mark.parametrize(
    ("primary_field", "tie_breaker_field", "message"),
    (
        (
            "",
            "notification_id",
            "primary_field must not be empty",
        ),
        (
            "   ",
            "notification_id",
            "primary_field must not be empty",
        ),
        (
            "created_at",
            "",
            "tie_breaker_field must not be empty",
        ),
        (
            "created_at",
            "   ",
            "tie_breaker_field must not be empty",
        ),
    ),
)
def test_build_deterministic_sort_rejects_empty_fields(
    primary_field: str,
    tie_breaker_field: str,
    message: str,
):
    with pytest.raises(
        SortConfigurationError,
        match=message,
    ):
        build_deterministic_sort(
            primary_field=primary_field,
            tie_breaker_field=tie_breaker_field,
            direction="asc",
        )


@pytest.mark.parametrize(
    ("primary_field", "tie_breaker_field", "message"),
    (
        (
            123,
            "notification_id",
            "primary_field must be a string",
        ),
        (
            "created_at",
            None,
            "tie_breaker_field must be a string",
        ),
    ),
)
def test_build_deterministic_sort_rejects_non_string_fields(
    primary_field: object,
    tie_breaker_field: object,
    message: str,
):
    with pytest.raises(
        SortConfigurationError,
        match=message,
    ):
        build_deterministic_sort(
            primary_field=primary_field,
            tie_breaker_field=tie_breaker_field,
            direction="asc",
        )


# PAGINATION CONTRACT:
# All page numbers are one-based, all page sizes are bounded, and offsets
# are derived internally rather than accepted from request input.

# ORDERING CONTRACT:
# Paginated services must map approved sort-field names to SQLAlchemy
# columns and include a stable unique tie-breaker.

# PRIVACY CONTRACT:
# Pagination metadata contains only counts and positions. It must not contain
# source code, clipboard text, passwords, tokens, or unreleased grade data.
