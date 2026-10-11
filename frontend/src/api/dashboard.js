import { api } from "./client.js";

export const dashboardApi = {
  student: () => api.get("/dashboards/student").then((r) => r.data),
};