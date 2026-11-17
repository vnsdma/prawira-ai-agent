import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file from project root or backend folder
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgrespassword@localhost:5432/prawira_agent_db"
    )

    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    # Gemini
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
    GEMINI_EMBEDDING_MODEL: str = os.getenv("GEMINI_EMBEDDING_MODEL", "models/text-embedding-004")

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    # WhatsApp
    WHATSAPP_GATEWAY: str = os.getenv("WHATSAPP_GATEWAY", "fonnte")
    FONNTE_TOKEN: str = os.getenv("FONNTE_TOKEN", "")
    STORE_DEFAULT_PHONE: str = os.getenv("STORE_DEFAULT_PHONE", "6283132001855")

    # Supabase Live Integration (Prawira Tobacco Production)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
