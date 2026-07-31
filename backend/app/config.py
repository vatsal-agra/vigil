from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://vigil:vigil@db:5432/vigil"
    redis_url: str = "redis://cache:6379/0"
    jwt_secret: str = "change-me-in-production"
    jwt_ttl_minutes: int = 60 * 24
    probe_interval_seconds: int = 30
    probe_timeout_seconds: float = 8.0
    failure_threshold: int = 2
    cors_origins: str = "http://localhost:3000"
    seed_demo_data: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
