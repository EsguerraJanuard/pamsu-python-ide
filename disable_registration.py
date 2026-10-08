import os

filepath = "backend/app/routers/registration.py"
if os.path.exists(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Block start_registration
    content = content.replace(
        "def start_registration_endpoint(\n    registration_data: RegistrationStartRequest,",
        "def start_registration_endpoint(\n    registration_data: RegistrationStartRequest,\n    background_tasks: BackgroundTasks,\n    db: Session = Depends(get_db),\n    delivery_adapter: OTPDeliveryAdapter = Depends(get_otp_delivery_adapter),\n) -> OTPChallengeResponse:\n    raise HTTPException(status_code=403, detail=\"Open registration is disabled per panel recommendations. Please contact the MIS/SuperAdmin to provision your account.\")\n\ndef old_start_registration_endpoint("
    )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Disabled public registration")
