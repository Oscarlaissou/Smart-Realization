from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ...core.database import Base

class Equipement(Base):                 # capteur | electrovanne | camera
    __tablename__ = "equipements"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True)
    type: Mapped[str] = mapped_column(String(20))
    en_ligne: Mapped[bool] = mapped_column(Boolean, default=True)
    parcelle_id: Mapped[int | None] = mapped_column(ForeignKey("parcelles.id"), nullable=True)

