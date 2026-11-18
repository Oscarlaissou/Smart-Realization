import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import fr from './fr.js'
import en from './en.js'

const langueEnregistree = localStorage.getItem('langue')
const langue = ['fr', 'en'].includes(langueEnregistree) ? langueEnregistree : 'fr'

i18n.use(initReactI18next).init({
  resources: {
    fr: { translation: fr },
    en: { translation: en },
  },
  lng: langue,
  fallbackLng: 'fr',
  interpolation: { escapeValue: false },
})

export function changerLangue(nouvelleLangue) {
  const valeur = nouvelleLangue === 'en' ? 'en' : 'fr'
  localStorage.setItem('langue', valeur)
  document.documentElement.lang = valeur
  return i18n.changeLanguage(valeur)
}

document.documentElement.lang = langue

export default i18n
