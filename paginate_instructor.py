import os

filepath = "frontend/src/features/instructor/InstructorReviewQueue.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Add import
content = content.replace(
    'import { useState, useEffect } from "react";',
    'import { useState, useEffect } from "react";\nimport Pagination from "../../components/ui/Pagination";'
)

# Add pagination state
content = content.replace(
    'const [submissions, setSubmissions] = useState([]);',
    'const [submissions, setSubmissions] = useState([]);\n  const [currentPage, setCurrentPage] = useState(1);\n  const itemsPerPage = 10;'
)

# Add derived state
content = content.replace(
    'const filteredSubmissions = submissions.filter(',
    'const filteredSubmissions = submissions.filter('
)
# We need to slice filteredSubmissions
# I'll just find where filteredSubmissions is used: `filteredSubmissions.map((sub, index) => (`
content = content.replace(
    'filteredSubmissions.map((sub, index) => (',
    'filteredSubmissions.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage).map((sub, index) => ('
)

# Add pagination component at the end of the table
content = content.replace(
    '            </table>\n          </div>',
    '            </table>\n          </div>\n          <Pagination currentPage={currentPage} totalPages={Math.ceil(filteredSubmissions.length / itemsPerPage)} onPageChange={setCurrentPage} />'
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Paginated InstructorReviewQueue")
