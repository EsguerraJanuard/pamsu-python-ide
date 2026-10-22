import logging
from typing import List

from app.core.database import get_db
from app.core.rate_limit import enforce_rate_limit, limit_per_user
from app.core.security import get_current_instructor, get_current_student
from app.models.domain_models import (PracticeAttempt, PracticeModule,
                                      PracticeProgress, PracticeTask, User)
from app.schemas.execution_schema import Judge0CallbackPayload
from app.schemas.practice_schema import (GrowthAnalyticsResponse,
                                         ModuleBreakdown,
                                         PracticeAiHintResponse,
                                         PracticeModuleBase,
                                         PracticeModuleCreate,
                                         PracticeModuleList,
                                         PracticeModuleUpdate,
                                         PracticeSubmissionRequest,
                                         PracticeSubmissionResponse,
                                         PracticeTaskBase, PracticeTaskCreate,
                                         PracticeTaskDetail,
                                         PracticeTaskUpdate)
from app.services import practice_evaluation_service as practice_evaluation
from app.services import practice_hint_store
from app.services.ai_tutor_service import (TUTOR_UNAVAILABLE_MESSAGE,
                                           generate_pedagogical_hint)
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/practice", tags=["Solo Practice"])

@router.get("/modules", response_model=List[PracticeModuleList])
def get_practice_modules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
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

