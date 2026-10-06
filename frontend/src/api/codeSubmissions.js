import { api } from "./client.js";

export const codeSubmissionsApi = {
  submit: (experiment_id, submitted_code, client_output, client_error) =>
    api
      .post("/code_submissions", {
        experiment_id,
        submitted_code,
        client_output: client_output ?? null,
        client_error: client_error ?? null,
      })
      .then((r) => r.data),

  list: (experiment_id) =>
    api.get("/code_submissions", { params: { experiment_id } }).then((r) => r.data),
};
