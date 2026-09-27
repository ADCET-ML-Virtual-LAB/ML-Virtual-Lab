from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, batches, experiments, quizzes, code_submissions, dashboards

app = FastAPI(title="ML Virtual Lab API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(batches.router)
app.include_router(experiments.router)
app.include_router(quizzes.router)
app.include_router(code_submissions.router)
app.include_router(dashboards.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
