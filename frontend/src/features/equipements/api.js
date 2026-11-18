// api.js (feature equipements)
// Passe par le client HTTP partagé (src/services/api.js).

import { api } from "../../services/api";

export const getEquipements = () => api("/equipements");

export const createEquipement = (data) =>
  api("/equipements", { method: "POST", body: JSON.stringify(data) });

export const updateEquipement = (id, data) =>
  api(`/equipements/${id}`, { method: "PUT", body: JSON.stringify(data) });

export const deleteEquipement = (id) =>
  api(`/equipements/${id}`, { method: "DELETE" });

// Pour remplir le menu déroulant "Parcelle associée" dans le formulaire.
export const getParcelles = () => api("/parcelles");