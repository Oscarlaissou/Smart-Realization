"""Contrôle d'accès commun : un utilisateur ne voit et ne modifie QUE ses propres données.

Règle unique pour toutes les fonctionnalités :
utilisateur -> ses exploitations -> leurs parcelles -> tout ce qui est rattaché à ces parcelles
(mesures, arrosages, alertes, apports, comptages, équipements...).

Un objet qui n'appartient pas à l'utilisateur renvoie 404 (et non 403) : on ne révèle pas
qu'il existe chez quelqu'un d'autre.
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..features.parcelles.models import Exploitation, Parcelle


def ids_exploitations(db: Session, user) -> list[int]:
    return [e.id for e in db.query(Exploitation.id).filter(Exploitation.user_id == user.id).all()]


def ids_parcelles(db: Session, user) -> list[int]:
    return [
        p.id
        for p in db.query(Parcelle.id)
        .join(Exploitation, Parcelle.exploitation_id == Exploitation.id)
        .filter(Exploitation.user_id == user.id)
        .all()
    ]


def parcelles_de(db: Session, user) -> list[Parcelle]:
    return (
        db.query(Parcelle)
        .join(Exploitation, Parcelle.exploitation_id == Exploitation.id)
        .filter(Exploitation.user_id == user.id)
        .order_by(Parcelle.id)
        .all()
    )


def parcelle_de(db: Session, pid: int, user) -> Parcelle:
    """La parcelle si elle appartient à l'utilisateur, sinon 404."""
    parcelle = (
        db.query(Parcelle)
        .join(Exploitation, Parcelle.exploitation_id == Exploitation.id)
        .filter(Parcelle.id == pid, Exploitation.user_id == user.id)
        .first()
    )
    if not parcelle:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Parcelle introuvable")
    return parcelle


def exploitation_principale(db: Session, user) -> Exploitation:
    """Première exploitation de l'utilisateur (créée à l'inscription), sinon 400."""
    exploitation = (
        db.query(Exploitation).filter(Exploitation.user_id == user.id).order_by(Exploitation.id).first()
    )
    if not exploitation:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Aucune exploitation associée à ce compte.")
    return exploitation
