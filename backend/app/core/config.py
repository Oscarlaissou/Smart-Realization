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

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
