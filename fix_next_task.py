import re

with open("frontend/src/features/practice/PracticeWorkspace.jsx", "r") as f:
    content = f.read()

# Remove setNextTaskId(null); from handleSubmit
content = content.replace("    setNextTaskId(null);\n", "")

# Remove the redundant re-calculation inside handleSubmit
redundant_calc = """      if (res.is_successful) {
        // Find next task id
        if (moduleDetails) {
          const tIndex = moduleDetails.tasks.findIndex(t => String(t.task_id) === String(taskId));
          if (tIndex !== -1 && tIndex < moduleDetails.tasks.length - 1) {
            setNextTaskId(moduleDetails.tasks[tIndex + 1].task_id);
          }
        }
      } else {"""
replacement = """      if (!res.is_successful) {"""
content = content.replace(redundant_calc, replacement)

with open("frontend/src/features/practice/PracticeWorkspace.jsx", "w") as f:
    f.write(content)
print("Removed bad recalculation")
