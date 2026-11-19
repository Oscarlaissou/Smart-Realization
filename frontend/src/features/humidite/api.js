import { messageErreur as formaterDetail } from '../../services/api.js'
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
    throw new Error(formaterDetail(data.detail) || messageErreur)
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

/**
 * Écoute en direct les nouvelles mesures (GET /humidite/flux, Server-Sent Events).
 * fetch (et non EventSource) pour pouvoir envoyer le jeton dans l'en-tête Authorization.
 * Se reconnecte tout seul après une coupure. Renvoie une fonction pour arrêter l'écoute.
 */
export function ecouterMesures({ onMesure, onEtat }) {
  let arrete = false
  let controleur = null
  let delai = 1000

  const boucle = async () => {
    while (!arrete) {
      controleur = new AbortController()
      try {
        const res = await fetch(`${API_URL}/humidite/flux`, {
          headers: headersAuth(),
          signal: controleur.signal,
        })
        if (res.status === 401) {
          onEtat?.('deconnecte')
          return
        }
        if (!res.ok || !res.body) throw new Error(`flux ${res.status}`)
        onEtat?.('direct')
        delai = 1000
        const lecteur = res.body.getReader()
        const decodeur = new TextDecoder()
        let tampon = ''
        for (;;) {
          const { value, done } = await lecteur.read()
          if (done) break
          tampon += decodeur.decode(value, { stream: true })
          let fin
          while ((fin = tampon.indexOf('\n\n')) >= 0) {
            const bloc = tampon.slice(0, fin)
            tampon = tampon.slice(fin + 2)
            const lignes = bloc.split('\n')
            const type = lignes.find((l) => l.startsWith('event:'))?.slice(6).trim()
            const donnees = lignes.filter((l) => l.startsWith('data:')).map((l) => l.slice(5)).join('\n')
            if (type === 'mesure' && donnees) {
              try {
                onMesure(JSON.parse(donnees))
              } catch {
                /* message illisible : ignoré */
              }
            }
          }
        }
      } catch {
        if (arrete) return
      }
      if (arrete) return
      onEtat?.('reconnexion')
      await new Promise((r) => setTimeout(r, delai))
      delai = Math.min(delai * 2, 15000)
    }
  }

  boucle()
  return () => {
    arrete = true
    controleur?.abort()
  }
}
