from sqlalchemy import create_engine, text
engine = create_engine('postgresql://postgres:mabangis123@localhost:5432/postgres')
with engine.connect() as conn:
    result = conn.execute(text("SELECT datname FROM pg_database"))
    for row in result:
        print(row[0])
