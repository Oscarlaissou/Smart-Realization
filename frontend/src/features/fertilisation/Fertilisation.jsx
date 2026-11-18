// Fertilisation.jsx
// Page "Fertilisation" : dose recommandée par culture (produits courants,
// quantité déjà calculée), historique des apports, apports à venir.
// Aucune donnée en dur : tout vient de l'API.
//
// Retiré par rapport à la maquette initiale (pas de vraie source derrière) :
// - l'ajustement "Météo"
// - le calendrier avec des dates déjà pré-remplies
// - "Importer une analyse (CSV)"
// - le champ "Stade de croissance"
// - la saisie manuelle d'analyse de sol (inutilisée pour l'instant)

import { useEffect, useState, useCallback } from "react";
import { getParcelles, getDose, getApports, creerApport } from "./api";
import "../../styles/gestion.css";

const APPORT_VIDE = { engrais: "", dose_kg_ha: "", date: "", realise: true };

export default function Fertilisation() {
  const [parcelles, setParcelles] = useState([]);
  const [parcelleId, setParcelleId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [dose, setDose] = useState(null);

  const [apportsRealises, setApportsRealises] = useState([]);
  const [apportsPrevus, setApportsPrevus] = useState([]);
  const [formApport, setFormApport] = useState(APPORT_VIDE);
  const [savingApport, setSavingApport] = useState(false);

  // ---- Chargement des parcelles ----
  useEffect(() => {
    getParcelles()
      .then((data) => {
        setParcelles(data);
        if (data.length > 0) setParcelleId(data[0].id);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  // ---- Chargement des données de la parcelle sélectionnée ----
  const chargerParcelle = useCallback(async (pid) => {
    if (!pid) return;
    setError(null);
    try {
      const [d, realises, prevus] = await Promise.all([
        getDose(pid),
        getApports(pid, true),
        getApports(pid, false),
      ]);
      setDose(d);
      setApportsRealises(realises);
      setApportsPrevus(prevus);
    } catch (e) {
      setError(e.message);
    }
  }, []);

  useEffect(() => {
    chargerParcelle(parcelleId);
  }, [parcelleId, chargerParcelle]);

  async function enregistrerApport(e) {
    e.preventDefault();
    setSavingApport(true);
    setError(null);
    try {
      await creerApport({
        parcelle_id: parcelleId,
        engrais: formApport.engrais,
        dose_kg_ha: Number(formApport.dose_kg_ha),
        date: formApport.date ? new Date(formApport.date).toISOString() : null,
        realise: formApport.realise,
      });
      setFormApport(APPORT_VIDE);
      await chargerParcelle(parcelleId);
    } catch (e) {
      setError(e.message);
    } finally {
      setSavingApport(false);
    }
  }

  if (loading) return <div style={{ padding: 40 }}>Chargement…</div>;

  return (
    <div style={{ padding: "0 40px 40px", display: "flex", flexDirection: "column", gap: 20 }}>
      {error && <div className="conn-banner conn-erreur">Erreur : {error}</div>}

      {parcelles.length === 0 ? (
        <p>Aucune parcelle enregistrée. Créez d'abord une parcelle.</p>
      ) : (
        <>
          <div role="group" aria-label="Choix de la parcelle" style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {parcelles.map((p) => (
              <button
                key={p.id}
                aria-pressed={p.id === parcelleId}
                className="btn-link"
                style={{
                  height: 40,
                  padding: "0 16px",
                  borderRadius: 999,
                  fontWeight: 600,
                  border: p.id === parcelleId ? "1px solid #12201A" : "1px solid #D5DED7",
                  background: p.id === parcelleId ? "#12201A" : "#FFFFFF",
                  color: p.id === parcelleId ? "#fff" : "#3C4A43",
                }}
                onClick={() => setParcelleId(p.id)}
              >
                {p.nom}
              </button>
            ))}
          </div>

          <div style={{ display: "flex", flexWrap: "wrap", gap: 20 }}>
            {/* Dose recommandée */}
            <section style={{ ...carteStyle, flex: "1 1 100%" }}>
              <h2 style={titreStyle}>Dose recommandée</h2>
              {dose && (
                <>
                  <div style={{ fontSize: 13, color: "#5B6B63" }}>
                    Culture : <strong>{dose.culture || "non renseignée"}</strong> · Surface : <strong>{dose.surface_ha} ha</strong>
                  </div>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
                    <thead>
                      <tr style={{ textAlign: "left", color: "#5B6B63", fontSize: 13 }}>
                        <th style={thStyle}>Type d'engrais</th>
                        <th style={thStyle}>Composition</th>
                        <th style={thStyle}>Par hectare</th>
                        <th style={thStyle}>Pour la parcelle</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(dose.produits_suggeres || []).map((p) => (
                        <tr key={p.nom}>
                          <td style={{ ...tdStyle, fontWeight: 600 }}>{p.nom}</td>
                          <td style={tdStyle}>{p.composition}</td>
                          <td style={tdStyle}>{p.quantite_kg_ha} kg/ha</td>
                          <td style={tdStyle}>{p.quantite_totale_kg} kg</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </>
              )}
            </section>
          </div>

          <div style={{ display: "flex", flexWrap: "wrap", gap: 20 }}>
            {/* Apports réalisés + formulaire */}
            <section style={{ ...carteStyle, flex: "2 1 440px" }}>
              <h2 style={titreStyle}>Apports</h2>

              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", minWidth: 380, borderCollapse: "collapse", fontSize: 14 }}>
                  <thead>
                    <tr style={{ textAlign: "left", color: "#5B6B63", fontSize: 13 }}>
                      <th style={thStyle}>Date</th>
                      <th style={thStyle}>Engrais</th>
                      <th style={thStyle}>Quantité</th>
                    </tr>
                  </thead>
                  <tbody>
                    {apportsRealises.length === 0 ? (
                      <tr><td colSpan={3} style={{ padding: 14 }}>Aucun apport réalisé pour l'instant.</td></tr>
                    ) : (
                      apportsRealises.map((a) => (
                        <tr key={a.id}>
                          <td style={tdStyle}>{new Date(a.date).toLocaleDateString("fr-FR")}</td>
                          <td style={tdStyle}>{a.engrais}</td>
                          <td style={tdStyle}>{a.dose_kg_ha} kg/ha</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              <form
                style={{ borderTop: "1px solid #E8EEE9", paddingTop: 18, display: "flex", flexDirection: "column", gap: 14 }}
                onSubmit={enregistrerApport}
              >
                <div style={{ fontSize: 14, fontWeight: 600 }}>Enregistrer un apport</div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 16 }}>
                  <div className="field">
                    <label htmlFor="f-date">Date</label>
                    <input id="f-date" type="date" value={formApport.date} onChange={(e) => setFormApport((f) => ({ ...f, date: e.target.value }))} required />
                  </div>
                  <div className="field">
                    <label htmlFor="f-eng">Engrais</label>
                    <input id="f-eng" value={formApport.engrais} onChange={(e) => setFormApport((f) => ({ ...f, engrais: e.target.value }))} placeholder="ex : NPK 15-15-15" required />
                  </div>
                  <ChampNombre label="Quantité (kg/ha)" value={formApport.dose_kg_ha} onChange={(v) => setFormApport((f) => ({ ...f, dose_kg_ha: v }))} />
                </div>
                <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 14 }}>
                  <input
                    type="checkbox"
                    checked={formApport.realise}
                    onChange={(e) => setFormApport((f) => ({ ...f, realise: e.target.checked }))}
                  />
                  Déjà réalisé (sinon, enregistré comme prévu/à venir)
                </label>
                <button type="submit" className="btn btn-primary" disabled={savingApport} style={{ alignSelf: "flex-start" }}>
                  {savingApport ? "Enregistrement…" : "Enregistrer l'apport"}
                </button>
              </form>
            </section>

            {/* Apports à venir */}
            <section style={{ ...carteStyle, flex: "1 1 280px", alignSelf: "flex-start" }}>
              <h2 style={titreStyle}>À venir</h2>
              {apportsPrevus.length === 0 ? (
                <p style={{ fontSize: 14, color: "#5B6B63" }}>Aucun apport prévu pour l'instant.</p>
              ) : (
                <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 10 }}>
                  {apportsPrevus.map((a) => (
                    <li key={a.id} style={{ fontSize: 14, display: "flex", justifyContent: "space-between", gap: 10 }}>
                      <span>{a.engrais} · {a.dose_kg_ha} kg/ha</span>
                      <span style={{ color: "#5B6B63" }}>{new Date(a.date).toLocaleDateString("fr-FR")}</span>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        </>
      )}
    </div>
  );
}

const carteStyle = {
  flex: "1 1 420px",
  minWidth: 0,
  background: "#FFFFFF",
  border: "1px solid #E3E9E4",
  borderRadius: 16,
  padding: 24,
  display: "flex",
  flexDirection: "column",
  gap: 16,
};
const titreStyle = { margin: 0, fontSize: 20 };
const thStyle = { padding: "10px 8px", borderBottom: "1px solid #E3E9E4", fontWeight: 500 };
const tdStyle = { padding: "12px 8px", borderBottom: "1px solid #EEF3EF" };

function ChampNombre({ label, value, onChange, step }) {
  return (
    <div className="field">
      <label>{label}</label>
      <input type="number" step={step || "1"} value={value} onChange={(e) => onChange(e.target.value)} />
    </div>
  );
}