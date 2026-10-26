import { api } from "./client.js";

// Instructor console API. All endpoints are instructors-only and scoped to the
// instructor's own batch on the server.
const exp = (batchId, experimentId) => `/instructor/batches/${batchId}/experiments/${experimentId}`;

export const instructorApi = {
  batches: () => api.get("/instructor/batches").then((r) => r.data),

  batch: (batchId) => api.get(`/instructor/batches/${batchId}`).then((r) => r.data),

  // Published experiments (number, title) for the sidebar submenu.
  experiments: () => api.get("/instructor/experiments").then((r) => r.data),

  // Read-only experiment content with answer keys.
  experiment: (experimentId) =>
    api.get(`/instructor/experiments/${experimentId}`).then((r) => r.data),

  statusTable: (batchId, experimentId) =>
    api.get(`${exp(batchId, experimentId)}/status`).then((r) => r.data),

  exportStatus: (batchId, experimentId) =>
    api.get(`${exp(batchId, experimentId)}/status/export`, { responseType: "blob" }).then((r) => r.data),

  // Assignment section
  assignmentContent: (experimentId) =>
    api.get(`/instructor/experiments/${experimentId}/assignment`).then((r) => r.data),

  assignmentTable: (batchId, experimentId) =>
    api.get(`${exp(batchId, experimentId)}/assignment-status`).then((r) => r.data),

  exportAssignment: (batchId, experimentId) =>
    api
      .get(`${exp(batchId, experimentId)}/assignment-status/export`, { responseType: "blob" })
      .then((r) => r.data),

  submission: (batchId, experimentId, studentId) =>
    api.get(`${exp(batchId, experimentId)}/assignment-status/${studentId}`).then((r) => r.data),
};
