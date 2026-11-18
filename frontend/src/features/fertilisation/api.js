// api.js (feature fertilisation)
import { api } from "../../services/api";

export const getParcelles = () => api("/parcelles");

export const getDernieresDonnees = (parcelleId) => api(`/fertilisation/donnees/${parcelleId}`);

export const saisirDonnees = (data) =>
  api("/fertilisation/donnees", { method: "POST", body: JSON.stringify(data) });

export const getDose = (parcelleId) => api(`/fertilisation/dose/${parcelleId}`);

export const getApports = (parcelleId, realise) => {
  const params = new URLSearchParams();
  if (realise !== undefined) params.set("realise", realise);
  const qs = params.toString() ? `?${params.toString()}` : "";
  return api(`/fertilisation/apports${qs}`).then((tous) =>
    parcelleId ? tous.filter((a) => a.parcelle_id === parcelleId) : tous
  );
};

export const creerApport = (data) =>
  api("/fertilisation/apports", { method: "POST", body: JSON.stringify(data) });