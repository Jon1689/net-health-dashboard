from fastapi import FastAPI

app = FastAPI(title="Network Health & Threat Dashboard")

@app.get("/")
def root():
    return {"message": "Net Health Dashboard API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}