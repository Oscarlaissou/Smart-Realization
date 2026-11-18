import { useTranslation } from 'react-i18next'

const CANAUX = ['notification', 'email', 'sms']

export default function PreferencesAlertes({
  preferences,
  profil,
  onChanger,
  onProfilChange,
  onEnregistrer,
  onTesterEmail,
  enCours,
}) {
  const { t } = useTranslation()

  return (
    <section className="carte alertes-preferences" aria-labelledby="preferences-alertes-titre">
      <div>
        <h2 id="preferences-alertes-titre" className="carte-titre">
          {t('alertes.preferences')}
        </h2>
        <p className="texte-discret">{t('alertes.preferencesAide')}</p>
      </div>

      <div className="table-defilante">
        <table className="table-preferences">
          <thead>
            <tr>
              <th scope="col">{t('alertes.type')}</th>
              {CANAUX.map((canal) => (
                <th key={canal} scope="col">
                  {t(`alertes.${canal}`)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {preferences.map((preference) => (
              <tr key={preference.categorie}>
                <td className="preference-libelle">
                  {t(`alertes.${preference.categorie}`, {
                    defaultValue: preference.libelle || preference.categorie,
                  })}
                </td>
                {CANAUX.map((canal) => (
                  <td key={canal}>
                    <input
                      type="checkbox"
                      checked={Boolean(preference[canal])}
                      aria-label={`${t(`alertes.${preference.categorie}`, {
                        defaultValue: preference.libelle || preference.categorie,
                      })} · ${t(`alertes.${canal}`)}`}
                      onChange={(evenement) =>
                        onChanger(preference.categorie, canal, evenement.target.checked)
                      }
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="preferences-contact">
        <div className="champ">
          <label htmlFor="preferences-telephone">{t('alertes.telephoneSms')}</label>
          <input
            id="preferences-telephone"
            type="tel"
            value={profil.telephone || ''}
            onChange={(evenement) => onProfilChange('telephone', evenement.target.value)}
          />
        </div>
        <div className="champ">
          <label htmlFor="preferences-email">{t('alertes.emailNotifications')}</label>
          <input id="preferences-email" type="email" value={profil.email || ''} readOnly />
        </div>
      </div>

      <div className="preferences-actions">
        <button
          type="button"
          className="bouton-primaire"
          disabled={enCours}
          onClick={onEnregistrer}
        >
          {t('alertes.enregistrerPreferences')}
        </button>
        <button
          type="button"
          className="bouton-secondaire"
          disabled={enCours}
          onClick={onTesterEmail}
        >
          {t('alertes.testerEmail')}
        </button>
      </div>
    </section>
  )
}
