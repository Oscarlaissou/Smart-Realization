from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ...core.database import Base


class Alerte(Base):
    __tablename__ = "alertes"
    id: Mapped[int] = mapped_column(primary_key=True)
    parcelle_id: Mapped[int | None] = mapped_column(ForeignKey("parcelles.id"), nullable=True)
    niveau: Mapped[str] = mapped_column(String(12))
    message: Mapped[str] = mapped_column(String(250))
    lue: Mapped[bool] = mapped_column(Boolean, default=False)
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PreferenceAlerte(Base):
    """Canaux choisis par un utilisateur pour chaque type d'alerte."""

    __tablename__ = "preferences_alertes"
    __table_args__ = (
        UniqueConstraint("user_id", "categorie", name="uq_preference_alerte_user_categorie"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    categorie: Mapped[str] = mapped_column(String(40))
    notification: Mapped[bool] = mapped_column(Boolean, default=True)
    email: Mapped[bool] = mapped_column(Boolean, default=False)
    sms: Mapped[bool] = mapped_column(Boolean, default=False)
