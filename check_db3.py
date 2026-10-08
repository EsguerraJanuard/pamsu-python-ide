from sqlalchemy import create_engine, text
engine = create_engine('postgresql://postgres:mabangis123@localhost:5432/pamsu_ide_db')
with engine.connect() as conn:
    result = conn.execute(text("SELECT first_name, last_name, email FROM users WHERE email LIKE '%202330%'"))
    for row in result:
        print(f"first_name: '{row[0]}', last_name: '{row[1]}', email: {row[2]}")
