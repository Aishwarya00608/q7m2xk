"""
Application configuration using Pydantic Settings.
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Elexon API
    ELEXON_BASE_URL: str = "https://data.elexon.co.uk/bmrs/api/v1"
    ELEXON_TIMEOUT: int = 60  # seconds

    # Day-ahead market decision cutoff
    # Nord Pool's official N2EX support documentation states that the UK
    # day-ahead gate closes at 09:50 GMT. January 2026 is GMT (UTC+0).
    # This remains configurable because a utility's purchasing process may
    # use a different operational cutoff.
    # A forecast is eligible for a delivery day D if it was published
    # at or before 09:50 UTC on day D-1.
    DAY_AHEAD_CUTOFF_HOUR_UTC: int = 9
    DAY_AHEAD_CUTOFF_MINUTE_UTC: int = 50

    # Analysis period
    ANALYSIS_START_DATE: str = "2026-01-01"
    ANALYSIS_END_DATE: str = "2026-01-31"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000", "http://localhost:4173"]

    # Cache TTL in seconds (30 minutes)
    CACHE_TTL_SECONDS: int = 1800

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
