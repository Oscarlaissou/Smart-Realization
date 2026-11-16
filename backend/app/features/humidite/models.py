from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ...core.database import Base

class Mesure(Base):                     # Humidité en temps réel
    __tablename__ = "mesures"
    id: Mapped[int] = mapped_column(primary_key=True)
    parcelle_id: Mapped[int] = mapped_column(ForeignKey("parcelles.id"), index=True)
    humidite: Mapped[float] = mapped_column(Float)
    horodatage: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

class CycleIrrigation(Base):            # programmation
    __tablename__ = "cycles_irrigation"
    id: Mapped[int] = mapped_column(primary_key=True)
    parcelle_id: Mapped[int] = mapped_column(ForeignKey("parcelles.id"))
    heure: Mapped[str] = mapped_column(String(5))
    duree_min: Mapped[int] = mapped_column(Integer)
    jours: Mapped[str] = mapped_column(String(60), default="tous")
    actif: Mapped[bool] = mapped_column(Boolean, default=True)

class Irrigation(Base):                 # journal des irrigations
    __tablename__ = "irrigations"
    id: Mapped[int] = mapped_column(primary_key=True)
    parcelle_id: Mapped[int] = mapped_column(ForeignKey("parcelles.id"))
    debut: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    duree_min: Mapped[int] = mapped_column(Integer, default=0)
    mode: Mapped[str] = mapped_column(String(12), default="manuel")

