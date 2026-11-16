// Appels API de la fonctionnalité « dashboard » (utiliser api() de ../../services/api.js)
import { api } from '../../services/api.js'

export const lister = (filtres = {}) => {
  const params = new URLSearchParams()

  if (filtres.periode) params.append('periode', filtres.periode)
  if (filtres.parcelle && filtres.parcelle !== 'Toutes les parcelles') {
    params.append('parcelle', filtres.parcelle)
  }
  if (filtres.culture && filtres.culture !== 'Toutes les cultures') {
    params.append('culture', filtres.culture)
  }

  const query = params.toString()
  return api(query ? `/dashboard/indicateurs?${query}` : '/dashboard/indicateurs')
}