from fastapi import FastAPI
from app.database import database
from app.routes.activity import router as activity_router

app = FastAPI(
    title="EcoChain Bharat API Gateway",
    version="1.0.0"
)

app.include_router(activity_router)

@app.get("/")
async def root():
    return {
        "message": "EcoChain Bharat API Running"
    }

@app.get("/health")
async def health():

    try:
        await database.command("ping")
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }