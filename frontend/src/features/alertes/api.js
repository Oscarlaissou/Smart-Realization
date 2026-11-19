// Appels API de la fonctionnalité « alertes » (utiliser api() de ../../services/api.js)
import { api } from '../../services/api.js'

// export const lister = () => api('/alertes')

// Compteur d'alertes non lues affiché dans l'en-tête partagé (Entete.jsx).
export const lireCompteur = () => api('/alertes/compteur')
