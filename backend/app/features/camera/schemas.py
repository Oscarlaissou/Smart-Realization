from datetime import datetime
from pydantic import BaseModel, EmailStr
from ...core.base_schema import ORM

class ComptageOut(ORM):
    id: int; parcelle_id: int; nb_plants: int; date: datetime

