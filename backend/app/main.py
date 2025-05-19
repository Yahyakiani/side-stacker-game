from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# from app.core.config import settings # We'll create this later
# from app.api.v1.endpoints import game_ws # We'll create this later

app = FastAPI(title="Side-Stacker Game API", version="0.1.0")

# CORS (Cross-Origin Resource Sharing) middleware
# Allows your frontend (running on a different port/domain) to communicate with the backend.
# Adjust origins as necessary for production.
origins = [
    "http://localhost",
    "http://localhost:5173", # Default Vite frontend port
    # Add your deployed frontend URL here later
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods
    allow_headers=["*"], # Allows all headers
)

@app.get("/")
async def root():
    return {"message": "Welcome to Side-Stacker Game API"}

@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "healthy"}

# TODO: Later, include routers for WebSockets and other API endpoints
# app.include_router(game_ws.router, prefix="/api/v1/ws", tags=["Game WebSocket"])

if __name__ == "__main__":
    import uvicorn
    # This is for running directly with `python app/main.py` if needed,
    # but Docker will use the CMD in Dockerfile.
    uvicorn.run(app, host="0.0.0.0", port=8000)