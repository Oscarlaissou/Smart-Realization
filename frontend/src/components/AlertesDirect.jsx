import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ecouter, utiliserTempsReel } from '../services/tempsReel.js'

const DUREE_AFFICHAGE_MS = 12000
const MAX_POPUPS = 4

const TITRES = {
  secheresse: 'Sol sec',
  exces_eau: "Excès d'eau",
  capteur: 'Capteur',
  vanne: 'Vanne',
  fuite: 'Fuite',
}

function heure(iso) {
  if (!iso) return ''
  const d = new Date(iso.endsWith('Z') ? iso : `${iso}Z`)
  return Number.isNaN(d.getTime()) ? '' : d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
}

// Popup affiché sur TOUTES les pages dès qu'une alerte est émise (signalement en direct)
export default function AlertesDirect() {
  const [popups, setPopups] = useState([])

  useEffect(() => {
    const liberer = utiliserTempsReel()
    const desabonner = ecouter((evenement) => {
      if (evenement.type !== 'alerte' || !evenement.alerte) return
      const popup = { ...evenement.alerte, parcelle: evenement.parcelle, cle: `${evenement.alerte.id}-${Date.now()}` }
      setPopups((liste) => [popup, ...liste.filter((p) => p.id !== popup.id)].slice(0, MAX_POPUPS))
      window.setTimeout(
        () => setPopups((liste) => liste.filter((p) => p.cle !== popup.cle)),
        DUREE_AFFICHAGE_MS,
      )
      window.dispatchEvent(new Event('sevia:alertes'))   // met à jour la cloche et la page Alertes
    })
    return () => {
      desabonner()
      liberer()
    }
  }, [])

  if (popups.length === 0) return null

  return (
    <div className="alertes-direct" aria-live="assertive">
      {popups.map((p) => (
        <div key={p.cle} className={`alerte-popup niveau-${p.niveau}`} role="alert">
          <div className="alerte-popup-entete">
            <strong>⚠ {TITRES[p.categorie] || 'Nouvelle alerte'}</strong>
            <span>{heure(p.date)}</span>
            <button
              type="button"
              aria-label="Fermer l'alerte"
              onClick={() => setPopups((liste) => liste.filter((x) => x.cle !== p.cle))}
            >
              ×
            </button>
          </div>
          <p>{p.message}</p>
          <Link
            to="/alertes"
            className="alerte-popup-lien"
            onClick={() => setPopups((liste) => liste.filter((x) => x.cle !== p.cle))}
          >
            Voir les alertes
          </Link>
        </div>
      ))}
    </div>
  )
}
