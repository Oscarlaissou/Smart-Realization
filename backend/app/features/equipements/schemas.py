from pydantic import BaseModel, Field, field_validator
from ...core.base_schema import ORM


class EquipementIn(BaseModel):
    code: str = Field(min_length=1, max_length=40)
    type: str = Field(min_length=1, max_length=20)
    parcelle_id: int | None = None
    en_ligne: bool = True

    @field_validator("code", "type")
    @classmethod
    def nettoyer(cls, valeur: str) -> str:
        valeur = valeur.strip()
        if not valeur:
            raise ValueError("Le code et le type sont obligatoires.")
        return valeur


class EquipementOut(ORM, EquipementIn):
    id: int
