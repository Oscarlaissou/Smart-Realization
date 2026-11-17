from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str = "sevia_cle_secrete_supabase_2026_fixe"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Paramètres MQTT (utilisés au démarrage dans main.py)
    MQTT_ENABLED: bool = False
    MQTT_BROKER: str = "localhost"
    MQTT_PORT: int = 1883
    MQTT_TOPIC: str = "sevia/#"
    MQTT_USERNAME: str | None = None
    MQTT_PASSWORD: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()