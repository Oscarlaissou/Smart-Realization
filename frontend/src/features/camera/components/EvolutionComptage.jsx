import { dateCourte, dateHeure, nombre } from '../format.js'

const X_DEBUT = 46
const X_FIN = 534
const Y_HAUT = 12
const Y_BAS = 212

// Courbe du nombre de plants comptés dans le temps (SVG, comme le tableau de bord)
export default function EvolutionComptage({ comptages, nomParcelle }) {
  if (comptages.length === 0) {
    return <p className="cam-vide">Aucun comptage pour cette parcelle. Chargez une image pour commencer.</p>
  }

  const valeurs = comptages.map((c) => Number(c.nb_plants) || 0)
  let min = Math.min(...valeurs)
  let max = Math.max(...valeurs)
  if (min === max) {
    min = Math.max(0, min - 10)
    max = max + 10
  }

  const ticks = [0, 1, 2, 3].map((i) => Math.round(max - ((max - min) * i) / 3))
  const yTicks = [0, 1, 2, 3].map((i) => Y_HAUT + (i * (Y_BAS - Y_HAUT)) / 3)

  const xDe = (i) =>
    comptages.length === 1 ? (X_DEBUT + X_FIN) / 2 : X_DEBUT + (i * (X_FIN - X_DEBUT)) / (comptages.length - 1)
  const yDe = (v) => Y_BAS - ((v - min) / (max - min)) * (Y_BAS - Y_HAUT)

  const points = comptages.map((c, i) => `${xDe(i).toFixed(1)},${yDe(valeurs[i]).toFixed(1)}`).join(' ')
  const pasLabel = Math.ceil(comptages.length / 6)   // évite des dates qui se chevauchent

  return (
    <svg
      role="img"
      aria-label={`Nombre de plants comptés dans le temps, parcelle ${nomParcelle}`}
      viewBox="0 0 560 240"
      width="100%"
      style={{ height: 'auto', display: 'block' }}
    >
      {yTicks.map((y, i) => (
        <g key={y}>
          <line x1={X_DEBUT} x2={X_FIN} y1={y} y2={y} stroke="#E8EEE9" />
          <text x="38" y={y + 4} textAnchor="end" fontSize="11" fill="#5B6B63" fontFamily="Inter,sans-serif">
            {nombre(ticks[i])}
          </text>
        </g>
      ))}

      {comptages.map((c, i) =>
        i % pasLabel === 0 || i === comptages.length - 1 ? (
          <text key={c.id} x={xDe(i)} y="232" textAnchor="middle" fontSize="11" fill="#5B6B63" fontFamily="Inter,sans-serif">
            {dateCourte(c.date)}
          </text>
        ) : null,
      )}

      {comptages.length > 1 && (
        <polyline points={points} fill="none" stroke="#1F7A4D" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
      )}

      {comptages.map((c, i) => (
        <circle key={c.id} cx={xDe(i)} cy={yDe(valeurs[i])} r="4" fill="#FFFFFF" stroke="#1F7A4D" strokeWidth="2">
          <title>{`${dateHeure(c.date)} : ${nombre(valeurs[i])} plants`}</title>
        </circle>
      ))}
    </svg>
  )
}