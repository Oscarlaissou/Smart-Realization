from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str = "sevia_cle_secrete_supabase_2026_fixe"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    # Supabase Storage (images de la caméra)
    SUPABASE_URL: str | None = None
    SUPABASE_SERVICE_KEY: str | None = None
    SUPABASE_BUCKET: str = "camera"

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

    # Comptage YOLO (F7.2) — modèle entraîné par backend/training/entrainer.py
    YOLO_ENABLED: bool = True          # le modèle backend/models/mais.pt est versionné : actif par défaut
    YOLO_MODEL: str = "mais.pt"         # fichier dans backend/models/
    YOLO_CONFIANCE: float = 0.15        # meilleur compromis mesuré par training/evaluer_comptage.py
    YOLO_IMGSZ: int = 640               # taille des tuiles (identique à l'entraînement)
    YOLO_ECHELLE: float = 0.5           # réduction avant découpage (identique à l'entraînement)
    YOLO_CHEVAUCHEMENT: int = 64        # recouvrement entre tuiles, en px
    YOLO_CLASSES: str = ""              # "" = toutes les classes du modèle
settings = Settings()