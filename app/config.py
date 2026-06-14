from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.

    Pydantic Settings reads from a .env file automatically.
    Every field here maps to an environment variable of the same name.
    This approach avoids hardcoded values and makes the app 12-factor compliant.
    """

    # Database connection string using asyncpg driver for async support
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/expenseflow"

    # JWT configuration
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = {
        "env_file": ".env",       # Load from .env file in project root
        "case_sensitive": True,    # Match exact casing of env var names
    }


# Singleton instance — imported wherever settings are needed
settings = Settings()
