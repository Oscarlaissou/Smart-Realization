
from datetime import date, datetime

from pydantic import BaseModel, Field, ConfigDict, field_validator

from ...core.base_schema import ORM


# ============================================================
# EXPLOITATIONS
# ============================================================

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
    user_id: int


# ============================================================
# ÉQUIPEMENTS ASSOCIÉS AUX PARCELLES
# ============================================================

class EquipementOut(BaseModel):
    id: int
    code: str
    type: str
    en_ligne: bool = Field(alias="enLigne")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )


# ============================================================
# CULTURES
# ============================================================

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


class CultureOut(BaseModel):
    id: int
    espece: str
    date_semis: datetime | None = Field(default=None, alias="dateSemis")
    parcelle_id: int

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )


# ============================================================
# PARCELLES
# ============================================================

class ParcelleIn(BaseModel):
    nom: str = Field(min_length=1, max_length=120)
    culture: str | None = None
    type_sol: str | None = Field(default=None, alias="typeSol")
    date_semis: date | None = Field(default=None, alias="dateSemis")
    surface_ha: float = Field(default=0, ge=0, le=100_000, alias="surface")
    surface_m2: float | None = Field(default=None, ge=0, alias="surfaceM2")
    seuil_humidite_min: float | None = Field(
        default=None, ge=0, le=100, alias="seuilHumiditeMin"
    )
    seuil_humidite_max: float | None = Field(
        default=None, ge=0, le=100, alias="seuilHumiditeMax"
    )
    exploitation_id: int = Field(gt=0)

    @field_validator("nom")
    @classmethod
    def nettoyer_nom(cls, valeur: str) -> str:
        valeur = valeur.strip()
        if not valeur:
            raise ValueError("Le nom de la parcelle est obligatoire.")
        return valeur

    model_config = ConfigDict(
        populate_by_name=True
    )


class ParcelleOut(ORM, ParcelleIn):
    id: int
    equipements: list[EquipementOut] = Field(default_factory=list)
    cultures: list[CultureOut] = Field(default_factory=list)

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
