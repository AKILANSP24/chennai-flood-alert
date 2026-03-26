from fastapi import FastAPI # type: ignore

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "Dashboard Placeholder. UI Implementation Pending."}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
