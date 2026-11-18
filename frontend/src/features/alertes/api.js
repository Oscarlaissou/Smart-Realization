import { api } from '../../services/api.js'

export const listerAlertes = (filtres = {}) => {
  const params = new URLSearchParams()
  if (filtres.categorie && filtres.categorie !== 'toutes') {
    params.append('categorie', filtres.categorie)
  }
  if (filtres.niveau) params.append('niveau', filtres.niveau)
  if (filtres.nonLues) params.append('non_lues', 'true')
  const requete = params.toString()
  return api(requete ? `/alertes?${requete}` : '/alertes')
}

export const lireCompteur = () => api('/alertes/compteur')

export const marquerLue = (id) => api(`/alertes/${id}/lue`, { method: 'POST' })

export const toutMarquerLues = () => api('/alertes/tout-lues', { method: 'POST' })

export const verifierAlertes = () => api('/alertes/verifier', { method: 'POST' })

export const lirePreferences = () => api('/alertes/preferences')

export const testerEmail = () => api('/alertes/test-email', { method: 'POST' })

export const enregistrerPreferences = (preferences) =>
  api('/alertes/preferences', {
    method: 'PUT',
    body: JSON.stringify(preferences),
  })
