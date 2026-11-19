import { api } from '../../services/api.js'

export const lireProfil = () => api('/auth/moi')

export const modifierProfil = (donnees) =>
  api('/auth/moi', { method: 'PUT', body: JSON.stringify(donnees) })

export const changerMotDePasse = (donnees) =>
  api('/auth/mot-de-passe', { method: 'POST', body: JSON.stringify(donnees) })

export const exporterDonnees = () => api('/auth/export')
