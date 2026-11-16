from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ...core.database import Base

class Alerte(Base):
    __tablename__ = "alertes"
    id: Mapped[int] = mapped_column(primary_key=True)
    parcelle_id: Mapped[int | None] = mapped_column(ForeignKey("parcelles.id"), nullable=True)
    niveau: Mapped[str] = mapped_column(String(12))
    message: Mapped[str] = mapped_column(String(250))
    lue: Mapped[bool] = mapped_column(Boolean, default=False)
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

