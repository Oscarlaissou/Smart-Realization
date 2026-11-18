import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'

function dateLisible(valeur, locale) {
  if (!valeur) return '—'
  const date = new Date(valeur)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleDateString(locale, { day: 'numeric', month: 'short', year: 'numeric' })
}

export default function FicheParcelle({
  parcelle,
  exploitations,
  equipements,
  onEnregistrer,
  onSupprimer,
  onAjouterCulture,
  onModifierCulture,
  onSupprimerCulture,
  enCours,
}) {
  const { t, i18n } = useTranslation()
  const locale = i18n.language === 'en' ? 'en-GB' : 'fr-FR'
  const [form, setForm] = useState({ nom: '', surface_ha: '', exploitation_id: '' })
  const [nouvelleCulture, setNouvelleCulture] = useState({ espece: '', date_semis: '' })
  const [cultureEnEdition, setCultureEnEdition] = useState(null)

  useEffect(() => {
    setForm({
      nom: parcelle?.nom || '',
      surface_ha: parcelle?.surface_ha ?? '',
      exploitation_id: parcelle?.exploitation_id || '',
    })
    setNouvelleCulture({ espece: '', date_semis: '' })
    setCultureEnEdition(null)
  }, [parcelle])

  if (!parcelle) return null

  const equipementsParcelle = equipements.filter(
    (equipement) => equipement.parcelle_id === parcelle.id,
  )
  const cultures = parcelle.cultures || []

  const envoyerParcelle = (evenement) => {
    evenement.preventDefault()
    onEnregistrer({
      nom: form.nom,
      surface_ha: Number(form.surface_ha),
      exploitation_id: Number(form.exploitation_id),
    })
  }

  const ajouterCulture = (evenement) => {
    evenement.preventDefault()
    onAjouterCulture({
      espece: nouvelleCulture.espece,
      date_semis: nouvelleCulture.date_semis
        ? `${nouvelleCulture.date_semis}T00:00:00`
        : null,
    })
    setNouvelleCulture({ espece: '', date_semis: '' })
  }

  const enregistrerCulture = (evenement) => {
    evenement.preventDefault()
    if (!cultureEnEdition) return
    onModifierCulture(cultureEnEdition.id, {
      espece: cultureEnEdition.espece,
      date_semis: cultureEnEdition.date_semis
        ? `${cultureEnEdition.date_semis.slice(0, 10)}T00:00:00`
        : null,
    })
    setCultureEnEdition(null)
  }

  return (
    <section className="carte parcelle-fiche" aria-labelledby="fiche-parcelle-titre">
      <div>
        <h2 id="fiche-parcelle-titre" className="parcelle-fiche-titre">
          {t('parcelles.ficheParcelle')}
        </h2>
        <p className="parcelle-fiche-sous-titre">
          {parcelle.nom} · {Number(parcelle.surface_ha || 0).toLocaleString(locale)}{' '}
          {t('common.ha')}
        </p>
      </div>

      <form className="parcelle-formulaire" onSubmit={envoyerParcelle}>
        <div className="champ">
          <label htmlFor="parcelle-nom">{t('parcelles.nom')}</label>
          <input
            id="parcelle-nom"
            value={form.nom}
            required
            onChange={(evenement) => setForm({ ...form, nom: evenement.target.value })}
          />
        </div>

        <div className="champ">
          <label htmlFor="parcelle-exploitation">{t('parcelles.exploitation')}</label>
          <select
            id="parcelle-exploitation"
            value={form.exploitation_id}
            required
            onChange={(evenement) =>
              setForm({ ...form, exploitation_id: evenement.target.value })
            }
          >
            {exploitations.map((exploitation) => (
              <option key={exploitation.id} value={exploitation.id}>
                {exploitation.nom}
              </option>
            ))}
          </select>
        </div>

        <div className="champ">
          <label htmlFor="parcelle-surface">{t('parcelles.surface')}</label>
          <input
            id="parcelle-surface"
            type="number"
            min="0"
            step="0.01"
            value={form.surface_ha}
            required
            onChange={(evenement) => setForm({ ...form, surface_ha: evenement.target.value })}
          />
        </div>

        <div className="champ">
          <span className="champ-legende">{t('parcelles.equipements')}</span>
          <div className="equipements-chips">
            {equipementsParcelle.length === 0 && (
              <span className="texte-discret">{t('parcelles.pasEquipement')}</span>
            )}
            {equipementsParcelle.map((equipement) => (
              <span
                key={equipement.id}
                className={`equipement-chip ${equipement.en_ligne ? 'en-ligne' : 'hors-ligne'}`}
              >
                <span className="equipement-point" aria-hidden="true" />
                {equipement.code} ·{' '}
                {equipement.en_ligne
                  ? t('parcelles.statutEnLigne')
                  : t('parcelles.statutHorsLigne')}
              </span>
            ))}
          </div>
        </div>

        <div className="parcelle-formulaire-actions">
          <button type="submit" className="bouton-primaire" disabled={enCours}>
            {t('common.enregistrerModifications')}
          </button>
          <button
            type="button"
            className="bouton-danger"
            disabled={enCours}
            onClick={() => {
              if (window.confirm(t('parcelles.confirmerSuppressionParcelle'))) {
                onSupprimer(parcelle.id)
              }
            }}
          >
            {t('common.supprimer')}
          </button>
        </div>
      </form>

      <div className="parcelle-cultures">
        <h3>{t('parcelles.cultures')}</h3>
        {cultures.length === 0 && (
          <p className="texte-discret">{t('parcelles.aucuneCulture')}</p>
        )}

        <ul className="culture-liste">
          {cultures.map((culture) => (
            <li key={culture.id} className="culture-ligne">
              {cultureEnEdition?.id === culture.id ? (
                <form className="culture-edition" onSubmit={enregistrerCulture}>
                  <input
                    aria-label={t('parcelles.espece')}
                    value={cultureEnEdition.espece}
                    required
                    onChange={(evenement) =>
                      setCultureEnEdition({ ...cultureEnEdition, espece: evenement.target.value })
                    }
                  />
                  <input
                    aria-label={t('parcelles.dateSemis')}
                    type="date"
                    value={cultureEnEdition.date_semis?.slice(0, 10) || ''}
                    onChange={(evenement) =>
                      setCultureEnEdition({
                        ...cultureEnEdition,
                        date_semis: evenement.target.value,
                      })
                    }
                  />
                  <button type="submit" className="lien-action">
                    {t('common.enregistrer')}
                  </button>
                  <button
                    type="button"
                    className="lien-action"
                    onClick={() => setCultureEnEdition(null)}
                  >
                    {t('common.annuler')}
                  </button>
                </form>
              ) : (
                <>
                  <span className="culture-nom">{culture.espece}</span>
                  <span className="culture-date">
                    {dateLisible(culture.date_semis, locale)}
                  </span>
                  <span className="culture-actions">
                    <button
                      type="button"
                      className="lien-action"
                      onClick={() =>
                        setCultureEnEdition({
                          id: culture.id,
                          espece: culture.espece,
                          date_semis: culture.date_semis,
                        })
                      }
                    >
                      {t('common.modifier')}
                    </button>
                    <button
                      type="button"
                      className="lien-action danger"
                      onClick={() => onSupprimerCulture(culture.id)}
                    >
                      {t('common.supprimer')}
                    </button>
                  </span>
                </>
              )}
            </li>
          ))}
        </ul>

        <form className="culture-ajout" onSubmit={ajouterCulture}>
          <input
            aria-label={t('parcelles.espece')}
            placeholder={t('parcelles.especePlaceholder')}
            value={nouvelleCulture.espece}
            required
            onChange={(evenement) =>
              setNouvelleCulture({ ...nouvelleCulture, espece: evenement.target.value })
            }
          />
          <input
            aria-label={t('parcelles.dateSemis')}
            type="date"
            value={nouvelleCulture.date_semis}
            onChange={(evenement) =>
              setNouvelleCulture({ ...nouvelleCulture, date_semis: evenement.target.value })
            }
          />
          <button type="submit" className="bouton-secondaire" disabled={enCours}>
            {t('parcelles.ajouterCulture')}
          </button>
        </form>
      </div>
    </section>
  )
}
