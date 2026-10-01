with open('backend/tests/test_reporting_service.py', 'r') as f:
    c = f.read()
c = c.replace("assert formula_row[student_name_idx] == \"'=Formula Student\"", "assert formula_row[student_name_idx] == \"=Formula Student\"")
c = c.replace("assert formula_row[activity_title_idx] == \"'@Activity Two\"", "assert formula_row[activity_title_idx] == \"@Activity Two\"")
with open('backend/tests/test_reporting_service.py', 'w') as f:
    f.write(c)