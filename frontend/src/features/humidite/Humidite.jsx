import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  lireApercuHumidite,
  declarerArrosageManuel,
  sauvegarderSeuilsParcelle,
} from './api.js'
import './Humidite.css'

const LIGNES_PAR_PAGE = 5

function formaterDate(isoString) {
  if (!isoString) return '—'
  const d = new Date(isoString.endsWith('Z') ? isoString : `${isoString}Z`)
  const maintenant = new Date()
  const heure = d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })

  if (d.toDateString() === maintenant.toDateString()) {
    return `Aujourd'hui ${heure}`
  }

  const hier = new Date(maintenant)
  hier.setDate(maintenant.getDate() - 1)
  if (d.toDateString() === hier.toDateString()) {
    return `Hier ${heure}`
  }

  return `${d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })} ${heure}`
}

export default function Humidite() {
  const [utilisateur, setUtilisateur] = useState({ nom: 'Exploitant', role: 'Exploitant' })
  const [alertesActives, setAlertesActives] = useState(0)
  const [bilanHebdo, setBilanHebdo] = useState({ volume_litres: 0, nb_apports: 0, economie_estimee_pct: 0 })

  const [parcelles, setParcelles] = useState([])
  const [parcelleId, setParcelleId] = useState(null)
  const [recherche, setRecherche] = useState('')
  const [arrosages, setArrosages] = useState([])

  // Pagination du journal
  const [pageJournal, setPageJournal] = useState(1)

  // Seuils MQTT de la parcelle sélectionnée
  const [seuilMin, setSeuilMin] = useState(30)
  const [seuilMax, setSeuilMax] = useState(65)
  const [sauvegardeSeuilsEnCours, setSauvegardeSeuilsEnCours] = useState(false)

  // Formulaire de déclaration d'arrosage terrain
  const [irrigParcelleId, setIrrigParcelleId] = useState('')
  const [irrigMethode, setIrrigMethode] = useState('Goutte-à-goutte')
  const [irrigDuree, setIrrigDuree] = useState('25')
  const [irrigVolume, setIrrigVolume] = useState('150')
  const [irrigNote, setIrrigNote] = useState('')
  const [ajoutIrrigEnCours, setAjoutIrrigEnCours] = useState(false)

  const [chargement, setChargement] = useState(true)
  const [erreur, setErreur] = useState('')
  const [succes, setSucces] = useState('')

  const rafraichirApercu = useCallback(async (initial = false) => {
    try {
      const data = await lireApercuHumidite()
      if (data?.utilisateur) setUtilisateur(data.utilisateur)
      setAlertesActives(data?.alertes_actives ?? 0)
      if (data?.bilan_hebdo) setBilanHebdo(data.bilan_hebdo)

      const listeP = data?.parcelles || []
      setParcelles(listeP)
      setArrosages(data?.arrosages || [])

      if (listeP.length > 0) {
        const premiere = listeP[0]
        setParcelleId((prev) => prev ?? premiere.id)
        setIrrigParcelleId((prev) => prev || String(premiere.id))
        if (initial) {
          setSeuilMin(Number(premiere.seuil_min ?? 30))
          setSeuilMax(Number(premiere.seuil_max ?? 65))
        }
      }
      setErreur('')
    } catch (err) {
      if (initial) setErreur(err.message || 'Erreur lors du chargement des données.')
    } finally {
      if (initial) setChargement(false)
    }
  }, [])

  // Chargement initial + actualisation MQTT toutes les 5 secondes
  useEffect(() => {
    rafraichirApercu(true)
    const timer = setInterval(() => rafraichirApercu(false), 5000)
    return () => clearInterval(timer)
  }, [rafraichirApercu])

  const selectionnerParcelle = (p) => {
    setParcelleId(p.id)
    setIrrigParcelleId(String(p.id))
    setSeuilMin(Number(p.seuil_min ?? 30))
    setSeuilMax(Number(p.seuil_max ?? 65))
  }

  const parcelleActive = parcelles.find((p) => p.id === parcelleId) || parcelles[0]
  const nomCourtParcelle = (p) => (p?.nom || '').replace(/^Parcelle\s+/i, '')

  const initiales = (utilisateur.nom || 'EX')
    .split(' ')
    .map((n) => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()

  const parcellesAffichees = parcelles.filter(
    (p) =>
      p.nom.toLowerCase().includes(recherche.toLowerCase().trim()) ||
      (p.culture || '').toLowerCase().includes(recherche.toLowerCase().trim())
  )

  // Jauge d'humidité MQTT
  const aUneMesure = parcelleActive?.humidite_actuelle !== null && parcelleActive?.humidite_actuelle !== undefined
  const humiditeActuelle = aUneMesure ? Math.round(Number(parcelleActive.humidite_actuelle)) : 0
  const longueurArc = 251.3
  const valeurArc = (Math.min(Math.max(humiditeActuelle, 0), 100) / 100) * longueurArc
  const cibleLongueur = (Math.max(seuilMax - seuilMin, 0) / 100) * longueurArc
  const cibleDecalage = -(seuilMin / 100) * longueurArc

  let etatSol = 'Plage optimale'
  let couleurEtatSol = '#14683F'
  if (!aUneMesure) {
    etatSol = 'En attente de sonde'
    couleurEtatSol = '#5B6B63'
  } else if (humiditeActuelle < Number(seuilMin)) {
    etatSol = 'Sol sec — Arrosage conseillé'
    couleurEtatSol = '#9A2C1E'
  } else if (humiditeActuelle > Number(seuilMax)) {
    etatSol = 'Trop humide'
    couleurEtatSol = '#8A4A07'
  }

  // Courbe sur 24 heures (utilise courbe_24h de /humidite/apercu)
  const courbe = parcelleActive?.courbe_24h || []
  const yDepuisHumidite = (h) => 212 - ((Math.min(Math.max(h, 0), 100)) / 100) * 200
  const pointsCourbe = courbe
    .map((m, i) => {
      const x = courbe.length === 1 ? 330 : 46 + (i * (614 - 46)) / (courbe.length - 1)
      return `${x.toFixed(1)},${yDepuisHumidite(Number(m.valeur)).toFixed(1)}`
    })
    .join(' ')

  const yBandTop = yDepuisHumidite(Number(seuilMax) || 65)
  const yBandBottom = yDepuisHumidite(Number(seuilMin) || 30)
  const bandHeight = Math.max(yBandBottom - yBandTop, 4)

  const enregistrerSeuils = async () => {
    if (!parcelleActive || sauvegardeSeuilsEnCours) return
    if (Number(seuilMin) >= Number(seuilMax)) {
      setErreur('Le seuil minimum doit être inférieur au seuil maximum.')
      return
    }

    setSauvegardeSeuilsEnCours(true)
    setErreur('')
    setSucces('')
    try {
      await sauvegarderSeuilsParcelle(parcelleActive.id, {
        seuil_humidite_min: Number(seuilMin),
        seuil_humidite_max: Number(seuilMax),
      })
      await rafraichirApercu(false)
      setSucces(`Seuils d'alerte MQTT enregistrés (${seuilMin} % – ${seuilMax} %).`)
      setTimeout(() => setSucces(''), 4000)
    } catch (err) {
      setErreur(err.message || "Impossible d'enregistrer les seuils.")
    } finally {
      setSauvegardeSeuilsEnCours(false)
    }
  }

  const appliquerRecommandation = () => {
    if (!parcelleActive) return
    if (parcelleActive.duree_estimee_min > 0) {
      setIrrigDuree(String(parcelleActive.duree_estimee_min))
    }
    if (parcelleActive.volume_conseille_litres > 0) {
      setIrrigVolume(String(parcelleActive.volume_conseille_litres))
    }
  }

  const soumettreArrosage = async (e) => {
    e.preventDefault()
    const idParcelleCible = Number(irrigParcelleId || parcelles[0]?.id)
    if (!idParcelleCible || ajoutIrrigEnCours) return

    setAjoutIrrigEnCours(true)
    setErreur('')
    setSucces('')
    try {
      await declarerArrosageManuel({
        parcelle_id: idParcelleCible,
        methode: irrigMethode,
        volume_litres: Math.max(0, Number(irrigVolume) || 0),
        duree_minutes: Math.max(1, Number(irrigDuree) || 15),
        notes: irrigNote.trim(),
      })

      await rafraichirApercu(false)
      setPageJournal(1)
      setIrrigNote('')
      setSucces('Arrosage terrain enregistré dans le journal.')
      setTimeout(() => setSucces(''), 4000)
    } catch (err) {
      setErreur(err.message || "Impossible d'enregistrer l'arrosage.")
    } finally {
      setAjoutIrrigEnCours(false)
    }
  }

  // Pagination du journal
  const totalPagesJournal = Math.max(1, Math.ceil(arrosages.length / LIGNES_PAR_PAGE))
  const pageJournalCourante = Math.min(pageJournal, totalPagesJournal)
  const indexDebutJournal = (pageJournalCourante - 1) * LIGNES_PAR_PAGE
  const arrosagesPagines = arrosages.slice(indexDebutJournal, indexDebutJournal + LIGNES_PAR_PAGE)

  const exporterJournal = () => {
    const lignes = [
      ['Date', 'Parcelle', 'Methode', 'Duree (min)', 'Volume (L)', 'Humidite avant (%)', 'Notes'],
      ...arrosages.map((a) => [
        formaterDate(a.date_arrosage),
        a.parcelle,
        a.methode,
        a.duree_minutes,
        a.volume_litres,
        a.humidite_avant ?? '—',
        (a.notes || '').replace(/;/g, ','),
      ]),
    ]
    const csv = '\ufeff' + lignes.map((l) => l.join(';')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'journal-arrosages-sevia.csv'
    link.click()
    URL.revokeObjectURL(url)
  }

  const niveauReco = parcelleActive?.niveau_urgence || 'optimal'

  return (
    <div className="hum-wrapper">
      <header className="hum-header">
        <div>
          <h1 className="hum-title">Humidité et irrigation</h1>
          <p className="hum-subtitle">Relevés capteurs MQTT, recommandations hydriques et suivi des arrosages terrain</p>
        </div>

        <div className="hum-header-actions">
          <label className="hum-search">
            <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#5B6B63" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M11 3a8 8 0 1 0 0 16 8 8 0 0 0 0-16zM21 21l-4.3-4.3" />
            </svg>
            <input
              aria-label="Rechercher une parcelle"
              placeholder="Rechercher une parcelle"
              value={recherche}
              onChange={(e) => setRecherche(e.target.value)}
            />
          </label>

          <span className="hum-lang" aria-label="Langue : français">
            <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <path d="M2 12h20M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20" />
            </svg>
            FR
          </span>

          <Link to="/alertes" aria-label={`Alertes, ${alertesActives} non lues`} className="hum-bell">
            <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#12201A" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9M10.3 21a1.94 1.94 0 0 0 3.4 0" />
            </svg>
            {alertesActives > 0 && <span className="hum-bell-badge">{alertesActives}</span>}
          </Link>

          <div className="hum-user">
            <div className="hum-avatar">{initiales}</div>
            <div>
              <div className="hum-user-name">{utilisateur.nom}</div>
              <div className="hum-user-role">{utilisateur.role}</div>
            </div>
          </div>
        </div>
      </header>

      {erreur && <div className="hum-banner-error">{erreur}</div>}
      {succes && <div className="hum-banner-info">{succes}</div>}
      {chargement && <div className="hum-banner-info">Chargement des capteurs MQTT...</div>}

      <div role="group" aria-label="Choix de la parcelle" className="hum-pills">
        {parcellesAffichees.map((p) => (
          <button
            key={p.id}
            type="button"
            aria-pressed={p.id === parcelleActive?.id}
            className={`hum-pill ${p.id === parcelleActive?.id ? 'active' : ''}`}
            onClick={() => selectionnerParcelle(p)}
          >
            {nomCourtParcelle(p)}
          </button>
        ))}
      </div>

      {/* Ligne 1 : Jauge MQTT + Courbe 24h + Recommandations & Seuils */}
      <div className="hum-row">
        <section className="hum-card hum-card-gauge">
          <div>
            <h2 className="hum-card-title">Humidité actuelle</h2>
            <p className="hum-card-sub">
              {parcelleActive
                ? `${parcelleActive.nom}${parcelleActive.culture ? ` · ${parcelleActive.culture}` : ''}`
                : 'Aucune parcelle configurée'}
            </p>
          </div>

          <div className="hum-gauge-box">
            <svg
              role="img"
              aria-label={`Jauge d'humidité : ${humiditeActuelle} %, plage cible de ${seuilMin} à ${seuilMax} %`}
              viewBox="0 0 220 140"
              width="260"
              style={{ height: 'auto', maxWidth: '100%' }}
            >
              <path d="M30 110 A80 80 0 0 1 190 110" fill="none" stroke="#E8EEE9" strokeWidth="18" />
              <path
                d="M30 110 A80 80 0 0 1 190 110"
                fill="none"
                stroke="#C9E8D7"
                strokeWidth="18"
                strokeDasharray={`${cibleLongueur} ${longueurArc}`}
                strokeDashoffset={cibleDecalage}
              />
              <path
                d="M30 110 A80 80 0 0 1 190 110"
                fill="none"
                stroke="#1D6FB8"
                strokeWidth="6"
                strokeLinecap="round"
                strokeDasharray={`${valeurArc} ${longueurArc}`}
              />
              <text x="110" y="100" textAnchor="middle" fontSize="38" fontWeight="700" fill="#12201A" fontFamily="Space Grotesk, sans-serif">
                {aUneMesure ? `${humiditeActuelle} %` : '—'}
              </text>
              <text x="110" y="124" textAnchor="middle" fontSize="13" fontWeight="600" fill={couleurEtatSol} fontFamily="Inter, sans-serif">
                {etatSol}
              </text>
            </svg>
          </div>

          <div className="hum-gauge-footer">
            <span className="hum-live-badge">
              <span className="hum-live-dot" />
              Flux MQTT actif
            </span>
            <span className="hum-target-text">
              Plage cible {seuilMin} à {seuilMax} %
            </span>
          </div>
        </section>

        <section className="hum-card hum-card-chart">
          <h2 className="hum-card-title">Humidité sur 24 heures</h2>

          <svg role="img" aria-label="Humidité sur 24 heures" viewBox="0 0 640 240" width="100%" style={{ height: 'auto', display: 'block' }}>
            <rect x="46" y={yBandTop} width="568" height={bandHeight} fill="#E3F4EA" />

            {[
              { y: 212, label: '0 %' },
              { y: 145.3, label: '33 %' },
              { y: 78.7, label: '66 %' },
              { y: 12, label: '100 %' },
            ].map((ligne) => (
              <g key={ligne.label}>
                <line x1="46" x2="614" y1={ligne.y} y2={ligne.y} stroke="#E8EEE9" />
                <text x="38" y={ligne.y + 4} textAnchor="end" fontSize="11" fill="#5B6B63" fontFamily="Inter,sans-serif">
                  {ligne.label}
                </text>
              </g>
            ))}

            {courbe.map((m, idx) => {
              const x = courbe.length === 1 ? 330 : 46 + (idx * (614 - 46)) / (courbe.length - 1)
              const etiquette = idx === courbe.length - 1 ? 'Maint.' : m.heure

              if (courbe.length > 7 && idx % 2 !== 0 && idx !== courbe.length - 1) {
                return null
              }

              return (
                <text key={m.id || idx} x={x} y="232" textAnchor="middle" fontSize="11" fill="#5B6B63" fontFamily="Inter,sans-serif">
                  {etiquette}
                </text>
              )
            })}

            {pointsCourbe && (
              <polyline
                points={pointsCourbe}
                fill="none"
                stroke="#1D6FB8"
                strokeWidth="2.5"
                strokeLinejoin="round"
                strokeLinecap="round"
              />
            )}
          </svg>

          <div className="hum-legend">
            <span className="hum-legend-item">
              <span className="hum-dot" style={{ background: '#1D6FB8' }} />
              Relevés capteur MQTT
            </span>
            <span className="hum-legend-item">
              <span className="hum-dot" style={{ background: '#C9E8D7' }} />
              Plage cible ({seuilMin}–{seuilMax} %)
            </span>
          </div>
        </section>

        <section className="hum-card hum-card-reco">
          <div className="hum-card-head">
            <h2 className="hum-card-title">Recommandations</h2>
            <span className={`hum-reco-badge ${niveauReco}`}>
              {parcelleActive?.badge_urgence || 'Analyse'}
            </span>
          </div>

          <div className={`hum-reco-hero ${niveauReco}`}>
            <div>
              <div className="hum-reco-volume-label">Apport d&apos;eau recommandé</div>
              <div className="hum-reco-volume-val">
                <strong>{(parcelleActive?.volume_conseille_litres ?? 0).toLocaleString('fr-FR')} L</strong>
                <span>({parcelleActive?.volume_m3 ?? 0} m³)</span>
              </div>
            </div>

            <div className="hum-reco-metrics">
              <div>
                <div className="hum-reco-metric-label">Dose surfacique</div>
                <div className="hum-reco-metric-val">{parcelleActive?.dose_l_m2 ?? 0} L/m²</div>
              </div>
              <div>
                <div className="hum-reco-metric-label">Durée conseillée</div>
                <div className="hum-reco-metric-val">
                  {parcelleActive?.duree_estimee_min ? `~${parcelleActive.duree_estimee_min} min` : '0 min'}
                </div>
              </div>
            </div>
          </div>

          <div className="hum-reco-info-list">
            <div className="hum-reco-info-item">
              <div className="hum-reco-info-title">
                {parcelleActive?.autonomie_titre || 'Autonomie hydrique'}
              </div>
              <div className="hum-reco-info-desc">
                {parcelleActive?.autonomie_detail || 'En attente des relevés capteurs.'}
              </div>
            </div>

            <div className="hum-reco-info-item">
              <div className="hum-reco-info-title">Fenêtre horaire conseillée</div>
              <div className="hum-reco-info-desc">
                {parcelleActive?.fenetre_horaire || 'Privilégier tôt le matin (05h30 – 07h30) ou après 18h00'}
              </div>
            </div>
          </div>

          {parcelleActive?.conseil_culture && (
            <div className="hum-reco-advice">
              {parcelleActive.conseil_culture}
            </div>
          )}

          <div className="hum-grid-2">
            <div className="hum-field">
              <label htmlFor="t-min">Seuil alerte bas (%)</label>
              <input
                id="t-min"
                type="number"
                min="5"
                max="80"
                value={seuilMin}
                onChange={(e) => setSeuilMin(Number(e.target.value))}
              />
            </div>
            <div className="hum-field">
              <label htmlFor="t-max">Seuil optimal max (%)</label>
              <input
                id="t-max"
                type="number"
                min="10"
                max="95"
                value={seuilMax}
                onChange={(e) => setSeuilMax(Number(e.target.value))}
              />
            </div>
          </div>

          <button
            type="button"
            className="hum-btn-outline"
            disabled={sauvegardeSeuilsEnCours || !parcelleActive}
            onClick={enregistrerSeuils}
          >
            {sauvegardeSeuilsEnCours ? 'Enregistrement...' : 'Enregistrer les seuils MQTT'}
          </button>
        </section>
      </div>

      {/* Ligne 2 : Déclaration d'arrosage terrain + Journal des irrigations */}
      <div className="hum-row">
        <section className="hum-card hum-card-cycles">
          <div className="hum-card-head">
            <div>
              <h2 className="hum-card-title">Déclarer un arrosage terrain</h2>
              <p className="hum-card-sub">
                Consignez chaque arrosage manuel effectué suite aux alertes ou recommandations MQTT
              </p>
            </div>

            {(parcelleActive?.volume_conseille_litres ?? 0) > 0 && (
              <button type="button" className="hum-btn-outline" onClick={appliquerRecommandation}>
                Appliquer la reco ({parcelleActive.volume_conseille_litres} L)
              </button>
            )}
          </div>

          <div className="hum-reco-info-item">
            <div className="hum-reco-info-title">Fonctionnement sans électrovanne</div>
            <div className="hum-reco-info-desc">
              Lorsqu&apos;un capteur MQTT descend sous <strong>{seuilMin} %</strong>, une alerte est créée. Après l&apos;arrosage manuel sur la parcelle, enregistrez l&apos;apport ci-dessous pour suivre votre consommation d&apos;eau.
            </div>
          </div>

          <form className="hum-new-cycle" style={{ borderTop: 0, paddingTop: 0 }} onSubmit={soumettreArrosage}>
            <div className="hum-grid-4">
              <div className="hum-field">
                <label htmlFor="irr-p">Parcelle arrosée</label>
                <select
                  id="irr-p"
                  value={irrigParcelleId}
                  onChange={(e) => setIrrigParcelleId(e.target.value)}
                >
                  {parcelles.map((p) => (
                    <option key={p.id} value={p.id}>{p.nom}</option>
                  ))}
                </select>
              </div>

              <div className="hum-field">
                <label htmlFor="irr-m">Méthode</label>
                <select
                  id="irr-m"
                  value={irrigMethode}
                  onChange={(e) => setIrrigMethode(e.target.value)}
                >
                  <option value="Goutte-à-goutte">Goutte-à-goutte</option>
                  <option value="Aspersion">Aspersion</option>
                  <option value="Arrosage manuel">Arrosage manuel</option>
                  <option value="Motopompe">Motopompe</option>
                </select>
              </div>

              <div className="hum-field">
                <label htmlFor="irr-d">Durée (min)</label>
                <input
                  id="irr-d"
                  type="number"
                  min="1"
                  max="360"
                  required
                  value={irrigDuree}
                  onChange={(e) => setIrrigDuree(e.target.value)}
                />
              </div>

              <div className="hum-field">
                <label htmlFor="irr-v">Volume estimé (L)</label>
                <input
                  id="irr-v"
                  type="number"
                  min="1"
                  max="100000"
                  required
                  value={irrigVolume}
                  onChange={(e) => setIrrigVolume(e.target.value)}
                />
              </div>
            </div>

            <div className="hum-field">
              <label htmlFor="irr-note">Observation terrain (optionnel)</label>
              <input
                id="irr-note"
                type="text"
                placeholder="Ex. Arrosage matinal suite à alerte sol sec"
                value={irrigNote}
                onChange={(e) => setIrrigNote(e.target.value)}
              />
            </div>

            <div>
              <button type="submit" disabled={ajoutIrrigEnCours || parcelles.length === 0} className="hum-btn-green-sm">
                {ajoutIrrigEnCours ? 'Enregistrement...' : 'Enregistrer l’arrosage'}
              </button>
            </div>
          </form>
        </section>

        <section className="hum-card hum-card-journal">
          <div className="hum-card-head">
            <h2 className="hum-card-title">Journal des irrigations</h2>
            <button type="button" className="hum-btn-outline" onClick={exporterJournal}>
              Exporter
            </button>
          </div>

          <div className="hum-bilan-strip">
            <span>
              Cumul 7 jours : <strong>{bilanHebdo.volume_litres.toLocaleString('fr-FR')} L</strong> ({bilanHebdo.nb_apports} apports)
            </span>
            <span>
              Efficience : <strong>-{bilanHebdo.economie_estimee_pct} % d&apos;eau</strong> vs arrosage fixe
            </span>
          </div>

          <div className="hum-table-wrap">
            <table className="hum-table" style={{ minWidth: '640px' }}>
              <thead>
                <tr>
                  <th scope="col">Date</th>
                  <th scope="col">Parcelle</th>
                  <th scope="col">Durée</th>
                  <th scope="col">Volume</th>
                  <th scope="col">Méthode</th>
                  <th scope="col">Humidité avant</th>
                </tr>
              </thead>
              <tbody>
                {arrosagesPagines.length === 0 && (
                  <tr>
                    <td colSpan="6" style={{ color: '#5B6B63' }}>Aucun arrosage enregistré.</td>
                  </tr>
                )}
                {arrosagesPagines.map((a) => (
                  <tr key={a.id}>
                    <td className="hum-td-bold">{formaterDate(a.date_arrosage)}</td>
                    <td>{a.parcelle.replace(/^Parcelle\s+/i, '')}</td>
                    <td>{a.duree_minutes} min</td>
                    <td>{Number(a.volume_litres || 0).toLocaleString('fr-FR')} L</td>
                    <td>
                      <span className="hum-badge-manuel">{a.methode}</span>
                    </td>
                    <td>
                      {a.humidite_avant != null ? (
                        <span className="hum-badge-auto">{Math.round(a.humidite_avant)} %</span>
                      ) : (
                        '—'
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {arrosages.length > LIGNES_PAR_PAGE && (
            <div className="hum-pagination">
              <span>
                Affichage {indexDebutJournal + 1}–{Math.min(indexDebutJournal + LIGNES_PAR_PAGE, arrosages.length)} sur {arrosages.length} arrosages
              </span>

              <div className="hum-page-controls">
                <button
                  type="button"
                  className="hum-page-btn"
                  disabled={pageJournalCourante === 1}
                  onClick={() => setPageJournal((p) => Math.max(1, p - 1))}
                >
                  ← Précédent
                </button>

                {Array.from({ length: totalPagesJournal }, (_, i) => i + 1).map((numPage) => (
                  <button
                    key={numPage}
                    type="button"
                    aria-current={pageJournalCourante === numPage ? 'page' : undefined}
                    className={`hum-page-btn ${pageJournalCourante === numPage ? 'active' : ''}`}
                    onClick={() => setPageJournal(numPage)}
                  >
                    {numPage}
                  </button>
                ))}

                <button
                  type="button"
                  className="hum-page-btn"
                  disabled={pageJournalCourante === totalPagesJournal}
                  onClick={() => setPageJournal((p) => Math.min(totalPagesJournal, p + 1))}
                >
                  Suivant →
                </button>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}