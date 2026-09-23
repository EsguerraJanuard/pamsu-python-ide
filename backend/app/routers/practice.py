import os
import base64
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.domain_models import User, PracticeModule, PracticeTask, PracticeProgress, PracticeAttempt
from app.schemas.practice_schema import PracticeModuleList, PracticeTaskDetail, PracticeSubmissionRequest, PracticeSubmissionResponse, GrowthAnalyticsResponse, ModuleBreakdown
from sqlalchemy import func

from app.core.security import get_current_instructor
from app.schemas.practice_schema import (
    PracticeModuleCreate,
    PracticeModuleUpdate,
    PracticeTaskCreate,
    PracticeTaskUpdate,
    PracticeModuleBase,
    PracticeTaskBase
)
from app.services.ast_evaluator import evaluate_ast_details

router = APIRouter(prefix="/practice", tags=["Solo Practice"])

@router.get("/modules", response_model=List[PracticeModuleList])
def get_practice_modules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    modules = db.query(PracticeModule).order_by(PracticeModule.order_index).all()
    progress = db.query(PracticeProgress).filter(PracticeProgress.student_id == current_user.user_id).all()
    completed_task_ids = {p.task_id for p in progress if p.is_completed}
    attempts_map = {p.task_id: p.attempts_count for p in progress}

    response_modules = []
    is_previous_module_completed = True

    for mod in modules:
        tasks = db.query(PracticeTask).filter(PracticeTask.module_id == mod.module_id).order_by(PracticeTask.order_index).all()
        
        task_details = []
        is_previous_task_completed = True
        module_is_completed = True if tasks else False

        for t in tasks:
            t_completed = t.task_id in completed_task_ids
            t_locked = not is_previous_module_completed or not is_previous_task_completed
            
            task_details.append(
                PracticeTaskDetail(
                    task_id=t.task_id,
                    title=t.title,
                    instructions=t.instructions,
                    starter_code=t.starter_code,
                    order_index=t.order_index,
                    expected_ast_patterns=t.expected_ast_patterns,
                    is_completed=t_completed,
                    attempts_count=attempts_map.get(t.task_id, 0),
                    is_locked=t_locked
                )
            )
            
            if not t_completed:
                is_previous_task_completed = False
                module_is_completed = False

        mod_locked = not is_previous_module_completed
        
        response_modules.append(
            PracticeModuleList(
                module_id=mod.module_id,
                title=mod.title,
                description=mod.description,
                order_index=mod.order_index,
                is_completed=module_is_completed,
                is_locked=mod_locked,
                tasks=task_details
            )
        )
        
        is_previous_module_completed = module_is_completed

    return response_modules

