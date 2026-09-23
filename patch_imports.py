import re

def add_import(filepath, import_stmt):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if import_stmt not in content:
        # insert after the last import statement
        lines = content.split('\n')
        last_import_idx = -1
        for i, line in enumerate(lines):
            if line.startswith('import '):
                last_import_idx = i
        
        if last_import_idx != -1:
            lines.insert(last_import_idx + 1, import_stmt)
            content = '\n'.join(lines)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

add_import('frontend/src/features/instructor/ClassManagement.jsx', "import AlertModal from '../../components/modals/AlertModal';")
add_import('frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx', "import AlertModal from '../../../components/modals/AlertModal';")
add_import('frontend/src/features/workspace/Workspace.jsx', "import ConfirmationModal from '../../components/modals/ConfirmationModal';")

