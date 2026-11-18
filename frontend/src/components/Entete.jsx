import { useTranslation } from 'react-i18next'

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
  children,
}) {
  const { t } = useTranslation()
  const profil = utilisateur || lireUtilisateurLocal()

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
