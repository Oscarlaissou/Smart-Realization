from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ...core.database import Base

class DonneeAgro(Base):                 # Fertilisation
    __tablename__ = "donnees_agro"
    id: Mapped[int] = mapped_column(primary_key=True)
    parcelle_id: Mapped[int] = mapped_column(ForeignKey("parcelles.id"))
    ph: Mapped[float] = mapped_column(Float, default=6.5)
    azote: Mapped[float] = mapped_column(Float, default=0)
    phosphore: Mapped[float] = mapped_column(Float, default=0)
    potassium: Mapped[float] = mapped_column(Float, default=0)

class Apport(Base):
    __tablename__ = "apports"
    id: Mapped[int] = mapped_column(primary_key=True)
    parcelle_id: Mapped[int] = mapped_column(ForeignKey("parcelles.id"))
    engrais: Mapped[str] = mapped_column(String(80))
    dose_kg_ha: Mapped[float] = mapped_column(Float)
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    realise: Mapped[bool] = mapped_column(Boolean, default=False)   # False = planifié (calendrier)

