from sqlalchemy import create_engine, text
engine = create_engine('postgresql://postgres:mabangis123@localhost:5432/pamsu_ide_db')
with engine.connect() as conn:
    result = conn.execute(text("SELECT email, password_hash, role FROM users WHERE email = 'admin@pampangastateu.edu.ph'"))
    row = result.fetchone()
    if row:
        print(f"email: {row[0]}, hash: {row[1]}, role: {row[2]}")
    else:
        print("Admin user not found!")
