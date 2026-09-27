with open('backend/tests/test_reporting_service.py', 'r') as f:
    content = f.read()

import re

# Find the start of test_gradebook_csv_export_is_owner_scoped_and_privacy_safe
start_idx = content.find("def test_gradebook_csv_export_is_owner_scoped_and_privacy_safe(")
end_idx = content.find("def test_gradebook_csv_export_denies_another_instructor(", start_idx)

original_func = content[start_idx:end_idx]

new_func = """def test_gradebook_excel_export_is_owner_scoped_and_privacy_safe(
    db_session: Session,
):
    import io
    import openpyxl

    context = _create_reporting_context(
        db_session,
    )

    export = build_gradebook_excel_export(
        db_session,
        instructor_id=context["owner"].user_id,
        class_id=context["classroom"].class_id,
    )

    assert export["filename"] == (
        f"classroom-{context['classroom'].class_id}-gradebook.xlsx"
    )
    assert export["media_type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert export["row_count"] == 3
    assert export["includes_raw_source"] is False

    wb = openpyxl.load_workbook(io.BytesIO(export["content"]))
    ws = wb.active
    rows = list(ws.values)
    
    # Check headers
    headers = rows[0]
    assert "raw_code" not in headers
    assert "standard_input" not in headers
    assert "feedback" not in headers
    assert "risk_score" not in headers
    assert "plagiarism_verdict" not in headers

    # Verify content doesn't contain prohibited values
    prohibited_values = {
        "PRIVATE UNOFFICIAL SOURCE",
        "PRIVATE ALPHA ONE SOURCE",
        "PRIVATE ALPHA TWO SOURCE",
        "PRIVATE FORMULA SOURCE",
        "PRIVATE STANDARD INPUT",
        "PRIVATE UNRELEASED FEEDBACK",
        "PRIVATE RELEASED ALPHA FEEDBACK",
        "PRIVATE RELEASED FORMULA FEEDBACK",
        "PRIVATE TASK DESCRIPTION",
        "PRIVATE TASK INSTRUCTIONS",
        "PRIVATE STARTER CODE",
    }
    for row in rows:
        for cell in row:
            if cell is not None and isinstance(cell, str):
                for prohibited in prohibited_values:
                    assert prohibited not in cell

    # Find the formula row
    school_id_idx = headers.index("school_id")
    student_name_idx = headers.index("student_name")
    activity_title_idx = headers.index("activity_title")

    formula_row = next(
        row for row in rows[1:] if str(row[school_id_idx]) == str(context["student_formula"].school_id)
    )

    assert formula_row[student_name_idx] == "'=Formula Student"
    assert formula_row[activity_title_idx] == "'@Activity Two"


"""

new_content = content[:start_idx] + new_func + content[end_idx:]

with open('backend/tests/test_reporting_service.py', 'w') as f:
    f.write(new_content)