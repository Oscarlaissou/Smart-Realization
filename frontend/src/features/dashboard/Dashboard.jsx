import { useState } from 'react'
import { Link } from 'react-router-dom'
import './Dashboard.css'

const DONNEES_GRAPHIQUE = {
  Eau: {
    legende: "Consommation d'eau cumulée par période, en m³",
    unite: 'm³',
    ticks: [350, 300, 250, 200, 150],
    points: '46.0,170.7 108.8,143.1 171.6,152.3 234.4,127.0 297.2,133.9 360.0,113.2 422.8,117.8 485.6,102.9 548.4,109.8 611.2,92.5 674.0,74.1',
  },
  Humidité: {
    legende: "Évolution de l'humidité moyenne du sol, en %",
    unite: '%',
    ticks: [60, 50, 40, 30, 20],
    points: '46.0,130.0 108.8,118.0 171.6,125.0 234.4,110.0 297.2,140.0 360.0,135.0 422.8,120.0 485.6,115.0 548.4,128.0 611.2,132.0 674.0,127.0',
  },
  Plants: {
    legende: 'Évolution du comptage de plants actifs',
    unite: 'plants',
    ticks: [13000, 12500, 12000, 11500, 11000],
    points: '46.0,195.0 108.8,180.0 171.6,168.0 234.4,155.0 297.2,142.0 360.0,130.0 422.8,118.0 485.6,104.0 548.4,92.0 611.2,80.0 674.0,71.0',
  },
  Engrais: {
    legende: "Cumul des apports d'engrais sur la période",
    unite: 'apports',
    ticks: [8, 6, 4, 2, 0],
    points: '46.0,213.0 108.8,213.0 171.6,184.5 234.4,184.5 297.2,155.8 360.0,155.8 422.8,127.0 485.6,127.0 548.4,98.3 611.2,98.3 674.0,98.3',
  },
}

const DATES_AXE_X = [
  { x: 46.0, label: '13 oct.' },
  { x: 108.8, label: '16 oct.' },
  { x: 171.6, label: '19 oct.' },
  { x: 234.4, label: '22 oct.' },
  { x: 297.2, label: '25 oct.' },
  { x: 360.0, label: '28 oct.' },
  { x: 422.8, label: '31 oct.' },
  { x: 485.6, label: '3 nov.' },
  { x: 548.4, label: '6 nov.' },
  { x: 611.2, label: '9 nov.' },
  { x: 674.0, label: '12 nov.' },
]

const PARCELLES_DATA = [
  { nom: 'Parcelle Nord', court: 'Nord', culture: 'Maïs', statut: 'Optimal', badgeClass: 'badge-ok', humidite: '41 %', eau: 96, largeur: 228.9, couleur: '#1F7A4D', yTexte: 21, yRect: 7, yVal: 23 },
  { nom: 'Parcelle Sud', court: 'Sud', culture: 'Tomate', statut: 'Irrigation', badgeClass: 'badge-info', humidite: '27 %', eau: 118, largeur: 281.4, couleur: '#1D6FB8', yTexte: 65, yRect: 51, yVal: 67 },
  { nom: 'Parcelle Est', court: 'Est', culture: 'Manioc', statut: 'Optimal', badgeClass: 'badge-ok', humidite: '35 %', eau: 74, largeur: 176.5, couleur: '#2FA36B', yTexte: 109, yRect: 95, yVal: 111 },
  { nom: 'Parcelle Ouest', court: 'Ouest', culture: 'Plantain', statut: 'Trop humide', badgeClass: 'badge-warn', humidite: '49 %', eau: 54, largeur: 128.8, couleur: '#7DD3A8', yTexte: 153, yRect: 139, yVal: 155 },
]

const ALERTES_DATA = [
  { niveau: 'Urgent', badgeClass: 'badge-danger', titre: 'Sol sec · Parcelle Sud', detail: 'Humidité à 27 % · 14:32' },
  { niveau: 'Attention', badgeClass: 'badge-warn', titre: 'Capteur C-09 hors service', detail: 'Parcelle Est · 11:05' },
  { niveau: 'Attention', badgeClass: 'badge-warn', titre: "Excès d'eau · Parcelle Ouest", detail: 'Humidité à 49 % · 09:40' },
]

