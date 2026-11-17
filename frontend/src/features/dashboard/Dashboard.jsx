import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { lister } from './api.js'
import './Dashboard.css'

const CONFIG_INDICATEURS = {
  Eau: { legende: "Consommation d'eau cumulée par période, en m³" },
  Humidité: { legende: "Évolution de l'humidité moyenne du sol, en %" },
  Plants: { legende: 'Évolution du comptage de plants actifs' },
  Engrais: { legende: "Cumul des apports d'engrais sur la période" },
}

const COULEURS_BARRES = ['#1F7A4D', '#1D6FB8', '#2FA36B', '#7DD3A8']

// Supprime les accents et met en minuscules pour une recherche souple ("mais" -> "Maïs")
function normaliser(texte = '') {
  return String(texte)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
}

function classeBadgeStatut(statut = '') {
  const s = normaliser(statut)
  if (s.includes('optimal')) return 'badge-ok'
  if (s.includes('irrigation')) return 'badge-info'
  if (s.includes('urgent')) return 'badge-danger'
  return 'badge-warn'
}

function construireCourbeSVG(serie = []) {
  if (!serie.length) {
    return { points: '', ticks: [100, 75, 50, 25, 0], labelsX: [] }
  }

  const valeurs = serie.map((d) => Number(d.valeur) || 0)
  let min = Math.min(...valeurs)
  let max = Math.max(...valeurs)

  if (min === max) {
    min = Math.max(0, min - 10)
    max = max + 10
  }

  const ticks = [0, 1, 2, 3, 4].map((i) => Math.round(max - ((max - min) * i) / 4))

  const xDebut = 46
  const xFin = 674
  const yHaut = 12
  const yBas = 242

  const points = serie
    .map((item, idx) => {
      const x =
        serie.length === 1
          ? (xDebut + xFin) / 2
          : xDebut + (idx * (xFin - xDebut)) / (serie.length - 1)
      const ratio = (Number(item.valeur) - min) / (max - min)
      const y = yBas - ratio * (yBas - yHaut)
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')

  const labelsX = serie.map((item, idx) => ({
    x:
      serie.length === 1
        ? (xDebut + xFin) / 2
        : xDebut + (idx * (xFin - xDebut)) / (serie.length - 1),
    label: item.date,
  }))

  return { points, ticks, labelsX }
}

export default function Dashboard() {
  const [periode, setPeriode] = useState('30 derniers jours')
  const [parcelle, setParcelle] = useState('Toutes les parcelles')
  const [culture, setCulture] = useState('Toutes les cultures')
  const [recherche, setRecherche] = useState('')
  const [indicateurActif, setIndicateurActif] = useState('Eau')

  const [donnees, setDonnees] = useState(null)
  const [chargement, setChargement] = useState(true)
  const [erreur, setErreur] = useState('')

  useEffect(() => {
    let actif = true
    setChargement(true)
    setErreur('')

    lister({ periode, parcelle, culture })
      .then((res) => {
        if (!actif) return
        setDonnees(res?.data || res)
      })
      .catch((err) => {
        if (!actif) return
        setErreur(err.message || 'Impossible de charger les données du tableau de bord.')
      })
      .finally(() => {
        if (actif) setChargement(false)
      })

    return () => {
      actif = false
    }
  }, [periode, parcelle, culture])

  const domaine = donnees?.domaine || {}
  const utilisateur = donnees?.utilisateur || {}
  const parcelles = donnees?.parcelles || []
  const alertes = donnees?.alertes || []
  const serieActive = donnees?.evolution?.[indicateurActif] || []

  const eauM3 = donnees?.eau_m3 ?? 0
  const humiditeMoyenne = donnees?.humidite_moyenne ?? 0
  const plantsComptes = donnees?.plants_comptes ?? 0
  const apportsEngrais = donnees?.apports_engrais ?? 0
  const alertesActives = donnees?.alertes_actives ?? 0

  // Filtrage global (sans accents ni casse) sur les parcelles ET les alertes
  const termeRecherche = normaliser(recherche)

  const parcellesFiltrees = parcelles.filter((p) => {
    if (!termeRecherche) return true
    return (
      normaliser(p.nom).includes(termeRecherche) ||
      normaliser(p.culture).includes(termeRecherche) ||
      normaliser(p.statut).includes(termeRecherche)
    )
  })

  const alertesFiltrees = alertes.filter((a) => {
    if (!termeRecherche) return true
    return (
      normaliser(a.titre).includes(termeRecherche) ||
      normaliser(a.detail).includes(termeRecherche) ||
      normaliser(a.niveau).includes(termeRecherche)
    )
  })

  const { points, ticks, labelsX } = construireCourbeSVG(serieActive)
  const maxEauParcelle = Math.max(...parcellesFiltrees.map((p) => Number(p.eau_m3) || 0), 1)

  const initiales = (utilisateur.nom || 'Utilisateur')
    .split(' ')
    .map((n) => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()

  // Export réel en PDF, Excel (.xls) ou CSV
  const exporterDonnees = (format) => {
    const fmt = format.toUpperCase()

    if (fmt === 'PDF') {
      window.print()
      return
    }

    const telechargerFichier = (blob, nomFichier) => {
      const url = URL.createObjectURL(blob)
      const lien = document.createElement('a')
      lien.href = url
      lien.download = nomFichier
      document.body.appendChild(lien)
      lien.click()
      document.body.removeChild(lien)
      URL.revokeObjectURL(url)
    }

    if (fmt === 'CSV') {
      const lignes = [
        ['RAPPORT SEVIA', domaine.nom || 'Domaine Les Collines', periode],
        [],
        ['Indicateur', 'Valeur'],
        ["Consommation d'eau (m3)", eauM3],
        ['Humidite moyenne (%)', humiditeMoyenne],
        ['Plants comptes', plantsComptes],
        ["Apports d'engrais", apportsEngrais],
        ['Alertes actives', alertesActives],
        [],
        ['Parcelle', 'Culture', 'Statut', 'Humidite (%)', 'Eau (m3)'],
        ...parcellesFiltrees.map((p) => [p.nom, p.culture, p.statut, p.humidite, p.eau_m3]),
      ]
      const contenuCSV = '\ufeff' + lignes.map((l) => l.join(';')).join('\n')
      const blob = new Blob([contenuCSV], { type: 'text/csv;charset=utf-8;' })
      telechargerFichier(blob, 'sevia-dashboard.csv')
      return
    }

    if (fmt === 'EXCEL') {
      const htmlExcel = `
        <html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel">
        <head><meta charset="UTF-8"></head>
        <body>
          <h3>Sevia – Tableau de bord (${domaine.nom || 'Domaine Les Collines'} · ${periode})</h3>
          <table border="1">
            <tr><th>Indicateur</th><th>Valeur</th></tr>
            <tr><td>Consommation d'eau (m³)</td><td>${eauM3}</td></tr>
            <tr><td>Humidité moyenne (%)</td><td>${humiditeMoyenne}</td></tr>
            <tr><td>Plants comptés</td><td>${plantsComptes}</td></tr>
            <tr><td>Apports d'engrais</td><td>${apportsEngrais}</td></tr>
            <tr><td>Alertes actives</td><td>${alertesActives}</td></tr>
          </table>
          <br/>
          <table border="1">
            <tr>
              <th>Parcelle</th>
              <th>Culture</th>
              <th>Statut</th>
              <th>Humidité (%)</th>
              <th>Eau (m³)</th>
            </tr>
            ${parcellesFiltrees
              .map(
                (p) => `
              <tr>
                <td>${p.nom}</td>
                <td>${p.culture}</td>
                <td>${p.statut}</td>
                <td>${p.humidite}</td>
                <td>${p.eau_m3}</td>
              </tr>`
              )
              .join('')}
          </table>
        </body>
        </html>`
      const blob = new Blob(['\ufeff', htmlExcel], { type: 'application/vnd.ms-excel;charset=utf-8;' })
      telechargerFichier(blob, 'sevia-dashboard.xls')
    }
  }

  return (
    <div className="dash-wrapper">
      <header className="dash-header">
        <div>
          <h1 className="dash-title">Tableau de bord</h1>
          <p className="dash-subtitle">
            {domaine.nom || 'Domaine Les Collines'} · {periode}
          </p>
        </div>

        <div className="dash-header-actions no-print">
          <label className="dash-search">
            <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#5B6B63" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M11 3a8 8 0 1 0 0 16 8 8 0 0 0 0-16zM21 21l-4.3-4.3" />
            </svg>
            <input
              aria-label="Rechercher"
              placeholder="Rechercher parcelle, culture, alerte..."
              value={recherche}
              onChange={(e) => setRecherche(e.target.value)}
            />
            {recherche && (
              <button
                type="button"
                className="dash-search-clear"
                aria-label="Effacer la recherche"
                onClick={() => setRecherche('')}
              >
                ✕
              </button>
            )}
          </label>

          <span className="dash-lang" aria-label="Langue : français">
            <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <path d="M2 12h20M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20" />
            </svg>
            FR
          </span>

          <Link to="/alertes" aria-label={`Alertes, ${alertesActives} non lues`} className="dash-bell">
            <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#12201A" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9M10.3 21a1.94 1.94 0 0 0 3.4 0" />
            </svg>
            {alertesActives > 0 && <span className="dash-bell-badge">{alertesActives}</span>}
          </Link>

          <div className="dash-user">
            <div className="dash-avatar">{initiales}</div>
            <div>
              <div className="dash-user-name">{utilisateur.nom || 'Exploitant'}</div>
              <div className="dash-user-role">{utilisateur.role || 'Compte actif'}</div>
            </div>
          </div>
        </div>
      </header>

      {erreur && <div className="dash-banner-error">{erreur}</div>}
      {chargement && <div className="dash-banner-loading no-print">Synchronisation avec Supabase en cours...</div>}

      <section className="dash-card no-print">
        <div className="dash-filters-row">
          <div className="dash-field">
            <label htmlFor="f-per">Période</label>
            <select id="f-per" value={periode} onChange={(e) => setPeriode(e.target.value)}>
              <option>30 derniers jours</option>
              <option>7 derniers jours</option>
              <option>Campagne en cours</option>
            </select>
          </div>

          <div className="dash-field">
            <label htmlFor="f-par">Parcelle</label>
            <select id="f-par" value={parcelle} onChange={(e) => setParcelle(e.target.value)}>
              <option>Toutes les parcelles</option>
              {parcelles.map((p) => (
                <option key={p.id || p.nom} value={p.nom}>{p.nom}</option>
              ))}
            </select>
          </div>

          <div className="dash-field">
            <label htmlFor="f-cul">Culture</label>
            <select id="f-cul" value={culture} onChange={(e) => setCulture(e.target.value)}>
              <option>Toutes les cultures</option>
              {[...new Set(parcelles.map((p) => p.culture).filter(Boolean))].map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          <div className="dash-exports">
            {['PDF', 'Excel', 'CSV'].map((fmt) => (
              <button key={fmt} type="button" className="btn-outline" onClick={() => exporterDonnees(fmt)}>
                <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 3v12M7 10l5 5 5-5M5 21h14" />
                </svg>
                {fmt}
              </button>
            ))}
          </div>
        </div>
      </section>

      <section aria-label="Indicateurs" className="dash-kpis">
        <div className="dash-kpi-card">
          <span className="dash-kpi-label">Consommation d&apos;eau</span>
          <div className="dash-kpi-val">
            <strong>{eauM3}</strong>
            <span>m³</span>
          </div>
          <div>
            <span className="badge badge-ok">Données à jour</span>
          </div>
        </div>

        <div className="dash-kpi-card">
          <span className="dash-kpi-label">Humidité moyenne</span>
          <div className="dash-kpi-val">
            <strong>{humiditeMoyenne}</strong>
            <span>%</span>
          </div>
          <div>
            <span className="badge badge-ok">Dans la plage cible</span>
          </div>
        </div>

        <div className="dash-kpi-card">
          <span className="dash-kpi-label">Plants comptés</span>
          <div className="dash-kpi-val">
            <strong>{Number(plantsComptes).toLocaleString('fr-FR')}</strong>
            <span>plants</span>
          </div>
          <div>
            <span className="badge badge-ok">Suivi actif</span>
          </div>
        </div>

        <div className="dash-kpi-card">
          <span className="dash-kpi-label">Apports d&apos;engrais</span>
          <div className="dash-kpi-val">
            <strong>{apportsEngrais}</strong>
            <span>réalisés</span>
          </div>
          <div>
            <span className="badge badge-info">Campagne suivie</span>
          </div>
        </div>

        <div className="dash-kpi-card">
          <span className="dash-kpi-label">Alertes actives</span>
          <div className="dash-kpi-val">
            <strong>{alertesActives}</strong>
            <span>à traiter</span>
          </div>
          <div>
            <span className="badge badge-warn">{alertesActives > 0 ? 'Attention requise' : 'Aucune alerte'}</span>
          </div>
        </div>
      </section>

      <div className="dash-row">
        <section className="dash-card dash-col-2">
          <h2 className="dash-card-title">Évolution des indicateurs</h2>

          <div role="group" aria-label="Indicateur affiché" className="dash-pills no-print">
            {Object.keys(CONFIG_INDICATEURS).map((onglet) => (
              <button
                key={onglet}
                type="button"
                aria-pressed={indicateurActif === onglet}
                className={`dash-pill ${indicateurActif === onglet ? 'active' : ''}`}
                onClick={() => setIndicateurActif(onglet)}
              >
                {onglet}
              </button>
            ))}
          </div>

          <svg role="img" aria-label={CONFIG_INDICATEURS[indicateurActif].legende} viewBox="0 0 700 270" width="100%" style={{ height: 'auto', display: 'block' }}>
            {[12, 69.5, 127, 184.5, 242].map((y, idx) => (
              <g key={y}>
                <line x1="46" x2="674" y1={y} y2={y} stroke="#E8EEE9" />
                <text x="38" y={y + 4} textAnchor="end" fontSize="11" fill="#5B6B63" fontFamily="Inter,sans-serif">
                  {ticks[idx]}
                </text>
              </g>
            ))}

            {labelsX.map((d, idx) => (
              <text key={idx} x={d.x} y="262" textAnchor="middle" fontSize="11" fill="#5B6B63" fontFamily="Inter,sans-serif">
                {d.label}
              </text>
            ))}

            {points && (
              <polyline
                points={points}
                fill="none"
                stroke="#1F7A4D"
                strokeWidth="2.5"
                strokeLinejoin="round"
                strokeLinecap="round"
              />
            )}
          </svg>

          <div className="dash-caption">{CONFIG_INDICATEURS[indicateurActif].legende}</div>
        </section>

        <section className="dash-card dash-col-1">
          <h2 className="dash-card-title">État des parcelles</h2>

          <ul className="dash-list">
            {parcellesFiltrees.length === 0 && !chargement && (
              <li className="dash-item-sub" style={{ padding: '16px 0' }}>
                Aucune parcelle ne correspond à « {recherche} ».
              </li>
            )}
            {parcellesFiltrees.map((p) => (
              <li key={p.id || p.nom} className="dash-list-item">
                <div>
                  <div className="dash-item-title">{p.nom}</div>
                  <div className="dash-item-sub">{p.culture}</div>
                </div>
                <div className="dash-item-right">
                  <span className={`badge ${classeBadgeStatut(p.statut)}`}>{p.statut}</span>
                  <span className="dash-item-pct">{p.humidite} %</span>
                </div>
              </li>
            ))}
          </ul>

          <Link to="/humidite" className="btn-outline btn-full no-print">
            Voir l&apos;humidité
          </Link>
        </section>
      </div>

      <div className="dash-row">
        <section className="dash-card dash-col-1">
          <h2 className="dash-card-title">Consommation d&apos;eau par parcelle</h2>

          <svg
            role="img"
            aria-label="Consommation d'eau par parcelle"
            viewBox={`0 0 520 ${Math.max(parcellesFiltrees.length * 44, 60)}`}
            width="100%"
            style={{ height: 'auto', display: 'block' }}
          >
            {parcellesFiltrees.map((p, idx) => {
              const largeur = (Number(p.eau_m3 || 0) / maxEauParcelle) * 290
              const yBase = idx * 44
              const nomCourt = p.nom.replace(/^Parcelle\s+/i, '')
              return (
                <g key={p.id || p.nom}>
                  <text x="0" y={yBase + 21} fontSize="13" fill="#12201A" fontFamily="Inter,sans-serif" fontWeight="500">
                    {nomCourt}
                  </text>
                  <rect
                    x="110"
                    y={yBase + 7}
                    width={Math.max(largeur, 4)}
                    height="22"
                    rx="5"
                    fill={COULEURS_BARRES[idx % COULEURS_BARRES.length]}
                  />
                  <text x={110 + Math.max(largeur, 4) + 8} y={yBase + 23} fontSize="13" fontWeight="600" fill="#12201A" fontFamily="Inter,sans-serif">
                    {p.eau_m3 ?? 0} m³
                  </text>
                </g>
              )
            })}
          </svg>
        </section>

        <section className="dash-card dash-col-1">
          <h2 className="dash-card-title">Dernières alertes</h2>

          <ul className="dash-list">
            {alertesFiltrees.length === 0 && !chargement && (
              <li className="dash-item-sub" style={{ padding: '16px 0' }}>
                {recherche ? `Aucune alerte ne correspond à « ${recherche} ».` : 'Aucune alerte active.'}
              </li>
            )}
            {alertesFiltrees.map((a, idx) => (
              <li key={a.id || idx} className="dash-alert-item">
                <span className={`badge ${classeBadgeStatut(a.niveau)}`}>{a.niveau}</span>
                <div style={{ flex: 1 }}>
                  <div className="dash-item-title">{a.titre}</div>
                  <div className="dash-item-sub">{a.detail}</div>
                </div>
              </li>
            ))}
          </ul>

          <Link to="/alertes" className="btn-outline btn-full no-print">
            Toutes les alertes
          </Link>
        </section>
      </div>
    </div>
  )
}