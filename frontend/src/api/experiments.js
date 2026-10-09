import { api } from "./client.js";

export const experimentsApi = {
  list: () => api.get("/experiments").then((r) => r.data),

  get: (slug) => api.get(`/experiments/${slug}`).then((r) => r.data),

  create: (data) => api.post("/experiments", data).then((r) => r.data),

  update: (slug, data) => api.patch(`/experiments/${slug}`, data).then((r) => r.data),

  setEvalSpec: (experimentId, data) =>
    api.post(`/experiments/${experimentId}/evaluation-spec`, data).then((r) => r.data),
};
