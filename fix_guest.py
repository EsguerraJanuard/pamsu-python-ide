import os
import re

filepath = "backend/app/routers/auth.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

replacement = """@router.post("/guest", response_model=TokenResponse, dependencies=[Depends(RateLimiter(times=2, seconds=60))])
def login_guest(db: Session = Depends(get_db)):
    import random
    import uuid
    from app.models.domain_models import Classroom, Enrollment
    from app.core.utils import get_utc_now
    
    short_id = str(uuid.uuid4())[:6]
    guest_email = f"guest_{short_id}@pampangastateu.edu.ph"
    
    guest = User(
        email=guest_email,
        first_name="Aspiring Student",
        last_name=f"Guest {short_id.upper()}",
        middle_name="",
        role="student",
        password_hash=get_password_hash("guest"),
        school_id=f"GST{random.randint(10000, 99999)}"
    )
    db.add(guest)
    db.commit()
    db.refresh(guest)
    
    # Auto-enroll guest in the first available class so they can see the system
    first_class = db.query(Classroom).first()
    if first_class:
        enroll = Enrollment(
            class_id=first_class.class_id,
            student_id=guest.user_id,
            status="active",
            joined_at=get_utc_now()
        )
        db.add(enroll)
        db.commit()

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(guest.user_id), "role": guest.role},
        expires_delta=access_token_expires,
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(guest)
    )"""

# We need to replace the entire login_guest function.
# It starts at @router.post("/guest" and ends before the next @router or end of file.
pattern = r"@router\.post\(\"/guest\".*?user=UserResponse\.model_validate\(guest\)\n    \)"
content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated auth.py")

filepath = "backend/app/routers/admin.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Hide guests from admin dashboard
content = content.replace(
    'users = db.query(User).filter(User.role != "admin").offset(skip).limit(limit).all()',
    'users = db.query(User).filter(User.role != "admin", ~User.email.startswith("guest_")).offset(skip).limit(limit).all()'
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated admin.py")
