import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.endpoints import temp_game_http # Import the new router
from app.api.v1.endpoints import game_ws
from app.api.v1.endpoints import user_stats

from app.core.logging_config import setup_logger, LOG_LEVEL

logger = setup_logger(__name__, level=LOG_LEVEL)

logger.info(f"Starting up {settings.PROJECT_NAME}...")
logger.info(f"Log level set to: {logging.getLevelName(logger.getEffectiveLevel())}")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS (Cross-Origin Resource Sharing) middleware
origins = [
    "http://localhost",
    "http://localhost:5173",  # Default frontend port
]
if hasattr(settings, 'CORS_ORIGINS') and settings.CORS_ORIGINS: # If defined in config
    origins.extend([str(origin) for origin in settings.CORS_ORIGINS if str(origin) not in origins])


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

logger.info(f"CORS middleware configured for origins: {origins}")


@app.get("/")
async def root():
    logger.debug("Root endpoint '/' was called.")
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}

@app.get(f"{settings.API_V1_STR}/health", tags=["Health"])
async def health_check():
    """
    Simple health check endpoint.
    """
    logger.info("Health check endpoint called.")
    return {"status": "healthy"}

# Include the temporary HTTP game router
app.include_router(
    temp_game_http.router, 
    prefix=f"{settings.API_V1_STR}/temp-game", # Prefix for these temp endpoints
    tags=["Temporary HTTP Game (In-Memory)"]    # Tag for OpenAPI docs
)

logger.info(
    f"Included temporary HTTP game router at prefix: {settings.API_V1_STR}/temp-game"
)


# WebSocket game router
app.include_router(
    game_ws.router, prefix=f"{settings.API_V1_STR}/ws-game", tags=["Game WebSocket"]
)


app.include_router(
    user_stats.router,
    prefix=settings.API_V1_STR, # Assuming /api/v1/users/{username}/stats
    tags=["User Statistics"]
)
logger.info(f"Included user statistics router at prefix: {settings.API_V1_STR}")

if __name__ == "__main__":

    logger.info("Running Uvicorn directly from main.py")
    uvicorn.run(app, host="0.0.0.0", port=8000)
