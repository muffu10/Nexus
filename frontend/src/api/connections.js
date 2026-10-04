import api from "./client";

export async function getConnections() {
  const response = await api.get("/connections");
  return response.data;
}

export async function getConnectionSchema(connectionId) {
  const response = await api.get(
    `/connections/${connectionId}/schema`
  );
  return response.data;
}

export async function getConnectionSamples(connectionId) {
  const response = await api.get(
    `/connections/${connectionId}/samples`
  );
  return response.data;
}

export async function getMappingSuggestions(connectionId) {
  const response = await api.get(
    `/connections/${connectionId}/mapping-suggestions`
  );
  return response.data;
}

export async function approveMapping(suggestionId) {
  const response = await api.post(
    `/mapping-suggestions/${suggestionId}/approve`
  );
  return response.data;
}

export async function getSyncHistory(connectionId) {
  const response = await api.get(
    `/connections/${connectionId}/sync-runs`
  );
  return response.data;
}

export async function runSync(connectionId) {
  const response = await api.post(
    `/connections/${connectionId}/sync`
  );
  return response.data;
}

export async function testConnection(data) {
  const response = await api.post(
    "/connections/test",
    data
  );

  return response.data;
}