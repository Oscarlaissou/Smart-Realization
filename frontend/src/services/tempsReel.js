// Connexion temps réel UNIQUE pour toute l'application (GET /humidite/flux, Server-Sent Events).
// Les pages et composants s'y abonnent : ecouter(rappel) pour les événements (« mesure », « alerte »),
// ecouterEtat(rappel) pour l'état de la connexion (connexion | direct | reconnexion | deconnecte).
// La connexion est partagée et comptée : elle reste ouverte tant qu'au moins un abonné en a besoin.
import { lireToken } from './api.js'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

const abonnes = new Set()
const abonnesEtat = new Set()
let etatCourant = 'connexion'
let utilisateurs = 0
let arreterConnexion = null
let arretDiffere = null

function changerEtat(etat) {
  etatCourant = etat
  abonnesEtat.forEach((rappel) => rappel(etat))
}

function ouvrir() {
  let arrete = false
  let controleur = null
  let delai = 1000

  const boucle = async () => {
    while (!arrete) {
      const token = lireToken()
      if (!token) {
        changerEtat('deconnecte')
        return
      }
      controleur = new AbortController()
      try {
        // fetch (et non EventSource) pour envoyer le jeton dans l'en-tête Authorization
        const res = await fetch(`${API_URL}/humidite/flux`, {
          headers: { Authorization: `Bearer ${token}` },
          signal: controleur.signal,
        })
        if (res.status === 401) {
          changerEtat('deconnecte')
          return
        }
        if (!res.ok || !res.body) throw new Error(`flux ${res.status}`)
        changerEtat('direct')
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
            const donnees = bloc
              .split('\n')
              .filter((l) => l.startsWith('data:'))
              .map((l) => l.slice(5))
              .join('\n')
            if (!donnees) continue
            try {
              const evenement = JSON.parse(donnees)
              abonnes.forEach((rappel) => rappel(evenement))
            } catch {
              /* message illisible : ignoré */
            }
          }
        }
      } catch {
        if (arrete) return
      }
      if (arrete) return
      changerEtat('reconnexion')
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

/** Démarre (ou réutilise) la connexion ; renvoie la fonction qui libère cet usage. */
export function utiliserTempsReel() {
  utilisateurs += 1
  window.clearTimeout(arretDiffere)
  if (!arreterConnexion) {
    changerEtat('connexion')
    arreterConnexion = ouvrir()
  }
  let libere = false
  return () => {
    if (libere) return
    libere = true
    utilisateurs -= 1
    // délai : un changement de page démonte puis remonte les composants sans couper la connexion
    arretDiffere = window.setTimeout(() => {
      if (utilisateurs <= 0 && arreterConnexion) {
        arreterConnexion()
        arreterConnexion = null
      }
    }, 3000)
  }
}

/** Coupe immédiatement la connexion (déconnexion de l'utilisateur). */
export function couperTempsReel() {
  window.clearTimeout(arretDiffere)
  arreterConnexion?.()
  arreterConnexion = null
  utilisateurs = 0
  changerEtat('deconnecte')
}

export function ecouter(rappel) {
  abonnes.add(rappel)
  return () => abonnes.delete(rappel)
}

export function ecouterEtat(rappel) {
  abonnesEtat.add(rappel)
  rappel(etatCourant)
  return () => abonnesEtat.delete(rappel)
}
