// Equipements.jsx
// Page "Équipements" : liste des capteurs/électrovannes/caméras + formulaire
// d'ajout/modification. Aucune donnée en dur : tout vient de l'API.
//
// Remarque : le champ "Clé d'authentification" du maquette n'est pas repris
// ici, car rien côté backend ne le stocke pour l'instant (pas de colonne
// pour ça). À ajouter plus tard si besoin, de la même façon qu'on a ajouté
// "derniere_donnee".

import { useEffect, useState, useCallback } from "react";
import {
  getEquipements,
  createEquipement,
  updateEquipement,
  deleteEquipement,
  getParcelles,
} from "./api";
import "../../styles/gestion.css";

const TYPES = [
  { valeur: "capteur", label: "Capteur" },
  { valeur: "electrovanne", label: "Électrovanne" },
  { valeur: "camera", label: "Caméra" },
];

function libelleType(type) {
  return TYPES.find((t) => t.valeur === type)?.label || type;
}

function depuis(dateIso) {
  if (!dateIso) return "—";
  const secondes = Math.max(0, Math.floor((Date.now() - new Date(dateIso + "Z")) / 1000));
  if (secondes < 60) return `il y a ${secondes}s`;
  const minutes = Math.floor(secondes / 60);
  if (minutes < 60) return `il y a ${minutes} min`;
  const heures = Math.floor(minutes / 60);
  return `il y a ${heures} h`;
}

const FORM_VIDE = { code: "", type: "capteur", parcelle_id: "" };

