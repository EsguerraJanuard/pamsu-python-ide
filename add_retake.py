import os
import re

filepath = "frontend/src/features/submissions/SubmissionDetails.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Add state and API
content = content.replace(
    'export default function SubmissionDetails({ submission, onBack }) {',
    'import { useState } from "react";\nimport api from "../../services/api";\n\nexport default function SubmissionDetails({ submission, onBack }) {\n  const [isRequesting, setIsRequesting] = useState(false);\n  const [retakeRequested, setRetakeRequested] = useState(submission.status === "retake_requested");\n\n  const handleRequestRetake = async () => {\n    setIsRequesting(true);\n    try {\n      await api.post(`/submissions/${submission.id}/retake-request`);\n      setRetakeRequested(true);\n    } catch (err) {\n      console.error("Failed to request retake", err);\n    } finally {\n      setIsRequesting(false);\n    }\n  };\n'
)

button_html = """
                  </div>
                  { (submission.status === 'graded' || submission.status === 'rejected') && !retakeRequested && (
                    <button
                      onClick={handleRequestRetake}
                      disabled={isRequesting}
                      className="mt-2 text-xs font-semibold px-3 py-1.5 bg-psu-maroon text-white dark:bg-psu-gold dark:text-black rounded hover:opacity-90 disabled:opacity-50"
                    >
                      {isRequesting ? 'Requesting...' : 'Request Retake'}
                    </button>
                  )}
                  { retakeRequested && (
                    <span className="mt-2 inline-block text-xs font-semibold px-3 py-1.5 bg-amber-500/10 text-amber-500 rounded border border-amber-500/20">
                      Retake Requested - Awaiting Instructor
                    </span>
                  )}
                  <p className="mt-1 text-xs text-text-muted">
"""

content = content.replace(
    '                  </div>\n                  <p className="mt-1 text-xs text-text-muted">',
    button_html
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Added Retake Request to SubmissionDetails")
