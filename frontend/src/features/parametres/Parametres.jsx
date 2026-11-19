import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import Entete from '../../components/Entete.jsx'
import { changerLangue } from '../../i18n/index.js'
import { changerMotDePasse, exporterDonnees, lireProfil, modifierProfil } from './api.js'
import './Parametres.css'

const CLE_CONTRASTE = 'sevia_contraste_eleve'
const CLE_UNITES = 'sevia_unites_metriques'
const CLE_FREQUENCE = 'sevia_frequence_sauvegarde'
const CLE_DERNIERE_SAUVEGARDE = 'sevia_derniere_sauvegarde'
const CLE_DONNEES = 'sevia_preferences_donnees'

function lireStockage(cle, valeurParDefaut) {
  try {
    const valeur = JSON.parse(localStorage.getItem(cle))
    return valeur ?? valeurParDefaut
  } catch {
    return valeurParDefaut
  }
}

function formaterDateHeure(valeur, locale) {
  if (!valeur) return '—'
  const date = new Date(valeur)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleString(locale, {
    day: 'numeric',
    month: 'long',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function Parametres() {
  const { t, i18n } = useTranslation()
  const locale = i18n.language === 'en' ? 'en-GB' : 'fr-FR'

  const [profil, setProfil] = useState({
    nom: '',
    telephone: '',
    email: '',
    role: 'Exploitant agricole',
    langue: i18n.language,
  })
  const [motDePasse, setMotDePasse] = useState({
    ancien_mot_de_passe: '',
    nouveau_mot_de_passe: '',
    confirmation: '',
  })
  const [contraste, setContraste] = useState(() => lireStockage(CLE_CONTRASTE, false))
  const [unites, setUnites] = useState(() => lireStockage(CLE_UNITES, true))
  const [frequence, setFrequence] = useState(
    () => localStorage.getItem(CLE_FREQUENCE) || '24h',
  )
  const [donnees, setDonnees] = useState(() =>
    lireStockage(CLE_DONNEES, {
      conserverImages: true,
      utiliserDonnees: true,
      recevoirRappels: true,
    }),
  )
  const [derniereSauvegarde, setDerniereSauvegarde] = useState(
    () => localStorage.getItem(CLE_DERNIERE_SAUVEGARDE) || '',
  )

  const [chargement, setChargement] = useState(true)
  const [enCours, setEnCours] = useState(false)
  const [erreur, setErreur] = useState('')
  const [succes, setSucces] = useState('')

  useEffect(() => {
    lireProfil()
      .then((resultat) => {
        setProfil({
          nom: resultat.nom || '',
          telephone: resultat.telephone || '',
          email: resultat.email || '',
          role: resultat.role || 'Exploitant agricole',
          langue: resultat.langue || i18n.language,
        })
      })
      .catch((exception) => setErreur(exception.message || t('common.erreurServeur')))
      .finally(() => setChargement(false))
  }, [i18n.language, t])

  useEffect(() => {
    document.documentElement.dataset.contraste = contraste ? 'eleve' : 'normal'
    localStorage.setItem(CLE_CONTRASTE, JSON.stringify(contraste))
  }, [contraste])

  useEffect(() => {
    if (!succes) return undefined
    const minuteur = window.setTimeout(() => setSucces(''), 4000)
    return () => window.clearTimeout(minuteur)
  }, [succes])

  const executer = async (action, messageSucces) => {
    setEnCours(true)
    setErreur('')
    try {
      await action()
      if (messageSucces) setSucces(messageSucces)
    } catch (exception) {
      setErreur(exception.message || t('common.erreurServeur'))
    } finally {
      setEnCours(false)
    }
  }

  const sauvegarderProfil = (evenement) => {
    evenement.preventDefault()
    executer(async () => {
      const resultat = await modifierProfil({
        nom: profil.nom,
        telephone: profil.telephone,
        role: profil.role,
        langue: profil.langue,
      })
      setProfil((precedent) => ({ ...precedent, ...resultat }))
      localStorage.setItem('utilisateur', JSON.stringify(resultat))
      if (resultat.langue !== i18n.language) {
        await changerLangue(resultat.langue)
      }
    }, t('parametres.succesProfil'))
  }

  const sauvegarderMotDePasse = (evenement) => {
    evenement.preventDefault()
    if (motDePasse.nouveau_mot_de_passe !== motDePasse.confirmation) {
      setErreur(t('parametres.erreurMotDePasse'))
      return
    }
    executer(async () => {
      await changerMotDePasse({
        ancien_mot_de_passe: motDePasse.ancien_mot_de_passe,
        nouveau_mot_de_passe: motDePasse.nouveau_mot_de_passe,
      })
      setMotDePasse({
        ancien_mot_de_passe: '',
        nouveau_mot_de_passe: '',
        confirmation: '',
      })
    }, t('parametres.succesMotDePasse'))
  }

  const telechargerSauvegarde = () => {
    executer(async () => {
      const donneesExportees = await exporterDonnees()
      const blob = new Blob([JSON.stringify(donneesExportees, null, 2)], {
        type: 'application/json;charset=utf-8',
      })
      const url = URL.createObjectURL(blob)
      const lien = document.createElement('a')
      lien.href = url
      lien.download = `sevia-sauvegarde-${new Date().toISOString().slice(0, 10)}.json`
      document.body.appendChild(lien)
      lien.click()
      document.body.removeChild(lien)
      URL.revokeObjectURL(url)

      const maintenant = new Date().toISOString()
      localStorage.setItem(CLE_DERNIERE_SAUVEGARDE, maintenant)
      setDerniereSauvegarde(maintenant)
      localStorage.setItem(CLE_FREQUENCE, frequence)
    }, t('parametres.succesSauvegarde'))
  }

  const mettreAJourDonnees = (cle, valeur) => {
    const suivantes = { ...donnees, [cle]: valeur }
    setDonnees(suivantes)
    localStorage.setItem(CLE_DONNEES, JSON.stringify(suivantes))
  }

  return (
    <div className="parametres-page">
      <Entete titre={t('parametres.titre')} sousTitre={t('parametres.sousTitre')} />

      {erreur && (
        <div className="bandeau bandeau-erreur" role="alert">
          {erreur}
        </div>
      )}
      {succes && (
        <div className="bandeau bandeau-succes" role="status">
          {succes}
        </div>
      )}
      {chargement && <div className="bandeau bandeau-info">{t('common.chargement')}</div>}

      <div className="parametres-grille">
        <section className="carte parametres-carte" aria-labelledby="profil-titre">
          <h2 id="profil-titre" className="carte-titre">
            {t('parametres.profil')}
          </h2>
          <form className="parametres-formulaire" onSubmit={sauvegarderProfil}>
            <div className="champ">
              <label htmlFor="parametres-nom">{t('parametres.nomComplet')}</label>
              <input
                id="parametres-nom"
                value={profil.nom}
                required
                onChange={(evenement) => setProfil({ ...profil, nom: evenement.target.value })}
              />
            </div>
            <div className="champ">
              <label htmlFor="parametres-telephone">{t('parametres.telephone')}</label>
              <input
                id="parametres-telephone"
                value={profil.telephone}
                onChange={(evenement) =>
                  setProfil({ ...profil, telephone: evenement.target.value })
                }
              />
            </div>
            <div className="champ">
              <label htmlFor="parametres-email">{t('parametres.email')}</label>
              <input id="parametres-email" value={profil.email} readOnly />
            </div>
            <div className="champ">
              <label htmlFor="parametres-role">{t('parametres.role')}</label>
              <select
                id="parametres-role"
                value={profil.role}
                onChange={(evenement) => setProfil({ ...profil, role: evenement.target.value })}
              >
                <option value="Exploitant agricole">Exploitant agricole</option>
                <option value="Technicien agricole / agronome">
                  Technicien agricole / agronome
                </option>
              </select>
            </div>
            <div className="champ parametres-champ-large">
              <label htmlFor="parametres-langue">{t('parametres.langueInterface')}</label>
              <select
                id="parametres-langue"
                value={profil.langue}
                onChange={(evenement) => setProfil({ ...profil, langue: evenement.target.value })}
              >
                <option value="fr">{t('parametres.francais')}</option>
                <option value="en">{t('parametres.anglais')}</option>
              </select>
            </div>
            <div className="parametres-actions parametres-champ-large">
              <button type="submit" className="bouton-primaire" disabled={enCours}>
                {t('parametres.enregistrerProfil')}
              </button>
            </div>
          </form>
        </section>

        <section className="carte parametres-carte" aria-labelledby="affichage-titre">
          <h2 id="affichage-titre" className="carte-titre">
            {t('parametres.langueAffichage')}
          </h2>
          <fieldset className="parametres-fieldset">
            <legend>{t('parametres.langueInterface')}</legend>
            <label className="parametres-option">
              <input
                type="radio"
                name="langue-interface"
                checked={profil.langue === 'fr'}
                onChange={() => setProfil({ ...profil, langue: 'fr' })}
              />
              {t('parametres.francais')}
              <span className="badge-statut ok">{t('parametres.parDefaut')}</span>
            </label>
            <label className="parametres-option">
              <input
                type="radio"
                name="langue-interface"
                checked={profil.langue === 'en'}
                onChange={() => setProfil({ ...profil, langue: 'en' })}
              />
              {t('parametres.anglais')}
            </label>
          </fieldset>

          <label className="parametres-option">
            <input
              type="checkbox"
              checked={contraste}
              onChange={(evenement) => setContraste(evenement.target.checked)}
            />
            {t('parametres.contraste')}
          </label>
          <label className="parametres-option">
            <input
              type="checkbox"
              checked={unites}
              onChange={(evenement) => {
                setUnites(evenement.target.checked)
                localStorage.setItem(CLE_UNITES, JSON.stringify(evenement.target.checked))
              }}
            />
            {t('parametres.unites')}
          </label>
        </section>

        <section className="carte parametres-carte" aria-labelledby="securite-titre">
          <h2 id="securite-titre" className="carte-titre">
            {t('parametres.securite')}
          </h2>
          <form className="parametres-formulaire" onSubmit={sauvegarderMotDePasse}>
            <div className="champ">
              <label htmlFor="ancien-mot-de-passe">{t('parametres.ancienMotDePasse')}</label>
              <input
                id="ancien-mot-de-passe"
                type="password"
                autoComplete="current-password"
                value={motDePasse.ancien_mot_de_passe}
                required
                onChange={(evenement) =>
                  setMotDePasse({
                    ...motDePasse,
                    ancien_mot_de_passe: evenement.target.value,
                  })
                }
              />
            </div>
            <div className="champ">
              <label htmlFor="nouveau-mot-de-passe">{t('parametres.nouveauMotDePasse')}</label>
              <input
                id="nouveau-mot-de-passe"
                type="password"
                autoComplete="new-password"
                minLength="6"
                value={motDePasse.nouveau_mot_de_passe}
                required
                onChange={(evenement) =>
                  setMotDePasse({
                    ...motDePasse,
                    nouveau_mot_de_passe: evenement.target.value,
                  })
                }
              />
            </div>
            <div className="champ parametres-champ-large">
              <label htmlFor="confirmation-mot-de-passe">
                {t('parametres.nouveauMotDePasse')} · {t('common.confirmer')}
              </label>
              <input
                id="confirmation-mot-de-passe"
                type="password"
                autoComplete="new-password"
                minLength="6"
                value={motDePasse.confirmation}
                required
                onChange={(evenement) =>
                  setMotDePasse({ ...motDePasse, confirmation: evenement.target.value })
                }
              />
            </div>
            <div className="parametres-actions parametres-champ-large">
              <button type="submit" className="bouton-primaire" disabled={enCours}>
                {t('parametres.changerMotDePasse')}
              </button>
            </div>
          </form>
        </section>

        <section className="carte parametres-carte" aria-labelledby="sauvegardes-titre">
          <h2 id="sauvegardes-titre" className="carte-titre">
            {t('parametres.sauvegardes')}
          </h2>
          <div className="sauvegarde-info">
            <b>{t('parametres.derniereSauvegarde')}</b>
            <span>{formaterDateHeure(derniereSauvegarde, locale)}</span>
          </div>
          <div className="champ">
            <label htmlFor="frequence-sauvegarde">{t('parametres.frequence')}</label>
            <select
              id="frequence-sauvegarde"
              value={frequence}
              onChange={(evenement) => {
                setFrequence(evenement.target.value)
                localStorage.setItem(CLE_FREQUENCE, evenement.target.value)
              }}
            >
              <option value="24h">{t('parametres.toutesLes24h')}</option>
              <option value="12h">{t('parametres.toutesLes12h')}</option>
              <option value="7j">{t('parametres.toutesLes7j')}</option>
            </select>
          </div>
          <div className="parametres-actions">
            <button
              type="button"
              className="bouton-primaire"
              disabled={enCours}
              onClick={telechargerSauvegarde}
            >
              {t('parametres.sauvegarderMaintenant')}
            </button>
            <button
              type="button"
              className="bouton-secondaire"
              onClick={() => setSucces(t('parametres.restaurationIndisponible'))}
            >
              {t('parametres.restaurer')}
            </button>
          </div>
        </section>

        <section className="carte parametres-carte parametres-champ-large" aria-labelledby="donnees-titre">
          <h2 id="donnees-titre" className="carte-titre">
            {t('parametres.donnees')}
          </h2>
          <label className="parametres-option">
            <input
              type="checkbox"
              checked={donnees.conserverImages}
              onChange={(evenement) =>
                mettreAJourDonnees('conserverImages', evenement.target.checked)
              }
            />
            {t('parametres.conserverImages')}
          </label>
          <label className="parametres-option">
            <input
              type="checkbox"
              checked={donnees.utiliserDonnees}
              onChange={(evenement) =>
                mettreAJourDonnees('utiliserDonnees', evenement.target.checked)
              }
            />
            {t('parametres.utiliserDonnees')}
          </label>
          <label className="parametres-option">
            <input
              type="checkbox"
              checked={donnees.recevoirRappels}
              onChange={(evenement) =>
                mettreAJourDonnees('recevoirRappels', evenement.target.checked)
              }
            />
            {t('parametres.recevoirRappels')}
          </label>
          <div className="parametres-actions">
            <button
              type="button"
              className="bouton-secondaire"
              disabled={enCours}
              onClick={telechargerSauvegarde}
            >
              {t('parametres.telechargerDonnees')}
            </button>
          </div>
        </section>
      </div>
    </div>
  )
}
