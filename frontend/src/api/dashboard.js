import { api } from "./client.js";

export const dashboardApi = {
  student: () => api.get("/dashboards/student").then((r) => r.data),

  instructor: (batch_id) =>
    api.get("/dashboards/instructor", { params: { batch_id } }).then((r) => r.data),

  exportCsv: (batch_id) =>
    api.get("/dashboards/instructor/export", {
      params: { batch_id },
      responseType: "blob",
    }).then((r) => r.data),
};
