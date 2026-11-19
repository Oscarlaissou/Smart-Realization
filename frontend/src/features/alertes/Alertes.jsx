import { useCallback, useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import Entete from '../../components/Entete.jsx'
import CarteAlerte from './components/CarteAlerte.jsx'
import PreferencesAlertes from './components/PreferencesAlertes.jsx'
import {
  enregistrerPreferences,
  lirePreferences,
  listerAlertes,
  marquerLue,
  testerEmail,
  toutMarquerLues,
  verifierAlertes,
} from './api.js'
import { lireProfil, modifierProfil } from '../parametres/api.js'
import './Alertes.css'

const CATEGORIES = ['toutes', 'secheresse', 'exces_eau', 'capteur', 'fuite', 'vanne']

function normaliser(texte = '') {
  return String(texte)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
}

const ALERTES_PAR_PAGE = 5

export default function Alertes() {
  const { t } = useTranslation()
  const [alertes, setAlertes] = useState([])
  const [preferences, setPreferences] = useState([])
  const [profil, setProfil] = useState({ nom: '', telephone: '', email: '', role: '', langue: 'fr' })
  const [filtre, setFiltre] = useState('toutes')
  const [recherche, setRecherche] = useState('')
  const [chargement, setChargement] = useState(true)
  const [enCours, setEnCours] = useState(false)
  const [erreur, setErreur] = useState('')
  const [succes, setSucces] = useState('')
  const [page, setPage] = useState(1)

  const charger = useCallback(async () => {
    setChargement(true)
    setErreur('')
    try {
      const [listeAlertes, listePreferences, profilActuel] = await Promise.all([
        listerAlertes(),
        lirePreferences(),
        lireProfil(),
      ])
      setAlertes(listeAlertes || [])
      setPreferences(listePreferences || [])
      setProfil(profilActuel || {})
    } catch (exception) {
      setErreur(exception.message || t('common.erreurServeur'))
    } finally {
      setChargement(false)
    }
  }, [t])

  useEffect(() => {
    charger()
  }, [charger])

  useEffect(() => {
    if (!succes) return undefined
    const minuteur = window.setTimeout(() => setSucces(''), 4000)
    return () => window.clearTimeout(minuteur)
  }, [succes])

  const nonLues = alertes.filter((alerte) => !alerte.lue).length

  const alertesAffichees = useMemo(() => {
    const terme = normaliser(recherche)
    return alertes.filter((alerte) => {
      if (filtre !== 'toutes' && alerte.categorie !== filtre) return false
      if (!terme) return true
      return (
        normaliser(alerte.message).includes(terme) ||
        normaliser(alerte.categorie).includes(terme)
      )
    })
  }, [alertes, filtre, recherche])

  // Pagination : ALERTES_PAR_PAGE alertes par page
  const nombrePages = Math.max(1, Math.ceil(alertesAffichees.length / ALERTES_PAR_PAGE))
  const pageCourante = Math.min(page, nombrePages)
  const alertesDeLaPage = alertesAffichees.slice(
    (pageCourante - 1) * ALERTES_PAR_PAGE,
    pageCourante * ALERTES_PAR_PAGE,
  )

  // Nouveau filtre ou nouvelle recherche : retour à la première page
  useEffect(() => {
    setPage(1)
  }, [filtre, recherche])

  const compterCategorie = (categorie) =>
    categorie === 'toutes'
      ? alertes.length
      : alertes.filter((alerte) => alerte.categorie === categorie).length

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

  const marquerUneLue = (id) => {
    executer(async () => {
      await marquerLue(id)
      setAlertes((liste) =>
        liste.map((alerte) => (alerte.id === id ? { ...alerte, lue: true } : alerte)),
      )
      window.dispatchEvent(new Event('sevia:alertes'))
    })
  }

  const marquerToutesLues = () => {
    executer(async () => {
      await toutMarquerLues()
      setAlertes((liste) => liste.map((alerte) => ({ ...alerte, lue: true })))
      window.dispatchEvent(new Event('sevia:alertes'))
    })
  }

  const verifier = () => {
    executer(async () => {
      await verifierAlertes()
      await charger()
      window.dispatchEvent(new Event('sevia:alertes'))
    }, t('alertes.succesVerification'))
  }

  const testerEnvoiEmail = () => {
    executer(async () => {
      await testerEmail()
    }, t('alertes.succesTestEmail'))
  }

  const changerPreference = (categorie, canal, valeur) => {
    setPreferences((liste) =>
      liste.map((preference) =>
        preference.categorie === categorie
          ? { ...preference, [canal]: valeur }
          : preference,
      ),
    )
  }

  const changerProfil = (champ, valeur) => {
    setProfil((precedent) => ({ ...precedent, [champ]: valeur }))
  }

  const sauvegarderPreferences = () => {
    executer(async () => {
      const resultat = await enregistrerPreferences(
        preferences.map((preference) => ({
          categorie: preference.categorie,
          notification: Boolean(preference.notification),
          email: Boolean(preference.email),
          sms: Boolean(preference.sms),
        })),
      )
      const profilMisAJour = await modifierProfil({
        nom: profil.nom,
        telephone: profil.telephone,
        role: profil.role,
        langue: profil.langue,
        email_alertes: (profil.email_alertes || '').trim() || null,
      })
      setPreferences(resultat || preferences)
      setProfil(profilMisAJour)
      localStorage.setItem('utilisateur', JSON.stringify(profilMisAJour))
    }, t('alertes.succesPreferences'))
  }

  return (
    <div className="alertes-page">
      <Entete
        titre={t('alertes.titre')}
        sousTitre={t('alertes.sousTitre', { nombre: nonLues })}
        recherche={recherche}
        onRecherche={setRecherche}
        placeholderRecherche={t('common.rechercherAlerte')}
        alertesActives={nonLues}
      >
        <button
          type="button"
          className="bouton-secondaire bouton-entete"
          disabled={enCours}
          onClick={verifier}
        >
          {t('alertes.verifier')}
        </button>
      </Entete>

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

      <div className="alertes-grille">
        <section className="carte alertes-liste" aria-labelledby="alertes-recentes-titre">
          <div className="carte-entete">
            <h2 id="alertes-recentes-titre" className="carte-titre">
              {t('alertes.recentes')}
            </h2>
            {nonLues > 0 && (
              <button
                type="button"
                className="lien-action"
                disabled={enCours}
                onClick={marquerToutesLues}
              >
                {t('alertes.toutMarquer')}
              </button>
            )}
          </div>

          <div role="group" aria-label={t('alertes.type')} className="alertes-pills">
            {CATEGORIES.map((categorie) => {
              const nombre = compterCategorie(categorie)
              if (categorie !== 'toutes' && nombre === 0) return null
              return (
                <button
                  key={categorie}
                  type="button"
                  aria-pressed={filtre === categorie}
                  className={`alertes-pill ${filtre === categorie ? 'active' : ''}`}
                  onClick={() => setFiltre(categorie)}
                >
                  {t(`alertes.${categorie}`)} ({nombre})
                </button>
              )
            })}
          </div>

          <ul className="alertes-liste-items">
            {alertesAffichees.length === 0 && (
              <li className="texte-discret">{t('alertes.aucuneAlerte')}</li>
            )}
            {alertesDeLaPage.map((alerte) => (
              <CarteAlerte
                key={alerte.id}
                alerte={alerte}
                preferences={preferences}
                enCours={enCours}
                onMarquerLue={marquerUneLue}
              />
            ))}
          </ul>

          {nombrePages > 1 && (
            <div role="navigation" className="alertes-pagination" aria-label={t('alertes.pagination')}>
              <button
                type="button"
                className="bouton-secondaire"
                disabled={pageCourante === 1}
                onClick={() => setPage(pageCourante - 1)}
              >
                {t('alertes.pagePrecedente')}
              </button>
              <span aria-live="polite">
                {t('alertes.pageSur', { page: pageCourante, total: nombrePages })}
              </span>
              <button
                type="button"
                className="bouton-secondaire"
                disabled={pageCourante === nombrePages}
                onClick={() => setPage(pageCourante + 1)}
              >
                {t('alertes.pageSuivante')}
              </button>
            </div>
          )}
        </section>

        <PreferencesAlertes
          preferences={preferences}
          profil={profil}
          onChanger={changerPreference}
          onProfilChange={changerProfil}
          onEnregistrer={sauvegarderPreferences}
          onTesterEmail={testerEnvoiEmail}
          enCours={enCours}
        />
      </div>
    </div>
  )
}
