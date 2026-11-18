import { useTranslation } from 'react-i18next'

const CLASSES_NIVEAU = {
  urgent: 'niveau-urgent',
  attention: 'niveau-attention',
  info: 'niveau-info',
}

export default function CarteAlerte({ alerte, preferences, onMarquerLue, enCours }) {
  const { t, i18n } = useTranslation()
  const preference = preferences.find(
    (item) => item.categorie === alerte.categorie,
  )
  const canaux = []
  if (!preference || preference.notification) canaux.push('notification')
  if (preference?.email) canaux.push('email')
  if (preference?.sms) canaux.push('sms')
  const locale = i18n.language === 'en' ? 'en-GB' : 'fr-FR'
  const date = alerte.date
    ? new Date(alerte.date.endsWith('Z') ? alerte.date : `${alerte.date}Z`)
    : null
  const dateAffichee = date
    ? date.toLocaleString(locale, {
        day: 'numeric',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
      })
    : '—'

  return (
    <li className={`alerte-ligne ${alerte.lue ? 'alerte-lue' : ''}`}>
      <span className={`alerte-point ${CLASSES_NIVEAU[alerte.niveau] || 'niveau-info'}`} aria-hidden="true" />
      <div className="alerte-contenu">
        <div className="alerte-entete">
          <div>
            <div className="alerte-titre">{alerte.message}</div>
            <div className="alerte-meta">
              <span>{dateAffichee}</span>
              <span className="alerte-categorie">
                {t(`alertes.${alerte.categorie}`, { defaultValue: alerte.categorie })}
              </span>
              <span className={`alerte-niveau ${CLASSES_NIVEAU[alerte.niveau] || 'niveau-info'}`}>
                {t(`alertes.${alerte.niveau}`, { defaultValue: alerte.niveau })}
              </span>
            </div>
          </div>
          {alerte.lue ? (
            <span className="alerte-lue-label">{t('alertes.lue')}</span>
          ) : (
            <button
              type="button"
              className="lien-action"
              disabled={enCours}
              onClick={() => onMarquerLue(alerte.id)}
            >
              {t('alertes.marquerLue')}
            </button>
          )}
        </div>
        {canaux.length > 0 && (
          <div className="alerte-canaux">
            {canaux.map((canal) => (
              <span key={canal} className="alerte-canal">
                {t(`alertes.${canal}`)}
              </span>
            ))}
          </div>
        )}
      </div>
    </li>
  )
}
