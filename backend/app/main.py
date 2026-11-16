from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.database import Base, engine
from .core.config import settings
from .features.auth import router as auth
from .features.parcelles import router as parcelles
from .features.equipements import router as equipements
from .features.humidite import router as humidite
from .features.alertes import router as alertes
from .features.fertilisation import router as fertilisation
from .features.camera import router as camera
from .features.dashboard import router as dashboard

app = FastAPI(title="Sevia API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    Base.metadata.create_all(engine)   # TODO : remplacer par Alembic (migrations)
    if settings.MQTT_ENABLED:
        from .mqtt import listener
        listener.demarrer()

for r in (auth, parcelles, equipements, humidite, alertes, fertilisation, camera, dashboard):
    app.include_router(r.router)

@app.get("/health", tags=["Système"])
def health():
    return {"status": "ok"}
