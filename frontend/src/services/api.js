// Toutes les requêtes vers le back passent par ici.
const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function api(chemin, options = {}) {
  const token = localStorage.getItem('token')
  const res = await fetch(BASE + chemin, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(token && { Authorization: `Bearer ${token}` }), ...options.headers },
  })
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText)
  return res.status === 204 ? null : res.json()
}

export async function connexion(email, motDePasse) {
  const corps = new URLSearchParams({ username: email, password: motDePasse })
  const res = await fetch(BASE + '/auth/login', { method: 'POST', body: corps })
  if (!res.ok) throw new Error('Identifiants incorrects')
  localStorage.setItem('token', (await res.json()).access_token)
}
