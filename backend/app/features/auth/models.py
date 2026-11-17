from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from ...core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    telephone: Mapped[str] = mapped_column(String(40), default="")
    role: Mapped[str] = mapped_column(String(80), default="Exploitant agricole")
    langue: Mapped[str] = mapped_column(String(10), default="fr", nullable=False)
    mot_de_passe_hash: Mapped[str] = mapped_column(String(255))
    cree_le: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)