@router.post("/tasks/{task_id}/submit", response_model=PracticeSubmissionResponse)
def submit_practice_task(
    task_id: int,
    request: PracticeSubmissionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(PracticeTask).filter(PracticeTask.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Practice task not found.")

    # 1. Gate 1: Judge0 Execution (Synchronous wait=true for fast practice feedback)
    judge0_url = os.environ.get("JUDGE0_API_URL", "http://judge0-server:2358")
    if judge0_url and not judge0_url.startswith("http"):
        judge0_url = f"https://{judge0_url}"
    judge0_key = os.environ.get("JUDGE0_API_KEY")
    judge0_host = os.environ.get("JUDGE0_HOST")
    
    source_b64 = base64.b64encode(request.code.encode('utf-8')).decode('utf-8')
    expected_out_b64 = base64.b64encode(task.expected_output.encode('utf-8')).decode('utf-8') if task.expected_output else None

    payload = {
        "source_code": source_b64,
        "language_id": 71, # Python
        "expected_output": expected_out_b64,
        "cpu_time_limit": 5.0,
        "memory_limit": 256000,
        "enable_network": False
    }

    execution_feedback = None
    is_successful = False
    
    try:
        
        headers = {}
        if judge0_key:
            headers["X-RapidAPI-Key"] = judge0_key
            headers["X-Auth-Token"] = judge0_key
        if judge0_host:
            headers["X-RapidAPI-Host"] = judge0_host

        with httpx.Client(timeout=httpx.Timeout(15.0)) as client:
            res = client.post(f"{judge0_url}/submissions?base64_encoded=true&wait=true", json=payload, headers=headers)
            res.raise_for_status()
            data = res.json()
            
            status_id = data.get("status", {}).get("id")
            stdout_b64 = data.get("stdout")
            stderr_b64 = data.get("stderr")
            compile_output_b64 = data.get("compile_output")
            message = data.get("message")
            
            stdout_decoded = base64.b64decode(stdout_b64).decode('utf-8') if stdout_b64 else ""
            stderr_decoded = base64.b64decode(stderr_b64).decode('utf-8') if stderr_b64 else ""
            compile_decoded = base64.b64decode(compile_output_b64).decode('utf-8') if compile_output_b64 else ""
            
            if status_id == 3: # Accepted
                is_successful = True
                execution_feedback = stdout_decoded
            elif status_id == 4: # Wrong Answer
                is_successful = False
                execution_feedback = f"Output did not match expected output.\nYour output:\n{stdout_decoded}"
            else:
                is_successful = False
                err_text = stderr_decoded or compile_decoded or str(message)
                execution_feedback = f"Execution Error:\n{err_text}"
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Execution service unavailable: {str(e)}")

    ast_feedback_msgs = []
    # 2. Gate 2: AST Structural Analysis
    if task.expected_ast_patterns:
        try:
            ast_res = evaluate_ast_details(request.code, task.expected_ast_patterns)
            
            if ast_res.get("syntax_error"):
                ast_feedback_msgs.append(f"Syntax Error: {ast_res['syntax_error'].get('message', 'Unknown syntax error')}")
            
            for finding in ast_res.get("findings", []):
                if not finding.get("passed", False):
                    ast_feedback_msgs.append(f"Missing {finding.get('label')}: {finding.get('message')}")
            
            if not ast_res.get("passed"):
                is_successful = False
                if not execution_feedback:
                    execution_feedback = "Code runs successfully but does not meet the structural requirements of this lesson."
        except Exception as e:
            ast_feedback_msgs = [f"AST Parsing error: {str(e)}"]
            is_successful = False

    # 3. Update Progress and Record Attempt
    progress = db.query(PracticeProgress).filter(
        PracticeProgress.student_id == current_user.user_id,
        PracticeProgress.task_id == task_id
    ).first()

    if not progress:
        progress = PracticeProgress(
            student_id=current_user.user_id,
            task_id=task_id,
            attempts_count=0
        )
        db.add(progress)
    
    progress.attempts_count += 1
    if is_successful and not progress.is_completed:
        progress.is_completed = True
        progress.completed_at = func.now()

    attempt = PracticeAttempt(
        student_id=current_user.user_id,
        task_id=task_id,
        submitted_code=request.code,
        is_successful=is_successful,
        execution_feedback=execution_feedback,
        ast_feedback=ast_feedback_msgs
    )
    db.add(attempt)
    db.commit()

    return PracticeSubmissionResponse(
        is_successful=is_successful,
        execution_feedback=execution_feedback,
        ast_feedback=ast_feedback_msgs,
        message="Practice task completed successfully!" if is_successful else "Keep trying!"
    )

def calculate_growth_for_student(db: Session, student_id: int) -> GrowthAnalyticsResponse:
    modules = db.query(PracticeModule).order_by(PracticeModule.order_index).all()
    
    total_tasks = 0
    completed_tasks = 0
    total_attempts = 0
    successful_attempts = 0
    
    breakdown = []
    
    for mod in modules:
        mod_tasks = db.query(PracticeTask).filter(PracticeTask.module_id == mod.module_id).all()
        task_ids = [t.task_id for t in mod_tasks]
        
        mod_total_tasks = len(task_ids)
        mod_completed = 0
        mod_attempts = 0
        
        if task_ids:
            # Count completed tasks
            completed_count = db.query(PracticeProgress).filter(
                PracticeProgress.student_id == student_id,
                PracticeProgress.task_id.in_(task_ids),
                PracticeProgress.is_completed == True
            ).count()
            mod_completed = completed_count
            
            # Count attempts
            attempts = db.query(PracticeAttempt).filter(
                PracticeAttempt.student_id == student_id,
                PracticeAttempt.task_id.in_(task_ids)
            ).all()
            mod_attempts = len(attempts)
            
            total_attempts += mod_attempts
            successful_attempts += sum(1 for a in attempts if a.is_successful)
            
        total_tasks += mod_total_tasks
        completed_tasks += mod_completed
        
        breakdown.append(ModuleBreakdown(
            module_title=mod.title,
            total_tasks=mod_total_tasks,
            completed_tasks=mod_completed,
            attempts_count=mod_attempts
        ))

    # Synthetic Growth Score Algorithm
    # 50% based on Completion
    completion_ratio = (completed_tasks / total_tasks) if total_tasks > 0 else 0
    
    # 50% based on Accuracy (Successful / Total Attempts)
    accuracy_ratio = (successful_attempts / total_attempts) if total_attempts > 0 else 0
    
    # If they completed things flawlessly, they get 100
    # If they completed things but brute forced, they might get 70
    growth_score = int((completion_ratio * 50) + (accuracy_ratio * 50))
    
    return GrowthAnalyticsResponse(
        overall_growth_score=growth_score,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        total_attempts=total_attempts,
        successful_attempts=successful_attempts,
        module_breakdown=breakdown
    )

@router.get("/analytics/growth", response_model=GrowthAnalyticsResponse)
def get_student_growth_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can view their personal growth dashboard")
    
    return calculate_growth_for_student(db, current_user.user_id)


# ==============================================================================
# INSTRUCTOR CRUD ENDPOINTS
# ==============================================================================

@router.get("/instructor/modules", response_model=List[PracticeModuleList])
def get_practice_modules_instructor(
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor)
):
    # Instructors can see all modules
    modules = db.query(PracticeModule).order_by(PracticeModule.order_index).all()
    response_modules = []
    
    for mod in modules:
        tasks = db.query(PracticeTask).filter(PracticeTask.module_id == mod.module_id).order_by(PracticeTask.order_index).all()
        task_details = []
        for t in tasks:
            task_details.append(
                PracticeTaskDetail(
                    task_id=t.task_id,
                    title=t.title,
                    instructions=t.instructions,
                    starter_code=t.starter_code,
                    order_index=t.order_index,
                    expected_ast_patterns=t.expected_ast_patterns,
                    is_completed=False,
                    attempts_count=0,
                    is_locked=False
                )
            )
        response_modules.append(
            PracticeModuleList(
                module_id=mod.module_id,
                title=mod.title,
                description=mod.description,
                order_index=mod.order_index,
                is_completed=False,
                is_locked=False,
                tasks=task_details
            )
        )
    return response_modules

@router.post("/modules", response_model=PracticeModuleBase)
def create_practice_module(
    request: PracticeModuleCreate,
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor)
):
    mod = PracticeModule(
        title=request.title,
        description=request.description,
        order_index=request.order_index,
        instructor_id=current_instructor.user_id
    )
    db.add(mod)
    db.commit()
    db.refresh(mod)
    return mod

