from sqlalchemy import create_engine, text
engine = create_engine('postgresql://postgres:mabangis123@localhost:5432/pamsu_ide_db')
with engine.connect() as conn:
    result = conn.execute(text("SELECT created_at FROM users WHERE email = 'admin@pampangastateu.edu.ph'"))
    row = result.fetchone()
    print("Created at:", row[0])
