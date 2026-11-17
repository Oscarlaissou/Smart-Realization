// api.js (feature parcelles)
// Passe par le client HTTP partagé (src/services/api.js), qui gère déjà
// la base URL et le token d'authentification (Bearer) automatiquement.

import { api } from "../../services/api";

export const checkHealth = () => api("/health");

export const getParcelles = () => api("/parcelles");
export const getParcelle = (id) => api(`/parcelles/${id}`);

export const createParcelle = (data) =>
  api("/parcelles", { method: "POST", body: JSON.stringify(data) });

export const updateParcelle = (id, data) =>
  api(`/parcelles/${id}`, { method: "PUT", body: JSON.stringify(data) });

export const deleteParcelle = (id) =>
  api(`/parcelles/${id}`, { method: "DELETE" });

export const getEquipements = () => api("/equipements");

export const associerEquipement = (parcelleId, equipementId) =>
  api(`/parcelles/${parcelleId}/equipements`, {
    method: "POST",
    body: JSON.stringify({ equipementId }),
  });

export const dissocierEquipement = (parcelleId, equipementId) =>
  api(`/parcelles/${parcelleId}/equipements/${equipementId}`, {
    method: "DELETE",
  });