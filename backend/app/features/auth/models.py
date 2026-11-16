from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ...core.database import Base

class User(Base):                       # Authentification
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    mot_de_passe: Mapped[str] = mapped_column(String(300))
    langue: Mapped[str] = mapped_column(String(5), default="fr")

