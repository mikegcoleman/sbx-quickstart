from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://devboard:devboard@db:5432/devboard"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    class Config:
        env_file = ".env"


settings = Settings()
