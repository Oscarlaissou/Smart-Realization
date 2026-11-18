import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { connexion } from '../../services/api.js'
import './Auth.css'

export function PanneauGaucheSevia() {
  return (
    <section className="auth-left">
      <svg aria-hidden="true" viewBox="0 0 720 360" fill="none" className="auth-waves">
        <path d="M-40 330 C 180 250, 420 380, 760 270" stroke="#2FA36B" strokeOpacity="0.45" strokeWidth="2" />
        <path d="M-40 290 C 180 210, 420 340, 760 230" stroke="#2FA36B" strokeOpacity="0.38" strokeWidth="2" />
        <path d="M-40 250 C 180 170, 420 300, 760 190" stroke="#2FA36B" strokeOpacity="0.30" strokeWidth="2" />
        <path d="M-40 210 C 180 130, 420 260, 760 150" stroke="#2FA36B" strokeOpacity="0.22" strokeWidth="2" />
        <path d="M-40 170 C 180 90, 420 220, 760 110" stroke="#2FA36B" strokeOpacity="0.15" strokeWidth="2" />
        <path d="M-40 130 C 180 50, 420 180, 760 70" stroke="#2FA36B" strokeOpacity="0.10" strokeWidth="2" />
      </svg>

      <div className="auth-brand">
        <div className="auth-brand-icon">
          <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#0F2A1E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.5 19 2c1 2 2 4.2 2 8 0 5.5-4.8 10-10 10zM2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12" />
          </svg>
        </div>
        <span className="auth-brand-name">Sevia</span>
      </div>

      <div className="auth-hero">
        <h2 className="auth-hero-title">Cultivez mieux, avec moins de ressources.</h2>

        <div aria-hidden="true" className="auth-cards-stage">
          <div className="auth-preview-card-1">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontFamily: 'Space Grotesk, sans-serif', fontSize: '15px', fontWeight: 700 }}>
                Humidité du sol
              </span>
              <span style={{ fontSize: '11px', fontWeight: 600, padding: '3px 9px', borderRadius: '999px', background: '#EEF3EF', color: '#3C4A43' }}>
                24 h
              </span>
            </div>
            <svg viewBox="0 0 430 130" width="100%" style={{ display: 'block', marginTop: '8px' }}>
              <rect x="0" y="34" width="430" height="46" fill="#E3F4EA" />
              <g stroke="#E3E9E4" strokeWidth="1">
                <path d="M0 20H430M0 57H430M0 94H430M0 126H430" />
              </g>
              <path d="M0 52C40 50 70 56 110 58S170 70 210 62 270 36 310 40 380 52 430 50" fill="none" stroke="#1F7A4D" strokeWidth="2.5" />
              <path d="M0 48C50 54 90 62 140 70S220 80 280 84 380 96 430 110" fill="none" stroke="#1D6FB8" strokeWidth="2.5" strokeDasharray="6 5" />
            </svg>
          </div>

          <div className="auth-preview-card-2">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', fontWeight: 700 }}>
              <span style={{ width: '9px', height: '9px', borderRadius: '5px', background: '#1D6FB8' }} />
              Irrigation en cours
            </div>
            <div style={{ marginTop: '6px', fontSize: '12px' }}>Parcelle Sud · 26 min sur 45</div>
            <div style={{ marginTop: '10px', height: '7px', borderRadius: '4px', background: '#BBD7F0' }}>
              <div style={{ width: '58%', height: '100%', borderRadius: '4px', background: '#1D6FB8' }} />
            </div>
          </div>

          <div className="auth-preview-card-3">
            <div style={{ fontSize: '12px', color: '#5B6B63' }}>Plants comptés</div>
            <div style={{ marginTop: '4px', fontFamily: 'Space Grotesk, sans-serif', fontSize: '30px', fontWeight: 700, letterSpacing: '-0.02em' }}>
              12 480 <span style={{ fontSize: '14px', fontWeight: 500, color: '#5B6B63' }}>plants</span>
            </div>
            <span style={{ display: 'inline-block', marginTop: '6px', fontSize: '11px', fontWeight: 600, padding: '3px 8px', borderRadius: '999px', background: '#E3F4EA', color: '#14683F' }}>
              +3,2 % en 7 jours
            </span>
          </div>
        </div>
      </div>

      <p className="auth-copyright">© 2026 Sevia</p>
    </section>
  )
}

