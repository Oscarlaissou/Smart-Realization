import { changerLangue } from '../i18n/index.js'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export function lireToken() {
  return localStorage.getItem('token')
}

export function enregistrerSession(token, utilisateur) {
  localStorage.setItem('token', token)
  if (utilisateur) {
    localStorage.setItem('utilisateur', JSON.stringify(utilisateur))
  }
}

export function deconnexion() {
  localStorage.removeItem('token')
  localStorage.removeItem('utilisateur')
}

// FastAPI renvoie soit un texte, soit (erreur de validation 422) une liste d'erreurs par champ
export function messageErreur(detail) {
  if (!detail) return ''
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((e) => {
        const champ = Array.isArray(e?.loc) ? e.loc[e.loc.length - 1] : ''
        const msg = (e?.msg || '').replace(/^Value error, /, '')
        return champ ? `${champ} : ${msg}` : msg
      })
      .filter(Boolean)
      .join(' · ')
  }
  return detail.message || JSON.stringify(detail)
}

export async function api(chemin, options = {}) {
  const token = lireToken()
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 25000)

  try {
    const res = await fetch(`${API_URL}${chemin}`, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    })

    if (res.status === 401 && !chemin.startsWith('/auth/')) {
      deconnexion()
      throw new Error('Session expirée, veuillez vous reconnecter.')
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(messageErreur(err.detail) || `Erreur serveur (${res.status})`)
    }

    return res.status === 204 ? null : res.json()
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new Error('Le serveur backend ne répond pas (vérifiez que FastAPI est lancé sur le port 8000).')
    }
    throw err
  } finally {
    clearTimeout(timeout)
  }
}

export async function connexion(email, motDePasse) {
  const data = await api('/auth/connexion', {
    method: 'POST',
    body: JSON.stringify({ email, mot_de_passe: motDePasse }),
  })
  enregistrerSession(data.access_token, data.utilisateur)
  if (data.utilisateur?.langue) changerLangue(data.utilisateur.langue)
  return data
}

export async function inscription(donnees) {
  const data = await api('/auth/inscription', {
    method: 'POST',
    body: JSON.stringify(donnees),
  })
  enregistrerSession(data.access_token, data.utilisateur)
  return data
}