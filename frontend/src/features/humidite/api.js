// Appels API de la fonctionnalité « humidite »
import { api } from '../../services/api.js'

export const lireContexte = () => api('/humidite/contexte')

export const listerParcelles = () => api('/humidite/parcelles')

export const lireRecommandations = (parcelleId, seuilMin = 30, seuilMax = 45) =>
  api(`/humidite/recommandations/${parcelleId}?seuil_min=${seuilMin}&seuil_max=${seuilMax}`)

export const listerMesures = (parcelleId, limite = 24) =>
  api(`/humidite/mesures/${parcelleId}?limite=${limite}`)

export const listerIrrigations = () => api('/humidite/irrigations')

export const listerCycles = () => api('/humidite/cycles')

export const ajouterCycle = (donnees) =>
  api('/humidite/cycles', {
    method: 'POST',
    body: JSON.stringify(donnees),
  })

export const basculerCycle = (cycleId) =>
  api(`/humidite/cycles/${cycleId}`, {
    method: 'PATCH',
  })

export const supprimerCycle = (cycleId) =>
  api(`/humidite/cycles/${cycleId}`, {
    method: 'DELETE',
  })