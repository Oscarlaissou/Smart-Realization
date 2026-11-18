from datetime import date, datetime

from pydantic import AliasChoices, BaseModel, Field, field_validator
from ...core.base_schema import ORM


def _alias(*noms: str) -> AliasChoices:
    """Accepte en entrée le nom Python (snake_case) ET l'ancien nom camelCase du front."""
    return AliasChoices(*noms)


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

    @field_validator("localisation", mode="before")
    @classmethod
    def nettoyer_localisation(cls, valeur: str | None) -> str:
        return (valeur or "").strip()


class ExploitationOut(ORM, ExploitationIn):
    id: int


class CultureIn(BaseModel):
    espece: str = Field(min_length=1, max_length=80)
    date_semis: datetime | None = Field(default=None, validation_alias=_alias("date_semis", "dateSemis"))

    @field_validator("espece")
    @classmethod
    def nettoyer_espece(cls, valeur: str) -> str:
        valeur = valeur.strip()
        if not valeur:
            raise ValueError("L'espèce cultivée est obligatoire.")
        return valeur


class CultureOut(ORM):
    id: int
    espece: str
    date_semis: datetime | None = None
    parcelle_id: int


class EquipementResume(ORM):
    """Équipement associé, renvoyé dans ParcelleOut."""
    id: int
    code: str
    type: str
    en_ligne: bool


class ParcelleIn(BaseModel):
    nom: str = Field(min_length=1, max_length=120)
    surface_ha: float = Field(default=0, ge=0, le=100_000, validation_alias=_alias("surface_ha", "surface"))
    exploitation_id: int = Field(gt=0, validation_alias=_alias("exploitation_id", "exploitationId"))
    # Champs ajoutés par la branche équipements / fertilisation (facultatifs)
    culture: str | None = Field(default=None, max_length=100)  # champ texte historique ; la vraie source est `cultures`
    type_sol: str | None = Field(default=None, max_length=100, validation_alias=_alias("type_sol", "typeSol"))
    date_semis: date | None = Field(default=None, validation_alias=_alias("date_semis", "dateSemis"))
    surface_m2: float | None = Field(default=None, ge=0, validation_alias=_alias("surface_m2", "surfaceM2"))
    seuil_humidite_min: float | None = Field(
        default=None, ge=0, le=100, validation_alias=_alias("seuil_humidite_min", "seuilHumiditeMin")
    )
    seuil_humidite_max: float | None = Field(
        default=None, ge=0, le=100, validation_alias=_alias("seuil_humidite_max", "seuilHumiditeMax")
    )

    @field_validator("nom")
    @classmethod
    def nettoyer_nom(cls, valeur: str) -> str:
        valeur = valeur.strip()
        if not valeur:
            raise ValueError("Le nom de la parcelle est obligatoire.")
        return valeur

    @field_validator("culture", "type_sol")
    @classmethod
    def nettoyer_texte(cls, valeur: str | None) -> str | None:
        if valeur is None:
            return None
        return valeur.strip() or None


class ParcelleOut(ORM):
    id: int
    nom: str
    surface_ha: float | None = 0
    exploitation_id: int | None = None
    culture: str | None = None
    type_sol: str | None = None
    date_semis: date | None = None
    surface_m2: float | None = None
    seuil_humidite_min: float | None = None
    seuil_humidite_max: float | None = None
    cultures: list[CultureOut] = []
    equipements: list[EquipementResume] = []


class AssocierEquipement(BaseModel):
    equipement_id: int = Field(gt=0, validation_alias=_alias("equipement_id", "equipementId"))
