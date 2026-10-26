// Assignment scores are stored as a percentage (0-100).
export function formatScore(score) {
  return `${Number(Number(score).toFixed(2))}%`;
}
