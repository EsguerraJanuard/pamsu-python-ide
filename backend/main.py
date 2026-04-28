from fastapi import FastAPI

# Ito yung nag-i-initialize ng backend app natin
app = FastAPI()


# Ito yung unang "endpoint" o URL natin
@app.get("/")
def read_root():
    return {"message": "Hello from PAMSU IDE Backend!"}
