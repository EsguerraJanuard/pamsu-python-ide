import os

filepath = "frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add Import
content = content.replace("import React, { useState, useEffect, useRef } from 'react';", "import React, { useState, useEffect, useRef } from 'react';\nimport ConfirmationModal from '../../../components/modals/ConfirmationModal';")

# 2. Add State
content = content.replace("const [savingGrade, setSavingGrade] = useState(false);", "const [savingGrade, setSavingGrade] = useState(false);\n  const [showRetakeModal, setShowRetakeModal] = useState(false);\n  const [retakeTargetType, setRetakeTargetType] = useState(null); // 'approve' or 'allow'")

# 3. Add handleRetakeConfirm function
handle_func = """
  const handleRetakeConfirm = async () => {
    if (!detailedSub) return;
    try {
      await api.patch(`/submissions/${detailedSub.sub_id || detailedSub.id}/allow-retake`);
      if (retakeTargetType === 'approve') {
        setNotice("Retake approved! Student can now resubmit.");
        setDetailedSub({...detailedSub, retake_allowed: true, retake_requested: false});
      } else {
        setNotice("Retake allowed! Student can now resubmit.");
        setDetailedSub({...detailedSub, retake_allowed: true});
      }
      fetchSubmissions();
    } catch (err) {
      setNotice("Failed to allow retake.");
    }
    setShowRetakeModal(false);
  };
"""
content = content.replace("const handleExport = () => {", handle_func + "\n  const handleExport = () => {")

# 4. Replace first onClick
first_onclick = """onClick={async () => {
                            if (!window.confirm("Are you sure you want to allow a retake? The student workspace will be unlocked.")) return;
                            try {
                              await api.patch(`/submissions/${detailedSub.sub_id || detailedSub.id}/allow-retake`);
                              setNotice("Retake approved! Student can now resubmit.");
                              setDetailedSub({...detailedSub, retake_allowed: true, retake_requested: false});
                              fetchSubmissions();
                            } catch (err) {
                              setNotice("Failed to approve retake.");
                            }
                          }}"""
new_first_onclick = """onClick={() => {
                            setRetakeTargetType('approve');
                            setShowRetakeModal(true);
                          }}"""
content = content.replace(first_onclick, new_first_onclick)

# 5. Replace second onClick
second_onclick = """onClick={async () => {
                            if (!window.confirm("Are you sure you want to allow a retake? The student workspace will be unlocked.")) return;
                            try {
                              await api.patch(`/submissions/${detailedSub.sub_id || detailedSub.id}/allow-retake`);
                              setNotice("Retake allowed! Student can now resubmit.");
                              setDetailedSub({...detailedSub, retake_allowed: true});
                              fetchSubmissions();
                            } catch (err) {
                              setNotice("Failed to allow retake.");
                            }
                          }}"""
new_second_onclick = """onClick={() => {
                            setRetakeTargetType('allow');
                            setShowRetakeModal(true);
                          }}"""
content = content.replace(second_onclick, new_second_onclick)

# 6. Add Modal Component at the end of the return
modal_jsx = """
      <ConfirmationModal
        isOpen={showRetakeModal}
        title="Allow Retake"
        message="Are you sure you want to allow a retake? The student's workspace will be unlocked and they can submit again."
        confirmText="Allow Retake"
        onConfirm={handleRetakeConfirm}
        onCancel={() => setShowRetakeModal(false)}
        isDanger={false}
      />
    </div>
"""
content = content.replace("</div>\n    </div>\n  );\n}", modal_jsx + "  );\n}")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Refactored Modal")
