import re

def process_grading_workspace():
    filepath = 'frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Imports
    content = content.replace("import InstructorSidebar from '../../../components/layout/InstructorSidebar';", 
                              "import InstructorSidebar from '../../../components/layout/InstructorSidebar';\nimport AlertModal from '../../../components/modals/AlertModal';")

    # State
    content = content.replace("const [savingGrade, setSavingGrade] = useState(false);", 
                              "const [savingGrade, setSavingGrade] = useState(false);\n  const [alertConfig, setAlertConfig] = useState(null);")

    # Alerts
    content = content.replace("alert('Grade saved successfully');", "setAlertConfig({ title: 'Success', message: 'Grade saved successfully', isError: false });")
    content = content.replace("alert('Failed to save grade');", "setAlertConfig({ title: 'Error', message: 'Failed to save grade', isError: true });")
    content = content.replace('alert("Failed to export Excel gradebook. Please try again.");', "setAlertConfig({ title: 'Export Failed', message: 'Failed to export Excel gradebook. Please try again.', isError: true });")

    # Render
    modal = """
      <AlertModal 
        isOpen={!!alertConfig} 
        title={alertConfig?.title} 
        message={alertConfig?.message} 
        isError={alertConfig?.isError} 
        onClose={() => setAlertConfig(null)} 
      />
    </div>"""
    content = re.sub(r'</div>\s*$', modal, content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def process_class_management():
    filepath = 'frontend/src/features/instructor/ClassManagement.jsx'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Imports
    content = content.replace("import CreateClassModal from '../../components/modals/CreateClassModal';", 
                              "import CreateClassModal from '../../components/modals/CreateClassModal';\nimport AlertModal from '../../components/modals/AlertModal';")

    # State
    content = content.replace("const [loading, setLoading] = useState(true);", 
                              "const [loading, setLoading] = useState(true);\n  const [alertConfig, setAlertConfig] = useState(null);")

    # Alerts
    content = content.replace("alert(typeof err === 'string' ? err : err.message || 'Failed to create classroom');", 
                              "setAlertConfig({ title: 'Error', message: typeof err === 'string' ? err : err.message || 'Failed to create classroom', isError: true });")
    content = content.replace("alert('Failed to update classroom status.');", 
                              "setAlertConfig({ title: 'Error', message: 'Failed to update classroom status.', isError: true });")

    # Render
    modal = """
      <AlertModal 
        isOpen={!!alertConfig} 
        title={alertConfig?.title} 
        message={alertConfig?.message} 
        isError={alertConfig?.isError} 
        onClose={() => setAlertConfig(null)} 
      />
    </div>"""
    content = re.sub(r'</div>\s*$', modal, content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def process_workspace():
    filepath = 'frontend/src/features/workspace/Workspace.jsx'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Imports
    content = content.replace("import { useParams, useNavigate } from \"react-router-dom\";", 
                              "import { useParams, useNavigate } from \"react-router-dom\";\nimport ConfirmationModal from '../../components/modals/ConfirmationModal';")

    # State
    content = content.replace("const [isSidebarOpen, setIsSidebarOpen] = useState(true);", 
                              "const [isSidebarOpen, setIsSidebarOpen] = useState(true);\n  const [confirmConfig, setConfirmConfig] = useState(null);")

    # Replace confirm function logic
    old_reset = """  const handleResetDraft = () => {
    const confirmed = window.confirm(
      "Reset this draft to the starter code?",
    );

    if (!confirmed) {
      return;
    }

    // Attempt to use activity starter code if available
    setCode(DEFAULT_CODE);
    setOutput("Draft reset to the starter code.");
    setExecutionStatus("idle");
    setNotice("Draft reset successfully.");
  };"""

    new_reset = """  const handleResetDraft = () => {
    setConfirmConfig({
      title: "Reset Draft",
      message: "Reset this draft to the starter code?",
      onConfirm: () => {
        setCode(DEFAULT_CODE);
        setOutput("Draft reset to the starter code.");
        setExecutionStatus("idle");
        setNotice("Draft reset successfully.");
        setConfirmConfig(null);
      }
    });
  };"""

    content = content.replace(old_reset, new_reset)

    # Render
    modal = """
      <ConfirmationModal 
        isOpen={!!confirmConfig} 
        title={confirmConfig?.title} 
        message={confirmConfig?.message} 
        onConfirm={confirmConfig?.onConfirm}
        onCancel={() => setConfirmConfig(null)} 
        isDanger={true}
        confirmText="Reset"
      />
    </div>"""
    content = re.sub(r'</div>\s*$', modal, content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)


def process_practice_module():
    filepath = 'frontend/src/features/instructor/PracticeModuleManager.jsx'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Imports
    content = content.replace("import InstructorSidebar from '../../components/layout/InstructorSidebar';", 
                              "import InstructorSidebar from '../../components/layout/InstructorSidebar';\nimport AlertModal from '../../components/modals/AlertModal';\nimport ConfirmationModal from '../../components/modals/ConfirmationModal';")

    # State
    content = content.replace("const [selectedModuleId, setSelectedModuleId] = useState(null);", 
                              "const [selectedModuleId, setSelectedModuleId] = useState(null);\n  const [alertConfig, setAlertConfig] = useState(null);\n  const [confirmConfig, setConfirmConfig] = useState(null);")

    # Replace Alerts
    content = content.replace("alert(err.message || 'Failed to save module');", "setAlertConfig({ title: 'Error', message: err.message || 'Failed to save module', isError: true });")
    content = content.replace("alert(err.message || 'Failed to delete module');", "setAlertConfig({ title: 'Error', message: err.message || 'Failed to delete module', isError: true });")
    content = content.replace('alert(err.message || \'Failed to save task. Ensure Expected AST Patterns is valid JSON (e.g. {"FunctionDef": 1})\');', 'setAlertConfig({ title: \'Error\', message: err.message || \'Failed to save task. Ensure Expected AST Patterns is valid JSON (e.g. {"FunctionDef": 1})\', isError: true });')
    content = content.replace("alert(err.message || 'Failed to delete task');", "setAlertConfig({ title: 'Error', message: err.message || 'Failed to delete task', isError: true });")

    # Replace Confirms
    old_delete_module = """  const handleDeleteModule = async (moduleId) => {
    if (!confirm('Are you sure you want to delete this module and ALL its tasks? This action cannot be undone.')) return;
    try {
      await api.delete(`/practice/modules/${moduleId}`);
      fetchModules();
    } catch (err) {
      setAlertConfig({ title: 'Error', message: err.message || 'Failed to delete module', isError: true });
    }
  };"""

    new_delete_module = """  const handleDeleteModule = (moduleId) => {
    setConfirmConfig({
      title: 'Delete Module',
      message: 'Are you sure you want to delete this module and ALL its tasks? This action cannot be undone.',
      isDanger: true,
      onConfirm: async () => {
        setConfirmConfig(null);
        try {
          await api.delete(`/practice/modules/${moduleId}`);
          fetchModules();
        } catch (err) {
          setAlertConfig({ title: 'Error', message: err.message || 'Failed to delete module', isError: true });
        }
      }
    });
  };"""
    content = content.replace(old_delete_module, new_delete_module)

    old_delete_task = """  const handleDeleteTask = async (taskId) => {
    if (!confirm('Are you sure you want to delete this task?')) return;
    try {
      await api.delete(`/practice/tasks/${taskId}`);
      fetchModules();
    } catch (err) {
      setAlertConfig({ title: 'Error', message: err.message || 'Failed to delete task', isError: true });
    }
  };"""

    new_delete_task = """  const handleDeleteTask = (taskId) => {
    setConfirmConfig({
      title: 'Delete Task',
      message: 'Are you sure you want to delete this task?',
      isDanger: true,
      onConfirm: async () => {
        setConfirmConfig(null);
        try {
          await api.delete(`/practice/tasks/${taskId}`);
          fetchModules();
        } catch (err) {
          setAlertConfig({ title: 'Error', message: err.message || 'Failed to delete task', isError: true });
        }
      }
    });
  };"""
    content = content.replace(old_delete_task, new_delete_task)

    # Render
    modal = """
      <AlertModal 
        isOpen={!!alertConfig} 
        title={alertConfig?.title} 
        message={alertConfig?.message} 
        isError={alertConfig?.isError} 
        onClose={() => setAlertConfig(null)} 
      />
      <ConfirmationModal 
        isOpen={!!confirmConfig} 
        title={confirmConfig?.title} 
        message={confirmConfig?.message} 
        onConfirm={confirmConfig?.onConfirm}
        onCancel={() => setConfirmConfig(null)} 
        isDanger={confirmConfig?.isDanger}
        confirmText="Delete"
      />
    </div>"""
    content = re.sub(r'</div>\s*$', modal, content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

process_grading_workspace()
process_class_management()
process_workspace()
process_practice_module()
