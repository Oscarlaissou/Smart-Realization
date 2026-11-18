from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SECRET_KEY: str = "sevia_cle_secrete_supabase_2026_fixe"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    MQTT_ENABLED: bool = True
    MQTT_HOST: str = "broker.hivemq.com"
    MQTT_BROKER: str | None = None
    MQTT_PORT: int = 1883
    MQTT_TOPIC: str = "sevia/#"
    MQTT_USERNAME: str | None = None
    MQTT_PASSWORD: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def model_post_init(self, __context) -> None:
        if self.MQTT_BROKER and self.MQTT_HOST == "broker.hivemq.com":
            self.MQTT_HOST = self.MQTT_BROKER
        elif not self.MQTT_BROKER:
            self.MQTT_BROKER = self.MQTT_HOST


settings = Settings()