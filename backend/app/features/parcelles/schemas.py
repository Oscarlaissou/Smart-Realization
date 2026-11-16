from datetime import datetime
from pydantic import BaseModel, EmailStr
from ...core.base_schema import ORM

class ExploitationIn(BaseModel):
    nom: str; localisation: str = ""

class ExploitationOut(ORM, ExploitationIn):
    id: int

class CultureIn(BaseModel):
    espece: str; date_semis: datetime | None = None

class CultureOut(ORM, CultureIn):
    id: int

class ParcelleIn(BaseModel):
    nom: str; surface_ha: float = 0; exploitation_id: int

class ParcelleOut(ORM, ParcelleIn):
    id: int; cultures: list[CultureOut] = []

