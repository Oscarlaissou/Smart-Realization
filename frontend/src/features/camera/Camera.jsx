import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { listerParcelles, listerComptages, envoyerImage } from './api.js'
import { dateHeure, nombre, nomCourt, normaliser } from './format.js'
import EvolutionComptage from './components/EvolutionComptage.jsx'
import ComparaisonDates from './components/ComparaisonDates.jsx'
import ImageParcelle from './components/ImageParcelle.jsx'
import './Camera.css'

const TAILLE_MAX = 8 * 1024 * 1024
const TYPES_ACCEPTES = ['image/jpeg', 'image/png', 'image/webp']

function utilisateurConnecte() {
  try {
    return JSON.parse(localStorage.getItem('utilisateur')) || {}
  } catch {
    return {}
  }
}

export default function Camera() {
  const [parcelles, setParcelles] = useState([])
  const [parcelleId, setParcelleId] = useState(null)
  const [comptages, setComptages] = useState([])
  const [recherche, setRecherche] = useState('')
  const [vue, setVue] = useState('detections')   // 'detections' | 'originale'

  const [chargement, setChargement] = useState(true)
  const [envoi, setEnvoi] = useState(false)
  const [erreur, setErreur] = useState('')
  const [info, setInfo] = useState('')
  const champFichier = useRef(null)

  const utilisateur = utilisateurConnecte()
  const initiales = (utilisateur.nom || 'Utilisateur')
    .split(' ')
    .map((n) => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()

  // 1. Parcelles de l'utilisateur
  useEffect(() => {
    let actif = true
    listerParcelles()
      .then((liste) => {
        if (!actif) return
        setParcelles(liste)
        setParcelleId(liste[0]?.id ?? null)
        if (liste.length === 0) setChargement(false)
      })
      .catch((err) => {
        if (!actif) return
        setErreur(err.message || 'Impossible de charger les parcelles.')
        setChargement(false)
      })
    return () => {
      actif = false
    }
  }, [])

  // 2. Comptages de la parcelle choisie
  const chargerComptages = (pid) => listerComptages(pid).then(setComptages)

  useEffect(() => {
    if (parcelleId == null) return undefined
    let actif = true
    setChargement(true)
    setErreur('')
    listerComptages(parcelleId)
      .then((liste) => actif && setComptages(liste))
      .catch((err) => actif && setErreur(err.message || 'Impossible de charger les comptages.'))
      .finally(() => actif && setChargement(false))
    return () => {
      actif = false
    }
  }, [parcelleId])

  const choisirParcelle = (id) => {
    setParcelleId(id)
    setInfo('')
    setErreur('')
  }

  // 3. Chargement d'une image par l'utilisateur
  const surFichierChoisi = async (e) => {
    const fichier = e.target.files?.[0]
    e.target.value = ''   // permet de re-choisir le même fichier ensuite
    if (!fichier || parcelleId == null) return

    setErreur('')
    setInfo('')
    if (!TYPES_ACCEPTES.includes(fichier.type)) {
      setErreur('Format non pris en charge : choisissez une image JPEG, PNG ou WebP.')
      return
    }
    if (fichier.size > TAILLE_MAX) {
      setErreur('Image trop lourde : 8 Mo maximum.')
      return
    }

    setEnvoi(true)
    try {
      const comptage = await envoyerImage(parcelleId, fichier)
      await chargerComptages(parcelleId)
      setInfo(`Image analysée : ${nombre(comptage.nb_plants)} plants détectés.`)
    } catch (err) {
      setErreur(err.message || "Impossible d'envoyer l'image.")
    } finally {
      setEnvoi(false)
    }
  }

  const parcelle = parcelles.find((p) => p.id === parcelleId)
  const termeRecherche = normaliser(recherche)
  const parcellesAffichees = parcelles.filter((p) => !termeRecherche || normaliser(p.nom).includes(termeRecherche))

  const dernier = comptages[comptages.length - 1]
  const precedent = comptages.length > 1 ? comptages[comptages.length - 2] : null
  const variation = dernier && precedent ? dernier.nb_plants - precedent.nb_plants : null

  const aDetections = Boolean(dernier?.image_detections_url)
  const srcDerniere =
    dernier && (vue === 'detections' && aDetections ? dernier.image_detections_url : dernier.image_url)

  return (
    <div className="cam-wrapper">
      <header className="cam-header">
        <div>
          <h1 className="cam-title">Suivi par caméra</h1>
          <p className="cam-subtitle">Images, comptage automatique et évolution dans le temps</p>
        </div>

        <div className="cam-header-actions">
          <label className="cam-search">
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

          <span className="cam-lang" aria-label="Langue : français">
            <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <path d="M2 12h20M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20" />
            </svg>
            FR
          </span>

          <Link to="/alertes" aria-label="Alertes" className="cam-bell">
            <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#12201A" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9M10.3 21a1.94 1.94 0 0 0 3.4 0" />
            </svg>
          </Link>

          <div className="cam-user">
            <div className="cam-avatar">{initiales}</div>
            <div>
              <div className="cam-user-name">{utilisateur.nom || 'Exploitant'}</div>
              <div className="cam-user-role">{utilisateur.role || 'Compte actif'}</div>
            </div>
          </div>
        </div>
      </header>

      {erreur && <div className="cam-banner cam-banner-error" role="alert">{erreur}</div>}
      {info && <div className="cam-banner cam-banner-ok" role="status">{info}</div>}
      {envoi && (
        <div className="cam-banner cam-banner-loading" role="status">
          Analyse de l&apos;image en cours… la première analyse peut prendre quelques instants.
        </div>
      )}

      {!chargement && parcelles.length === 0 && !erreur && (
        <section className="cam-card">
          <p className="cam-vide">Aucune parcelle pour votre compte. Créez d&apos;abord une exploitation et une parcelle.</p>
        </section>
      )}

      {parcelles.length > 0 && (
        <>
          <div role="group" aria-label="Choix de la parcelle" className="cam-pills">
            {parcellesAffichees.map((p) => (
              <button
                key={p.id}
                type="button"
                aria-pressed={p.id === parcelleId}
                className={`cam-pill ${p.id === parcelleId ? 'active' : ''}`}
                onClick={() => choisirParcelle(p.id)}
              >
                {nomCourt(p.nom)}
              </button>
            ))}
            {parcellesAffichees.length === 0 && <span className="cam-legende">Aucune parcelle ne correspond à « {recherche} ».</span>}
          </div>

          <div className="cam-row">
            <section className="cam-card cam-col-2">
              <div className="cam-card-head">
                <h2 className="cam-card-title">Dernière image{parcelle ? ` · ${parcelle.nom}` : ''}</h2>
                {aDetections && (
                  <div role="group" aria-label="Type d'image" className="cam-segment">
                    <button type="button" aria-pressed={vue === 'detections'} className={vue === 'detections' ? 'active' : ''} onClick={() => setVue('detections')}>
                      Détections
                    </button>
                    <button type="button" aria-pressed={vue === 'originale'} className={vue === 'originale' ? 'active' : ''} onClick={() => setVue('originale')}>
                      Originale
                    </button>
                  </div>
                )}
              </div>

              {dernier ? (
                <ImageParcelle src={srcDerniere} alt={`Dernière image de la parcelle ${parcelle?.nom || ''}`} />
              ) : (
                <div className="cam-image cam-image-vide">{chargement ? 'Chargement…' : "Aucune image pour l'instant"}</div>
              )}

              <div className="cam-card-foot">
                <span className="cam-legende">
                  {dernier ? `${dateHeure(dernier.date)} · ${nombre(dernier.nb_plants)} plants détectés` : 'Chargez une image pour lancer le comptage.'}
                </span>

                <input
                  ref={champFichier}
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  onChange={surFichierChoisi}
                  hidden
                />
                <button
                  type="button"
                  className="cam-btn"
                  disabled={envoi || parcelleId == null}
                  onClick={() => champFichier.current?.click()}
                >
                  <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 16V4M7 9l5-5 5 5M5 20h14" />
                  </svg>
                  {envoi ? 'Analyse…' : 'Charger une image'}
                </button>
              </div>
            </section>

            <section className="cam-card cam-col-1 cam-col-top">
              <h2 className="cam-card-title">Comptage des plants</h2>

              <div className="cam-count">
                <div className="cam-count-val">{dernier ? nombre(dernier.nb_plants) : '–'}</div>
                <div className="cam-legende">
                  {dernier ? `plants comptés le ${dateHeure(dernier.date)}` : 'Aucun comptage enregistré'}
                </div>
              </div>

              {variation !== null && (
                <span className={`cam-badge ${variation > 0 ? 'cam-badge-ok' : variation < 0 ? 'cam-badge-warn' : 'cam-badge-info'}`}>
                  {variation > 0 ? '+' : ''}
                  {nombre(variation)} plants depuis le comptage précédent
                </span>
              )}
            </section>
          </div>

          <div className="cam-row">
            <section className="cam-card cam-col-a">
              <h2 className="cam-card-title">Évolution du comptage</h2>
              <EvolutionComptage comptages={comptages} nomParcelle={parcelle ? nomCourt(parcelle.nom) : ''} />
            </section>

            <section className="cam-card cam-col-b">
              <h2 className="cam-card-title">Comparer les images par date</h2>
              <ComparaisonDates comptages={comptages} />
            </section>
          </div>
        </>
      )}
    </div>
  )
}