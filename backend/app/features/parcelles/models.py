from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ...core.database import Base

class Exploitation(Base):               # Gestion des plantations
    __tablename__ = "exploitations"
    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(120))
    localisation: Mapped[str] = mapped_column(String(180), default="")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

class Parcelle(Base):
    __tablename__ = "parcelles"
    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(120))
    surface_ha: Mapped[float] = mapped_column(Float, default=0)
    exploitation_id: Mapped[int] = mapped_column(ForeignKey("exploitations.id"))
    cultures: Mapped[list["Culture"]] = relationship(cascade="all, delete-orphan")

class Culture(Base):
    __tablename__ = "cultures"
    id: Mapped[int] = mapped_column(primary_key=True)
    espece: Mapped[str] = mapped_column(String(80))
    date_semis: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    parcelle_id: Mapped[int] = mapped_column(ForeignKey("parcelles.id"))

