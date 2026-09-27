with open('backend/tests/test_openapi_contracts.py', 'r') as f:
    c = f.read()
c = c.replace('"text/csv"', '"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"')
with open('backend/tests/test_openapi_contracts.py', 'w') as f:
    f.write(c)

with open('backend/tests/test_reporting_router.py', 'r') as f:
    d = f.read()
d = d.replace('build_gradebook_csv_export', 'build_gradebook_excel_export')
with open('backend/tests/test_reporting_router.py', 'w') as f:
    f.write(d)

with open('backend/tests/test_reporting_service.py', 'r') as f:
    e = f.read()
e = e.replace('build_gradebook_csv_export', 'build_gradebook_excel_export')
with open('backend/tests/test_reporting_service.py', 'w') as f:
    f.write(e)