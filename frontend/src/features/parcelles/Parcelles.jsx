
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import Entete from '../../components/Entete.jsx'
import {
  ajouterCulture,
  creerExploitation,
  creerParcelle,
  listerEquipements,
  listerExploitations,
  listerParcelles,
  modifierCulture,
  modifierParcelle,
  supprimerCulture,
  supprimerParcelle,
  associerEquipement,
  dissocierEquipement,
} from './api.js'
import './Parcelles.css'

function normaliser(texte = '') {
  return String(texte)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
}

function dateCourte(valeur, locale) {
  if (!valeur) return '—'
  const date = new Date(valeur)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleDateString(locale, {
    day: 'numeric',
    month: 'short',
  })
}

export default function Parcelles() {
  const { t, i18n } = useTranslation()
  const locale = i18n.language === 'en' ? 'en-GB' : 'fr-FR'

  const [exploitations, setExploitations] = useState([])
  const [parcelles, setParcelles] = useState([])
  const [equipements, setEquipements] = useState([])

  const [selectionId, setSelectionId] = useState(null)
  const [recherche, setRecherche] = useState('')
  const [filtreExploitation, setFiltreExploitation] = useState('toutes')

  const [modeCreation, setModeCreation] = useState(false)
  const [afficherNouvelleExploitation, setAfficherNouvelleExploitation] =
    useState(false)

  const [creation, setCreation] = useState({
    nom: '',
    surface_ha: '',
    exploitation_id: '',
  })

  const [nouvelleExploitation, setNouvelleExploitation] = useState({
    nom: '',
    localisation: '',
  })

  const [chargement, setChargement] = useState(true)
  const [enCours, setEnCours] = useState(false)
  const [erreur, setErreur] = useState('')
  const [succes, setSucces] = useState('')

  const [culture, setCulture] = useState('')
  const [dateSemis, setDateSemis] = useState('')
  const [cultureEnEdition, setCultureEnEdition] = useState(null)

  const [nomEdition, setNomEdition] = useState('')
  const [surfaceEdition, setSurfaceEdition] = useState('')
  const [exploitationEdition, setExploitationEdition] = useState('')

  const charger = useCallback(async (idSelection = null) => {
    setChargement(true)
    setErreur('')

    try {
      const [
        listeExploitations,
        listeParcelles,
        listeEquipements,
      ] = await Promise.all([
        listerExploitations(),
        listerParcelles(),
        listerEquipements(),
      ])

      setExploitations(listeExploitations || [])
      setParcelles(listeParcelles || [])
      setEquipements(listeEquipements || [])

      setSelectionId((precedent) => {
        if (
          idSelection !== null &&
          listeParcelles?.some((p) => p.id === idSelection)
        ) {
          return idSelection
        }

        if (listeParcelles?.some((p) => p.id === precedent)) {
          return precedent
        }

        return listeParcelles?.[0]?.id ?? null
      })

      setCreation((precedent) => ({
        ...precedent,
        exploitation_id:
          precedent.exploitation_id || listeExploitations?.[0]?.id || '',
      }))
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

  const parcelleSelectionnee = useMemo(
    () => parcelles.find((p) => p.id === selectionId) || null,
    [parcelles, selectionId],
  )

  useEffect(() => {
    if (!parcelleSelectionnee) return

    setNomEdition(parcelleSelectionnee.nom || '')
    setSurfaceEdition(parcelleSelectionnee.surface_ha ?? '')
    setExploitationEdition(parcelleSelectionnee.exploitation_id ?? '')
    setCulture('')
    setDateSemis('')
    setCultureEnEdition(null)
  }, [parcelleSelectionnee])

  const parcellesAffichees = useMemo(() => {
    const terme = normaliser(recherche)

    return parcelles.filter((parcelle) => {
      if (
        filtreExploitation !== 'toutes' &&
        parcelle.exploitation_id !== Number(filtreExploitation)
      ) {
        return false
      }

      if (!terme) return true

      const cultures = (parcelle.cultures || [])
        .map((c) => c.espece)
        .join(' ')

      return (
        normaliser(parcelle.nom).includes(terme) ||
        normaliser(cultures).includes(terme)
      )
    })
  }, [parcelles, recherche, filtreExploitation])

  const surfaceTotale = parcelles.reduce(
    (total, parcelle) => total + Number(parcelle.surface_ha || 0),
    0,
  )

  const equipementsEnLigne = equipements.filter(
    (equipement) => equipement.en_ligne,
  ).length

  const executer = async (action, messageSucces) => {
    setEnCours(true)
    setErreur('')

    try {
      await action()

      if (messageSucces) {
        setSucces(messageSucces)
      }
    } catch (exception) {
      setErreur(exception.message || t('common.erreurServeur'))
    } finally {
      setEnCours(false)
    }
  }

  const creerLaParcelle = async (evenement) => {
    evenement.preventDefault()

    let idCree = null

    await executer(async () => {
      const parcelle = await creerParcelle({
        nom: creation.nom,
        surface_ha: Number(creation.surface_ha),
        exploitation_id: Number(creation.exploitation_id),
      })

      idCree = parcelle.id

      setModeCreation(false)

      setCreation({
        nom: '',
        surface_ha: '',
        exploitation_id: creation.exploitation_id,
      })

      await charger(idCree)
    }, t('parcelles.succesCreation'))

    if (idCree) {
      window.dispatchEvent(new Event('sevia:alertes'))
    }
  }

  const creerUneExploitation = async (evenement) => {
    evenement.preventDefault()

    await executer(async () => {
      const exploitation = await creerExploitation({
        nom: nouvelleExploitation.nom,
        localisation: nouvelleExploitation.localisation,
      })

      setNouvelleExploitation({
        nom: '',
        localisation: '',
      })

      setAfficherNouvelleExploitation(false)

      setCreation((precedent) => ({
        ...precedent,
        exploitation_id: exploitation.id,
      }))

      await charger()
    }, t('parcelles.succesCreation'))
  }

  const enregistrerParcelle = async (evenement) => {
    evenement.preventDefault()

    if (!parcelleSelectionnee) return

    await executer(async () => {
      await modifierParcelle(parcelleSelectionnee.id, {
        nom: nomEdition,
        surface_ha: Number(surfaceEdition),
        exploitation_id: Number(exploitationEdition),
      })

      await charger(parcelleSelectionnee.id)
    }, t('parcelles.succesModification'))
  }

  const supprimerLaParcelle = (id) => {
    if (!window.confirm('Voulez-vous vraiment supprimer cette parcelle ?')) {
      return
    }

    executer(async () => {
      await supprimerParcelle(id)
      setSelectionId(null)
      setModeCreation(false)
      await charger()
    }, t('parcelles.succesSuppression'))
  }

  const ajouterOuModifierCulture = async (evenement) => {
    evenement.preventDefault()

    if (!parcelleSelectionnee || !culture.trim()) return

    const donnees = {
      espece: culture.trim(),
      date_semis: dateSemis || null,
    }

    await executer(async () => {
      if (cultureEnEdition) {
        await modifierCulture(cultureEnEdition.id, donnees)
      } else {
        await ajouterCulture(parcelleSelectionnee.id, donnees)
      }

      setCulture('')
      setDateSemis('')
      setCultureEnEdition(null)

      await charger(parcelleSelectionnee.id)
    }, cultureEnEdition
      ? t('parcelles.succesModification')
      : t('parcelles.succesCulture'))
  }

  const supprimerUneCulture = (cultureId) => {
    if (!window.confirm('Supprimer cette culture ?')) return

    executer(async () => {
      await supprimerCulture(cultureId)
      await charger(parcelleSelectionnee.id)
    }, t('parcelles.succesSuppressionCulture'))
  }

  const associerUnEquipement = async (evenement) => {
    const equipementId = Number(evenement.target.value)

    if (!equipementId || !parcelleSelectionnee) return

    await executer(async () => {
      await associerEquipement(parcelleSelectionnee.id, equipementId)
      await charger(parcelleSelectionnee.id)
    }, 'Équipement associé avec succès.')
    
    evenement.target.value = ''
  }

  const dissocierUnEquipement = (equipementId) => {
    if (!parcelleSelectionnee) return

    executer(async () => {
      await dissocierEquipement(parcelleSelectionnee.id, equipementId)
      await charger(parcelleSelectionnee.id)
    }, 'Équipement dissocié avec succès.')
  }

  const equipementsParcelle = parcelleSelectionnee
    ? equipements.filter(
        (e) => e.parcelle_id === parcelleSelectionnee.id,
      )
    : []

  const equipementsDisponibles = equipements.filter(
    (e) =>
      !e.parcelle_id ||
      e.parcelle_id === parcelleSelectionnee?.id,
  ).filter(
    (e) => !equipementsParcelle.some((associe) => associe.id === e.id),
  )

  return (
    <div className="parcelles-page">
      <Entete
        titre={t('parcelles.titre')}
        sousTitre={t('parcelles.sousTitre')}
        recherche={recherche}
        onRecherche={setRecherche}
        placeholderRecherche={t('common.rechercherParcelle')}
      >
        <button
          type="button"
          className="bouton-primaire bouton-entete"
          disabled={exploitations.length === 0}
          onClick={() => {
            setModeCreation(true)
            setSelectionId(null)
          }}
        >
          {t('parcelles.nouvelleParcelle')}
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

      {chargement && (
        <div className="bandeau bandeau-info">
          {t('common.chargement')}
        </div>
      )}

      <section
        aria-label={t('parcelles.resumeParcelles')}
        className="parcelles-resume"
      >
        <div className="carte-resume">
          <span>{t('parcelles.resumeParcelles')}</span>
          <strong>{parcelles.length}</strong>
        </div>

        <div className="carte-resume">
          <span>{t('parcelles.surfaceTotale')}</span>
          <strong>
            {surfaceTotale.toLocaleString(locale, {
              maximumFractionDigits: 2,
            })}
            {' '}
            <small>{t('common.ha')}</small>
          </strong>
        </div>

        <div className="carte-resume">
          <span>{t('parcelles.equipementsEnLigne')}</span>
          <strong>
            {equipementsEnLigne}
            <small> / {equipements.length}</small>
          </strong>
        </div>
      </section>

      {exploitations.length === 0 && (
        <section className="carte parcelle-exploitation-creation">
          <h2>{t('parcelles.nouvelleExploitation')}</h2>
          <p className="texte-discret">
            {t('parcelles.aucuneExploitation')}
          </p>

          <form
            className="formulaire-exploitation"
            onSubmit={creerUneExploitation}
          >
            <div className="champ">
              <label htmlFor="exploitation-nom">
                {t('parcelles.nomExploitation')}
              </label>
              <input
                id="exploitation-nom"
                value={nouvelleExploitation.nom}
                required
                onChange={(e) =>
                  setNouvelleExploitation({
                    ...nouvelleExploitation,
                    nom: e.target.value,
                  })
                }
              />
            </div>

            <div className="champ">
              <label htmlFor="exploitation-localisation">
                {t('parcelles.localisation')}
              </label>
              <input
                id="exploitation-localisation"
                value={nouvelleExploitation.localisation}
                onChange={(e) =>
                  setNouvelleExploitation({
                    ...nouvelleExploitation,
                    localisation: e.target.value,
                  })
                }
              />
            </div>

            <button
              type="submit"
              className="bouton-primaire"
              disabled={enCours}
            >
              {t('parcelles.creerExploitation')}
            </button>
          </form>
        </section>
      )}

      {(afficherNouvelleExploitation || exploitations.length > 0) && (
        <div className="parcelles-grille">
          <section
            className="carte parcelles-liste"
            aria-labelledby="liste-parcelles-titre"
          >
            <div className="carte-entete">
              <h2 id="liste-parcelles-titre">
                {t('parcelles.liste')}
              </h2>

              <div className="liste-filtres">
                <select
                  aria-label={t('parcelles.exploitation')}
                  value={filtreExploitation}
                  onChange={(e) =>
                    setFiltreExploitation(e.target.value)
                  }
                >
                  <option value="toutes">{t('common.toutes')}</option>

                  {exploitations.map((exploitation) => (
                    <option
                      key={exploitation.id}
                      value={exploitation.id}
                    >
                      {exploitation.nom}
                    </option>
                  ))}
                </select>

                <button
                  type="button"
                  className="lien-action"
                  onClick={() =>
                    setAfficherNouvelleExploitation((v) => !v)
                  }
                >
                  {t('parcelles.nouvelleExploitation')}
                </button>
              </div>
            </div>

            <div className="table-defilante">
              <table className="table-parcelles">
                <caption className="sr-only">
                  {t('parcelles.liste')}
                </caption>

                <thead>
                  <tr>
                    <th scope="col">{t('parcelles.nom')}</th>
                    <th scope="col">{t('parcelles.surface')}</th>
                    <th scope="col">{t('parcelles.culture')}</th>
                    <th scope="col">{t('parcelles.dateSemis')}</th>
                    <th scope="col">{t('parcelles.equipements')}</th>
                    <th scope="col">
                      <span className="sr-only">
                        {t('common.modifier')}
                      </span>
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {parcellesAffichees.length === 0 && (
                    <tr>
                      <td colSpan="6" className="texte-discret">
                        {recherche
                          ? t('common.aucunResultat')
                          : t('parcelles.aucuneParcelle')}
                      </td>
                    </tr>
                  )}

                  {parcellesAffichees.map((parcelle) => {
                    const cultures = parcelle.cultures || []

                    const equipementsAssocies = equipements.filter(
                      (e) => e.parcelle_id === parcelle.id,
                    )

                    const enLigne = equipementsAssocies.filter(
                      (e) => e.en_ligne,
                    ).length

                    return (
                      <tr
                        key={parcelle.id}
                        className={
                          parcelle.id === selectionId && !modeCreation
                            ? 'ligne-active'
                            : ''
                        }
                        onClick={() => {
                          setSelectionId(parcelle.id)
                          setModeCreation(false)
                        }}
                      >
                        <td className="cellule-nom">
                          {parcelle.nom}
                        </td>

                        <td>
                          {Number(parcelle.surface_ha || 0).toLocaleString(locale)}
                          {' '}
                          {t('common.ha')}
                        </td>

                        <td>
                          {cultures.length
                            ? cultures.map((c) => c.espece).join(', ')
                            : '—'}
                        </td>

                        <td>
                          {dateCourte(cultures[0]?.date_semis, locale)}
                        </td>

                        <td>
                          {equipementsAssocies.length > 0 ? (
                            <span
                              className={`badge-statut ${
                                enLigne === equipementsAssocies.length
                                  ? 'ok'
                                  : 'attention'
                              }`}
                            >
                              {t('parcelles.enLigne', {
                                enLigne,
                                total: equipementsAssocies.length,
                              })}
                            </span>
                          ) : (
                            <span className="texte-discret">
                              {t('parcelles.pasEquipement')}
                            </span>
                          )}
                        </td>

                        <td className="cellule-action">
                          <button
                            type="button"
                            className="lien-action"
                            onClick={(e) => {
                              e.stopPropagation()
                              setSelectionId(parcelle.id)
                              setModeCreation(false)
                            }}
                          >
                            {t('common.modifier')}
                          </button>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </section>

          {afficherNouvelleExploitation && (
            <section className="carte parcelle-exploitation-creation">
              <h2>{t('parcelles.nouvelleExploitation')}</h2>

              <form
                className="formulaire-exploitation"
                onSubmit={creerUneExploitation}
              >
                <div className="champ">
                  <label htmlFor="nouvelle-exploitation-nom">
                    {t('parcelles.nomExploitation')}
                  </label>
                  <input
                    id="nouvelle-exploitation-nom"
                    value={nouvelleExploitation.nom}
                    required
                    onChange={(e) =>
                      setNouvelleExploitation({
                        ...nouvelleExploitation,
                        nom: e.target.value,
                      })
                    }
                  />
                </div>

                <div className="champ">
                  <label htmlFor="nouvelle-exploitation-localisation">
                    {t('parcelles.localisation')}
                  </label>
                  <input
                    id="nouvelle-exploitation-localisation"
                    value={nouvelleExploitation.localisation}
                    onChange={(e) =>
                      setNouvelleExploitation({
                        ...nouvelleExploitation,
                        localisation: e.target.value,
                      })
                    }
                  />
                </div>

                <button
                  type="submit"
                  className="bouton-primaire"
                  disabled={enCours}
                >
                  {t('parcelles.creerExploitation')}
                </button>
              </form>
            </section>
          )}

          {modeCreation ? (
            <section className="carte parcelle-fiche">
              <h2 className="parcelle-fiche-titre">
                {t('parcelles.nouvelleParcelle')}
              </h2>

              <form
                className="parcelle-formulaire"
                onSubmit={creerLaParcelle}
              >
                <div className="champ">
                  <label htmlFor="creation-parcelle-nom">
                    {t('parcelles.nom')}
                  </label>
                  <input
                    id="creation-parcelle-nom"
                    value={creation.nom}
                    required
                    onChange={(e) =>
                      setCreation({ ...creation, nom: e.target.value })
                    }
                  />
                </div>

                <div className="champ">
                  <label htmlFor="creation-parcelle-exploitation">
                    {t('parcelles.exploitation')}
                  </label>
                  <select
                    id="creation-parcelle-exploitation"
                    value={creation.exploitation_id}
                    required
                    onChange={(e) =>
                      setCreation({
                        ...creation,
                        exploitation_id: e.target.value,
                      })
                    }
                  >
                    <option value="">Choisir une exploitation</option>

                    {exploitations.map((exploitation) => (
                      <option
                        key={exploitation.id}
                        value={exploitation.id}
                      >
                        {exploitation.nom}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="champ">
                  <label htmlFor="creation-parcelle-surface">
                    {t('parcelles.surface')}
                  </label>
                  <input
                    id="creation-parcelle-surface"
                    type="number"
                    min="0"
                    step="0.01"
                    value={creation.surface_ha}
                    required
                    onChange={(e) =>
                      setCreation({
                        ...creation,
                        surface_ha: e.target.value,
                      })
                    }
                  />
                </div>

                <div className="parcelle-formulaire-actions">
                  <button
                    type="submit"
                    className="bouton-primaire"
                    disabled={enCours}
                  >
                    {t('common.creer')}
                  </button>

                  <button
                    type="button"
                    className="bouton-secondaire"
                    onClick={() => setModeCreation(false)}
                  >
                    {t('common.annuler')}
                  </button>
                </div>
              </form>
            </section>
          ) : parcelleSelectionnee ? (
            <section className="carte parcelle-fiche">
              <div>
                <h2 className="parcelle-fiche-titre">
                  {parcelleSelectionnee.nom}
                </h2>

                <p className="parcelle-fiche-sous-titre">
                  {t('parcelles.sousTitre')}
                </p>
              </div>

              <form
                className="parcelle-formulaire"
                onSubmit={enregistrerParcelle}
              >
                <div className="champ">
                  <label htmlFor="edition-parcelle-nom">
                    {t('parcelles.nom')}
                  </label>
                  <input
                    id="edition-parcelle-nom"
                    value={nomEdition}
                    required
                    onChange={(e) => setNomEdition(e.target.value)}
                  />
                </div>

                <div className="champ">
                  <label htmlFor="edition-parcelle-exploitation">
                    {t('parcelles.exploitation')}
                  </label>
                  <select
                    id="edition-parcelle-exploitation"
                    value={exploitationEdition}
                    required
                    onChange={(e) =>
                      setExploitationEdition(e.target.value)
                    }
                  >
                    {exploitations.map((exploitation) => (
                      <option
                        key={exploitation.id}
                        value={exploitation.id}
                      >
                        {exploitation.nom}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="champ">
                  <label htmlFor="edition-parcelle-surface">
                    {t('parcelles.surface')}
                  </label>
                  <input
                    id="edition-parcelle-surface"
                    type="number"
                    min="0"
                    step="0.01"
                    value={surfaceEdition}
                    required
                    onChange={(e) => setSurfaceEdition(e.target.value)}
                  />
                </div>

                <div className="parcelle-formulaire-actions">
                  <button
                    type="submit"
                    className="bouton-primaire"
                    disabled={enCours}
                  >
                    {t('common.enregistrer')}
                  </button>

                  <button
                    type="button"
                    className="bouton-secondaire"
                    disabled={enCours}
                    onClick={() => supprimerLaParcelle(parcelleSelectionnee.id)}
                  >
                    {t('common.supprimer')}
                  </button>
                </div>
              </form>

              <hr />

              <h3>{t('parcelles.culture')}</h3>

              {(parcelleSelectionnee.cultures || []).map((item) => (
                <div className="ligne-culture" key={item.id}>
                  <span>
                    {item.espece}
                    {' — '}
                    {dateCourte(item.date_semis, locale)}
                  </span>

                  <button
                    type="button"
                    className="lien-action"
                    onClick={() => {
                      setCultureEnEdition(item)
                      setCulture(item.espece)
                      setDateSemis(item.date_semis?.slice(0, 10) || '')
                    }}
                  >
                    {t('common.modifier')}
                  </button>

                  <button
                    type="button"
                    className="lien-action"
                    onClick={() => supprimerUneCulture(item.id)}
                  >
                    {t('common.supprimer')}
                  </button>
                </div>
              ))}

              <form
                className="parcelle-formulaire"
                onSubmit={ajouterOuModifierCulture}
              >
                <div className="champ">
                  <label htmlFor="edition-culture">
                    Espèce cultivée
                  </label>
                  <input
                    id="edition-culture"
                    value={culture}
                    required
                    onChange={(e) => setCulture(e.target.value)}
                    placeholder="Ex. : Maïs, tomate, manioc"
                  />
                </div>

                <div className="champ">
                  <label htmlFor="edition-date-semis">
                    {t('parcelles.dateSemis')}
                  </label>
                  <input
                    id="edition-date-semis"
                    type="date"
                    value={dateSemis}
                    onChange={(e) => setDateSemis(e.target.value)}
                  />
                </div>

                <div className="parcelle-formulaire-actions">
                  <button
                    type="submit"
                    className="bouton-primaire"
                    disabled={enCours}
                  >
                    {cultureEnEdition
                      ? 'Modifier la culture'
                      : 'Ajouter une culture'}
                  </button>

                  {cultureEnEdition && (
                    <button
                      type="button"
                      className="bouton-secondaire"
                      onClick={() => {
                        setCultureEnEdition(null)
                        setCulture('')
                        setDateSemis('')
                      }}
                    >
                      {t('common.annuler')}
                    </button>
                  )}
                </div>
              </form>

              <hr />

              <h3>{t('parcelles.equipements')}</h3>

              {equipementsParcelle.length === 0 ? (
                <p className="texte-discret">
                  Aucun équipement associé à cette parcelle.
                </p>
              ) : (
                equipementsParcelle.map((equipement) => (
                  <div className="ligne-culture" key={equipement.id}>
                    <span>
                      {equipement.code}
                      {' — '}
                      {equipement.type}
                      {' · '}
                      {equipement.en_ligne ? 'En ligne' : 'Hors ligne'}
                    </span>

                    <button
                      type="button"
                      className="lien-action"
                      disabled={enCours}
                      onClick={() => dissocierUnEquipement(equipement.id)}
                    >
                      Dissocier
                    </button>
                  </div>
                ))
              )}

              {equipementsDisponibles.length > 0 && (
                <div className="champ">
                  <label htmlFor="association-equipement">
                    Associer un équipement
                  </label>

                  <select
                    id="association-equipement"
                    defaultValue=""
                    disabled={enCours}
                    onChange={associerUnEquipement}
                  >
                    <option value="">Choisir un équipement...</option>

                    {equipementsDisponibles.map((equipement) => (
                      <option
                        key={equipement.id}
                        value={equipement.id}
                      >
                        {equipement.code} ({equipement.type})
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </section>
          ) : (
            <section className="carte parcelle-fiche">
              <p className="texte-discret">
                {t('parcelles.choisirParcelle')}
              </p>
            </section>
          )}
        </div>
      )}
    </div>
  )
}
