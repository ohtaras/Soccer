from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import fixtures, predictions

app = FastAPI(title="Soccer Prediction API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(fixtures.router, prefix="/api")
app.include_router(predictions.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
