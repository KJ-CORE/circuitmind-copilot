from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routes import router as api_router
from app.config import settings

try:
    Base.metadata.create_all(bind=engine)
    print("[Database] Tables created successfully.")
except Exception as e:
    print(f"[Database] Error creating tables on startup: {e}")

app = FastAPI(
    title=settings.app_name,
    description="CircuitMind API - Natural Language Electronics Design Co-pilot",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "environment": settings.environment
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
