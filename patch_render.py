import re

def process_file_render(filepath, modal_component):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the last </div> before );
    # A bit hard with regex, let's just insert it right before the last "  );\n}" or similar
    pattern = r'(\s*</div>\s*\);\s*\}?\s*export default)'
    
    # Try finding the match
    match = re.search(r'(</div>\s*\)\s*;\s*\}?\s*export default)', content)
    if match:
        replacement = f"{modal_component}\n{match.group(1)}"
        content = content.replace(match.group(1), replacement)
    else:
        # Just look for the last </div>
        idx = content.rfind("</div>")
        if idx != -1:
            content = content[:idx] + modal_component + "\n" + content[idx:]

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

alert_modal = """
      <AlertModal 
        isOpen={!!alertConfig} 
        title={alertConfig?.title} 
        message={alertConfig?.message} 
        isError={alertConfig?.isError} 
        onClose={() => setAlertConfig(null)} 
      />"""

confirm_modal = """
      <ConfirmationModal 
        isOpen={!!confirmConfig} 
        title={confirmConfig?.title} 
        message={confirmConfig?.message} 
        onConfirm={confirmConfig?.onConfirm}
        onCancel={() => setConfirmConfig(null)} 
        isDanger={confirmConfig?.isDanger}
        confirmText="Confirm"
      />"""

process_file_render('frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx', alert_modal)
process_file_render('frontend/src/features/instructor/ClassManagement.jsx', alert_modal)
process_file_render('frontend/src/features/workspace/Workspace.jsx', confirm_modal)
process_file_render('frontend/src/features/instructor/PracticeModuleManager.jsx', alert_modal + "\n" + confirm_modal)
