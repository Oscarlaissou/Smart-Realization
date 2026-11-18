from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.security import (
    hacher_mot_de_passe,
    verifier_mot_de_passe,
    creer_token,
    current_user,
)
from .models import User
from .schemas import ProfilIn
from ..parcelles.models import Exploitation

router = APIRouter(prefix="/auth", tags=["Authentification"])


class InscriptionIn(BaseModel):
    nom: str
    telephone: str = ""
    email: EmailStr
    nom_exploitation: str
    role: str = "Exploitant agricole"
    mot_de_passe: str


class ConnexionIn(BaseModel):
    email: EmailStr
    mot_de_passe: str


def _utilisateur_json(utilisateur: User) -> dict:
    return {
        "id": utilisateur.id,
        "nom": utilisateur.nom,
        "email": utilisateur.email,
        "telephone": utilisateur.telephone,
        "role": utilisateur.role,
        "langue": utilisateur.langue,
    }


@router.post("/inscription", status_code=201)
def inscrire(donnees: InscriptionIn, db: Session = Depends(get_db)):
    email_propre = donnees.email.lower().strip()
    if db.query(User).filter(User.email == email_propre).first():
        raise HTTPException(400, "Cette adresse e-mail est déjà utilisée.")

    if len(donnees.mot_de_passe) < 6:
        raise HTTPException(400, "Le mot de passe doit contenir au moins 6 caractères.")

    try:
        utilisateur = User(
            nom=donnees.nom.strip(),
            telephone=donnees.telephone.strip(),
            email=email_propre,
            role=donnees.role.strip() or "Exploitant agricole",
            langue="fr",
            mot_de_passe_hash=hacher_mot_de_passe(donnees.mot_de_passe),
        )
        db.add(utilisateur)
        db.flush()  # Génère utilisateur.id sans fermer la transaction

        champs_expl = {
            "nom": donnees.nom_exploitation.strip() or f"Exploitation de {utilisateur.nom}"
        }
        if hasattr(Exploitation, "localisation"):
            champs_expl["localisation"] = ""
        if hasattr(Exploitation, "user_id"):
            champs_expl["user_id"] = utilisateur.id
        elif hasattr(Exploitation, "proprietaire_id"):
            champs_expl["proprietaire_id"] = utilisateur.id

        exploitation = Exploitation(**champs_expl)
        db.add(exploitation)
        db.commit()  # Valide User et Exploitation en une seule requête Supabase
        db.refresh(utilisateur)
    except Exception as e:
        db.rollback()
        raise HTTPException(400, f"Erreur lors de l'enregistrement : {e}")

    token = creer_token(utilisateur.id, utilisateur.email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "utilisateur": _utilisateur_json(utilisateur),
    }


@router.post("/connexion")
def connecter(donnees: ConnexionIn, db: Session = Depends(get_db)):
    email_propre = donnees.email.lower().strip()
    utilisateur = db.query(User).filter(User.email == email_propre).first()

    if not utilisateur or not verifier_mot_de_passe(donnees.mot_de_passe, utilisateur.mot_de_passe_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Adresse e-mail ou mot de passe incorrect.",
        )

    token = creer_token(utilisateur.id, utilisateur.email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "utilisateur": _utilisateur_json(utilisateur),
    }


@router.get("/moi")
def profil_connecte(user: User = Depends(current_user)):
    return _utilisateur_json(user)


@router.put("/moi")
def modifier_profil(
    donnees: ProfilIn,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    user.nom = donnees.nom
    user.telephone = donnees.telephone
    user.role = donnees.role
    user.langue = donnees.langue
    db.commit()
    db.refresh(user)
    return _utilisateur_json(user)


