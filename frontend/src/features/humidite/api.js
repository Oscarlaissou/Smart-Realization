const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

function headersAuth() {
  const token = localStorage.getItem('token')
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
}

async function gererReponse(res, messageErreur) {
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || messageErreur)
  }
  return res.json()
}

export async function lireApercuHumidite() {
  const res = await fetch(`${API_URL}/humidite/apercu`, {
    headers: headersAuth(),
  })
  return gererReponse(res, "Impossible de charger les données d'humidité.")
}

export async function declarerArrosageManuel(donnees) {
  const res = await fetch(`${API_URL}/humidite/arrosages`, {
    method: 'POST',
    headers: headersAuth(),
    body: JSON.stringify(donnees),
  })
  return gererReponse(res, "Impossible d'enregistrer l'arrosage.")
}

export async function sauvegarderSeuilsParcelle(parcelleId, seuils) {
  const res = await fetch(`${API_URL}/humidite/parcelles/${parcelleId}/seuils`, {
    method: 'PATCH',
    headers: headersAuth(),
    body: JSON.stringify(seuils),
  })
  return gererReponse(res, "Impossible d'enregistrer les seuils.")
}