export default function Dashboard() {
  const [periode, setPeriode] = useState('30 derniers jours')
  const [parcelle, setParcelle] = useState('Toutes les parcelles')
  const [culture, setCulture] = useState('Toutes les cultures')
  const [recherche, setRecherche] = useState('')
  const [indicateurActif, setIndicateurActif] = useState('Eau')

  const graphe = DONNEES_GRAPHIQUE[indicateurActif]

  const parcellesFiltrees = PARCELLES_DATA.filter((p) => {
    const matchParcelle = parcelle === 'Toutes les parcelles' || p.nom === parcelle
    const matchCulture = culture === 'Toutes les cultures' || p.culture === culture
    const matchRecherche =
      !recherche.trim() ||
      p.nom.toLowerCase().includes(recherche.toLowerCase()) ||
      p.culture.toLowerCase().includes(recherche.toLowerCase())
    return matchParcelle && matchCulture && matchRecherche
  })

  const exporterDonnees = (format) => {
    alert(`Export ${format} généré (${periode} · ${parcelle} · ${culture})`)
  }

  return (
    <div className="dash-wrapper">
      {/* En-tête */}
      <header className="dash-header">
        <div>
          <h1 className="dash-title">Tableau de bord</h1>
          <p className="dash-subtitle">Domaine Les Collines · mesures reçues il y a 3 s</p>
        </div>

        <div className="dash-header-actions">
          <label className="dash-search">
            <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#5B6B63" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M11 3a8 8 0 1 0 0 16 8 8 0 0 0 0-16zM21 21l-4.3-4.3" />
            </svg>
            <input
              aria-label="Rechercher"
              placeholder="Rechercher"
              value={recherche}
              onChange={(e) => setRecherche(e.target.value)}
            />
          </label>

          <span className="dash-lang" aria-label="Langue : français">
            <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <path d="M2 12h20M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20" />
            </svg>
            FR
          </span>

          <Link to="/alertes" aria-label="Alertes, 3 non lues" className="dash-bell">
            <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#12201A" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9M10.3 21a1.94 1.94 0 0 0 3.4 0" />
            </svg>
            <span className="dash-bell-badge">3</span>
          </Link>

          <div className="dash-user">
            <div className="dash-avatar">PM</div>
            <div>
              <div className="dash-user-name">Paul Mbarga</div>
              <div className="dash-user-role">Exploitant</div>
            </div>
          </div>
        </div>
      </header>

      {/* Filtres et Exports */}
      <section className="dash-card">
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
              <option>Parcelle Nord</option>
              <option>Parcelle Sud</option>
              <option>Parcelle Est</option>
              <option>Parcelle Ouest</option>
            </select>
          </div>

          <div className="dash-field">
            <label htmlFor="f-cul">Culture</label>
            <select id="f-cul" value={culture} onChange={(e) => setCulture(e.target.value)}>
              <option>Toutes les cultures</option>
              <option>Maïs</option>
              <option>Tomate</option>
              <option>Manioc</option>
              <option>Plantain</option>
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

      {/* 5 Indicateurs KPI */}
      <section aria-label="Indicateurs" className="dash-kpis">
        <div className="dash-kpi-card">
          <span className="dash-kpi-label">Consommation d&apos;eau</span>
          <div className="dash-kpi-val">
            <strong>342</strong>
            <span>m³</span>
          </div>
          <div>
            <span className="badge badge-ok">−8 % vs mois dernier</span>
          </div>
        </div>

        <div className="dash-kpi-card">
          <span className="dash-kpi-label">Humidité moyenne</span>
          <div className="dash-kpi-val">
            <strong>38</strong>
            <span>%</span>
          </div>
          <div>
            <span className="badge badge-ok">Dans la plage cible</span>
          </div>
        </div>

        <div className="dash-kpi-card">
          <span className="dash-kpi-label">Plants comptés</span>
          <div className="dash-kpi-val">
            <strong>12 480</strong>
            <span>plants</span>
          </div>
          <div>
            <span className="badge badge-ok">+3,2 % en 7 jours</span>
          </div>
        </div>

        <div className="dash-kpi-card">
          <span className="dash-kpi-label">Apports d&apos;engrais</span>
          <div className="dash-kpi-val">
            <strong>5</strong>
            <span>ce mois</span>
          </div>
          <div>
            <span className="badge badge-info">1 à venir cette semaine</span>
          </div>
        </div>

        <div className="dash-kpi-card">
          <span className="dash-kpi-label">Alertes actives</span>
          <div className="dash-kpi-val">
            <strong>3</strong>
            <span>à traiter</span>
          </div>
          <div>
            <span className="badge badge-warn">1 urgente</span>
          </div>
        </div>
      </section>

      {/* Ligne 2 : Graphique d'évolution + État des parcelles */}
      <div className="dash-row">
        <section className="dash-card dash-col-2">
          <h2 className="dash-card-title">Évolution des indicateurs</h2>

          <div role="group" aria-label="Indicateur affiché" className="dash-pills">
            {Object.keys(DONNEES_GRAPHIQUE).map((onglet) => (
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

          <svg role="img" aria-label={graphe.legende} viewBox="0 0 700 270" width="100%" style={{ height: 'auto', display: 'block' }}>
            {[12, 69.5, 127, 184.5, 242].map((y, idx) => (
              <g key={y}>
                <line x1="46" x2="674" y1={y} y2={y} stroke="#E8EEE9" />
                <text x="38" y={y + 4} textAnchor="end" fontSize="11" fill="#5B6B63" fontFamily="Inter,sans-serif">
                  {graphe.ticks[idx]}
                </text>
              </g>
            ))}

            {DATES_AXE_X.map((d) => (
              <text key={d.label} x={d.x} y="262" textAnchor="middle" fontSize="11" fill="#5B6B63" fontFamily="Inter,sans-serif">
                {d.label}
              </text>
            ))}

            <polyline
              points={graphe.points}
              fill="none"
              stroke="#1F7A4D"
              strokeWidth="2.5"
              strokeLinejoin="round"
              strokeLinecap="round"
            />
          </svg>

          <div className="dash-caption">{graphe.legende}</div>
        </section>

        <section className="dash-card dash-col-1">
          <h2 className="dash-card-title">État des parcelles</h2>

          <ul className="dash-list">
            {parcellesFiltrees.map((p) => (
              <li key={p.nom} className="dash-list-item">
                <div>
                  <div className="dash-item-title">{p.nom}</div>
                  <div className="dash-item-sub">{p.culture}</div>
                </div>
                <div className="dash-item-right">
                  <span className={`badge ${p.badgeClass}`}>{p.statut}</span>
                  <span className="dash-item-pct">{p.humidite}</span>
                </div>
              </li>
            ))}
          </ul>

          <Link to="/humidite" className="btn-outline btn-full">
            Voir l&apos;humidité
          </Link>
        </section>
      </div>

      {/* Ligne 3 : Consommation par parcelle + Dernières alertes */}
      <div className="dash-row">
        <section className="dash-card dash-col-1">
          <h2 className="dash-card-title">Consommation d&apos;eau par parcelle</h2>

          <svg role="img" aria-label="Consommation d'eau par parcelle" viewBox="0 0 520 180" width="100%" style={{ height: 'auto', display: 'block' }}>
            {PARCELLES_DATA.map((p) => (
              <g key={p.court}>
                <text x="0" y={p.yTexte} fontSize="13" fill="#12201A" fontFamily="Inter,sans-serif" fontWeight="500">
                  {p.court}
                </text>
                <rect x="110" y={p.yRect} width={p.largeur} height="22" rx="5" fill={p.couleur} />
                <text x={110 + p.largeur + 8} y={p.yVal} fontSize="13" fontWeight="600" fill="#12201A" fontFamily="Inter,sans-serif">
                  {p.eau} m³
                </text>
              </g>
            ))}
          </svg>
        </section>

        <section className="dash-card dash-col-1">
          <h2 className="dash-card-title">Dernières alertes</h2>

          <ul className="dash-list">
            {ALERTES_DATA.map((a, idx) => (
              <li key={idx} className="dash-alert-item">
                <span className={`badge ${a.badgeClass}`}>{a.niveau}</span>
                <div style={{ flex: 1 }}>
                  <div className="dash-item-title">{a.titre}</div>
                  <div className="dash-item-sub">{a.detail}</div>
                </div>
              </li>
            ))}
          </ul>

          <Link to="/alertes" className="btn-outline btn-full">
            Toutes les alertes
          </Link>
        </section>
      </div>
    </div>
  )
}