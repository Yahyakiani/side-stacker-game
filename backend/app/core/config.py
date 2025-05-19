from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

# Load .env file from the backend directory
# This is useful if config.py is imported before main.py fully sets up paths
# or when running scripts directly.
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
else:
    # Fallback if .env is in the root of the backend directory (e.g. when running locally without docker)
    load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str = "Side-Stacker Game"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@host:port/db")

    # We can add more settings here as needed
    # e.g., CORS_ORIGINS: list = ["http://localhost:5173"]

    class Config:
        case_sensitive = True
        # env_file = ".env" # pydantic-settings can also load .env directly
        # env_file_encoding = 'utf-8'

settings = Settings()

# print(f"Loaded DATABASE_URL: {settings.DATABASE_URL}") # For debugging