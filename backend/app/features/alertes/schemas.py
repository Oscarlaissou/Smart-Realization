from datetime import datetime

from pydantic import BaseModel, Field, field_validator
from ...core.base_schema import ORM


class AlerteOut(ORM):
    id: int
    parcelle_id: int | None
    niveau: str
    message: str
    lue: bool
    date: datetime
    categorie: str = "systeme"
    canaux: list[str] = []


class PreferenceIn(BaseModel):
    categorie: str = Field(min_length=1, max_length=40)
    notification: bool = True
    email: bool = False
    sms: bool = False

    @field_validator("categorie")
    @classmethod
    def normaliser_categorie(cls, valeur: str) -> str:
        return valeur.strip().lower()


class PreferenceOut(ORM, PreferenceIn):
    id: int | None = None
    libelle: str = ""


class CompteurOut(BaseModel):
    non_lues: int
    total: int
