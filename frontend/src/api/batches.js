import { api } from "./client.js";

export const batchesApi = {
  list: () => api.get("/batches").then((r) => r.data),

  get: (id) => api.get(`/batches/${id}`).then((r) => r.data),

  create: (name, academic_year) =>
    api.post("/batches", { name, academic_year }).then((r) => r.data),

  uploadStudents: (batch_id, students) =>
    api.post(`/batches/${batch_id}/students`, { students }).then((r) => r.data),

  listStudents: (batch_id) =>
    api.get(`/batches/${batch_id}/students`).then((r) => r.data),

  assignInstructor: (batch_id, instructor_id) =>
    api.post(`/batches/${batch_id}/instructors`, { instructor_id }).then((r) => r.data),
};
