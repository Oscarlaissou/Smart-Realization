from datetime import datetime
from pydantic import BaseModel, EmailStr
from ...core.base_schema import ORM

class MesureIn(BaseModel):
    parcelle_id: int; humidite: float

class MesureOut(ORM, MesureIn):
    id: int; horodatage: datetime

class CycleIn(BaseModel):
    parcelle_id: int; heure: str; duree_min: int; jours: str = "tous"; actif: bool = True

class CycleOut(ORM, CycleIn):
    id: int

class IrrigationOut(ORM):
    id: int; parcelle_id: int; debut: datetime; duree_min: int; mode: str

