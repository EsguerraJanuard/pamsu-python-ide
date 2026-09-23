from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Final, Literal


MIN_PAGE: Final[int] = 1
DEFAULT_PAGE: Final[int] = 1

MIN_PAGE_SIZE: Final[int] = 1
DEFAULT_PAGE_SIZE: Final[int] = 25
MAX_PAGE_SIZE: Final[int] = 100

SortDirection = Literal["asc", "desc"]


class PaginationError(ValueError):
    """Raised when pagination parameters are invalid."""


class SortConfigurationError(ValueError):
    """Raised when deterministic sorting is invalid."""


def _require_integer(
    *,
    value: object,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(
        value,
        int,
    ):
        raise PaginationError(f"{field_name} must be an integer.")

    return value


def _require_non_empty_field_name(
    *,
    value: object,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise SortConfigurationError(f"{field_name} must be a string.")

    normalized_value = value.strip()

    if not normalized_value:
        raise SortConfigurationError(f"{field_name} must not be empty.")

    return normalized_value


@dataclass(
    frozen=True,
    slots=True,
)
class PaginationBounds:
    """
    Defines the accepted page and page-size boundaries.

    Different endpoints may supply a smaller maximum page size, but no
    endpoint should exceed the global maximum unless explicitly approved.
    """

    minimum_page: int = MIN_PAGE
    minimum_page_size: int = MIN_PAGE_SIZE
    maximum_page_size: int = MAX_PAGE_SIZE

    def __post_init__(self) -> None:
        minimum_page = _require_integer(
            value=self.minimum_page,
            field_name="minimum_page",
        )
        minimum_page_size = _require_integer(
            value=self.minimum_page_size,
            field_name="minimum_page_size",
        )
        maximum_page_size = _require_integer(
            value=self.maximum_page_size,
            field_name="maximum_page_size",
        )

        if minimum_page < 1:
            raise PaginationError("minimum_page must be at least 1.")

        if minimum_page_size < 1:
            raise PaginationError("minimum_page_size must be at least 1.")

        if maximum_page_size < minimum_page_size:
            raise PaginationError(
                "maximum_page_size must be greater than or equal to minimum_page_size."
            )

        if maximum_page_size > MAX_PAGE_SIZE:
            raise PaginationError(
                "maximum_page_size must not exceed the global "
                f"maximum of {MAX_PAGE_SIZE}."
            )


DEFAULT_PAGINATION_BOUNDS: Final[PaginationBounds] = PaginationBounds()


@dataclass(
    frozen=True,
    slots=True,
)
class PaginationRequest:
    """
    Validated one-based pagination parameters.

    The offset is always derived rather than accepted from the caller.
    """

    page: int
    page_size: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


@dataclass(
    frozen=True,
    slots=True,
)
class PaginationMetadata:
    """Consistent pagination metadata returned by list endpoints."""

    page: int
    page_size: int
    total_items: int
    total_pages: int
    from_item: int
    to_item: int


@dataclass(
    frozen=True,
    slots=True,
)
class SortField:
    """One field in a deterministic ordering definition."""

    field_name: str
    direction: SortDirection


def validate_pagination(
    *,
    page: int,
    page_size: int,
    bounds: PaginationBounds = DEFAULT_PAGINATION_BOUNDS,
) -> PaginationRequest:
    validated_page = _require_integer(
        value=page,
        field_name="page",
    )
    validated_page_size = _require_integer(
        value=page_size,
        field_name="page_size",
    )

    if validated_page < bounds.minimum_page:
        raise PaginationError(
            f"page must be greater than or equal to {bounds.minimum_page}."
        )

    if not (
        bounds.minimum_page_size <= validated_page_size <= bounds.maximum_page_size
    ):
        raise PaginationError(
            "page_size must be between "
            f"{bounds.minimum_page_size} and "
            f"{bounds.maximum_page_size}."
        )

    return PaginationRequest(
        page=validated_page,
        page_size=validated_page_size,
    )


def calculate_total_pages(
    *,
    total_items: int,
    page_size: int,
) -> int:
    validated_total_items = _require_integer(
        value=total_items,
        field_name="total_items",
    )
    validated_page_size = _require_integer(
        value=page_size,
        field_name="page_size",
    )

    if validated_total_items < 0:
        raise PaginationError("total_items must be greater than or equal to 0.")

    if validated_page_size < 1:
        raise PaginationError("page_size must be greater than or equal to 1.")

    if validated_total_items == 0:
        return 0

    return ceil(validated_total_items / validated_page_size)


def calculate_item_range(
    *,
    pagination: PaginationRequest,
    total_items: int,
) -> tuple[int, int]:
    validated_total_items = _require_integer(
        value=total_items,
        field_name="total_items",
    )

    if validated_total_items < 0:
        raise PaginationError("total_items must be greater than or equal to 0.")

    if validated_total_items == 0 or pagination.offset >= validated_total_items:
        return 0, 0

    from_item = pagination.offset + 1
    to_item = min(
        pagination.offset + pagination.page_size,
        validated_total_items,
    )

    return from_item, to_item


def build_pagination_metadata(
    *,
    pagination: PaginationRequest,
    total_items: int,
) -> PaginationMetadata:
    total_pages = calculate_total_pages(
        total_items=total_items,
        page_size=pagination.page_size,
    )

    from_item, to_item = calculate_item_range(
        pagination=pagination,
        total_items=total_items,
    )

    return PaginationMetadata(
        page=pagination.page,
        page_size=pagination.page_size,
        total_items=total_items,
        total_pages=total_pages,
        from_item=from_item,
        to_item=to_item,
    )


def normalize_sort_direction(
    direction: str,
) -> SortDirection:
    if not isinstance(direction, str):
        raise SortConfigurationError("sort direction must be a string.")

    normalized_direction = direction.strip().lower()

    if normalized_direction not in {
        "asc",
        "desc",
    }:
        raise SortConfigurationError("sort direction must be either 'asc' or 'desc'.")

    return normalized_direction


def build_deterministic_sort(
    *,
    primary_field: str,
    tie_breaker_field: str,
    direction: str,
) -> tuple[SortField, ...]:
    """
    Builds an ordering definition with a stable unique tie-breaker.

    Services remain responsible for mapping these approved field names to
    SQLAlchemy columns. User-provided field names must never be inserted
    directly into SQL text.
    """

    validated_primary_field = _require_non_empty_field_name(
        value=primary_field,
        field_name="primary_field",
    )

    validated_tie_breaker_field = _require_non_empty_field_name(
        value=tie_breaker_field,
        field_name="tie_breaker_field",
    )

    validated_direction = normalize_sort_direction(direction)

    primary_sort = SortField(
        field_name=validated_primary_field,
        direction=validated_direction,
    )

    if validated_primary_field == validated_tie_breaker_field:
        return (primary_sort,)

    return (
        primary_sort,
        SortField(
            field_name=validated_tie_breaker_field,
            direction=validated_direction,
        ),
    )


# PAGINATION BOUNDARY:
# API callers provide only one-based page and bounded page_size values.
# Database offsets are derived internally.

# ORDERING BOUNDARY:
# Every paginated database query must include a stable unique tie-breaker.
# Services map approved sort fields to SQLAlchemy columns and never insert
# untrusted field names directly into SQL.

# GLOBAL LIMIT BOUNDARY:
# No endpoint may exceed MAX_PAGE_SIZE without an explicit roadmap change.
