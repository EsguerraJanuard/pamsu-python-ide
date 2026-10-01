import os
import re

filepath = "frontend/src/features/submissions/Submissions.jsx"
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
    'const [submissions, setSubmissions] = useState([]);\n  const [currentPage, setCurrentPage] = useState(1);\n  const itemsPerPage = 5;'
)

# Replace map
content = content.replace(
    '{submissions.map((submission, index) => {',
    '{submissions.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage).map((submission, index) => {'
)

# Add pagination component
content = re.sub(
    r'(</section>\n\s*</main>)',
    r'  <Pagination currentPage={currentPage} totalPages={Math.ceil(submissions.length / itemsPerPage)} onPageChange={setCurrentPage} />\n      \1',
    content
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Paginated Submissions")
