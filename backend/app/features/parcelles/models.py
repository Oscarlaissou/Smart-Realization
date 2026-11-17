from datetime import date
from sqlalchemy import String, Float, Date
from sqlalchemy.orm import Mapped, mapped_column

from ...core.database import Base


class Parcelle(Base):
    __tablename__ = "parcelles"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(100))
    culture: Mapped[str | None] = mapped_column(String(100), nullable=True)
    surface: Mapped[float | None] = mapped_column(Float, nullable=True)
    date_semis: Mapped[date | None] = mapped_column(Date, nullable=True)
    type_sol: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Pas de relationship() ici : on évite de modifier equipements/models.py.
    # Le routeur interroge directement la table equipements via parcelle_id.