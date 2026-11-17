import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  lireContexte,
  listerParcelles,
  lireRecommandations,
  listerMesures,
  listerIrrigations,
  listerCycles,
  ajouterCycle,
  basculerCycle,
  supprimerCycle,
} from './api.js'
import './Humidite.css'

const CYCLES_PAR_PAGE = 4
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

  const [parcelles, setParcelles] = useState([])
  const [parcelleId, setParcelleId] = useState(null)
  const [recherche, setRecherche] = useState('')

  const [mesures, setMesures] = useState([])
  const [recommandation, setRecommandation] = useState(null)
  const [irrigations, setIrrigations] = useState([])
  const [cycles, setCycles] = useState([])

  // Pagination des cycles et du journal
  const [pageCycles, setPageCycles] = useState(1)
  const [pageJournal, setPageJournal] = useState(1)

  // Seuils cibles
  const [seuilMin, setSeuilMin] = useState(30)
  const [seuilMax, setSeuilMax] = useState(45)

  // Nouveau cycle
  const [nouvelleHeure, setNouvelleHeure] = useState('06:00')
  const [nouvelleDuree, setNouvelleDuree] = useState('30')
  const [nouvelleFrequence, setNouvelleFrequence] = useState('Tous les jours')
  const [nouvelleParcelleId, setNouvelleParcelleId] = useState('')
  const [ajoutCycleEnCours, setAjoutCycleEnCours] = useState(false)

  const [chargement, setChargement] = useState(true)
  const [erreur, setErreur] = useState('')
  const [succes, setSucces] = useState('')

  const chargerTout = useCallback(async () => {
    try {
      setErreur('')
      const [ctx, listeP, listeIrr, listeCyc] = await Promise.all([
        lireContexte(),
        listerParcelles(),
        listerIrrigations(),
        listerCycles(),
      ])

      if (ctx?.utilisateur) setUtilisateur(ctx.utilisateur)
      setAlertesActives(ctx?.alertes_actives ?? 0)

      setParcelles(listeP || [])
      setIrrigations(listeIrr || [])
      setCycles(listeCyc || [])

      if (listeP && listeP.length > 0) {
        setParcelleId((prev) => prev ?? (listeP[1]?.id || listeP[0].id))
        setNouvelleParcelleId((prev) => prev || String(listeP[1]?.id || listeP[0].id))
      }
    } catch (err) {
      setErreur(err.message || 'Erreur lors du chargement des données.')
    } finally {
      setChargement(false)
    }
  }, [])

  useEffect(() => {
    chargerTout()
  }, [chargerTout])

  // Rafraîchissement des mesures et des recommandations toutes les 5 secondes
  useEffect(() => {
    if (!parcelleId) return

    const rafraichirParcelle = () => {
      listerMesures(parcelleId, 12)
        .then((res) => setMesures(res || []))
        .catch(() => {})

      lireRecommandations(parcelleId, seuilMin, seuilMax)
        .then((res) => setRecommandation(res))
        .catch(() => {})
    }

    rafraichirParcelle()
    const timer = setInterval(rafraichirParcelle, 5000)

    return () => clearInterval(timer)
  }, [parcelleId, seuilMin, seuilMax])

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

  // Jauge d'humidité
  const derniereMesure = mesures[0]
  const humiditeActuelle = derniereMesure ? Math.round(Number(derniereMesure.humidite)) : 0
  const longueurArc = 251.3
  const valeurArc = (Math.min(Math.max(humiditeActuelle, 0), 100) / 100) * longueurArc
  const cibleLongueur = (Math.max(seuilMax - seuilMin, 0) / 100) * longueurArc
  const cibleDecalage = -(seuilMin / 100) * longueurArc

  let etatSol = 'Plage optimale'
  let couleurEtatSol = '#14683F'
  if (humiditeActuelle < Number(seuilMin)) {
    etatSol = 'Sol sec'
    couleurEtatSol = '#9A2C1E'
  } else if (humiditeActuelle > Number(seuilMax)) {
    etatSol = 'Trop humide'
    couleurEtatSol = '#8A4A07'
  }

  // Courbe sur 24 heures
  const mesuresChrono = [...mesures].reverse()
  const yDepuisHumidite = (h) => 212 - ((Math.min(Math.max(h, 20), 50) - 20) / 30) * 200
  const pointsCourbe = mesuresChrono
    .map((m, i) => {
      const x =
        mesuresChrono.length === 1
          ? 330
          : 46 + (i * (614 - 46)) / (mesuresChrono.length - 1)
      return `${x.toFixed(1)},${yDepuisHumidite(Number(m.humidite)).toFixed(1)}`
    })
    .join(' ')

  const yBandTop = yDepuisHumidite(Number(seuilMax) || 45)
  const yBandBottom = yDepuisHumidite(Number(seuilMin) || 30)
  const bandHeight = Math.max(yBandBottom - yBandTop, 4)

  // Ajouter un cycle programmé
  const creerCycle = async (e) => {
    e.preventDefault()
    const idParcelleCible = Number(nouvelleParcelleId || parcelles[0]?.id)
    if (!idParcelleCible || ajoutCycleEnCours) return

    setAjoutCycleEnCours(true)
    setErreur('')
    setSucces('')
    try {
      await ajouterCycle({
        parcelle_id: idParcelleCible,
        heure: nouvelleHeure.slice(0, 5),
        duree_min: Math.max(1, Number(nouvelleDuree) || 30),
        jours: nouvelleFrequence,
        actif: true,
      })
      const listeCyc = await listerCycles()
      const nouveauxCycles = listeCyc || []
      setCycles(nouveauxCycles)
      setPageCycles(Math.max(1, Math.ceil(nouveauxCycles.length / CYCLES_PAR_PAGE)))
      setSucces(`Cycle programmé à ${nouvelleHeure.slice(0, 5)} ajouté avec succès.`)
      setTimeout(() => setSucces(''), 4000)
    } catch (err) {
      setErreur(err.message || "Impossible d'ajouter le cycle.")
    } finally {
      setAjoutCycleEnCours(false)
    }
  }

  const changerEtatCycle = async (cycleId) => {
    try {
      const maj = await basculerCycle(cycleId)
      setCycles((prev) => prev.map((c) => (c.id === cycleId ? maj : c)))
    } catch (err) {
      setErreur(err.message || 'Impossible de modifier le cycle.')
    }
  }

  const retirerCycle = async (cycleId) => {
    try {
      await supprimerCycle(cycleId)
      setCycles((prev) => prev.filter((c) => c.id !== cycleId))
    } catch (err) {
      setErreur(err.message || 'Impossible de supprimer le cycle.')
    }
  }

  // Pagination des cycles programmés
  const totalPagesCycles = Math.max(1, Math.ceil(cycles.length / CYCLES_PAR_PAGE))
  const pageCyclesCourante = Math.min(pageCycles, totalPagesCycles)
  const indexDebutCycles = (pageCyclesCourante - 1) * CYCLES_PAR_PAGE
  const cyclesPagines = cycles.slice(indexDebutCycles, indexDebutCycles + CYCLES_PAR_PAGE)

  // Pagination du journal des irrigations
  const totalPagesJournal = Math.max(1, Math.ceil(irrigations.length / LIGNES_PAR_PAGE))
  const pageJournalCourante = Math.min(pageJournal, totalPagesJournal)
  const indexDebutJournal = (pageJournalCourante - 1) * LIGNES_PAR_PAGE
  const irrigationsPaginees = irrigations.slice(indexDebutJournal, indexDebutJournal + LIGNES_PAR_PAGE)

  const exporterJournal = () => {
    const lignes = [
      ['Date', 'Parcelle', 'Duree (min)', 'Volume estime (L)', 'Mode'],
      ...irrigations.map((irr) => {
        const p = parcelles.find((item) => item.id === irr.parcelle_id)
        return [
          formaterDate(irr.debut),
          nomCourtParcelle(p) || `Parcelle #${irr.parcelle_id}`,
          irr.duree_min,
          irr.duree_min * 60,
          irr.mode,
        ]
      }),
    ]
    const csv = '\ufeff' + lignes.map((l) => l.join(';')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'journal-irrigations.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  const niveauReco = recommandation?.niveau_urgence || (humiditeActuelle < seuilMin ? 'urgent' : 'optimal')

  return (
    <div className="hum-wrapper">
      <header className="hum-header">
        <div>
          <h1 className="hum-title">Humidité et irrigation</h1>
          <p className="hum-subtitle">Mesures en temps réel, recommandations hydriques et journal d&apos;arrosage</p>
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
      {chargement && <div className="hum-banner-info">Chargement des capteurs d&apos;humidité...</div>}

      <div role="group" aria-label="Choix de la parcelle" className="hum-pills">
        {parcellesAffichees.map((p) => (
          <button
            key={p.id}
            type="button"
            aria-pressed={p.id === parcelleId}
            className={`hum-pill ${p.id === parcelleId ? 'active' : ''}`}
            onClick={() => setParcelleId(p.id)}
          >
            {nomCourtParcelle(p)}
          </button>
        ))}
      </div>

      {/* Ligne 1 : Jauge + Courbe 24h + Recommandations intelligentes */}
      <div className="hum-row">
        <section className="hum-card hum-card-gauge">
          <div>
            <h2 className="hum-card-title">Humidité actuelle</h2>
            <p className="hum-card-sub">
              {parcelleActive ? `${parcelleActive.nom} · ${parcelleActive.culture}` : 'Sélectionnez une parcelle'}
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
                {humiditeActuelle} %
              </text>
              <text x="110" y="124" textAnchor="middle" fontSize="13" fontWeight="600" fill={couleurEtatSol} fontFamily="Inter, sans-serif">
                {etatSol}
              </text>
            </svg>
          </div>

          <div className="hum-gauge-footer">
            <span className="hum-live-badge">
              <span className="hum-live-dot" />
              Capteur actif
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
              { y: 212, label: '20 %' },
              { y: 145.3, label: '30 %' },
              { y: 78.7, label: '40 %' },
              { y: 12, label: '50 %' },
            ].map((ligne) => (
              <g key={ligne.label}>
                <line x1="46" x2="614" y1={ligne.y} y2={ligne.y} stroke="#E8EEE9" />
                <text x="38" y={ligne.y + 4} textAnchor="end" fontSize="11" fill="#5B6B63" fontFamily="Inter,sans-serif">
                  {ligne.label}
                </text>
              </g>
            ))}

            {mesuresChrono.map((m, idx) => {
              const x =
                mesuresChrono.length === 1
                  ? 330
                  : 46 + (idx * (614 - 46)) / (mesuresChrono.length - 1)
              const d = new Date(m.horodatage.endsWith('Z') ? m.horodatage : `${m.horodatage}Z`)
              const etiquette =
                idx === mesuresChrono.length - 1
                  ? 'Maint.'
                  : d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })

              if (mesuresChrono.length > 7 && idx % 2 !== 0 && idx !== mesuresChrono.length - 1) {
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
              Humidité mesurée
            </span>
            <span className="hum-legend-item">
              <span className="hum-dot" style={{ background: '#C9E8D7' }} />
              Plage cible
            </span>
          </div>
        </section>

        {/* Carte 3 : Recommandations d'irrigation */}
        <section className="hum-card hum-card-reco">
          <div className="hum-card-head">
            <h2 className="hum-card-title">Recommandations</h2>
            <span className={`hum-reco-badge ${niveauReco}`}>
              {recommandation?.badge_urgence || 'Analyse en cours'}
            </span>
          </div>

          {/* Volume d'eau recommandé */}
          <div className={`hum-reco-hero ${niveauReco}`}>
            <div>
              <div className="hum-reco-volume-label">Apport d&apos;eau recommandé</div>
              <div className="hum-reco-volume-val">
                <strong>{(recommandation?.volume_litres ?? 0).toLocaleString('fr-FR')} L</strong>
                <span>({recommandation?.volume_m3 ?? 0} m³)</span>
              </div>
            </div>

            <div className="hum-reco-metrics">
              <div>
                <div className="hum-reco-metric-label">Dose surfacique</div>
                <div className="hum-reco-metric-val">{recommandation?.dose_l_m2 ?? 0} L/m²</div>
              </div>
              <div>
                <div className="hum-reco-metric-label">Durée conseillée</div>
                <div className="hum-reco-metric-val">
                  {recommandation?.duree_estimee_min ? `~${recommandation.duree_estimee_min} min` : '0 min'}
                </div>
              </div>
            </div>
          </div>

          {/* Autonomie hydrique + Fenêtre horaire */}
          <div className="hum-reco-info-list">
            <div className="hum-reco-info-item">
              <div className="hum-reco-info-title">
                {recommandation?.autonomie_titre || 'Autonomie hydrique'}
              </div>
              <div className="hum-reco-info-desc">
                {recommandation?.autonomie_detail || 'Calcul de la courbe d’évaporation en cours...'}
              </div>
            </div>

            <div className="hum-reco-info-item">
              <div className="hum-reco-info-title">Fenêtre horaire conseillée</div>
              <div className="hum-reco-info-desc">
                {recommandation?.fenetre_horaire || 'Privilégier tôt le matin (05h30 – 07h30) ou après 18h00'}
              </div>
            </div>
          </div>

          {/* Conseil agronomique selon la culture */}
          {recommandation?.conseil_culture && (
            <div className="hum-reco-advice">
              {recommandation.conseil_culture}
            </div>
          )}

          {/* Paramétrage des seuils cibles */}
          <div className="hum-grid-2">
            <div className="hum-field">
              <label htmlFor="t-min">Seuil minimum (%)</label>
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
              <label htmlFor="t-max">Seuil maximum (%)</label>
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
        </section>
      </div>

      {/* Ligne 2 : Programmation des cycles + Journal des irrigations */}
      <div className="hum-row">
        <section className="hum-card hum-card-cycles">
          <h2 className="hum-card-title">Programmation des cycles</h2>

          <div className="hum-table-wrap">
            <table className="hum-table">
              <thead>
                <tr>
                  <th scope="col">Horaire</th>
                  <th scope="col">Durée</th>
                  <th scope="col">Fréquence</th>
                  <th scope="col">Parcelle</th>
                  <th scope="col">État</th>
                  <th scope="col"></th>
                </tr>
              </thead>
              <tbody>
                {cyclesPagines.length === 0 && (
                  <tr>
                    <td colSpan="6" style={{ color: '#5B6B63' }}>Aucun cycle programmé.</td>
                  </tr>
                )}
                {cyclesPagines.map((c) => {
                  const p = parcelles.find((item) => item.id === c.parcelle_id)
                  return (
                    <tr key={c.id}>
                      <td className="hum-td-bold">{c.heure}</td>
                      <td>{c.duree_min} min</td>
                      <td>{c.jours}</td>
                      <td>{nomCourtParcelle(p) || `#${c.parcelle_id}`}</td>
                      <td>
                        <label className="hum-check-label">
                          <input
                            type="checkbox"
                            checked={Boolean(c.actif)}
                            onChange={() => changerEtatCycle(c.id)}
                          />
                          Actif
                        </label>
                      </td>
                      <td>
                        <button
                          type="button"
                          className="hum-btn-icon-del"
                          aria-label={`Supprimer le cycle de ${c.heure}`}
                          onClick={() => retirerCycle(c.id)}
                        >
                          Supprimer
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {cycles.length > CYCLES_PAR_PAGE && (
            <div className="hum-pagination">
              <span>
                Affichage {indexDebutCycles + 1}–{Math.min(indexDebutCycles + CYCLES_PAR_PAGE, cycles.length)} sur {cycles.length} cycles
              </span>

              <div className="hum-page-controls">
                <button
                  type="button"
                  className="hum-page-btn"
                  disabled={pageCyclesCourante === 1}
                  onClick={() => setPageCycles((p) => Math.max(1, p - 1))}
                >
                  ← Précédent
                </button>

                {Array.from({ length: totalPagesCycles }, (_, i) => i + 1).map((numPage) => (
                  <button
                    key={numPage}
                    type="button"
                    aria-current={pageCyclesCourante === numPage ? 'page' : undefined}
                    className={`hum-page-btn ${pageCyclesCourante === numPage ? 'active' : ''}`}
                    onClick={() => setPageCycles(numPage)}
                  >
                    {numPage}
                  </button>
                ))}

                <button
                  type="button"
                  className="hum-page-btn"
                  disabled={pageCyclesCourante === totalPagesCycles}
                  onClick={() => setPageCycles((p) => Math.min(totalPagesCycles, p + 1))}
                >
                  Suivant →
                </button>
              </div>
            </div>
          )}

          <form className="hum-new-cycle" onSubmit={creerCycle}>
            <div style={{ fontSize: '14px', fontWeight: 600 }}>Nouveau cycle</div>
            <div className="hum-grid-4">
              <div className="hum-field">
                <label htmlFor="n-h">Horaire</label>
                <input
                  id="n-h"
                  type="time"
                  required
                  value={nouvelleHeure}
                  onChange={(e) => setNouvelleHeure(e.target.value)}
                />
              </div>
              <div className="hum-field">
                <label htmlFor="n-d">Durée (min)</label>
                <input
                  id="n-d"
                  type="number"
                  min="1"
                  max="240"
                  required
                  value={nouvelleDuree}
                  onChange={(e) => setNouvelleDuree(e.target.value)}
                />
              </div>
              <div className="hum-field">
                <label htmlFor="n-f">Fréquence</label>
                <select
                  id="n-f"
                  value={nouvelleFrequence}
                  onChange={(e) => setNouvelleFrequence(e.target.value)}
                >
                  <option>Tous les jours</option>
                  <option>Tous les 2 jours</option>
                  <option>Lun, mer, ven</option>
                  <option>Chaque semaine</option>
                </select>
              </div>
              <div className="hum-field">
                <label htmlFor="n-p">Parcelle</label>
                <select
                  id="n-p"
                  value={nouvelleParcelleId}
                  onChange={(e) => setNouvelleParcelleId(e.target.value)}
                >
                  {parcelles.map((p) => (
                    <option key={p.id} value={p.id}>{p.nom}</option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <button type="submit" disabled={ajoutCycleEnCours} className="hum-btn-green-sm">
                {ajoutCycleEnCours ? 'Enregistrement...' : 'Ajouter le cycle'}
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

          {recommandation?.bilan_hebdo && (
            <div className="hum-bilan-strip">
              <span>
                Cumul 7 jours : <strong>{recommandation.bilan_hebdo.volume_litres.toLocaleString('fr-FR')} L</strong> ({recommandation.bilan_hebdo.nb_apports} apports)
              </span>
              <span>
                Efficience : <strong>-{recommandation.bilan_hebdo.economie_estimee_pct} % d&apos;eau</strong> vs arrosage fixe
              </span>
            </div>
          )}

          <div className="hum-table-wrap">
            <table className="hum-table" style={{ minWidth: '640px' }}>
              <thead>
                <tr>
                  <th scope="col">Date</th>
                  <th scope="col">Parcelle</th>
                  <th scope="col">Durée</th>
                  <th scope="col">Volume</th>
                  <th scope="col">Mode</th>
                  <th scope="col">Déclencheur</th>
                </tr>
              </thead>
              <tbody>
                {irrigationsPaginees.length === 0 && (
                  <tr>
                    <td colSpan="6" style={{ color: '#5B6B63' }}>Aucune irrigation enregistrée.</td>
                  </tr>
                )}
                {irrigationsPaginees.map((irr) => {
                  const p = parcelles.find((item) => item.id === irr.parcelle_id)
                  const estAuto = (irr.mode || '').toLowerCase().startsWith('auto')
                  const volumeLitres = (Number(irr.duree_min) || 0) * 60

                  return (
                    <tr key={irr.id}>
                      <td className="hum-td-bold">{formaterDate(irr.debut)}</td>
                      <td>{nomCourtParcelle(p) || `#${irr.parcelle_id}`}</td>
                      <td>{irr.duree_min} min</td>
                      <td>{volumeLitres.toLocaleString('fr-FR')} L</td>
                      <td>
                        <span className={estAuto ? 'hum-badge-auto' : 'hum-badge-manuel'}>
                          {estAuto ? 'Automatique' : 'Programmé'}
                        </span>
                      </td>
                      <td>{estAuto ? 'Seuil capteur' : 'Cycle planifié'}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {irrigations.length > LIGNES_PAR_PAGE && (
            <div className="hum-pagination">
              <span>
                Affichage {indexDebutJournal + 1}–{Math.min(indexDebutJournal + LIGNES_PAR_PAGE, irrigations.length)} sur {irrigations.length} irrigations
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