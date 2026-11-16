from datetime import datetime
from pydantic import BaseModel, EmailStr
from ...core.base_schema import ORM

class UserCreate(BaseModel):
    nom: str
    email: EmailStr
    mot_de_passe: str

class UserOut(ORM):
    id: int; nom: str; email: str; langue: str

class Token(BaseModel):
    access_token: str; token_type: str = "bearer"