export default function Equipements() {
  const [equipements, setEquipements] = useState([]);
  const [parcelles, setParcelles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filtre, setFiltre] = useState("tous");

  const [mode, setMode] = useState(null); // null | 'create' | 'edit'
  const [selectedId, setSelectedId] = useState(null);
  const [form, setForm] = useState(FORM_VIDE);
  const [saving, setSaving] = useState(false);

  const charger = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [eqs, pcs] = await Promise.all([getEquipements(), getParcelles()]);
      setEquipements(eqs);
      setParcelles(pcs);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    charger();
    // Rafraîchit "il y a Xs" régulièrement sans recharger l'API.
    const id = setInterval(() => setEquipements((e) => [...e]), 5000);
    return () => clearInterval(id);
  }, [charger]);

  const nomParcelle = (id) => {
    const p = parcelles.find((p) => p.id === id);
    return p ? `${p.nom} (ID ${p.id})` : "—";
  };

  const listeFiltree =
    filtre === "tous" ? equipements : equipements.filter((e) => e.type === filtre);

  const nbTotal = equipements.length;
  const nbEnLigne = equipements.filter((e) => e.en_ligne).length;
  const nbHorsService = nbTotal - nbEnLigne;

  function ouvrirCreation() {
    setMode("create");
    setSelectedId(null);
    setForm(FORM_VIDE);
  }

  function ouvrirEdition(eq) {
    setMode("edit");
    setSelectedId(eq.id);
    setForm({ code: eq.code, type: eq.type, parcelle_id: eq.parcelle_id ?? "" });
  }

  function fermerPanneau() {
    setMode(null);
    setSelectedId(null);
    setForm(FORM_VIDE);
  }

  function majChamp(champ, valeur) {
    setForm((f) => ({ ...f, [champ]: valeur }));
  }

  async function enregistrer() {
    setSaving(true);
    setError(null);
    const payload = {
      code: form.code,
      type: form.type,
      parcelle_id: form.parcelle_id === "" ? null : Number(form.parcelle_id),
    };
    try {
      if (mode === "create") {
        await createEquipement(payload);
      } else if (mode === "edit" && selectedId) {
        await updateEquipement(selectedId, payload);
      }
      await charger();
      fermerPanneau();
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  async function supprimer(id) {
    if (!window.confirm("Supprimer définitivement cet équipement ?")) return;
    setError(null);
    try {
      await deleteEquipement(id);
      if (selectedId === id) fermerPanneau();
      await charger();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div style={{ padding: "0 40px 40px", display: "flex", flexDirection: "column", gap: 20 }}>
      {error && <div className="conn-banner conn-erreur">Erreur : {error}</div>}

      <section
        aria-label="Résumé"
        style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 20 }}
      >
        <CarteResume label="Équipements" valeur={nbTotal} />
        <CarteResume label="En ligne" valeur={nbEnLigne} unite={`sur ${nbTotal}`} />
        <CarteResume label="Hors service" valeur={nbHorsService} />
      </section>

      <div style={{ display: "flex", flexWrap: "wrap", gap: 20 }}>
        <section
          style={{
            flex: "3 1 560px",
            minWidth: 0,
            background: "#FFFFFF",
            border: "1px solid #E3E9E4",
            borderRadius: 16,
            padding: 24,
            display: "flex",
            flexDirection: "column",
            gap: 18,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
            <h2 style={{ margin: 0, fontSize: 20 }}>Liste des équipements</h2>
            <button className="btn btn-primary" onClick={ouvrirCreation}>
              Ajouter un équipement
            </button>
          </div>

          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {["tous", ...TYPES.map((t) => t.valeur)].map((v) => (
              <button
                key={v}
                className="btn-link"
                style={{
                  padding: "6px 12px",
                  borderRadius: 999,
                  background: filtre === v ? "#0F2A1E" : "#F2F5F2",
                  color: filtre === v ? "#fff" : "#1B2B20",
                }}
                onClick={() => setFiltre(v)}
              >
                {v === "tous" ? "Tous" : libelleType(v)} (
                {v === "tous" ? equipements.length : equipements.filter((e) => e.type === v).length}
                )
              </button>
            ))}
          </div>

          {loading ? (
            <p>Chargement des équipements…</p>
          ) : listeFiltree.length === 0 ? (
            <p>Aucun équipement enregistré pour le moment.</p>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", minWidth: 560, borderCollapse: "collapse", fontSize: 14 }}>
                <thead>
                  <tr style={{ textAlign: "left", color: "#5B6B63", fontSize: 13 }}>
                    <th style={{ padding: "10px 12px", borderBottom: "1px solid #E3E9E4" }}>Identifiant</th>
                    <th style={{ padding: "10px 12px", borderBottom: "1px solid #E3E9E4" }}>Type</th>
                    <th style={{ padding: "10px 12px", borderBottom: "1px solid #E3E9E4" }}>Parcelle</th>
                    <th style={{ padding: "10px 12px", borderBottom: "1px solid #E3E9E4" }}>État</th>
                    <th style={{ padding: "10px 12px", borderBottom: "1px solid #E3E9E4" }}>Dernière donnée</th>
                    <th style={{ padding: "10px 12px", borderBottom: "1px solid #E3E9E4" }} />
                  </tr>
                </thead>
                <tbody>
                  {listeFiltree.map((eq) => (
                    <tr key={eq.id}>
                      <td style={{ padding: "14px 8px", fontWeight: 600 }}>{eq.code}</td>
                      <td style={{ padding: "14px 8px" }}>{libelleType(eq.type)}</td>
                      <td style={{ padding: "14px 8px" }}>{nomParcelle(eq.parcelle_id)}</td>
                      <td style={{ padding: "14px 8px" }}>
                        <span className={`badge ${eq.en_ligne ? "badge-ok" : "badge-warn"}`}>
                          {eq.en_ligne ? "En ligne" : "Hors service"}
                        </span>
                      </td>
                      <td style={{ padding: "14px 8px" }}>
                        {eq.type === "capteur" ? depuis(eq.derniere_donnee) : "—"}
                      </td>
                      <td style={{ padding: "14px 8px", textAlign: "right", whiteSpace: "nowrap" }}>
                        <button className="btn-link" onClick={() => ouvrirEdition(eq)}>
                          Modifier
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {mode && (
          <section
            style={{
              flex: "2 1 300px",
              minWidth: 0,
              background: "#FFFFFF",
              border: "1px solid #E3E9E4",
              borderRadius: 16,
              padding: 24,
              display: "flex",
              flexDirection: "column",
              gap: 20,
              alignSelf: "flex-start",
            }}
          >
            <h2 style={{ margin: 0, fontSize: 20 }}>
              {mode === "create" ? "Ajouter un équipement" : `Modifier ${form.code}`}
            </h2>

            <form
              style={{ display: "flex", flexDirection: "column", gap: 16 }}
              onSubmit={(e) => {
                e.preventDefault();
                enregistrer();
              }}
            >
              <div className="field">
                <label htmlFor="e-type">Type</label>
                <select id="e-type" value={form.type} onChange={(e) => majChamp("type", e.target.value)}>
                  {TYPES.map((t) => (
                    <option key={t.valeur} value={t.valeur}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="field">
                <label htmlFor="e-code">Identifiant</label>
                <input
                  id="e-code"
                  value={form.code}
                  onChange={(e) => majChamp("code", e.target.value)}
                  placeholder="ex : C-13"
                  required
                />
              </div>

              <div className="field">
                <label htmlFor="e-parcelle">Parcelle associée</label>
                <select
                  id="e-parcelle"
                  value={form.parcelle_id}
                  onChange={(e) => majChamp("parcelle_id", e.target.value)}
                >
                  <option value="">Aucune</option>
                  {parcelles.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.nom} (ID {p.id})
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: 10, paddingTop: 4 }}>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? "Enregistrement…" : mode === "create" ? "Enregistrer l'équipement" : "Enregistrer les modifications"}
                </button>
                {mode === "edit" && (
                  <button type="button" className="btn btn-danger" onClick={() => supprimer(selectedId)}>
                    Supprimer l'équipement
                  </button>
                )}
                <button type="button" className="btn-link" style={{ alignSelf: "center" }} onClick={fermerPanneau}>
                  Annuler
                </button>
              </div>
            </form>
          </section>
        )}
      </div>
    </div>
  );
}

function CarteResume({ label, valeur, unite }) {
  return (
    <div
      style={{
        background: "#FFFFFF",
        border: "1px solid #E3E9E4",
        borderRadius: 16,
        padding: 22,
        display: "flex",
        flexDirection: "column",
        gap: 10,
      }}
    >
      <span style={{ fontSize: 14, color: "#5B6B63", fontWeight: 500 }}>{label}</span>
      <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
        <span style={{ fontSize: 34, fontWeight: 700 }}>{valeur}</span>
        {unite && <span style={{ fontSize: 14, color: "#5B6B63" }}>{unite}</span>}
      </div>
    </div>
  );
}