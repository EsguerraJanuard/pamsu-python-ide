with open("frontend/src/features/workspace/Workspace.jsx", "r") as f:
    lines = f.read().split('\n')

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if 'const handleRun = async () => {' in line:
        start_idx = i
        break

if start_idx != -1:
    for i in range(start_idx, len(lines)):
        if '  const handleCheck = async () => {' in lines[i]:
            end_idx = i - 1
            break

if start_idx != -1 and end_idx != -1:
    handle_run_code = """  const handleRun = async () => {
    if (isRunCooldown) return;
    if (!activityId) {
      setExecutionStatus("unavailable");
      setActivePanel("output");
      setOutput("No activity selected.");
      return;
    }
    
    setIsRunCooldown(true);
    setTimeout(() => setIsRunCooldown(false), 3000);
    
    setRunAttemptCount((count) => count + 1);
    setExecutionStatus("running");
    setActivePanel("output");
    setOutput("Running code on Judge0 server...");
    
    try {
      const execRes = await api.post("/execution/requests/", {
        request_kind: "run",
        task_id: parseInt(activityId),
        source_code: code,
        standard_input: standardInput || ""
      });
      pollExecution(execRes.execution_id, false);
    } catch (err) {
      setExecutionStatus("failed");
      const isOffline = err.message === "Failed to fetch" || err.message === "Network Error";
      const msg = isOffline ? "Backend server is not connected or python sandbox is offline." : `Failed to start execution: ${err.message || err.detail || 'Unknown error'}`;
      setOutput(msg);
      setNotice(msg);
    }
  };
"""
    new_lines = lines[:start_idx] + handle_run_code.strip('\n').split('\n') + [""] + lines[end_idx+1:]
    with open("frontend/src/features/workspace/Workspace.jsx", "w") as f:
        f.write('\n'.join(new_lines))
    print("Fixed handleRun")
else:
    print("Could not find block")
