"""Diffusion en temps réel (Server-Sent Events) des nouvelles mesures vers les pages ouvertes.

Les mesures arrivent depuis des threads (client MQTT, routes synchrones de FastAPI) ;
chaque page abonnée a sa file asyncio. publier() est sûr depuis n'importe quel thread.

Limite : la diffusion se fait dans le processus de l'API. Avec plusieurs workers uvicorn,
il faudrait un relais commun (ex. Redis pub/sub ou Supabase Realtime).
"""
import asyncio
import json
import threading
from dataclasses import dataclass


@dataclass(eq=False)
class Abonne:
    user_id: int
    file: asyncio.Queue
    boucle: asyncio.AbstractEventLoop


_abonnes: set[Abonne] = set()
_verrou = threading.Lock()

# Arrêt du serveur : uvicorn attend que TOUTES les connexions se ferment avant de s'arrêter
# (Ctrl+C, ou rechargement --reload après une modification du code). Un flux SSE ne se ferme
# jamais tout seul : sans ce signal, le serveur restait bloqué sur « Waiting for connections to close ».
ARRET = threading.Event()


def installer_arret_sur_signal() -> None:
    """À appeler au démarrage de l'app : sur SIGINT/SIGTERM (et SIGBREAK sous Windows), on prévient
    les flux ouverts qu'ils doivent se fermer, puis on laisse uvicorn faire son arrêt normal."""
    import signal

    if threading.current_thread() is not threading.main_thread():
        return
    for nom in ("SIGINT", "SIGTERM", "SIGBREAK"):
        sig = getattr(signal, nom, None)
        if sig is None:
            continue
        precedent = signal.getsignal(sig)

        def gestionnaire(numero, cadre, _precedent=precedent):
            ARRET.set()
            if callable(_precedent):
                _precedent(numero, cadre)
            elif _precedent == signal.SIG_DFL and numero == signal.SIGINT:
                raise KeyboardInterrupt

        try:
            signal.signal(sig, gestionnaire)
        except (ValueError, OSError):   # signal non disponible sur cette plateforme
            pass


def abonner(user_id: int) -> Abonne:
    abonne = Abonne(user_id=user_id, file=asyncio.Queue(maxsize=100), boucle=asyncio.get_running_loop())
    with _verrou:
        _abonnes.add(abonne)
    return abonne


def desabonner(abonne: Abonne) -> None:
    with _verrou:
        _abonnes.discard(abonne)


def _deposer(abonne: Abonne, message: str) -> None:
    try:
        abonne.file.put_nowait(message)
    except asyncio.QueueFull:   # page qui ne lit plus : on ignore plutôt que de bloquer
        pass


def publier(user_id: int, evenement: dict) -> int:
    """Envoie l'événement à toutes les pages ouvertes de cet utilisateur. Renvoie le nombre de pages."""
    message = json.dumps(evenement, default=str)
    with _verrou:
        cibles = [a for a in _abonnes if a.user_id == user_id]
    for abonne in cibles:
        abonne.boucle.call_soon_threadsafe(_deposer, abonne, message)
    return len(cibles)
