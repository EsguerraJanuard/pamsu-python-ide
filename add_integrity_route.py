import os

filepath = "backend/app/routers/users.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

route = """from pydantic import BaseModel

class IntegrityUpdate(BaseModel):
    is_graded: bool
    tab_switch_increment: int
    blocked_paste_increment: int
    mouseleave_increment: int

@router.patch(
    "/me/integrity",
    status_code=status.HTTP_200_OK,
    summary="Deduct points from academic integrity score",
)
def update_integrity_score(
    payload: IntegrityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Weight factors
    paste_weight = 2.0 if payload.is_graded else 0.5
    tab_weight = 1.0 if payload.is_graded else 0.2
    mouse_weight = 0.5 if payload.is_graded else 0.1
    
    deduction = (
        (payload.blocked_paste_increment * paste_weight) +
        (payload.tab_switch_increment * tab_weight) +
        (payload.mouseleave_increment * mouse_weight)
    )
    
    if deduction > 0:
        current_user.academic_integrity_score = max(0.0, current_user.academic_integrity_score - deduction)
        db.commit()
        db.refresh(current_user)
        
    return {"academic_integrity_score": current_user.academic_integrity_score}
"""

content = content.replace("router = APIRouter(", route + "\nrouter = APIRouter(")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated users.py with integrity route")