@router.put("/modules/{module_id}", response_model=PracticeModuleBase)
def update_practice_module(
    module_id: int,
    request: PracticeModuleUpdate,
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor)
):
    mod = db.query(PracticeModule).filter(PracticeModule.module_id == module_id).first()
    if not mod:
        raise HTTPException(status_code=404, detail="Module not found")
    
    if mod.instructor_id is None:
        raise HTTPException(status_code=403, detail="Cannot edit default seeded modules")
    
    if request.title is not None:
        mod.title = request.title
    if request.description is not None:
        mod.description = request.description
    if request.order_index is not None:
        mod.order_index = request.order_index
        
    db.commit()
    db.refresh(mod)
    return mod

@router.delete("/modules/{module_id}")
def delete_practice_module(
    module_id: int,
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor)
):
    mod = db.query(PracticeModule).filter(PracticeModule.module_id == module_id).first()
    if not mod:
        raise HTTPException(status_code=404, detail="Module not found")
        
    if mod.instructor_id is None:
        raise HTTPException(status_code=403, detail="Cannot delete default seeded modules")
        
    db.delete(mod)
    db.commit()
    return {"message": "Module deleted"}

@router.post("/modules/{module_id}/tasks", response_model=PracticeTaskBase)
def create_practice_task(
    module_id: int,
    request: PracticeTaskCreate,
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor)
):
    mod = db.query(PracticeModule).filter(PracticeModule.module_id == module_id).first()
    if not mod:
        raise HTTPException(status_code=404, detail="Module not found")
        
    if mod.instructor_id is None:
        raise HTTPException(status_code=403, detail="Cannot modify default seeded modules")
        
    task = PracticeTask(
        module_id=module_id,
        title=request.title,
        instructions=request.instructions,
        starter_code=request.starter_code,
        expected_output=request.expected_output,
        expected_ast_patterns=request.expected_ast_patterns,
        order_index=request.order_index
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.put("/tasks/{task_id}", response_model=PracticeTaskBase)
def update_practice_task(
    task_id: int,
    request: PracticeTaskUpdate,
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor)
):
    task = db.query(PracticeTask).filter(PracticeTask.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    mod = task.module
    if mod.instructor_id is None:
        raise HTTPException(status_code=403, detail="Cannot modify default seeded modules")
        
    if request.title is not None:
        task.title = request.title
    if request.instructions is not None:
        task.instructions = request.instructions
    if request.starter_code is not None:
        task.starter_code = request.starter_code
    if request.expected_output is not None:
        task.expected_output = request.expected_output
    if request.expected_ast_patterns is not None:
        task.expected_ast_patterns = request.expected_ast_patterns
    if request.order_index is not None:
        task.order_index = request.order_index
        
    db.commit()
    db.refresh(task)
    return task

@router.delete("/tasks/{task_id}")
def delete_practice_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor)
):
    task = db.query(PracticeTask).filter(PracticeTask.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    mod = task.module
    if mod.instructor_id is None:
        raise HTTPException(status_code=403, detail="Cannot modify default seeded modules")
        
    db.delete(task)
    db.commit()
    return {"message": "Task deleted"}
