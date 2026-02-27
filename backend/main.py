
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.config import settings
from backend.routers import gateway, analytics, security, external
from backend.dependencies import get_db  # Now async version

app = FastAPI(
    title="AegisCAN-RT API",
    description="Real-time BLE-to-CAN gateway with AI security features",
    version="0.1.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
)

# CORS - allow Streamlit frontend (port 8501)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "*"  # temporary for testing - remove in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(gateway.router, prefix="/api/gateway", tags=["Gateway"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(external.router, prefix="/api/external", tags=["External Data"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "environment": settings.ENVIRONMENT}

# Example: protected endpoint using DB (uncomment when needed)
# @app.get("/test-db")
# async def test_db(db: AsyncSession = Depends(get_db)):
#     return {"db_connected": True}

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )