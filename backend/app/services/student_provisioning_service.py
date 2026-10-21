"""
MIS masterlist import: create student accounts from a CSV or .xlsx file.

Every row must carry the student's own university email, official school
ID and name. Nothing is inferred or generated: a school ID is never taken
from an email and an email is never built from a school ID. Each value is
checked with the same rules as every other account (UserBase).

No password is set or sent. Each account gets an unusable password marker
that no password can match, and the student sets their own password through
the existing password-reset OTP flow on their university mailbox.

Valid rows are created in one transaction. If the database rejects the
batch (for example a concurrent import used the same school ID), nothing is
created and MasterlistConflictError is raised.
"""

import csv
import io
import secrets
from collections import Counter
from dataclasses import dataclass
from typing import Literal

from app.models.domain_models import User
from app.schemas.user_schema import UserBase
from app.services.classroom_service import apply_pending_enrollments
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

# Same ceiling as instructor bulk enrollment.
MAX_MASTERLIST_ROWS = 500
MAX_MASTERLIST_BYTES = 2 * 1024 * 1024

UNUSABLE_PASSWORD_PREFIX = "!"

MasterlistRowStatus = Literal["created", "skipped", "failed"]


class MasterlistFileError(ValueError):
    """The file as a whole cannot be imported; nothing was created."""


class MasterlistConflictError(RuntimeError):
    """The database rejected the batch; nothing was created."""


class MasterlistRowResult(BaseModel):
    row: int = Field(..., ge=2)
    email: str | None = None
    status: MasterlistRowStatus
    reason: str | None = None

    model_config = ConfigDict(extra="forbid")


class MasterlistImportResult(BaseModel):
    created: int = 0
    skipped: int = 0
    failed: int = 0
    enrolled_from_pending: int = 0
    pending_left: int = 0
    rows: list[MasterlistRowResult] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class _ParsedRow:
    def __init__(self, row_number: int, values: dict[str, str], numeric_school_id: bool):
        self.row_number = row_number
        self.values = values
        self.numeric_school_id = numeric_school_id
        self.identity: UserBase | None = None
        self.result: MasterlistRowResult | None = None


@dataclass(frozen=True)
class ProvisionedStudent:
    """A created account, as the welcome email needs it.

    first_name and last_name are the file's own columns when it had them
    (empty when it had a single name column), so the greeting never has to
    guess where a surname like "Dela Cruz" starts.
    """

    email: str
    school_id: str
    full_name: str
    first_name: str
    last_name: str


def make_unusable_password_hash() -> str:
    """Return a per-account value that no password can ever verify against.

    It is not a bcrypt hash, so verify_password always returns False for it.
    A password-reset completion replaces it with a real hash.
    """

    return UNUSABLE_PASSWORD_PREFIX + secrets.token_urlsafe(32)


def _normalize_header(value: object) -> str:
    return "_".join(str(value or "").strip().lower().replace("-", " ").split())


def _cell_to_text(value: object) -> tuple[str, bool]:
    """Return (text, was_numeric). Excel stores digit-only IDs as numbers."""

    if value is None:
        return "", False

    if isinstance(value, bool):
        return str(value), False

    if isinstance(value, int):
        return str(value), True

    if isinstance(value, float):
        if value.is_integer():
            return str(int(value)), True
        return str(value), True

    return str(value).strip(), False


def _read_csv_rows(content: bytes) -> list[list[tuple[str, bool]]]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise MasterlistFileError(
            "The CSV file must be saved with UTF-8 encoding."
        ) from error

    try:
        return [
            [(cell.strip(), False) for cell in record]
            for record in csv.reader(io.StringIO(text))
        ]
    except csv.Error as error:
        raise MasterlistFileError("The CSV file could not be read.") from error


def _read_xlsx_rows(content: bytes) -> list[list[tuple[str, bool]]]:
    from openpyxl import load_workbook

    try:
        workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    except Exception as error:
        # openpyxl raises several unrelated types for corrupt archives.
        raise MasterlistFileError("The .xlsx file could not be read.") from error

    try:
        sheet = workbook.worksheets[0] if workbook.worksheets else None

        if sheet is None:
            raise MasterlistFileError("The .xlsx file has no worksheet.")

        rows: list[list[tuple[str, bool]]] = []

        for record in sheet.iter_rows(values_only=True):
            rows.append([_cell_to_text(cell) for cell in record])

            # Header plus the row limit plus one is enough to reject an
            # oversized sheet without reading all of it.
            if len(rows) > MAX_MASTERLIST_ROWS + 2:
                break

        return rows
    finally:
        workbook.close()


