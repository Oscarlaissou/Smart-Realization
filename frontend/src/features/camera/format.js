// Le backend renvoie des dates UTC sans suffixe de fuseau (« 2026-11-18T10:39:56.121650 ») :
// sans « Z », le navigateur les lirait comme de l'heure locale et décalerait l'affichage.
export function lireDate(iso) {
  if (!iso) return null
  const txt = /([zZ]|[+-]\d{2}:?\d{2})$/.test(iso) ? iso : `${iso}Z`
  const d = new Date(txt)
  return Number.isNaN(d.getTime()) ? null : d
}

export const nombre = (n) => Number(n || 0).toLocaleString('fr-FR')

// 12 nov.
export function dateCourte(iso) {
  const d = lireDate(iso)
  return d ? d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' }) : ''
}

// 12 nov. 2026
export function dateLongue(iso) {
  const d = lireDate(iso)
  return d ? d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' }) : ''
}

// 12 nov. 2026 · 08:00
export function dateHeure(iso) {
  const d = lireDate(iso)
  if (!d) return ''
  const h = d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
  return `${dateLongue(iso)} · ${h}`
}

// « Parcelle Nord » -> « Nord » (comme dans le tableau de bord)
export const nomCourt = (nom = '') => nom.replace(/^Parcelle\s+/i, '')

// Supprime les accents et met en minuscules pour une recherche souple
export function normaliser(texte = '') {
  return String(texte)
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .trim()
}