export default function Connexion() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [motDePasse, setMotDePasse] = useState('')
  const [voirMdp, setVoirMdp] = useState(false)
  const [resterConnecte, setResterConnecte] = useState(true)
  const [erreur, setErreur] = useState('')
  const [chargement, setChargement] = useState(false)

  const gererSoumission = async (e) => {
    e.preventDefault()
    setErreur('')
    setChargement(true)
    try {
      await connexion(email, motDePasse)
      navigate('/')
    } catch (err) {
      setErreur(err.message || 'Adresse e-mail ou mot de passe incorrect.')
    } finally {
      setChargement(false)
    }
  }

  return (
    <div className="auth-page">
      <PanneauGaucheSevia />

      <section className="auth-right">
        <Link to="/parametres" aria-label="Langue : français" className="auth-lang-btn">
          FR
        </Link>

        <div className="auth-box-login">
          <div>
            <h1 className="auth-title">Bon retour parmi nous</h1>
            <p className="auth-subtitle">Connectez-vous à votre exploitation.</p>
          </div>

          {erreur && <div className="auth-error">{erreur}</div>}

          <form className="auth-form" onSubmit={gererSoumission}>
            <div className="auth-field">
              <label htmlFor="email">Adresse e-mail</label>
              <div className="auth-input-wrap">
                <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#5B6B63" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="auth-input-icon">
                  <path d="M4 4h16v16H4zM4 6l8 7 8-7" />
                </svg>
                <input
                  id="email"
                  type="email"
                  required
                  className="auth-input"
                  placeholder="nom@exploitation.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>

            <div className="auth-field">
              <label htmlFor="mdp">Mot de passe</label>
              <div className="auth-input-wrap">
                <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#5B6B63" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="auth-input-icon">
                  <path d="M5 11h14v10H5zM8 11V7a4 4 0 0 1 8 0v4" />
                </svg>
                <input
                  id="mdp"
                  type={voirMdp ? 'text' : 'password'}
                  required
                  className="auth-input has-eye"
                  placeholder="••••••••"
                  value={motDePasse}
                  onChange={(e) => setMotDePasse(e.target.value)}
                />
                <button
                  type="button"
                  className="auth-eye-btn"
                  aria-label={voirMdp ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
                  onClick={() => setVoirMdp((v) => !v)}
                >
                  <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#5B6B63" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                </button>
              </div>
            </div>

            <div className="auth-row-between">
              <label className="auth-checkbox-label">
                <input
                  type="checkbox"
                  checked={resterConnecte}
                  onChange={(e) => setResterConnecte(e.target.checked)}
                />
                Rester connecté
              </label>
              <Link to="/mot-de-passe" className="auth-link">
                Mot de passe oublié ?
              </Link>
            </div>

            <button type="submit" disabled={chargement} className="auth-btn-primary">
              {chargement ? 'Connexion en cours...' : 'Se connecter'}
            </button>

            <div className="auth-divider">
              <span />ou<span />
            </div>

            <button
              type="button"
              className="auth-btn-google"
              onClick={() => setErreur('La connexion Google OAuth sera activée prochainement.')}
            >
              <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.5 12.2c0-.8-.1-1.4-.2-2H12v3.9h5.9a5 5 0 0 1-2.2 3.3v2.7h3.5c2-1.9 3.3-4.7 3.3-7.9z" />
                <path fill="#34A853" d="M12 23c3 0 5.5-1 7.3-2.7l-3.5-2.7c-1 .7-2.3 1.1-3.8 1.1-2.9 0-5.4-2-6.3-4.6H2.1v2.8A11 11 0 0 0 12 23z" />
                <path fill="#FBBC05" d="M5.7 14.1a6.6 6.6 0 0 1 0-4.2V7.1H2.1a11 11 0 0 0 0 9.8z" />
                <path fill="#EA4335" d="M12 5.4c1.6 0 3.1.6 4.2 1.7l3.1-3.1A11 11 0 0 0 2.1 7.1l3.6 2.8C6.6 7.4 9.1 5.4 12 5.4z" />
              </svg>
              Continuer avec Google
            </button>
          </form>

          <p className="auth-footer-text">
            Pas encore de compte ?{' '}
            <Link to="/inscription" className="auth-link-bold">
              Créer un compte
            </Link>
          </p>
        </div>
      </section>
    </div>
  )
}