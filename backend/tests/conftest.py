"""Les tests n'utilisent JAMAIS la base Supabase : base SQLite en mémoire (voir app/core/database.py).
Ce fichier est chargé par pytest avant les modules de test, donc avant l'import de l'application."""
import os

os.environ["SEVIA_TESTS"] = "1"
os.environ["DATABASE_URL"] = "sqlite://"
os.environ.setdefault("MQTT_ENABLED", "false")
os.environ.setdefault("YOLO_ENABLED", "false")
