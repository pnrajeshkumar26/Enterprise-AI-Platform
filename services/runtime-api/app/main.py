from fastapi import FastAPI

app = FastAPI(
    title="Enterprise AI Platform Runtime API",
    version="0.1.0",
    description="Production-grade Runtime API for Enterprise AI Platform",
)

@app.get("/")
def root():
    return {
        "message": "Welcome to Enterprise AI Platform Runtime API"
    }