from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    LOW_STOCK_THRESHOLD: int = 20

    class Config:
        env_file = ".env"


settings = Settings()