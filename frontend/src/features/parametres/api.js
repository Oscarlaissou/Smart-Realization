import { api } from '../../services/api.js'

export const lireProfil = () => api('/auth/moi')

export const modifierProfil = (donnees) =>
  api('/auth/moi', { method: 'PUT', body: JSON.stringify(donnees) })
