from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator
from ...core.base_schema import ORM


class UserCreate(BaseModel):
    nom: str
    email: EmailStr
    mot_de_passe: str


class UserOut(ORM):
    id: int
    nom: str
    email: str
    langue: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProfilIn(BaseModel):
    nom: str = Field(min_length=1, max_length=120)
    telephone: str = Field(default="", max_length=40)
    role: str = Field(default="Exploitant agricole", max_length=80)
    langue: str = Field(default="fr", max_length=10)
    # Adresse des alertes : "" ou absente = aucune ; envoyée seule, elle ne touche pas aux autres champs
    email_alertes: EmailStr | None = None

    @field_validator("email_alertes", mode="before")
    @classmethod
    def email_vide(cls, valeur):
        if valeur is None:
            return None
        valeur = str(valeur).strip()
        return valeur or None

    @field_validator("nom", "telephone", "role", "langue")
    @classmethod
    def nettoyer(cls, valeur: str) -> str:
        return valeur.strip()

    @field_validator("nom")
    @classmethod
    def verifier_nom(cls, valeur: str) -> str:
        if not valeur:
            raise ValueError("Le nom est obligatoire.")
        return valeur

    @field_validator("langue")
    @classmethod
    def verifier_langue(cls, valeur: str) -> str:
        if valeur not in {"fr", "en"}:
            raise ValueError("Langue prise en charge : fr ou en")
        return valeur


class MotDePasseIn(BaseModel):
    ancien_mot_de_passe: str
    nouveau_mot_de_passe: str = Field(min_length=6, max_length=128)
