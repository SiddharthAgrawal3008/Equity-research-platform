from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.financial_data import router as financial_data_router
from backend.routes.pipeline import router as pipeline_router
from backend.routes.chat import router as chat_router

app = FastAPI(title="Equity Research Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route registrations
app.include_router(financial_data_router, prefix="/api")
app.include_router(pipeline_router, prefix="/api")
app.include_router(chat_router, prefix="/api")


@app.get("/")
def root():
    return {"message": "Equity Research Platform API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}
