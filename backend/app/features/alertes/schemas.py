from datetime import datetime
from pydantic import BaseModel, EmailStr
from ...core.base_schema import ORM

class AlerteOut(ORM):
    id: int; parcelle_id: int | None; niveau: str; message: str; lue: bool; date: datetime

