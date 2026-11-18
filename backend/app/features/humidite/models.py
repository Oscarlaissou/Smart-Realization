from datetime import datetime
from sqlalchemy import Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column
from ...core.database import Base


class MesureHumidite(Base):
    __tablename__ = "mesures_humidite"

    id: Mapped[int] = mapped_column(primary_key=True)
    parcelle_id: Mapped[int] = mapped_column(ForeignKey("parcelles.id", ondelete="CASCADE"), index=True)
    valeur: Mapped[float] = mapped_column(Float)
    enregistre_le: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    @hybrid_property
    def humidite(self) -> float:
        return self.valeur

    @hybrid_property
    def horodatage(self) -> datetime:
        return self.enregistre_le


class ArrosageManuel(Base):
    __tablename__ = "arrosages_manuels"

    id: Mapped[int] = mapped_column(primary_key=True)
    parcelle_id: Mapped[int] = mapped_column(ForeignKey("parcelles.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    methode: Mapped[str] = mapped_column(String(60), default="Goutte-à-goutte")
    volume_litres: Mapped[float] = mapped_column(Float, default=0.0)
    duree_minutes: Mapped[int] = mapped_column(Integer, default=0)
    humidite_avant: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str] = mapped_column(String(255), default="")
    date_arrosage: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    @hybrid_property
    def debut(self) -> datetime:
        return self.date_arrosage

    @hybrid_property
    def duree_min(self) -> int:
        return self.duree_minutes

    @hybrid_property
    def mode(self) -> str:
        return self.methode


# Alias de compatibilité pour dashboard/router.py et les autres modules existants
Mesure = MesureHumidite
Irrigation = ArrosageManuel