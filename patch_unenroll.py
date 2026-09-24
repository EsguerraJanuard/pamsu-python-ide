import os

service_file = "backend/app/services/classroom_service.py"
router_file = "backend/app/routers/classrooms.py"

service_code = open(service_file).read()

unenroll_code = """
def unenroll_student(db: Session, student_id: int, class_id: int) -> None:
    classroom = get_classroom_by_id(db, class_id)
    
    enrollment = db.query(Enrollment).filter(
        Enrollment.class_id == class_id,
        Enrollment.student_id == student_id
    ).first()
    
    if not enrollment:
        raise EnrollmentNotFoundError("You are not enrolled in this classroom.")
        
    db.delete(enrollment)
    
    _record_audit(
        db=db,
        action="student_unenrolled",
        actor_id=student_id,
        resource_type="enrollment",
        resource_id=enrollment.enrollment_id,
        details={
            "class_id": class_id,
            "subject_code": classroom.subject_code,
            "status": "removed"
        }
    )
    db.commit()
"""

if "def unenroll_student" not in service_code:
    with open(service_file, "a") as f:
        f.write("\n" + unenroll_code)

router_code = open(router_file).read()

if "unenroll_student" not in router_code:
    router_code = router_code.replace("update_enrollment_status,", "update_enrollment_status,\\n    unenroll_student,\\n    EnrollmentNotFoundError,")

endpoint_code = """
@router.delete(
    "/{class_id}/enrollment",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="unenroll_student_from_class",
    summary="Unenroll from a classroom",
)
def unenroll_student_endpoint(
    class_id: int = Path(...),
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
) -> None:
    try:
        unenroll_student(
            db=db,
            student_id=current_student.user_id,
            class_id=class_id
        )
    except EnrollmentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ClassroomNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
"""

if "def unenroll_student_endpoint" not in router_code:
    with open(router_file, "w") as f:
        f.write(router_code + "\\n" + endpoint_code)

print("Patch applied.")
