import { useEffect, useState } from 'react'
import { urlImage } from '../api.js'

// Image d'un comptage, avec un message si elle n'est plus accessible (supprimée, réseau, etc.)
export default function ImageParcelle({ src, alt, parcelle }) {
  const [erreur, setErreur] = useState(false)

  useEffect(() => setErreur(false), [src])

  if (!src || erreur) {
    return (
      <div className="cam-image cam-image-vide" role="img" aria-label={alt}>
        {erreur ? "Image inaccessible" : "Pas d'image"}
      </div>
    )
  }

  return (
    <div className="cam-image-cadre">
      <img className="cam-image" src={urlImage(src)} alt={alt} onError={() => setErreur(true)} />
      {parcelle && <span className="cam-image-parcelle">Parcelle : {parcelle}</span>}
    </div>
  )
}