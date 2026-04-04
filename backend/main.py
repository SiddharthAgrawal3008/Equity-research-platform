from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.analysis import router as analysis_router

app = FastAPI(title="Equity Research Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route registrations
app.include_router(analysis_router, prefix="/api")


@app.get("/")
def root():
    return {"message": "Equity Research Platform API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}
