from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict


class EquipementOut(BaseModel):
    """Équipement associé, renvoyé dans ParcelleOut. Alias camelCase pour matcher le front."""

    id: int
    code: str
    type: str
    en_ligne: bool = Field(alias="enLigne")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class CultureOut(BaseModel):
    id: int
    espece: str
    date_semis: datetime | None = Field(default=None, alias="dateSemis")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ParcelleBase(BaseModel):
    nom: str
    culture: str | None = None  # champ texte historique, affiché tant que `cultures` est vide
    type_sol: str | None = Field(default=None, alias="typeSol")
    date_semis: date | None = Field(default=None, alias="dateSemis")
    surface_ha: float | None = Field(default=None, alias="surface")
    surface_m2: float | None = Field(default=None, alias="surfaceM2")
    seuil_humidite_min: float | None = Field(default=None, alias="seuilHumiditeMin")
    seuil_humidite_max: float | None = Field(default=None, alias="seuilHumiditeMax")

    model_config = ConfigDict(populate_by_name=True)


class ParcelleCreate(ParcelleBase):
    pass


class ParcelleUpdate(ParcelleBase):
    pass


class ParcelleOut(ParcelleBase):
    id: int
    equipements: list[EquipementOut] = []
    cultures: list[CultureOut] = []

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AssocierEquipement(BaseModel):
    equipement_id: int = Field(alias="equipementId")

    model_config = ConfigDict(populate_by_name=True)