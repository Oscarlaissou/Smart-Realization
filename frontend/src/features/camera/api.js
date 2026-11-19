// Appels API de la fonctionnalité « camera » (utiliser api() de ../../services/api.js)
import { api, lireToken, deconnexion, messageErreur } from '../../services/api.js'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

// Parcelles de l'utilisateur connecté (pastilles Nord / Sud / ...)
export const listerParcelles = () => api('/camera/parcelles')

// Tous les comptages d'une parcelle, triés par date croissante
export const listerComptages = (pid) => api(`/camera/${pid}/comptages`)

// Envoi d'une image choisie par l'utilisateur : stockage + comptage YOLO côté serveur.
// api() force « Content-Type: application/json », ce qui casserait un envoi de fichier
// (le navigateur doit fixer lui-même le multipart) : on appelle donc fetch directement.
export async function envoyerImage(pid, fichier) {
  const token = lireToken()
  const formData = new FormData()
  formData.append('fichier', fichier)

  const controller = new AbortController()
  // Le 1er comptage charge le modèle YOLO : on laisse 3 minutes
  const timeout = setTimeout(() => controller.abort(), 180000)

  try {
    const res = await fetch(`${API_URL}/camera/${pid}/images`, {
      method: 'POST',
      body: formData,
      signal: controller.signal,
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })

    if (res.status === 401) {
      deconnexion()
      throw new Error('Session expirée, veuillez vous reconnecter.')
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(messageErreur(err.detail) || `Erreur serveur (${res.status})`)
    }
    return res.json()
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new Error("L'analyse de l'image prend trop de temps. Réessayez dans un instant.")
    }
    throw err
  } finally {
    clearTimeout(timeout)
  }
}

// Supabase Storage renvoie une URL absolue ; le mode local renvoie « /media/... » (relatif à l'API)
export const urlImage = (url) => {
  if (!url) return ''
  return url.startsWith('http') ? url : `${API_URL}${url}`
}