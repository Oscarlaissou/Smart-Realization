from datetime import datetime
from pydantic import BaseModel, EmailStr
from ...core.base_schema import ORM

class EquipementIn(BaseModel):
    code: str; type: str; parcelle_id: int | None = None

class EquipementOut(ORM, EquipementIn):
    id: int; en_ligne: bool
    derniere_donnee: datetime | None = None