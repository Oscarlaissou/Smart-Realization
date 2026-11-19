"""Connexion à la base de données : Supabase (PostgreSQL hébergé) uniquement.

DATABASE_URL (dans backend/.env) doit être l'URL de connexion Supabase :
Supabase > Project Settings > Database > Connection string (« Transaction pooler »).
Aucune base locale n'est utilisée par l'application.

Seule exception : les tests automatiques (backend/tests/conftest.py) utilisent une base SQLite
EN MÉMOIRE, pour ne jamais écrire de comptes de test dans la vraie base Supabase.
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

from .config import settings

MODE_TESTS = os.getenv("SEVIA_TESTS") == "1"


def _verifier_url_supabase(url: str) -> None:
    if not url.startswith(("postgresql://", "postgresql+psycopg2://", "postgres://")) or "supabase" not in url:
        raise RuntimeError(
            "DATABASE_URL doit pointer vers la base Supabase (aucune base locale). "
            "Copier la « Connection string » de Supabase dans backend/.env (voir .env.example)."
        )


if MODE_TESTS:
    engine = create_engine(
        "sqlite://",                                  # en mémoire : rien n'est écrit sur le disque
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    _verifier_url_supabase(settings.DATABASE_URL)
    engine = create_engine(
        settings.DATABASE_URL.replace("postgres://", "postgresql://", 1),
        pool_pre_ping=True,   # Teste la connexion avant chaque requête et reconnecte si Supabase l'a coupée
        pool_recycle=280,     # Renouvelle les connexions toutes les 4 min 40
        pool_size=5,
        max_overflow=10,
        connect_args={
            "sslmode": "require",
            "connect_timeout": 10,
        },
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
