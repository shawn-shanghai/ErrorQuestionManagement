from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import auth, subjects, tags, questions, review, study, admin, uploads

app = FastAPI(title="ExamCenter API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(subjects.router, prefix="/api/subjects", tags=["subjects"])
app.include_router(tags.router, prefix="/api/tags", tags=["tags"])
app.include_router(questions.router, prefix="/api/questions", tags=["questions"])
app.include_router(review.router, prefix="/api/review", tags=["review"])
app.include_router(study.router, prefix="/api/study", tags=["study"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(uploads.router, prefix="/uploads", tags=["uploads"])


@app.get("/api/health")
def health():
    return {"status": "ok"}
