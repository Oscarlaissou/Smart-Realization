from datetime import datetime
from pydantic import Field, computed_field
from ...core.base_schema import ORM
from . import stockage


class ComptageOut(ORM):
    id: int
    parcelle_id: int
    nb_plants: int
    date: datetime
    image_path: str
    detections_path: str | None = Field(default=None, exclude=True)   # sert à calculer l'URL, pas renvoyé tel quel

    @computed_field
    @property
    def image_url(self) -> str:
        """URL de l'image : Supabase Storage (ou /media en mode local)."""
        return stockage.url_publique(self.image_path)

    @computed_field
    @property
    def image_detections_url(self) -> str:
        """Image avec les cadres YOLO ; vide si YOLO était désactivé lors de l'envoi."""
        return stockage.url_publique(self.detections_path) if self.detections_path else ""


class ParcelleCameraOut(ORM):
    """Parcelle telle que la page « Suivi par caméra » en a besoin (pastilles de choix)."""
    id: int
    nom: str