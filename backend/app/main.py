from fastapi.staticfiles import StaticFiles
from .features.camera.stockage import DOSSIER_UPLOADS
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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

# Origines autorisées (front) : CORS_ORIGINS dans backend/.env, séparées par des virgules
ORIGINS = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    origin = request.headers.get("origin", "")
    headers = {"Access-Control-Allow-Origin": origin} if origin in ORIGINS else {}
    return JSONResponse(
        status_code=500,
        content={"detail": f"Erreur interne : {exc}"},
        headers=headers,
    )


@app.on_event("startup")
def startup():
    # Ferme les flux temps réel à l'arrêt, sinon Ctrl+C / --reload restent bloqués
    from .core.temps_reel import installer_arret_sur_signal
    installer_arret_sur_signal()
    Base.metadata.create_all(engine)
    from .core.database import appliquer_migrations_legeres
    appliquer_migrations_legeres()
    if settings.MQTT_ENABLED:
        from .mqtt import listener
        listener.demarrer()


for r in (auth, parcelles, equipements, humidite, alertes, fertilisation, camera, dashboard):
    app.include_router(r.router)

DOSSIER_UPLOADS.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=DOSSIER_UPLOADS), name="media")

@app.get("/health", tags=["Système"])
def health():
    return {"status": "ok"}

    demarrer_mqtt()