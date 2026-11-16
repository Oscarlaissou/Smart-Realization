import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { connexion } from '../../services/api.js'

// Exemple fonctionnel : sert de modèle pour les autres pages.
export default function Connexion() {
  const [email, setEmail] = useState(''); const [mdp, setMdp] = useState(''); const [erreur, setErreur] = useState('')
  const nav = useNavigate()
  async function envoyer(e) {
    e.preventDefault()
    try { await connexion(email, mdp); nav('/') } catch (err) { setErreur(err.message) }
  }
  return (
    <form onSubmit={envoyer} style={{ maxWidth: 360, margin: '80px auto', display: 'grid', gap: 12 }}>
      <h1>Connexion</h1>
      <input placeholder="Adresse e-mail" value={email} onChange={e => setEmail(e.target.value)} />
      <input type="password" placeholder="Mot de passe" value={mdp} onChange={e => setMdp(e.target.value)} />
      {erreur && <p style={{ color: '#B42318' }}>{erreur}</p>}
      <button>Se connecter</button>
      <Link to="/inscription">Créer un compte</Link>
    </form>)
}
