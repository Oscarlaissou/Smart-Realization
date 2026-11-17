import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { inscription } from '../../services/api.js'
import { PanneauGaucheSevia } from './Connexion.jsx'
import './Auth.css'

function calculerForceMdp(mdp) {
  if (!mdp) return { score: 3, label: 'Solide' }
  let score = 0
  if (mdp.length >= 6) score += 1
  if (mdp.length >= 8) score += 1
  if (/[A-Z]/.test(mdp) && /[a-z]/.test(mdp)) score += 1
  if (/[0-9!@#$%^&*]/.test(mdp)) score += 1

  const labels = ['Faible', 'Moyen', 'Correct', 'Solide', 'Très fort']
  return { score: Math.max(1, score), label: labels[Math.max(1, score)] }
}

export default function Inscription() {
  const navigate = useNavigate()
  const [nom, setNom] = useState('')
  const [telephone, setTelephone] = useState('')
  const [email, setEmail] = useState('')
  const [nomExploitation, setNomExploitation] = useState('')
  const [role, setRole] = useState('Exploitant agricole')
  const [motDePasse, setMotDePasse] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [voirMdp1, setVoirMdp1] = useState(false)
  const [voirMdp2, setVoirMdp2] = useState(false)
  const [conditionsAcceptees, setConditionsAcceptees] = useState(true)
  const [erreur, setErreur] = useState('')
  const [chargement, setChargement] = useState(false)

  const force = calculerForceMdp(motDePasse)

  const gererInscription = async (e) => {
    e.preventDefault()
    setErreur('')

    if (!conditionsAcceptees) {
      setErreur("Veuillez accepter les conditions d'utilisation.")
      return
    }
    if (motDePasse !== confirmation) {
      setErreur('Les deux mots de passe ne correspondent pas.')
      return
    }

    setChargement(true)
    try {
      await inscription({
        nom,
        telephone,
        email,
        nom_exploitation: nomExploitation,
        role,
        mot_de_passe: motDePasse,
      })
      navigate('/')
    } catch (err) {
      setErreur(err.message || 'Erreur lors de la création du compte.')
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

        <div className="auth-box-register">
          <div>
            <h1 className="auth-title">Créer un compte</h1>
          </div>

          {erreur && <div className="auth-error">{erreur}</div>}

          <form className="auth-form" onSubmit={gererInscription}>
            <div className="auth-section-label">Vous</div>

            <div className="auth-grid-2">
              <div className="auth-field">
                <label htmlFor="nom">Nom complet</label>
                <div className="auth-input-wrap">
                  <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#5B6B63" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="auth-input-icon">
                    <path d="M20 21a8 8 0 0 0-16 0M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z" />
                  </svg>
                  <input
                    id="nom"
                    required
                    className="auth-input"
                    placeholder="Paul Mbarga"
                    value={nom}
                    onChange={(e) => setNom(e.target.value)}
                  />
                </div>
              </div>

              <div className="auth-field">
                <label htmlFor="tel">Téléphone</label>
                <div className="auth-input-wrap">
                  <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#5B6B63" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="auth-input-icon">
                    <path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2" />
                  </svg>
                  <input
                    id="tel"
                    className="auth-input"
                    placeholder="6 12 34 56 78"
                    value={telephone}
                    onChange={(e) => setTelephone(e.target.value)}
                  />
                </div>
              </div>
            </div>

            <div className="auth-field">
              <label htmlFor="mail">Adresse e-mail</label>
              <div className="auth-input-wrap">
                <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#5B6B63" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="auth-input-icon">
                  <path d="M4 4h16v16H4zM4 6l8 7 8-7" />
                </svg>
                <input
                  id="mail"
                  type="email"
                  required
                  className="auth-input"
                  placeholder="nom@exploitation.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>

            <div className="auth-section-label">Votre exploitation</div>

            <div className="auth-grid-2">
              <div className="auth-field">
                <label htmlFor="expl">Nom de l&apos;exploitation</label>
                <div className="auth-input-wrap">
                  <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#5B6B63" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="auth-input-icon">
                    <path d="M3 11l9-8 9 8M5 10v10h14V10" />
                  </svg>
                  <input
                    id="expl"
                    required
                    className="auth-input"
                    placeholder="Domaine Les Collines"
                    value={nomExploitation}
                    onChange={(e) => setNomExploitation(e.target.value)}
                  />
                </div>
              </div>

              <div className="auth-field">
                <label htmlFor="role">Votre rôle</label>
                <select
                  id="role"
                  className="auth-select"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                >
                  <option>Exploitant agricole</option>
                  <option>Technicien agricole / agronome</option>
                  <option>Responsable d&apos;exploitation</option>
                  <option>Technicien de maintenance IoT</option>
                </select>
              </div>
            </div>

            <div className="auth-section-label">Sécurité</div>

            <div className="auth-grid-2">
              <div className="auth-field">
                <label htmlFor="mdp1">Mot de passe</label>
                <div className="auth-input-wrap">
                  <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#5B6B63" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="auth-input-icon">
                    <path d="M5 11h14v10H5zM8 11V7a4 4 0 0 1 8 0v4" />
                  </svg>
                  <input
                    id="mdp1"
                    type={voirMdp1 ? 'text' : 'password'}
                    required
                    className="auth-input has-eye"
                    placeholder="••••••••"
                    value={motDePasse}
                    onChange={(e) => setMotDePasse(e.target.value)}
                  />
                  <button
                    type="button"
                    className="auth-eye-btn"
                    aria-label="Afficher ou masquer le mot de passe"
                    onClick={() => setVoirMdp1((v) => !v)}
                  >
                    <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#5B6B63" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                  </button>
                </div>
              </div>

              <div className="auth-field">
                <label htmlFor="mdp2">Confirmer le mot de passe</label>
                <div className="auth-input-wrap">
                  <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#5B6B63" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="auth-input-icon">
                    <path d="M5 11h14v10H5zM8 11V7a4 4 0 0 1 8 0v4" />
                  </svg>
                  <input
                    id="mdp2"
                    type={voirMdp2 ? 'text' : 'password'}
                    required
                    className="auth-input has-eye"
                    placeholder="••••••••"
                    value={confirmation}
                    onChange={(e) => setConfirmation(e.target.value)}
                  />
                  <button
                    type="button"
                    className="auth-eye-btn"
                    aria-label="Afficher ou masquer la confirmation"
                    onClick={() => setVoirMdp2((v) => !v)}
                  >
                    <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#5B6B63" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>

            <div className="auth-strength">
              {[1, 2, 3, 4].map((niveau) => (
                <span
                  key={niveau}
                  className={`auth-strength-bar ${force.score >= niveau ? 'filled' : ''}`}
                />
              ))}
              <span className="auth-strength-text">{force.label}</span>
            </div>

            <label className="auth-checkbox-label" style={{ alignItems: 'flex-start', lineHeight: 1.5 }}>
              <input
                type="checkbox"
                style={{ marginTop: '2px' }}
                checked={conditionsAcceptees}
                onChange={(e) => setConditionsAcceptees(e.target.checked)}
              />
              J&apos;accepte les conditions d&apos;utilisation
            </label>

            <button type="submit" disabled={chargement} className="auth-btn-primary">
              {chargement ? 'Création du compte...' : 'Créer mon compte'}
            </button>
          </form>

          <p className="auth-footer-text">
            Vous avez déjà un compte ?{' '}
            <Link to="/connexion" className="auth-link-bold">
              Se connecter
            </Link>
          </p>
        </div>
      </section>
    </div>
  )
}