def _read_rows(content: bytes, filename: str | None) -> list[list[tuple[str, bool]]]:
    if not content:
        raise MasterlistFileError("The uploaded file is empty.")

    if len(content) > MAX_MASTERLIST_BYTES:
        raise MasterlistFileError("The uploaded file is larger than 2 MB.")

    lowered_name = (filename or "").strip().lower()

    if lowered_name.endswith(".xlsx"):
        return _read_xlsx_rows(content)

    if lowered_name.endswith(".xls"):
        raise MasterlistFileError(
            "Old .xls files are not supported. Save the masterlist as .xlsx or CSV."
        )

    if lowered_name.endswith(".csv"):
        return _read_csv_rows(content)

    raise MasterlistFileError("Upload the masterlist as a .csv or .xlsx file.")


def _parse_masterlist(content: bytes, filename: str | None) -> list[_ParsedRow]:
    raw_rows = _read_rows(content, filename)

    # Skip leading blank lines before the header.
    while raw_rows and not any(text for text, _ in raw_rows[0]):
        raw_rows.pop(0)

    if not raw_rows:
        raise MasterlistFileError("The uploaded file has no header row.")

    headers = [_normalize_header(text) for text, _ in raw_rows[0]]
    header_set = set(headers)

    has_name = "name" in header_set or {"first_name", "last_name"} <= header_set

    if not {"email", "school_id"} <= header_set or not has_name:
        raise MasterlistFileError(
            "The masterlist must have a header row with the columns email, "
            "school_id, and either name or first_name and last_name."
        )

    duplicated_headers = [header for header, count in Counter(headers).items() if header and count > 1]

    if duplicated_headers:
        raise MasterlistFileError(
            f"The header row repeats the column(s): {', '.join(sorted(duplicated_headers))}."
        )

    parsed: list[_ParsedRow] = []

    for offset, record in enumerate(raw_rows[1:], start=2):
        if not any(text for text, _ in record):
            continue

        values: dict[str, str] = {}
        numeric_school_id = False

        for index, header in enumerate(headers):
            if not header:
                continue

            text, was_numeric = record[index] if index < len(record) else ("", False)
            values[header] = text

            if header == "school_id":
                numeric_school_id = was_numeric

        parsed.append(_ParsedRow(offset, values, numeric_school_id))

        if len(parsed) > MAX_MASTERLIST_ROWS:
            raise MasterlistFileError(
                f"The masterlist has more than {MAX_MASTERLIST_ROWS} rows. "
                "Split it into smaller files."
            )

    if not parsed:
        raise MasterlistFileError("The masterlist has no student rows.")

    return parsed


def _row_name(values: dict[str, str]) -> str:
    if values.get("name", "").strip():
        return values["name"]

    parts = [
        values.get("first_name", ""),
        values.get("middle_name", ""),
        values.get("last_name", ""),
    ]
    return " ".join(part.strip() for part in parts if part and part.strip())


def _describe_validation_error(error: ValidationError, row: _ParsedRow) -> str:
    first_error = error.errors()[0]
    field = first_error.get("loc", ("",))[0]

    if field == "school_id":
        if not row.values.get("school_id", "").strip():
            return "Missing school ID."

        reason = "School ID must be 10 digits or the ####-##### format."

        if row.numeric_school_id:
            reason += (
                " Excel stored it as a number, which drops leading zeros; "
                "format the school_id column as Text."
            )

        return reason

    if field == "email":
        if not row.values.get("email", "").strip():
            return "Missing email."
        return "Email must be a valid @pampangastateu.edu.ph address."

    if field == "name":
        if not _row_name(row.values):
            return "Missing name."
        return "Name must be at most 150 characters."

    return "The row is not valid."


def _fail(row: _ParsedRow, reason: str) -> None:
    email = row.values.get("email", "").strip().lower() or None
    row.result = MasterlistRowResult(row=row.row_number, email=email, status="failed", reason=reason)


