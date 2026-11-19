import { useState } from 'react'
import { NavLink, Route, Routes, Navigate, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import Connexion from './features/auth/Connexion.jsx'
import Inscription from './features/auth/Inscription.jsx'
import Dashboard from './features/dashboard/Dashboard.jsx'
import Parcelles from './features/parcelles/Parcelles.jsx'
import Equipements from './features/equipements/Equipements.jsx'
import Humidite from './features/humidite/Humidite.jsx'
import Fertilisation from './features/fertilisation/Fertilisation.jsx'
import Camera from './features/camera/Camera.jsx'
import Alertes from './features/alertes/Alertes.jsx'
import Parametres from './features/parametres/Parametres.jsx'

const ICONES = {
  dashboard: 'M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z',
  parcelles:
    'M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0zM12 7a3 3 0 1 0 0 6 3 3 0 0 0 0-6z',
  equipements: 'M9 2v4M15 2v4M5 8h14v8a4 4 0 0 1-4 4H9a4 4 0 0 1-4-4zM12 20v2',
  humidite: 'M12 2.7c-3.5 4.2-6 7.2-6 10.3a6 6 0 0 0 12 0c0-3.1-2.5-6.1-6-10.3z',
  fertilisation:
    'M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.5 19 2c1 2 2 4.2 2 8 0 5.5-4.8 10-10 10zM2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12',
  camera:
    'M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3zM12 10a3 3 0 1 0 0 6 3 3 0 0 0 0-6z',
  alertes: 'M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9M10.3 21a1.94 1.94 0 0 0 3.4 0',
  parametres: 'M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6',
}

function Espace({ children }) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [menuOuvert, setMenuOuvert] = useState(false)

  if (!localStorage.getItem('token')) return <Navigate to="/connexion" />

  const deconnexion = () => {
    localStorage.removeItem('token')
    navigate('/connexion')
  }

  const liens = [
    ['/', t('nav.dashboard'), ICONES.dashboard],
    ['/parcelles', t('nav.parcelles'), ICONES.parcelles],
    ['/equipements', t('nav.equipements'), ICONES.equipements],
    ['/humidite', t('nav.humidite'), ICONES.humidite],
    ['/fertilisation', t('nav.fertilisation'), ICONES.fertilisation],
    ['/camera', t('nav.camera'), ICONES.camera],
    ['/alertes', t('nav.alertes'), ICONES.alertes],
    ['/parametres', t('nav.parametres'), ICONES.parametres],
  ]

  return (
    <div className="layout">
      <a className="skip-link" href="#contenu-principal">
        {t('common.allerAuContenu')}
      </a>
      <nav
        className={`app-nav ${menuOuvert ? 'menu-ouvert' : ''}`}
        aria-label={t('nav.navigationPrincipale')}
      >
        <div className="nav-top">
          <div className="nav-brand">
            <div className="nav-logo">
              <svg
                aria-hidden="true"
                width="21"
                height="21"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#0F2A1E"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.5 19 2c1 2 2 4.2 2 8 0 5.5-4.8 10-10 10zM2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12" />
              </svg>
            </div>
            <span className="nav-brand-name">Sevia</span>
            <button
              type="button"
              className="nav-burger"
              aria-expanded={menuOuvert}
              aria-controls="navigation-principale"
              aria-label={menuOuvert ? t('nav.fermerMenu') : t('nav.menu')}
              onClick={() => setMenuOuvert((ouvert) => !ouvert)}
            >
              <svg
                aria-hidden="true"
                width="22"
                height="22"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              >
                {menuOuvert ? (
                  <path d="M18 6 6 18M6 6l12 12" />
                ) : (
                  <path d="M3 6h18M3 12h18M3 18h18" />
                )}
              </svg>
            </button>
          </div>

          <div id="navigation-principale" className="nav-links">
            {liens.map(([to, nom, icone]) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                onClick={() => setMenuOuvert(false)}
              >
                <svg
                  aria-hidden="true"
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d={icone} />
                </svg>
                <span>{nom}</span>
              </NavLink>
            ))}
          </div>
        </div>

        <div className="nav-bottom">
          <div className="nav-farm-card">
            <div className="nav-farm-title">{t('nav.domaine')}</div>
            <div className="nav-farm-sub">{t('nav.resumeFerme')}</div>
          </div>
          <button type="button" onClick={deconnexion} className="nav-logout">
            {t('nav.deconnexion')}
          </button>
        </div>
      </nav>
      <main id="contenu-principal" tabIndex="-1">
        {children}
      </main>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/connexion" element={<Connexion />} />
      <Route path="/inscription" element={<Inscription />} />
      <Route
        path="/"
        element={
          <Espace>
            <Dashboard />
          </Espace>
        }
      />
      <Route path="/dashboard" element={<Navigate to="/" replace />} />
      <Route
        path="/parcelles"
        element={
          <Espace>
            <Parcelles />
          </Espace>
        }
      />
      <Route
        path="/equipements"
        element={
          <Espace>
            <Equipements />
          </Espace>
        }
      />
      <Route
        path="/humidite"
        element={
          <Espace>
            <Humidite />
          </Espace>
        }
      />
      <Route
        path="/fertilisation"
        element={
          <Espace>
            <Fertilisation />
          </Espace>
        }
      />
      <Route
        path="/camera"
        element={
          <Espace>
            <Camera />
          </Espace>
        }
      />
      <Route
        path="/alertes"
        element={
          <Espace>
            <Alertes />
          </Espace>
        }
      />
      <Route
        path="/parametres"
        element={
          <Espace>
            <Parametres />
          </Espace>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
