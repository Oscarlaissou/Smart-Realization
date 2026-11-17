// Parcelles.jsx
// Page "Parcelles" : liste des parcelles + panneau de création/édition.
// Aucune donnée en dur : tout vient de l'API (voir ./api.js).
// Suppose que la route /equipements existe dans votre routeur (react-router)
// pour le bouton "Gérer les équipements".

import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import {
  checkHealth,
  getParcelles,
  createParcelle,
  updateParcelle,
  deleteParcelle,
  getEquipements,
  associerEquipement,
  dissocierEquipement,
} from "./api";
import "./Parcelles.css";

const FORM_VIDE = {
  nom: "",
  culture: "",
  surface: "",
  dateSemis: "",
  typeSol: "",
  equipements: [], // [{ id, code, enLigne }]
};

export default function Parcelles() {
  const [parcelles, setParcelles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [dbStatus, setDbStatus] = useState("chargement"); // 'chargement' | 'ok' | 'erreur'

  const [allEquipements, setAllEquipements] = useState([]);

  const [mode, setMode] = useState(null); // null | 'create' | 'edit'
  const [selectedId, setSelectedId] = useState(null);
  const [form, setForm] = useState(FORM_VIDE);
  const [saving, setSaving] = useState(false);

  // ---- Chargement initial ----

  const chargerParcelles = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getParcelles();
      setParcelles(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Test de connexion à la base, via le backend
    checkHealth()
      .then(() => setDbStatus("ok"))
      .catch(() => setDbStatus("erreur"));

    chargerParcelles();

    getEquipements()
      .then(setAllEquipements)
      .catch(() => {
        /* la page reste utilisable même si cette liste échoue à charger */
      });
  }, [chargerParcelles]);

  // ---- Résumé (calculé à partir des données reçues, jamais en dur) ----

  const nbParcelles = parcelles.length;
  const surfaceTotale = parcelles
    .reduce((somme, p) => somme + Number(p.surface || 0), 0)
    .toLocaleString("fr-FR", { maximumFractionDigits: 1 });
  const equipementsEnLigne = parcelles.reduce(
    (s, p) => s + (p.equipements || []).filter((e) => e.enLigne).length,
    0
  );
  const equipementsTotal = parcelles.reduce(
    (s, p) => s + (p.equipements || []).length,
    0
  );

  // ---- Sélection / panneau ----

  function ouvrirCreation() {
    setMode("create");
    setSelectedId(null);
    setForm(FORM_VIDE);
  }

  function ouvrirEdition(parcelle) {
    setMode("edit");
    setSelectedId(parcelle.id);
    setForm({
      nom: parcelle.nom,
      culture: parcelle.culture,
      surface: parcelle.surface,
      dateSemis: parcelle.dateSemis,
      typeSol: parcelle.typeSol,
      equipements: parcelle.equipements || [],
    });
  }

  function fermerPanneau() {
    setMode(null);
    setSelectedId(null);
    setForm(FORM_VIDE);
  }

  function majChamp(champ, valeur) {
    setForm((f) => ({ ...f, [champ]: valeur }));
  }

  // ---- Équipements associés (dans le panneau) ----

  const equipementsDisponibles = allEquipements.filter(
    (eq) => !form.equipements.some((assoc) => assoc.id === eq.id)
  );

  async function ajouterEquipement(e) {
    const equipementId = e.target.value;
    if (!equipementId) return;
    const equip = allEquipements.find((eq) => String(eq.id) === equipementId);
    if (!equip) return;

    if (mode === "edit" && selectedId) {
      try {
        await associerEquipement(selectedId, equip.id);
      } catch (err) {
        setError(err.message);
        return;
      }
    }
    setForm((f) => ({ ...f, equipements: [...f.equipements, equip] }));
    e.target.value = "";
  }

  async function retirerEquipement(equip) {
    if (mode === "edit" && selectedId) {
      try {
        await dissocierEquipement(selectedId, equip.id);
      } catch (err) {
        setError(err.message);
        return;
      }
    }
    setForm((f) => ({
      ...f,
      equipements: f.equipements.filter((eq) => eq.id !== equip.id),
    }));
  }

  // ---- Enregistrer / Supprimer une parcelle ----

  async function enregistrer() {
    setSaving(true);
    setError(null);
    try {
      if (mode === "create") {
        await createParcelle(form);
      } else if (mode === "edit" && selectedId) {
        await updateParcelle(selectedId, form);
      }
      await chargerParcelles();
      fermerPanneau();
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  async function supprimer(id) {
    if (!window.confirm("Supprimer définitivement cette parcelle ?")) return;
    setError(null);
    try {
      await deleteParcelle(id);
      if (selectedId === id) fermerPanneau();
      await chargerParcelles();
    } catch (e) {
      setError(e.message);
    }
  }

  // ---- Rendu ----

  return (
    <div style={{ padding: "0 40px 40px", display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Indicateur de connexion à la base, pour vérifier le branchement API <-> MySQL */}
      <span className={`conn-banner conn-${dbStatus}`}>
        {dbStatus === "chargement" && "Vérification de la connexion à la base…"}
        {dbStatus === "ok" && "✓ Connecté à la base de données"}
        {dbStatus === "erreur" && "✗ Impossible de joindre l'API / la base de données"}
      </span>

      {error && (
        <div className="conn-banner conn-erreur">Erreur : {error}</div>
      )}

      {/* Cartes résumé */}
      <section
        aria-label="Résumé"
        style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))", gap: 20 }}
      >
        <CarteResume label="Parcelles" valeur={nbParcelles} />
        <CarteResume label="Surface totale" valeur={surfaceTotale} unite="ha" />
        <CarteResume
          label="Équipements en ligne"
          valeur={equipementsEnLigne}
          unite={`sur ${equipementsTotal}`}
        />
      </section>

      <div style={{ display: "flex", flexWrap: "wrap", gap: 20 }}>
        {/* Liste des parcelles */}
        <section
          style={{
            flex: "3 1 520px",
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
            <h2 style={{ margin: 0, fontSize: 20 }}>Liste des parcelles</h2>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              {/* À adapter : /equipements doit correspondre à la route de votre page Équipements */}
              <Link to="/equipements" className="btn btn-secondary" style={{ display: "inline-flex", alignItems: "center", textDecoration: "none" }}>
                Gérer les équipements
              </Link>
              <button className="btn btn-primary" onClick={ouvrirCreation}>
                Nouvelle parcelle
              </button>
            </div>
          </div>

          {loading ? (
            <p>Chargement des parcelles…</p>
          ) : parcelles.length === 0 ? (
            <p>Aucune parcelle enregistrée pour le moment.</p>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", minWidth: 560, borderCollapse: "collapse", fontSize: 14 }}>
                <thead>
                  <tr style={{ textAlign: "left", color: "#5B6B63", fontSize: 13 }}>
                    <th style={{ padding: "10px 12px", borderBottom: "1px solid #E3E9E4" }}>Parcelle</th>
                    <th style={{ padding: "10px 12px", borderBottom: "1px solid #E3E9E4" }}>Surface</th>
                    <th style={{ padding: "10px 12px", borderBottom: "1px solid #E3E9E4" }}>Date de semis</th>
                    <th style={{ padding: "10px 12px", borderBottom: "1px solid #E3E9E4" }}>Type de sol</th>
                    <th style={{ padding: "10px 12px", borderBottom: "1px solid #E3E9E4" }}>Équipements</th>
                    <th style={{ padding: "10px 12px", borderBottom: "1px solid #E3E9E4" }} />
                  </tr>
                </thead>
                <tbody>
                  {parcelles.map((p) => {
                    const total = (p.equipements || []).length;
                    const enLigne = (p.equipements || []).filter((e) => e.enLigne).length;
                    const complet = total > 0 && enLigne === total;
                    return (
                      <tr key={p.id} className="parcelles-row">
                        <td style={{ padding: "14px 8px", fontWeight: 600 }}>
                          {p.nom}
                          <span style={{ display: "block", fontWeight: 400, fontSize: 13, color: "#5B6B63" }}>
                            {p.culture}
                          </span>
                        </td>
                        <td style={{ padding: "14px 8px" }}>{p.surface} ha</td>
                        <td style={{ padding: "14px 8px" }}>{p.dateSemis}</td>
                        <td style={{ padding: "14px 8px" }}>{p.typeSol}</td>
                        <td style={{ padding: "14px 8px" }}>
                          <span className={`badge ${complet ? "badge-ok" : "badge-warn"}`}>
                            {enLigne}/{total} en ligne
                          </span>
                        </td>
                        <td style={{ padding: "14px 8px", textAlign: "right", whiteSpace: "nowrap" }}>
                          <button className="btn-link" onClick={() => ouvrirEdition(p)}>
                            Modifier
                          </button>
                          <button
                            className="btn-link"
                            style={{ color: "#9A2C1E", marginLeft: 14 }}
                            onClick={() => supprimer(p.id)}
                          >
                            Supprimer
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* Panneau création / édition — ne s'affiche que si on a cliqué sur un bouton */}
        {mode && (
          <section
            style={{
              flex: "2 1 320px",
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
            <div>
              <h2 style={{ margin: 0, fontSize: 20 }}>
                {mode === "create" ? "Nouvelle parcelle" : `Modifier la parcelle ${form.nom}`}
              </h2>
              <p style={{ margin: "4px 0 0", fontSize: 13, color: "#5B6B63" }}>
                Ces informations servent aux recommandations d'engrais et aux prévisions.
              </p>
            </div>

            <form
              style={{ display: "flex", flexDirection: "column", gap: 16 }}
              onSubmit={(e) => {
                e.preventDefault();
                enregistrer();
              }}
            >
              <div className="field">
                <label htmlFor="p-nom">Nom de la parcelle</label>
                <input
                  id="p-nom"
                  value={form.nom}
                  onChange={(e) => majChamp("nom", e.target.value)}
                  required
                />
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 16 }}>
                <div className="field">
                  <label htmlFor="p-culture">Culture</label>
                  <select
                    id="p-culture"
                    value={form.culture}
                    onChange={(e) => majChamp("culture", e.target.value)}
                  >
                    <option value="">—</option>
                    <option>Maïs</option>
                    <option>Tomate</option>
                    <option>Manioc</option>
                    <option>Plantain</option>
                  </select>
                </div>
                <div className="field">
                  <label htmlFor="p-surface">Surface (ha)</label>
                  <input
                    id="p-surface"
                    type="number"
                    step="0.1"
                    value={form.surface}
                    onChange={(e) => majChamp("surface", e.target.value)}
                    required
                  />
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 16 }}>
                <div className="field">
                  <label htmlFor="p-date">Date de semis</label>
                  <input
                    id="p-date"
                    type="date"
                    value={form.dateSemis}
                    onChange={(e) => majChamp("dateSemis", e.target.value)}
                  />
                </div>
                <div className="field">
                  <label htmlFor="p-sol">Type de sol</label>
                  <select
                    id="p-sol"
                    value={form.typeSol}
                    onChange={(e) => majChamp("typeSol", e.target.value)}
                  >
                    <option value="">—</option>
                    <option>Limono-argileux</option>
                    <option>Sableux</option>
                    <option>Argileux</option>
                  </select>
                </div>
              </div>

              <div>
                <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 8 }}>
                  Équipements associés
                </div>
                <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexWrap: "wrap", gap: 8 }}>
                  {form.equipements.map((eq) => (
                    <li key={eq.id} className="equip-chip">
                      <span className={`dot ${eq.enLigne ? "" : "offline"}`} />
                      {eq.code} · {eq.enLigne ? "En ligne" : "Hors ligne"}
                      <button
                        type="button"
                        className="remove"
                        aria-label={`Retirer ${eq.code}`}
                        onClick={() => retirerEquipement(eq)}
                      >
                        ×
                      </button>
                    </li>
                  ))}
                </ul>

                {equipementsDisponibles.length > 0 && (
                  <select
                    style={{ marginTop: 10, height: 42, borderRadius: 10, border: "1px solid #D5DED7", padding: "0 10px", width: "100%" }}
                    defaultValue=""
                    onChange={ajouterEquipement}
                  >
                    <option value="" disabled>
                      + Associer un équipement…
                    </option>
                    {equipementsDisponibles.map((eq) => (
                      <option key={eq.id} value={eq.id}>
                        {eq.code} ({eq.type})
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: 10, paddingTop: 4 }}>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? "Enregistrement…" : mode === "create" ? "Créer la parcelle" : "Enregistrer les modifications"}
                </button>
                {mode === "edit" && (
                  <button type="button" className="btn btn-danger" onClick={() => supprimer(selectedId)}>
                    Supprimer la parcelle
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
