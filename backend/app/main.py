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

ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

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
    Base.metadata.create_all(engine)
    if settings.MQTT_ENABLED:
        from .mqtt import listener
        listener.demarrer()


for r in (auth, parcelles, equipements, humidite, alertes, fertilisation, camera, dashboard):
    app.include_router(r.router)


@app.get("/health", tags=["Système"])
def health():
    return {"status": "ok"}