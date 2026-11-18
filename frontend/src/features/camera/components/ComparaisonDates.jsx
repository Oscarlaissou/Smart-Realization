import { useEffect, useState } from 'react'
import { dateHeure, nombre } from '../format.js'
import ImageParcelle from './ImageParcelle.jsx'

function ChoixImage({ id, label, comptages, valeur, onChange }) {
  const comptage = comptages.find((c) => String(c.id) === String(valeur))
  const src = comptage?.image_detections_url || comptage?.image_url

  return (
    <div className="cam-compare-col">
      <div className="cam-field">
        <label htmlFor={id}>{label}</label>
        <select id={id} value={valeur} onChange={(e) => onChange(e.target.value)}>
          {comptages.map((c) => (
            <option key={c.id} value={c.id}>
              {dateHeure(c.date)}
            </option>
          ))}
        </select>
      </div>
      <ImageParcelle src={src} alt={`Image de la parcelle, ${label}`} />
      <span className="cam-legende">{comptage ? `${nombre(comptage.nb_plants)} plants` : ''}</span>
    </div>
  )
}

// Deux images de la même parcelle à deux dates, avec l'écart de plants
export default function ComparaisonDates({ comptages }) {
  const [idA, setIdA] = useState('')
  const [idB, setIdB] = useState('')

  // À chaque changement de parcelle ou nouvel envoi : A = avant-dernier, B = dernier
  useEffect(() => {
    if (comptages.length >= 2) {
      setIdA(String(comptages[comptages.length - 2].id))
      setIdB(String(comptages[comptages.length - 1].id))
    } else {
      setIdA('')
      setIdB('')
    }
  }, [comptages])

  if (comptages.length < 2) {
    return <p className="cam-vide">Il faut au moins deux images pour comparer deux dates.</p>
  }

  const a = comptages.find((c) => String(c.id) === idA)
  const b = comptages.find((c) => String(c.id) === idB)
  const ecart = a && b ? b.nb_plants - a.nb_plants : null

  return (
    <>
      <div className="cam-compare-grid">
        <ChoixImage id="d1" label="Date A" comptages={comptages} valeur={idA} onChange={setIdA} />
        <ChoixImage id="d2" label="Date B" comptages={comptages} valeur={idB} onChange={setIdB} />
      </div>

      {ecart !== null && (
        <div className="cam-badges">
          <span className={`cam-badge ${ecart > 0 ? 'cam-badge-ok' : ecart < 0 ? 'cam-badge-warn' : 'cam-badge-info'}`}>
            {ecart > 0 ? '+' : ''}
            {nombre(ecart)} plants entre A et B
          </span>
        </div>
      )}
    </>
  )
}