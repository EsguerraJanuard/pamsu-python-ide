import os

filepath = "frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Add import if not exists
if "ConfirmationModal" not in content:
    content = content.replace(
        "import React, { useState, useEffect, useRef } from 'react';",
        "import React, { useState, useEffect, useRef } from 'react';\nimport ConfirmationModal from '../../../components/modals/ConfirmationModal';"
    )

# Add state
if "showRetakeModal" not in content:
    content = content.replace(
        "const [savingGrade, setSavingGrade] = useState(false);",
        "const [savingGrade, setSavingGrade] = useState(false);\n  const [showRetakeModal, setShowRetakeModal] = useState(false);\n  const [retakeTargetId, setRetakeTargetId] = useState(null);"
    )

# Replace window.confirm calls with setting state
# There are two places with: if (!window.confirm("Are you sure you want to allow a retake? The student workspace will be unlocked.")) return;
# Let's just create a wrapper function for the handleAllowRetake logic. Wait, they might be inline.
# I'll manually edit it using regex or just rewrite it cleanly.
