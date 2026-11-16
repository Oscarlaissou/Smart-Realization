from datetime import datetime
from pydantic import BaseModel, EmailStr
from ...core.base_schema import ORM

class DonneeAgroIn(BaseModel):
    parcelle_id: int; ph: float = 6.5; azote: float = 0; phosphore: float = 0; potassium: float = 0

class DonneeAgroOut(ORM, DonneeAgroIn):
    id: int

class ApportIn(BaseModel):
    parcelle_id: int; engrais: str; dose_kg_ha: float; date: datetime | None = None; realise: bool = False

class ApportOut(ORM, ApportIn):
    id: int; date: datetime

