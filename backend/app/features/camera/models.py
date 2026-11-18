from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ...core.database import Base

class Comptage(Base):                   # Caméra
    __tablename__ = "comptages"
    id: Mapped[int] = mapped_column(primary_key=True)
    parcelle_id: Mapped[int] = mapped_column(ForeignKey("parcelles.id"))
    image_path: Mapped[str] = mapped_column(Text, default="")
    detections_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    nb_plants: Mapped[int] = mapped_column(Integer, default=0)
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

