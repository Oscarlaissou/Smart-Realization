from datetime import datetime

from pydantic import BaseModel, Field, field_validator
from ...core.base_schema import ORM


class ExploitationIn(BaseModel):
    nom: str = Field(min_length=1, max_length=120)
    localisation: str = Field(default="", max_length=180)

    @field_validator("nom")
    @classmethod
    def nettoyer_nom(cls, valeur: str) -> str:
        valeur = valeur.strip()
        if not valeur:
            raise ValueError("Le nom de l'exploitation est obligatoire.")
        return valeur

    @field_validator("localisation")
    @classmethod
    def nettoyer_localisation(cls, valeur: str) -> str:
        return valeur.strip()


class ExploitationOut(ORM, ExploitationIn):
    id: int


class CultureIn(BaseModel):
    espece: str = Field(min_length=1, max_length=80)
    date_semis: datetime | None = None

    @field_validator("espece")
    @classmethod
    def nettoyer_espece(cls, valeur: str) -> str:
        valeur = valeur.strip()
        if not valeur:
            raise ValueError("L'espèce cultivée est obligatoire.")
        return valeur


class CultureOut(ORM, CultureIn):
    id: int
    parcelle_id: int


class ParcelleIn(BaseModel):
    nom: str = Field(min_length=1, max_length=120)
    surface_ha: float = Field(default=0, ge=0, le=100_000)
    exploitation_id: int = Field(gt=0)

    @field_validator("nom")
    @classmethod
    def nettoyer_nom(cls, valeur: str) -> str:
        valeur = valeur.strip()
        if not valeur:
            raise ValueError("Le nom de la parcelle est obligatoire.")
        return valeur


class ParcelleOut(ORM, ParcelleIn):
    id: int
    cultures: list[CultureOut] = []
