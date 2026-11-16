from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://sevia:sevia@localhost:5432/sevia"
    SECRET_KEY: str = "dev-secret"
    MQTT_HOST: str = "localhost"
    MQTT_PORT: int = 1883
    MQTT_ENABLED: bool = False  # passer à True quand le broker tourne
    class Config:
        env_file = ".env"

settings = Settings()
