
import { api } from '../../services/api.js'

// ============================================================
// EXPLOITATIONS
// ============================================================

export const listerExploitations = () =>
  api('/exploitations')

export const creerExploitation = (donnees) =>
  api('/exploitations', {
    method: 'POST',
    body: JSON.stringify(donnees),
  })

export const modifierExploitation = (id, donnees) =>
  api(`/exploitations/${id}`, {
    method: 'PUT',
    body: JSON.stringify(donnees),
  })

export const supprimerExploitation = (id) =>
  api(`/exploitations/${id}`, {
    method: 'DELETE',
  })


// ============================================================
// PARCELLES
// ============================================================

export const listerParcelles = (exploitationId) =>
  api(
    exploitationId
      ? `/parcelles?exploitation_id=${exploitationId}`
      : '/parcelles',
  )

export const lireParcelle = (id) =>
  api(`/parcelles/${id}`)

export const creerParcelle = (donnees) =>
  api('/parcelles', {
    method: 'POST',
    body: JSON.stringify(donnees),
  })

export const modifierParcelle = (id, donnees) =>
  api(`/parcelles/${id}`, {
    method: 'PUT',
    body: JSON.stringify(donnees),
  })

export const supprimerParcelle = (id) =>
  api(`/parcelles/${id}`, {
    method: 'DELETE',
  })


// ============================================================
// CULTURES
// ============================================================

export const listerCultures = (parcelleId) =>
  api(`/parcelles/${parcelleId}/cultures`)

export const ajouterCulture = (parcelleId, donnees) =>
  api(`/parcelles/${parcelleId}/cultures`, {
    method: 'POST',
    body: JSON.stringify(donnees),
  })

export const modifierCulture = (cultureId, donnees) =>
  api(`/cultures/${cultureId}`, {
    method: 'PUT',
    body: JSON.stringify(donnees),
  })

export const supprimerCulture = (cultureId) =>
  api(`/cultures/${cultureId}`, {
    method: 'DELETE',
  })


// ============================================================
// ÉQUIPEMENTS
// ============================================================

export const listerEquipements = () =>
  api('/equipements')

export const getEquipements = () =>
  listerEquipements()

export const associerEquipement = (parcelleId, equipementId) =>
  api(
    `/parcelles/${parcelleId}/equipements?equipement_id=${equipementId}`,
    {
      method: 'POST',
    },
  )

export const dissocierEquipement = (parcelleId, equipementId) =>
  api(`/parcelles/${parcelleId}/equipements/${equipementId}`, {
    method: 'DELETE',
  })


// ============================================================
// VÉRIFICATION DU SERVEUR
// ============================================================

export const checkHealth = () =>
  api('/health')

// Alias pour compatibilité avec l'autre branche

export const getParcelles = () =>
  listerParcelles()

export const getParcelle = (id) =>
  lireParcelle(id)

export const createParcelle = (data) =>
  creerParcelle(data)

export const updateParcelle = (id, data) =>
  modifierParcelle(id, data)

export const deleteParcelle = (id) =>
  supprimerParcelle(id)
