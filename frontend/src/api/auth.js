import { api } from "./client.js";

export const authApi = {
  login: (email, password) =>
    api.post("/auth/login", { email, password }).then((r) => r.data),

  me: () => api.get("/auth/me").then((r) => r.data),

  changePassword: (current_password, new_password) =>
    api.post("/auth/change-password", { current_password, new_password }).then((r) => r.data),

  createInstructor: (full_name, email, password) =>
    api.post("/auth/instructors", { full_name, email, password }).then((r) => r.data),

  listUsers: () => api.get("/auth/users").then((r) => r.data),
};
