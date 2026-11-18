from datetime import date, datetime
from sqlalchemy import String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...core.database import Base


class Exploitation(Base):
    """Une exploitation agricole, créée automatiquement à l'inscription
    (voir features/auth/router.py)."""

    __tablename__ = "exploitations"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(150))
    localisation: Mapped[str | None] = mapped_column(String(200), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)


class Parcelle(Base):
    __tablename__ = "parcelles"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(100))
    # Champ texte historique déjà présent sur la table (en plus de la relation `cultures`
    # ci-dessous, qui est la vraie source pour le dashboard).
    culture: Mapped[str | None] = mapped_column(String(100), nullable=True)
    type_sol: Mapped[str | None] = mapped_column(String(100), nullable=True)
    date_semis: Mapped[date | None] = mapped_column(Date, nullable=True)
    surface_ha: Mapped[float | None] = mapped_column(Float, nullable=True)
    surface_m2: Mapped[float | None] = mapped_column(Float, nullable=True)
    seuil_humidite_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    seuil_humidite_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    exploitation_id: Mapped[int | None] = mapped_column(
        ForeignKey("exploitations.id"), nullable=True
    )

    cultures: Mapped[list["Culture"]] = relationship(back_populates="parcelle")

    # Pas de relationship() vers Equipement : on évite de modifier equipements/models.py.
    # Le routeur parcelles interroge directement la table equipements via parcelle_id.


class Culture(Base):
    """Une culture plantée sur une parcelle (ex: Maïs, Tomate), avec sa propre
    date de semis — une parcelle peut avoir plusieurs cultures dans le temps."""

    __tablename__ = "cultures"

    id: Mapped[int] = mapped_column(primary_key=True)
    espece: Mapped[str] = mapped_column(String(100))
    date_semis: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    parcelle_id: Mapped[int] = mapped_column(ForeignKey("parcelles.id"))

    parcelle: Mapped["Parcelle"] = relationship(back_populates="cultures")