from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SECRET_KEY: str = "sevia_cle_secrete_supabase_2026_fixe"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    # Supabase Storage (images de la caméra)
    SUPABASE_SERVICE_KEY: str | None = None
    SUPABASE_BUCKET: str = "camera"

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

    # Comptage YOLO (F7.2) — modèle entraîné par backend/training/entrainer.py
    YOLO_ENABLED: bool = True          # le modèle backend/models/mais.pt est versionné : actif par défaut
    YOLO_MODEL: str = "mais.pt"         # fichier dans backend/models/
    YOLO_CONFIANCE: float = 0.15        # meilleur compromis mesuré par training/evaluer_comptage.py
    YOLO_IMGSZ: int = 640               # taille des tuiles (identique à l'entraînement)
    YOLO_ECHELLE: float = 0.5           # réduction avant découpage (identique à l'entraînement)
    YOLO_CHEVAUCHEMENT: int = 64        # recouvrement entre tuiles, en px
    YOLO_CLASSES: str = ""              # "" = toutes les classes du modèle


settings = Settings()
