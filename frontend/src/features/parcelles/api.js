import { api } from '../../services/api.js'

export const listerExploitations = () => api('/exploitations')

export const creerExploitation = (donnees) =>
  api('/exploitations', { method: 'POST', body: JSON.stringify(donnees) })

export const modifierExploitation = (id, donnees) =>
  api(`/exploitations/${id}`, { method: 'PUT', body: JSON.stringify(donnees) })

export const supprimerExploitation = (id) =>
  api(`/exploitations/${id}`, { method: 'DELETE' })

export const listerParcelles = (exploitationId) =>
  api(
    exploitationId ? `/parcelles?exploitation_id=${exploitationId}` : '/parcelles',
  )

export const lireParcelle = (id) => api(`/parcelles/${id}`)

export const creerParcelle = (donnees) =>
  api('/parcelles', { method: 'POST', body: JSON.stringify(donnees) })

export const modifierParcelle = (id, donnees) =>
  api(`/parcelles/${id}`, { method: 'PUT', body: JSON.stringify(donnees) })

export const supprimerParcelle = (id) =>
  api(`/parcelles/${id}`, { method: 'DELETE' })

export const listerCultures = (parcelleId) => api(`/parcelles/${parcelleId}/cultures`)

export const ajouterCulture = (parcelleId, donnees) =>
  api(`/parcelles/${parcelleId}/cultures`, {
    method: 'POST',
    body: JSON.stringify(donnees),
  })

export const modifierCulture = (cultureId, donnees) =>
  api(`/cultures/${cultureId}`, { method: 'PUT', body: JSON.stringify(donnees) })

export const supprimerCulture = (cultureId) =>
  api(`/cultures/${cultureId}`, { method: 'DELETE' })

export const listerEquipements = () => api('/equipements')

export const associerEquipement = (parcelleId, equipementId) =>
  api(`/parcelles/${parcelleId}/equipements`, {
    method: 'POST',
    body: JSON.stringify({ equipement_id: equipementId }),
  })

export const dissocierEquipement = (parcelleId, equipementId) =>
  api(`/parcelles/${parcelleId}/equipements/${equipementId}`, { method: 'DELETE' })
