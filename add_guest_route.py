import os

filepath = "backend/app/routers/admin.py"
if os.path.exists(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    guest_schema = """
class GuestCreate(BaseModel):
    email: str
    first_name: str
    last_name: str
    password: str

@router.post("/guests", response_model=UserResponse)
def create_guest(
    request: GuestCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Guest with this email already exists")
    
    new_guest = User(
        email=request.email,
        first_name=request.first_name,
        last_name=request.last_name,
        role="guest",
        password_hash=get_password_hash(request.password),
        school_id="GUEST-" + str(random.randint(1000, 9999)),
        email_verified=True
    )
    db.add(new_guest)
    db.commit()
    db.refresh(new_guest)
    return new_guest
"""
    # Insert right before create_instructor
    if "@router.post(\"/instructors\"" in content:
        content = content.replace('@router.post("/instructors"', guest_schema + '\n@router.post("/instructors"')
        
        # Make sure random is imported
        if "import random" not in content:
            content = "import random\n" + content
            
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print("Added guest provisioning endpoint")
