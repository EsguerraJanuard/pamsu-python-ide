from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hash_val = "$2b$04$jf5/T0RFkx12gtXhOJs8X.8UNmxNtAIx5ELoSlVXQeNarkQjXN8QW"
print("Admin@2026 match:", pwd_context.verify("Admin@2026", hash_val))
