"""
Configuration settings for Game API service
"""
import os


class Settings:
    """Application settings"""

    # Database settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://gameuser:gamepassword@localhost:5432/videogame_calendar"
    )
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))

    # Redis settings
    REDIS_URL: str | None = os.getenv("REDIS_URL", "redis://localhost:6379")

    # API settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # CORS settings
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")

    # Cache settings
    CACHE_TTL_GAMES: int = int(os.getenv("CACHE_TTL_GAMES", "300"))  # 5 minutes
    CACHE_TTL_GAME_DETAIL: int = int(os.getenv("CACHE_TTL_GAME_DETAIL", "600"))  # 10 minutes
    CACHE_TTL_SEARCH: int = int(os.getenv("CACHE_TTL_SEARCH", "600"))  # 10 minutes
    CACHE_TTL_REFERENCE: int = int(os.getenv("CACHE_TTL_REFERENCE", "1800"))  # 30 minutes

    # Pagination settings
    DEFAULT_PAGE_SIZE: int = int(os.getenv("DEFAULT_PAGE_SIZE", "20"))
    MAX_PAGE_SIZE: int = int(os.getenv("MAX_PAGE_SIZE", "100"))

# Global settings instance
settings = Settings()