@router.post(
    "/tasks/{task_id}/submit",
    response_model=PracticeSubmissionResponse,
    # Each submission is a paid Judge0 call.
    dependencies=[Depends(limit_per_user("practice_submit", limit=3, window_seconds=10))],
)
def submit_practice_task(
    task_id: int,
    request: PracticeSubmissionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    """Save the attempt and queue it for Judge0; answers at once with status "pending".

    Judge0 runs the code in the background and calls back with the result
    (PUT /practice/internal/judge0-callback); poll GET
    /practice/attempts/{attempt_id} until the status is "completed" or "failed".
    """
    task = db.query(PracticeTask).filter(PracticeTask.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Practice task not found.")

    attempt = practice_evaluation.new_pending_attempt(
        db, student_id=current_user.user_id, task_id=task_id, code=request.code,
    )
    if not practice_evaluation.queue_practice_attempt(db, attempt):
        raise HTTPException(status_code=503, detail="The code execution service is unavailable. Please try again shortly.")

    return practice_evaluation.to_response(attempt)


@router.get(
    "/attempts/{attempt_id}",
    response_model=PracticeSubmissionResponse,
    # The practice page polls this every 1.5 s while Judge0 runs the code.
    dependencies=[Depends(limit_per_user("practice_attempt_poll", limit=90, window_seconds=60))],
)
def get_practice_attempt(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    attempt = (
        db.query(PracticeAttempt)
        .filter(PracticeAttempt.attempt_id == attempt_id, PracticeAttempt.student_id == current_user.user_id)
        .first()
    )
    if not attempt:
        raise HTTPException(status_code=404, detail="Practice attempt not found.")

    # An attempt Judge0 never answered is closed here, so the page stops waiting.
    attempt = practice_evaluation.expire_if_stale(db, attempt)
    return practice_evaluation.to_response(attempt)


@router.put(
    "/internal/judge0-callback",
    status_code=200,
    include_in_schema=False,
)
def apply_practice_judge0_callback(
    payload: Judge0CallbackPayload,
    attempt_id: int = Query(..., gt=0),
    correlation_id: str = Query(..., min_length=36, max_length=36),
    db: Session = Depends(get_db),
):
    """Judge0's result for a practice attempt.

    Judge0 sends no credentials. The correlation_id, a random UUID that only
    the server and Judge0 see, binds the call to one pending attempt; an
    unknown pair is 404 and a finished attempt is 409 (nothing changes).
    """
    try:
        attempt = practice_evaluation.record_judge0_result(
            db, attempt_id=attempt_id, correlation_id=correlation_id, payload=payload,
        )
    except practice_evaluation.PracticeAttemptNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Practice attempt not found or correlation token mismatch.") from exc
    except practice_evaluation.PracticeAttemptFinishedError as exc:
        raise HTTPException(status_code=409, detail="Practice attempt is already finished.") from exc
    return {"attempt_id": attempt.attempt_id, "status": attempt.status}


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
            
            # Count judged attempts only: pending ones have no verdict yet and
            # failed ones never ran (system errors, not the student's tries).
            attempts = db.query(PracticeAttempt).filter(
                PracticeAttempt.student_id == student_id,
                PracticeAttempt.task_id.in_(task_ids),
                PracticeAttempt.status == "completed",
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
    current_user: User = Depends(get_current_student)
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
    if mod.instructor_id != current_instructor.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this module")
    
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
    if mod.instructor_id != current_instructor.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this module")
        
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
    if mod.instructor_id != current_instructor.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this module")
        
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
    if mod.instructor_id != current_instructor.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to modify tasks in this module")
        
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
    if mod.instructor_id != current_instructor.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete tasks in this module")
        
    db.delete(task)
    db.commit()
    return {"message": "Task deleted"}



def _generate_hint_bg(attempt_id: int, task_instructions: str, student_code: str, error_output: str):
    # Runs after the response is sent; it needs no database session.
    try:
        hint = generate_pedagogical_hint(
            task_instructions=task_instructions,
            student_code=student_code,
            error_output=error_output,
        )

        if hint:
            practice_hint_store.save_hint(attempt_id, hint)
        else:
            practice_hint_store.save_failure(attempt_id)
    except Exception:
        logger.exception("AI hint generation failed for practice attempt %s.", attempt_id)
        practice_hint_store.save_failure(attempt_id)
    finally:
        practice_hint_store.release_generation(attempt_id)


@router.post(
    "/attempts/{attempt_id}/ai-hint",
    response_model=PracticeAiHintResponse,
    # The client polls this route until the hint is ready; polls are a
    # database read and a Redis GET. Only calls that start a Gemini request
    # count against the "practice_ai_hint" limit below.
    dependencies=[Depends(limit_per_user("practice_ai_hint_poll", limit=60, window_seconds=60))],
)
def get_ai_hint(
    attempt_id: int,
    background_tasks: BackgroundTasks,
    # After a failed generation the client sends retry=true to try again;
    # plain polls get the "unavailable" answer until it expires.
    retry: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    attempt = db.query(PracticeAttempt).filter(PracticeAttempt.attempt_id == attempt_id, PracticeAttempt.student_id == current_user.user_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Practice attempt not found.")
    
    if attempt.status == "pending":
        raise HTTPException(status_code=409, detail="This attempt is still being checked.")
    if attempt.status == "failed":
        raise HTTPException(status_code=400, detail="This attempt could not be run, so there is no result to explain.")
    if attempt.is_successful:
        raise HTTPException(status_code=400, detail="Cannot generate AI hint for successful attempts.")

    hint = practice_hint_store.get_hint(attempt_id)
    if hint:
        return PracticeAiHintResponse(ai_hint=hint, status="completed")

    failed = practice_hint_store.generation_failed(attempt_id)
    if failed and not retry:
        # "completed" keeps clients that predate `unavailable` from polling
        # (and starting a new generation) in a loop.
        return PracticeAiHintResponse(ai_hint=TUTOR_UNAVAILABLE_MESSAGE, status="completed", unavailable=True)

    # Only the first caller starts a generation; later polls wait for it.
    if not practice_hint_store.claim_generation(attempt_id):
        return PracticeAiHintResponse(ai_hint=None, status="processing")

    try:
        enforce_rate_limit(scope="practice_ai_hint", identifier=str(current_user.user_id), limit=10, window_seconds=300)
    except HTTPException:
        practice_hint_store.release_generation(attempt_id)
        raise

    if failed:
        practice_hint_store.clear_failure(attempt_id)

    error_output = attempt.execution_feedback or "The output did not match the expected output."
    if attempt.ast_feedback:
        error_output += "\n" + "\n".join(str(message) for message in attempt.ast_feedback)

    background_tasks.add_task(
        _generate_hint_bg,
        attempt_id,
        attempt.task.instructions,
        attempt.submitted_code,
        error_output,
    )

    return PracticeAiHintResponse(ai_hint=None, status="processing")
