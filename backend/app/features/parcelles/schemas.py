from datetime import date
from pydantic import BaseModel, Field, ConfigDict


class EquipementOut(BaseModel):
    """Représentation d'un équipement associé, renvoyée dans ParcelleOut.
    Les alias camelCase matchent ce qu'attend le front (Parcelles.jsx)."""

    id: int
    code: str
    type: str
    en_ligne: bool = Field(alias="enLigne")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ParcelleBase(BaseModel):
    nom: str
    culture: str | None = None
    surface: float | None = None
    date_semis: date | None = Field(default=None, alias="dateSemis")
    type_sol: str | None = Field(default=None, alias="typeSol")

    # populate_by_name=True : accepte aussi bien le nom python (date_semis)
    # que l'alias camelCase (dateSemis) envoyé par le front.
    model_config = ConfigDict(populate_by_name=True)


class ParcelleCreate(ParcelleBase):
    pass


class ParcelleUpdate(ParcelleBase):
    pass


class ParcelleOut(ParcelleBase):
    id: int
    equipements: list[EquipementOut] = []

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AssocierEquipement(BaseModel):
    equipement_id: int = Field(alias="equipementId")

    model_config = ConfigDict(populate_by_name=True)