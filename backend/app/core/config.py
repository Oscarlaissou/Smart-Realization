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

    # Notifications par e-mail (smtplib)
    NOTIFICATIONS_EMAIL_ACTIVES: bool = False
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USE_TLS: bool = True
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "alertes@sevia.local"

    # Notifications par SMS (Twilio ou Africa's Talking)
    NOTIFICATIONS_SMS_ACTIVES: bool = False
    SMS_PROVIDER: str = ""  # "twilio" ou "africastalking"
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""
    AFRICASTALKING_USERNAME: str = ""
    AFRICASTALKING_API_KEY: str = ""
    AFRICASTALKING_FROM: str = "SEVIA"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def model_post_init(self, __context) -> None:
        if self.MQTT_BROKER and self.MQTT_HOST == "broker.hivemq.com":
            self.MQTT_HOST = self.MQTT_BROKER
        elif not self.MQTT_BROKER:
            self.MQTT_BROKER = self.MQTT_HOST


settings = Settings()
