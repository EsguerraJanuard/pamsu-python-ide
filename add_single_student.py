import os

filepath = "backend/app/routers/admin.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

schema_code = """class InstructorCreate(BaseModel):
    email: str
    first_name: str
    last_name: str
    password: str

class StudentCreate(BaseModel):
    email: str
    first_name: str
    last_name: str
    school_id: str
    password: str"""
    
content = content.replace("class InstructorCreate(BaseModel):\n    email: str\n    first_name: str\n    last_name: str\n    password: str", schema_code)

route_code = """@router.post("/students", response_model=UserResponse)
def create_student(
    request: StudentCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    existing = db.query(User).filter((User.email == request.email) | (User.school_id == request.school_id)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student with this email or school ID already exists")
    
    new_student = User(
        email=request.email,
        first_name=request.first_name,
        last_name=request.last_name,
        role="student",
        password_hash=get_password_hash(request.password),
        school_id=request.school_id,
        email_verified=True
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student

@router.post("/instructors", response_model=UserResponse)"""

content = content.replace('@router.post("/instructors", response_model=UserResponse)', route_code)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated admin.py")