def import_masterlist(
    *,
    db: Session,
    content: bytes,
    filename: str | None,
    actor_user_id: int,
) -> tuple[MasterlistImportResult, list[ProvisionedStudent]]:
    """
    Validate a masterlist and create the accounts it describes.

    Returns the per-row result and the accounts created, which the caller
    may notify only after this function has committed them.
    """

    rows = _parse_masterlist(content, filename)

    for row in rows:
        try:
            row.identity = UserBase(
                name=_row_name(row.values),
                school_id=row.values.get("school_id", ""),
                email=row.values.get("email", ""),
            )
        except ValidationError as error:
            _fail(row, _describe_validation_error(error, row))

    valid_rows = [row for row in rows if row.result is None]

    # A value repeated inside the file cannot be resolved, so every copy fails.
    email_counts = Counter(row.identity.email for row in valid_rows)
    school_id_counts = Counter(row.identity.school_id for row in valid_rows)

    for row in valid_rows:
        if email_counts[row.identity.email] > 1:
            _fail(row, "This email appears on more than one row of the file.")
        elif school_id_counts[row.identity.school_id] > 1:
            _fail(row, "This school ID appears on more than one row of the file.")

    valid_rows = [row for row in rows if row.result is None]

    existing_by_email: dict[str, User] = {}
    existing_by_school_id: dict[str, User] = {}

    if valid_rows:
        emails = [row.identity.email for row in valid_rows]
        school_ids = [row.identity.school_id for row in valid_rows]

        existing_users = (
            db.query(User)
            .filter(
                or_(
                    func.lower(User.email).in_(emails),
                    User.school_id.in_(school_ids),
                )
            )
            .all()
        )

        for user in existing_users:
            existing_by_email[user.email.strip().lower()] = user
            existing_by_school_id[user.school_id] = user

    rows_to_create: list[_ParsedRow] = []

    for row in valid_rows:
        identity = row.identity
        by_email = existing_by_email.get(identity.email)
        by_school_id = existing_by_school_id.get(identity.school_id)

        if by_email is None and by_school_id is None:
            rows_to_create.append(row)
        elif by_email is not None and by_email is by_school_id:
            if by_email.role != "student":
                _fail(row, "This email belongs to a non-student account.")
            else:
                row.result = MasterlistRowResult(
                    row=row.row_number,
                    email=identity.email,
                    status="skipped",
                    reason="An account with this email and school ID already exists.",
                )
        elif by_email is not None:
            _fail(row, "This email already belongs to an account with a different school ID.")
        else:
            _fail(row, "This school ID already belongs to an account with a different email.")

    created_users: list[tuple[_ParsedRow, User]] = []
    enrolled_from_pending = 0
    pending_left = 0

    try:
        for row in rows_to_create:
            identity = row.identity
            new_user = User(
                email=identity.email,
                name=identity.name,
                role="student",
                password_hash=make_unusable_password_hash(),
                school_id=identity.school_id,
                email_verified=True,
                is_active=True,
            )
            db.add(new_user)
            db.flush()

            pending_result = apply_pending_enrollments(
                db=db,
                student=new_user,
                actor_user_id=actor_user_id,
            )
            enrolled_from_pending += len(pending_result.enrolled_class_ids)
            pending_left += len(pending_result.skipped)
            created_users.append((row, new_user))

        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise MasterlistConflictError(
            "No accounts were created: another account with one of these "
            "emails or school IDs was saved at the same time. Upload the file again."
        ) from error
    except Exception:
        db.rollback()
        raise

    # Rows count as created only after the commit succeeded.
    for row, _ in created_users:
        row.result = MasterlistRowResult(
            row=row.row_number,
            email=row.identity.email,
            status="created",
        )

    results = [row.result for row in rows]

    return (
        MasterlistImportResult(
            created=sum(1 for result in results if result.status == "created"),
            skipped=sum(1 for result in results if result.status == "skipped"),
            failed=sum(1 for result in results if result.status == "failed"),
            enrolled_from_pending=enrolled_from_pending,
            pending_left=pending_left,
            rows=results,
        ),
        [
            ProvisionedStudent(
                email=user.email,
                school_id=user.school_id,
                full_name=user.name,
                first_name=row.values.get("first_name", "").strip(),
                last_name=row.values.get("last_name", "").strip(),
            )
            for row, user in created_users
        ],
    )
