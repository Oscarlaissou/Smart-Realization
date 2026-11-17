from datetime import datetime
from pydantic import BaseModel
from ...core.base_schema import ORM


class MesureIn(BaseModel):
    parcelle_id: int
    humidite: float


class MesureOut(ORM, MesureIn):
    id: int
    horodatage: datetime


class CycleIn(BaseModel):
    parcelle_id: int
    heure: str
    duree_min: int
    jours: str = "Tous les jours"
    actif: bool = True


class CycleToggle(BaseModel):
    actif: bool


class CycleOut(ORM, CycleIn):
    id: int


class IrrigationOut(ORM):
    id: int
    parcelle_id: int
    debut: datetime
    duree_min: int
    mode: str