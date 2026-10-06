import { api } from "./client.js";

export const quizzesApi = {
  get: (quizId) => api.get(`/quizzes/${quizId}`).then((r) => r.data),

  submit: (quizId, answers) =>
    api.post(`/quizzes/${quizId}/submit`, { answers }).then((r) => r.data),

  create: (experimentId, data) =>
    api.post(`/experiments/${experimentId}/quizzes`, data).then((r) => r.data),
};
