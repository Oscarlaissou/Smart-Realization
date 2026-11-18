import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { lireToken } from '../services/api.js'
import { lireCompteur } from '../features/alertes/api.js'

function lireUtilisateurLocal() {
  try {
    return JSON.parse(localStorage.getItem('utilisateur') || '{}')
  } catch {
    return {}
  }
}

function initialesDe(nom = '') {
  return (
    nom
      .split(' ')
      .filter(Boolean)
      .map((partie) => partie[0])
      .join('')
      .slice(0, 2)
      .toUpperCase() || 'SV'
  )
}

export default function Entete({
  titre,
  sousTitre,
  recherche,
  onRecherche,
  placeholderRecherche,
  utilisateur,
  alertesActives,
  children,
}) {
  const { t } = useTranslation()
  const [compteur, setCompteur] = useState(0)
  const profil = utilisateur || lireUtilisateurLocal()
  const nombreAlertes = alertesActives ?? compteur

  useEffect(() => {
    if (alertesActives !== undefined || !lireToken()) return undefined
    let actif = true

    const charger = () => {
      lireCompteur()
        .then((resultat) => {
          if (actif) setCompteur(resultat?.non_lues ?? 0)
        })
        .catch(() => {})
    }

    charger()
    const intervalle = window.setInterval(charger, 60000)
    const rafraichir = () => charger()
    window.addEventListener('sevia:alertes', rafraichir)

    return () => {
      actif = false
      window.clearInterval(intervalle)
      window.removeEventListener('sevia:alertes', rafraichir)
    }
  }, [alertesActives])

  return (
    <header className="app-entete">
      <div className="app-entete-titre">
        <h1>{titre}</h1>
        {sousTitre && <p>{sousTitre}</p>}
      </div>

      <div className="app-entete-actions">
        {onRecherche && (
          <label className="app-recherche">
            <svg
              aria-hidden="true"
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#5B6B63"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M11 3a8 8 0 1 0 0 16 8 8 0 0 0 0-16zM21 21l-4.3-4.3" />
            </svg>
            <input
              type="search"
              aria-label={placeholderRecherche || t('common.rechercher')}
              placeholder={placeholderRecherche || t('common.rechercher')}
              value={recherche}
              onChange={(event) => onRecherche(event.target.value)}
            />
          </label>
        )}

        {children}

        <Link
          to="/alertes"
          className="app-cloche"
          aria-label={t('common.alertesNonLues', { nombre: nombreAlertes })}
        >
          <svg
            aria-hidden="true"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#12201A"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9M10.3 21a1.94 1.94 0 0 0 3.4 0" />
          </svg>
          {nombreAlertes > 0 && <span className="app-cloche-badge">{nombreAlertes}</span>}
        </Link>

        <div className="app-utilisateur">
          <div className="app-avatar" aria-hidden="true">
            {initialesDe(profil.nom)}
          </div>
          <div className="app-utilisateur-texte">
            <div className="app-utilisateur-nom">{profil.nom || t('entete.compte')}</div>
            <div className="app-utilisateur-role">
              {profil.role || t('entete.roleParDefaut')}
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
